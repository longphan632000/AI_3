from services.ai_config import resolve_ai_setting
from services.ai_errors import AIProviderError
from services.openai_service import OpenAIService
from services.gemini_service import GeminiService
from services.ai_deadline import phase_budget, remaining_timeout
from services.local_brain_service import LocalBrainService, _PASSAGES
from services.local_model_service import LocalModelService, setting_bool, setting_int
import json
import logging
import threading

LOGGER = logging.getLogger(__name__)


class AIProviderService:
    """
    Prefer the selected cloud API, then the local model and domain brain.
    """
    def __init__(self, provider_name=None):
        if provider_name is None:
            configured_provider = resolve_ai_setting('AI_PROVIDER', 'gemini')[0].lower()
        else:
            configured_provider = provider_name.strip().lower()

        if configured_provider not in ('gemini', 'deepseek', 'openai'):
            raise AIProviderError('AI_PROVIDER phải là gemini hoặc deepseek.', 'AI_CONFIG')
        self.primary_provider_name = 'gemini' if configured_provider == 'gemini' else 'deepseek'
        self.provider_name = self.primary_provider_name
        self.fallback_enabled = setting_bool('AI_LOCAL_FALLBACK_ENABLED')
        self.api_budget = setting_int('AI_PRIMARY_BUDGET_SECONDS', 30, 1, 120)
        self.local_model = LocalModelService() if self.fallback_enabled else None
        self.local_brain = LocalBrainService()
        self._lock = threading.Lock()
        self._primary_failed = threading.Event()
        self._model_failed = threading.Event()
        self._used = set()
        self._failures = set()
        self.primary_error = None
        try:
            self.provider = GeminiService() if self.primary_provider_name == 'gemini' else OpenAIService()
        except AIProviderError as error:
            if not self.fallback_enabled:
                raise
            self.provider = None
            self.primary_error = error

    def bind_context(self, request, data):
        self.local_brain = LocalBrainService(request, data)

    def record_verified_ranking(self):
        self._record('local_rules')

    def _record(self, engine):
        with self._lock:
            self._used.add(engine)
            self.provider_name = '+'.join(sorted(self._used))

    def _failure(self, error):
        with self._lock:
            self._failures.add(error.code)
        LOGGER.warning('AI fallback reason=%s', error.code)

    def execution_metadata(self):
        with self._lock:
            engines = sorted(self._used)
            codes = sorted(self._failures)
        local_used = any(name.startswith('local_') for name in engines)
        labels = {'gemini': 'Gemini API', 'deepseek': 'DeepSeek API', 'local_llm': 'mô hình Qwen3 chạy tại máy',
                  'local_rules': 'bộ xử lý nghiệp vụ cục bộ'}
        return {
            'primary': self.primary_provider_name, 'used_providers': engines, 'fallback_used': local_used,
            'failure_codes': codes,
            'notice': 'Nguồn xử lý: ' + ', '.join(labels[name] for name in engines) + '.',
        }

    def fallback_status(self, probe=False):
        model = self.local_model
        return {'enabled': self.fallback_enabled, 'domain_brain_ready': self.fallback_enabled,
                'model_enabled': bool(model and model.enabled),
                'model_installed': bool(model and model.installed),
                'model_reachable': model.reachable() if model and probe else None,
                'model_name': 'Qwen3-1.7B-Q8_0',
                'policy': 'api_then_local_model_then_domain_brain'}

    def _validate_primary(self, content, json_output):
        if self.local_brain.request.get('staffing_v2'):
            # Staffing IDs are checked against eligibility/count and rendered from
            # verified facts by the coordinator, before any draft is persisted.
            return content
        if not self.fallback_enabled:
            return content
        if json_output and _PASSAGES.get() is not None:
            try:
                data = json.loads(content.strip().removeprefix('```json').removesuffix('```').strip())
                rows = data['items']
                ids = [row[0] if isinstance(row, list) else row['id'] for row in rows]
                if any(isinstance(identifier, bool) or not isinstance(identifier, int) for identifier in ids):
                    raise ValueError('id type')
                if len(ids) != len(set(ids)) or set(ids) != {row['id'] for row in _PASSAGES.get()}:
                    raise ValueError('incomplete source')
            except (ValueError, KeyError, TypeError, IndexError) as error:
                raise AIProviderError('API trả cấu trúc biên bản không đầy đủ.', 'AI_INVALID_RESPONSE') from error
        elif self.local_brain.request:
            from services.ai_response_validator import validate_ai_response
            data = self.local_brain.data
            if self.local_brain.request['task_type'] == 'weekly_summary':
                refs = {'tasks': [task['task_id'] for task in data.get('tasks', [])],
                        'members': [task['assignee_id'] for task in data.get('tasks', []) if task.get('assignee_id')]}
            else:
                refs = {'tasks': [data['task']['id']] if data.get('task') else [],
                        'members': [row['user_id'] for row in data.get('candidates', [])]}
            if not validate_ai_response(content, self.local_brain.request, refs, data)['is_valid']:
                raise AIProviderError('Kết quả API không đối chiếu được với dữ liệu dự án.', 'AI_INVALID_RESPONSE')
        return content

    def generate_response(self, prompt_text, max_output_tokens=4096, json_output=False):
        if not self.fallback_enabled:
            result = self.provider.generate_content(prompt_text, max_output_tokens=max_output_tokens,
                                                    json_output=json_output)
            self._record(self.primary_provider_name)
            return result
        if not self._primary_failed.is_set():
            try:
                if self.primary_error:
                    raise self.primary_error
                with phase_budget(self.api_budget, reserve=5):
                    content = self.provider.generate_content(prompt_text, max_output_tokens=max_output_tokens,
                                                             json_output=json_output)
                content = self._validate_primary(content, json_output)
                self._record(self.primary_provider_name)
                return content
            except AIProviderError as error:
                self._primary_failed.set()
                self._failure(error)
        return self.generate_local_response(prompt_text, max_output_tokens, json_output)

    def generate_local_response(self, prompt_text, max_output_tokens=4096, json_output=False):
        # Rank candidates with exact capacity arithmetic; prose generation cannot change the ranking.
        use_model = self.local_brain.request.get('task_type') != 'assignment_suggestion'
        if (use_model and self.local_model.enabled and not self._model_failed.is_set()
                and len(prompt_text) <= 12_000 and remaining_timeout(10) >= 5):
            try:
                with phase_budget(self.local_model.timeout, reserve=2):
                    local_prompt = self.local_brain.model_prompt(prompt_text, json_output)
                    content = self.local_model.generate_content(
                        local_prompt, min(max_output_tokens, 384), json_output,
                        response_schema=self.local_brain.model_schema() if json_output else None)
                content = self.local_brain.validate_model_response(content, json_output)
                self._record('local_llm')
                if not json_output:
                    self._record('local_rules')
                return content
            except AIProviderError as error:
                self._model_failed.set()
                self._failure(error)
        remaining_timeout(1)
        result = self.local_brain.generate_response(json_output=json_output)
        self._record('local_rules')
        return result
