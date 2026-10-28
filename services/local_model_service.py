"""A project-owned llama.cpp CPU runtime. No cloud key or external requests."""

import atexit
import json
import os
from pathlib import Path
import subprocess
import threading
import time
import urllib.error
import urllib.request

from services.ai_config import resolve_ai_setting
from services.ai_deadline import remaining_timeout
from services.ai_errors import AIProviderError

ROOT = Path(__file__).resolve().parents[1]
MODEL_ALIAS = 'project-local-brain'
_START_LOCK = threading.Lock()
_GENERATION_LOCK = threading.Lock()
_PROCESS = None


def setting_bool(name, default=True):
    value = resolve_ai_setting(name, 'true' if default else 'false')[0].lower()
    if value not in ('true', 'false'):
        raise AIProviderError(f'{name} phải là true hoặc false.', 'AI_CONFIG')
    return value == 'true'


def setting_int(name, default, minimum, maximum):
    try:
        value = int(resolve_ai_setting(name, str(default))[0])
    except ValueError as error:
        raise AIProviderError(f'{name} phải là số nguyên hợp lệ.', 'AI_CONFIG') from error
    if not minimum <= value <= maximum:
        raise AIProviderError(f'{name} phải nằm trong khoảng {minimum} đến {maximum}.', 'AI_CONFIG')
    return value


class LocalModelService:
    def __init__(self):
        # A fixed loopback address prevents accidental transmission to a cloud server.
        self.port = setting_int('LOCAL_AI_PORT', 18081, 1024, 65535)
        self.base_url = f'http://127.0.0.1:{self.port}'
        self.model_path = ROOT / 'local_models' / 'Qwen3-1.7B-Q8_0.gguf'
        self.executable = ROOT / 'runtime' / 'local_ai' / 'llama-server.exe'
        self.timeout = setting_int('LOCAL_AI_TIMEOUT_SECONDS', 45, 1, 120)
        self.enabled = setting_bool('LOCAL_AI_MODEL_ENABLED')
        self.autostart = setting_bool('LOCAL_AI_AUTOSTART')
        # Do not send loopback traffic or source text through system HTTP proxies.
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    @property
    def installed(self):
        return self.executable.is_file() and self.model_path.is_file()

    def _request(self, path, payload=None, timeout=2):
        request = urllib.request.Request(
            self.base_url + path,
            data=json.dumps(payload, ensure_ascii=False).encode('utf-8') if payload is not None else None,
            headers={'Content-Type': 'application/json'},
        )
        with self.opener.open(request, timeout=remaining_timeout(timeout)) as response:
            raw = response.read(2 * 1024 * 1024 + 1)
        if len(raw) > 2 * 1024 * 1024:
            raise AIProviderError('Phản hồi mô hình cục bộ vượt giới hạn.', 'AI_LOCAL_INVALID_RESPONSE')
        return json.loads(raw)

    def reachable(self):
        try:
            response = self._request('/v1/models', timeout=0.5)
            return any(row.get('id') == MODEL_ALIAS for row in response.get('data', []))
        except (OSError, ValueError, AIProviderError, AttributeError, TypeError):
            return False

    def ensure_running(self):
        global _PROCESS
        if not self.enabled:
            raise AIProviderError('Mô hình cục bộ đang tắt.', 'AI_LOCAL_DISABLED')
        if self.reachable():
            return
        if not self.autostart or not self.installed:
            raise AIProviderError('Mô hình cục bộ chưa sẵn sàng.', 'AI_LOCAL_UNAVAILABLE')
        if not _START_LOCK.acquire(timeout=remaining_timeout(self.timeout)):
            raise AIProviderError('Mô hình cục bộ đang khởi động.', 'AI_LOCAL_BUSY')
        try:
            if self.reachable():
                return
            if _PROCESS is None or _PROCESS.poll() is not None:
                # The model process needs no database, SMTP or cloud credentials.
                child_env = {key: value for key, value in os.environ.items()
                             if key.upper() in ('SYSTEMROOT', 'WINDIR', 'PATH', 'TEMP', 'TMP', 'COMSPEC')}
                flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                _PROCESS = subprocess.Popen([
                    str(self.executable), '-m', str(self.model_path), '--host', '127.0.0.1',
                    '--port', str(self.port), '-c', '8192', '-np', '1', '-t', '4',
                    '--alias', MODEL_ALIAS, '--jinja', '--no-webui', '--log-disable',
                ], cwd=str(self.executable.parent), env=child_env, creationflags=flags,
                    stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            start_deadline = time.monotonic() + remaining_timeout(self.timeout)
            while time.monotonic() < start_deadline:
                if self.reachable():
                    return
                if _PROCESS.poll() is not None:
                    break
                time.sleep(min(0.2, remaining_timeout(0.2)))
            raise AIProviderError('Chưa khởi động được mô hình cục bộ trong thời gian cho phép.', 'AI_LOCAL_UNAVAILABLE')
        finally:
            _START_LOCK.release()

    def generate_content(self, prompt, max_output_tokens=1024, json_output=False, response_schema=None):
        if not _GENERATION_LOCK.acquire(blocking=False):
            raise AIProviderError('Mô hình cục bộ đang xử lý yêu cầu khác.', 'AI_LOCAL_BUSY')
        try:
            self.ensure_running()
            payload = {
                'model': MODEL_ALIAS, 'stream': False, 'temperature': 0.1,
                'max_tokens': min(max_output_tokens, 1024),
                'chat_template_kwargs': {'enable_thinking': False},
                'messages': [{'role': 'user', 'content': prompt}],
            }
            if json_output:
                payload['response_format'] = {'type': 'json_object'}
                if response_schema is not None:
                    payload['response_format']['schema'] = response_schema
            response = self._request('/v1/chat/completions', payload, timeout=self.timeout)
            choices = response.get('choices') or []
            if not choices or choices[0].get('finish_reason') == 'length':
                raise AIProviderError('Mô hình cục bộ trả kết quả thiếu hoặc bị cắt.', 'AI_LOCAL_INVALID_RESPONSE')
            content = choices[0].get('message', {}).get('content')
            if not isinstance(content, str) or not content.strip():
                raise AIProviderError('Mô hình cục bộ trả nội dung không hợp lệ.', 'AI_LOCAL_INVALID_RESPONSE')
            return content.strip()
        except AIProviderError:
            raise
        except (OSError, ValueError, AttributeError, TypeError) as error:
            raise AIProviderError('Không xử lý được bằng mô hình cục bộ.', 'AI_LOCAL_UNAVAILABLE') from error
        finally:
            _GENERATION_LOCK.release()


def stop_owned_runtime():
    """Only terminate the model process started by this Python process."""
    global _PROCESS
    if _PROCESS is not None and _PROCESS.poll() is None:
        _PROCESS.terminate()
        try:
            _PROCESS.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _PROCESS.kill()
            _PROCESS.wait(timeout=5)
    _PROCESS = None


atexit.register(stop_owned_runtime)
