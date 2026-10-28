"""DeepSeek-only adapter using the OpenAI chat completions protocol."""

import errno
import logging
import socket
import ssl

from services.ai_config import key_is_configured, resolve_ai_setting
from services.ai_deadline import pause_retry, remaining_timeout
from services.ai_errors import AIProviderError

LOGGER = logging.getLogger(__name__)
MAX_ATTEMPTS = 3
DEEPSEEK_MODEL = 'deepseek-v4.1-flash-1017'


def provider_failure(error):
    """Classify SDK failures and their causes without exposing request details."""
    if isinstance(error, AIProviderError):
        return error
    causes, seen = [], set()
    cause = error
    while cause is not None and id(cause) not in seen:
        seen.add(id(cause))
        causes.append(cause)
        cause = cause.__cause__ or cause.__context__
    diagnostics = {}
    for cause in causes:
        for field in ('errno', 'winerror', 'verify_code'):
            value = getattr(cause, field, None)
            if isinstance(value, int):
                diagnostics[field] = value
    status = getattr(error, 'status_code', None)
    if isinstance(status, int):
        diagnostics['http_status'] = status
        if status in (401, 403):
            return AIProviderError('Khóa DeepSeek bị từ chối hoặc không có quyền truy cập.',
                                   'AI_KEY_REJECTED', diagnostics=diagnostics)
        if status == 404:
            return AIProviderError('Model DeepSeek không khả dụng trên API đã cấu hình.',
                                   'AI_MODEL_UNAVAILABLE', diagnostics=diagnostics)
        if status == 429:
            return AIProviderError('DeepSeek đang giới hạn số lần gọi hoặc hạn mức tài khoản.',
                                   'AI_RATE_LIMIT', retryable=True, diagnostics=diagnostics)
        if status in (500, 502, 503, 504):
            return AIProviderError('Dịch vụ DeepSeek tạm thời không khả dụng. Vui lòng thử lại sau.',
                                   'AI_SERVICE_UNAVAILABLE', retryable=True, diagnostics=diagnostics)
        return AIProviderError(f'Dịch vụ DeepSeek trả về lỗi HTTP {status}.',
                               'AI_HTTP_ERROR', diagnostics=diagnostics)
    if any(isinstance(item, ssl.SSLCertVerificationError) for item in causes):
        return AIProviderError('Không xác minh được chứng chỉ HTTPS của API DeepSeek.',
                               'AI_TLS_CERTIFICATE', diagnostics=diagnostics)
    if any(isinstance(item, (ssl.SSLEOFError, ssl.SSLZeroReturnError)) for item in causes):
        return AIProviderError('Kết nối tới DeepSeek bị đóng trước khi nhận đủ phản hồi.',
                               'AI_CONNECTION', retryable=True, diagnostics=diagnostics)
    if any(isinstance(item, ssl.SSLError) for item in causes):
        return AIProviderError('Không thiết lập được kết nối TLS an toàn tới API DeepSeek.',
                               'AI_TLS_ERROR', diagnostics=diagnostics)
    if (any(isinstance(item, PermissionError) for item in causes)
            or diagnostics.get('winerror') == 10013
            or diagnostics.get('errno') in (errno.EACCES, errno.EPERM, 10013)):
        return AIProviderError('Tiến trình máy chủ không được phép kết nối Internet tới DeepSeek.',
                               'AI_NETWORK_DENIED', diagnostics=diagnostics)
    dns_error = next((item for item in causes if isinstance(item, socket.gaierror)), None)
    if dns_error is not None:
        return AIProviderError('Không phân giải được tên miền API DeepSeek.', 'AI_DNS',
                               retryable=dns_error.errno == socket.EAI_AGAIN, diagnostics=diagnostics)
    if any(isinstance(item, TimeoutError) or 'timeout' in type(item).__name__.lower() for item in causes):
        return AIProviderError('DeepSeek xử lý quá thời gian chờ. Vui lòng thử lại.',
                               'AI_TIMEOUT', retryable=True, diagnostics=diagnostics)
    if any(isinstance(item, OSError) or any(name in type(item).__name__.lower()
           for name in ('connection', 'connect', 'readerror', 'writeerror', 'protocolerror')) for item in causes):
        return AIProviderError('Không kết nối được API DeepSeek. Hãy kiểm tra mạng hoặc URL.',
                               'AI_CONNECTION', retryable=True, diagnostics=diagnostics)
    return AIProviderError('Dịch vụ DeepSeek trả về lỗi không xác định. Vui lòng thử lại.',
                           diagnostics=diagnostics)


class OpenAIService:
    """Use the same DeepSeek model for general tasks and meeting minutes."""

    def __init__(self):
        self.api_key, self.key_source = resolve_ai_setting('OPENAI_API_KEY')
        self.base_url = resolve_ai_setting('OPENAI_BASE_URL', 'https://discovery-api.intern-ai.org.cn/v1')[0]
        self.model = resolve_ai_setting('OPENAI_MODEL', DEEPSEEK_MODEL)[0]
        self.meeting_model = resolve_ai_setting('OPENAI_MEETING_MODEL', self.model)[0]
        if self.model != DEEPSEEK_MODEL or self.meeting_model != DEEPSEEK_MODEL:
            raise AIProviderError(f'Ứng dụng chỉ sử dụng model {DEEPSEEK_MODEL} cho tất cả tác vụ AI.', 'AI_CONFIG')
        self.probe_scope = 'chat_completion'
        self.last_probe_error_code = None
        self.last_probe_diagnostics = {}
        try:
            self.timeout = int(resolve_ai_setting('AI_TIMEOUT_SECONDS', '60')[0])
            self.meeting_timeout = int(resolve_ai_setting('AI_MEETING_TIMEOUT_SECONDS', '60')[0])
        except ValueError as error:
            raise AIProviderError('Thời gian chờ AI phải là số giây hợp lệ.', 'AI_CONFIG') from error
        if not 1 <= self.timeout <= 120:
            raise AIProviderError('AI_TIMEOUT_SECONDS phải nằm trong khoảng 1 đến 120 giây.', 'AI_CONFIG')
        if not 1 <= self.meeting_timeout <= 180:
            raise AIProviderError('AI_MEETING_TIMEOUT_SECONDS phải nằm trong khoảng 1 đến 180 giây.', 'AI_CONFIG')

    @property
    def configured(self):
        return key_is_configured(self.api_key)

    def _get_client(self, timeout=None):
        try:
            from openai import OpenAI
        except ImportError as error:
            raise AIProviderError('Thư viện openai chưa được cài đặt trên hệ thống.', 'AI_CONFIG') from error
        return OpenAI(base_url=self.base_url, api_key=self.api_key or 'unconfigured',
                      timeout=timeout or self.timeout, max_retries=0)

    def probe_model(self, model=None):
        self.last_probe_error_code = None
        self.last_probe_diagnostics = {}
        if not self.configured:
            return self._failed_probe(AIProviderError('Chưa nạp khóa DeepSeek hợp lệ.', 'AI_KEY_MISSING'))
        if model is not None and model != DEEPSEEK_MODEL:
            return self._failed_probe(AIProviderError('Chỉ cho phép kiểm tra model DeepSeek đã cấu hình.', 'AI_CONFIG'))
        client = None
        try:
            client = self._get_client(timeout=self.timeout)
            response = client.chat.completions.create(
                model=self.model, messages=[{'role': 'user', 'content': 'Reply with exactly OK.'}],
                max_tokens=64, temperature=0.1,
            )
            self._response_text(response)
            return True, f'DeepSeek ({self.model}) đã xác thực khóa và tạo phản hồi thử thành công.'
        except Exception as error:  # noqa: BLE001 - diagnostics must hide SDK exception text
            return self._failed_probe(provider_failure(error))
        finally:
            if client is not None:
                client.close()

    def _failed_probe(self, failure):
        self.last_probe_error_code = failure.code
        self.last_probe_diagnostics = failure.diagnostics
        return False, str(failure)

    @staticmethod
    def _response_text(response):
        choices = getattr(response, 'choices', None) or []
        if not choices:
            raise AIProviderError('DeepSeek không trả về nội dung.', 'AI_INVALID_RESPONSE')
        if getattr(choices[0], 'finish_reason', None) == 'length':
            raise AIProviderError('Kết quả DeepSeek bị cắt do giới hạn độ dài.', 'AI_INVALID_RESPONSE')
        content = getattr(getattr(choices[0], 'message', None), 'content', None)
        if not isinstance(content, str) or not content.strip():
            raise AIProviderError('DeepSeek không trả về nội dung văn bản hợp lệ.', 'AI_INVALID_RESPONSE')
        return content.strip()

    def generate_content(self, prompt_text, max_output_tokens=4096, json_output=False):
        if not self.configured:
            raise AIProviderError('Trợ lý AI chưa được cấu hình khóa DeepSeek.', 'AI_KEY_MISSING')
        request_timeout = self.meeting_timeout if json_output else self.timeout
        kwargs = {'model': self.model, 'messages': [{'role': 'user', 'content': prompt_text}],
                  'temperature': 0.1, 'max_tokens': max_output_tokens}
        if json_output:
            kwargs['response_format'] = {'type': 'json_object'}
            # Classification only needs grounded extraction, not a reasoning trace.
            kwargs['reasoning_effort'] = 'none'
        client = self._get_client(timeout=request_timeout)
        try:
            for attempt in range(MAX_ATTEMPTS):
                try:
                    response = client.chat.completions.create(timeout=remaining_timeout(request_timeout), **kwargs)
                    return self._response_text(response)
                except AIProviderError:
                    raise
                except Exception as error:
                    failure = provider_failure(error)
                    LOGGER.warning('DeepSeek failure code=%s attempt=%s/%s', failure.code, attempt + 1, MAX_ATTEMPTS)
                    if not failure.retryable or attempt == MAX_ATTEMPTS - 1:
                        raise failure from error
                    if failure.code == 'AI_SERVICE_UNAVAILABLE':
                        kwargs.pop('response_format', None)
                    pause_retry(2 ** attempt)
        finally:
            client.close()
