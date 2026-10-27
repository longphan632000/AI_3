from services.ai_deadline import remaining_timeout, pause_retry
"""Gemini adapter. A provider failure must not look like a real summary."""

import http.client
import errno
import json
import logging
import socket
import ssl
import time
import urllib.error
import urllib.request

from services.ai_config import key_is_configured, resolve_ai_setting


LOGGER = logging.getLogger(__name__)
MAX_ATTEMPTS = 3


class AIProviderError(RuntimeError):
    def __init__(self, message, code='AI_PROVIDER_ERROR', *, retryable=False, diagnostics=None):
        super().__init__(message)
        self.code = code
        self.retryable = retryable
        self.diagnostics = diagnostics or {}


def transport_failure(error):
    """Classify OS/TLS failures without exposing exception text or request secrets."""
    reason = error.reason if isinstance(error, urllib.error.URLError) else error
    diagnostic = {'reason_type': type(reason).__name__}
    for field in ('errno', 'winerror', 'verify_code'):
        value = getattr(reason, field, None)
        if isinstance(value, int):
            diagnostic[field] = value
    if (not isinstance(reason, ssl.SSLError) and
            (isinstance(reason, PermissionError) or diagnostic.get('winerror') == 10013
             or diagnostic.get('errno') in (errno.EACCES, errno.EPERM, 10013))):
        return AIProviderError(
            'Tiến trình máy chủ không được phép kết nối Internet tới Gemini. '
            'Hãy chạy máy chủ trong môi trường cho phép kết nối mạng, ngoài sandbox hạn chế mạng, '
            'và kiểm tra quyền kết nối HTTPS tới Google.',
            'AI_NETWORK_DENIED', diagnostics=diagnostic)
    if isinstance(reason, ssl.SSLCertVerificationError):
        return AIProviderError(
            'Không xác minh được chứng chỉ HTTPS của Gemini. Hãy kiểm tra ngày giờ hệ thống '
            'và chứng chỉ tin cậy của máy chủ hoặc proxy.',
            'AI_TLS_CERTIFICATE', diagnostics=diagnostic)
    if isinstance(reason, ssl.SSLError):
        return AIProviderError('Không thiết lập được kết nối TLS an toàn tới Gemini. '
                               'Hãy kiểm tra cấu hình TLS hoặc proxy của máy chủ.',
                               'AI_TLS_ERROR', diagnostics=diagnostic)
    if isinstance(reason, (TimeoutError, socket.timeout)):
        return AIProviderError('Gemini xử lý quá thời gian chờ. Hãy thử lại hoặc chia tệp nhỏ hơn.',
                               'AI_TIMEOUT', retryable=True, diagnostics=diagnostic)
    if isinstance(reason, socket.gaierror):
        return AIProviderError('Máy chủ không phân giải được tên miền Gemini. '
                               'Hãy kiểm tra DNS và kết nối mạng của máy chủ.',
                               'AI_DNS', retryable=reason.errno == socket.EAI_AGAIN, diagnostics=diagnostic)
    return AIProviderError('Không kết nối được Gemini. Hãy kiểm tra mạng hoặc proxy rồi thử lại.',
                           'AI_CONNECTION', retryable=True, diagnostics=diagnostic)


def http_failure(error):
    """Only stable error codes are exposed; never forward a provider error body."""
    diagnostic = {'http_status': error.code}
    invalid_key = False
    if error.code == 400:
        try:
            body = json.loads(error.read(16384).decode('utf-8'))
            invalid_key = any(isinstance(item, dict) and item.get('reason') in
                              ('API_KEY_INVALID', 'API_KEY_EXPIRED')
                              for item in body.get('error', {}).get('details', []))
        except (ValueError, AttributeError, TypeError, OSError):
            pass
    if invalid_key or error.code in (401, 403):
        return AIProviderError('Khóa Gemini bị từ chối hoặc không có quyền truy cập.',
                               'AI_KEY_REJECTED', diagnostics=diagnostic)
    if error.code == 404:
        return AIProviderError('Mô hình Gemini được cấu hình không khả dụng. '
                               'Hãy kiểm tra GEMINI_MODEL và GEMINI_MEETING_MODEL.',
                               'AI_MODEL_UNAVAILABLE', diagnostics=diagnostic)
    if error.code == 429:
        return AIProviderError('Gemini đang giới hạn số lần gọi hoặc hạn mức tài khoản. '
                               'Hãy kiểm tra quota trong Google AI Studio và thử lại sau.',
                               'AI_RATE_LIMIT', retryable=True, diagnostics=diagnostic)
    if error.code in (500, 502, 503, 504):
        return AIProviderError('Dịch vụ Gemini tạm thời không khả dụng. Vui lòng thử lại sau.',
                               'AI_SERVICE_UNAVAILABLE', retryable=True, diagnostics=diagnostic)
    return AIProviderError(f'Dịch vụ Gemini trả về lỗi HTTP {error.code}.',
                           'AI_HTTP_ERROR', diagnostics=diagnostic)


def log_failure(failure, attempt):
    LOGGER.warning('Gemini failure code=%s reason=%s errno=%s winerror=%s http=%s attempt=%s/%s',
                   failure.code, failure.diagnostics.get('reason_type'),
                   failure.diagnostics.get('errno'), failure.diagnostics.get('winerror'),
                   failure.diagnostics.get('http_status'), attempt, MAX_ATTEMPTS)


class GeminiService:
    def __init__(self):
        self.api_key, self.key_source = resolve_ai_setting('GEMINI_API_KEY')
        timeout, _ = resolve_ai_setting('AI_TIMEOUT_SECONDS', '30')
        meeting_timeout, _ = resolve_ai_setting('AI_MEETING_TIMEOUT_SECONDS', '90')
        self.model = resolve_ai_setting('GEMINI_MODEL', 'gemini-3.8-flash')[0]
        self.meeting_model = resolve_ai_setting('GEMINI_MEETING_MODEL', self.model)[0]
        self.last_probe_error_code = None
        self.last_probe_diagnostics = {}
        try:
            self.timeout = int(timeout)
            self.meeting_timeout = int(meeting_timeout)
        except ValueError as error:
            raise AIProviderError('Thời gian chờ AI phải là số giây hợp lệ.', 'AI_CONFIG') from error
        if not 1 <= self.timeout <= 120:
            raise AIProviderError('AI_TIMEOUT_SECONDS phải nằm trong khoảng 1 đến 120 giây.', 'AI_CONFIG')
        if not 1 <= self.meeting_timeout <= 180:
            raise AIProviderError('AI_MEETING_TIMEOUT_SECONDS phải nằm trong khoảng 1 đến 180 giây.', 'AI_CONFIG')

    @property
    def configured(self):
        return key_is_configured(self.api_key)

    def probe_model(self, model=None):
        """Read-only provider check for the admin diagnostics page."""
        self.last_probe_error_code = None
        self.last_probe_diagnostics = {}
        if not self.configured:
            return self._failed_probe(AIProviderError('Chưa nạp khóa Gemini hợp lệ.', 'AI_KEY_MISSING'))
        target_model = model or self.model
        url = f'https://generativelanguage.googleapis.com/v1beta/models/{target_model}'
        request = urllib.request.Request(url, headers={'x-goog-api-key': self.api_key})
        try:
            with urllib.request.urlopen(request, timeout=min(self.timeout, 10)) as response:
                model = json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as error:
            return self._failed_probe(http_failure(error))
        except (urllib.error.URLError, OSError, http.client.HTTPException) as error:
            return self._failed_probe(transport_failure(error))
        except (ValueError, UnicodeError):
            return self._failed_probe(AIProviderError('Gemini trả về phản hồi không đọc được.', 'AI_INVALID_RESPONSE'))
        if not isinstance(model, dict):
            return self._failed_probe(AIProviderError('Gemini trả về thông tin model sai cấu trúc.', 'AI_INVALID_RESPONSE'))
        if 'generateContent' not in (model.get('supportedGenerationMethods') or []):
            return self._failed_probe(AIProviderError('Mô hình này không hỗ trợ tạo nội dung.', 'AI_MODEL_UNAVAILABLE'))
        return True, 'Gemini đã xác nhận khóa và mô hình có thể tạo nội dung.'

    def _failed_probe(self, failure):
        self.last_probe_error_code = failure.code
        self.last_probe_diagnostics = failure.diagnostics
        log_failure(failure, 1)
        return False, str(failure)

    def generate_content(self, prompt_text, max_output_tokens=4096, json_output=False):
        if not self.configured:
            raise AIProviderError('Trợ lý AI chưa được cấu hình khóa Gemini. Không thể tạo bản nháp đáng tin cậy.', 'AI_KEY_MISSING')

        target_model = self.meeting_model if json_output else self.model
        url = f'https://generativelanguage.googleapis.com/v1beta/models/{target_model}:generateContent'
        payload = {
            'contents': [{'parts': [{'text': prompt_text}]}],
            'generationConfig': {'maxOutputTokens': max_output_tokens},
        }
        if json_output:
            payload['generationConfig']['responseMimeType'] = 'application/json'
        request = urllib.request.Request(
            url,
            data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
            headers={'Content-Type': 'application/json', 'x-goog-api-key': self.api_key},
            method='POST',
        )
        request_timeout = self.meeting_timeout if json_output else self.timeout
        for attempt in range(MAX_ATTEMPTS):
            try:
                with urllib.request.urlopen(request, timeout=remaining_timeout(request_timeout)) as response:
                    response_bytes = response.read()
                break
            except urllib.error.HTTPError as error:
                failure = http_failure(error)
                log_failure(failure, attempt + 1)
                if failure.retryable and attempt < MAX_ATTEMPTS - 1:
                    retry_after = error.headers.get('Retry-After') if error.headers else None
                    delay = min(int(retry_after), 5) if retry_after and retry_after.isdigit() else 2 ** attempt
                    pause_retry(delay)
                    continue
                raise failure from error
            except (urllib.error.URLError, OSError, http.client.HTTPException) as error:
                failure = transport_failure(error)
                log_failure(failure, attempt + 1)
                if failure.retryable and attempt < MAX_ATTEMPTS - 1:
                    pause_retry(2 ** attempt)
                    continue
                raise failure from error

        try:
            result = json.loads(response_bytes.decode('utf-8'))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            LOGGER.warning('Gemini returned invalid JSON')
            raise AIProviderError('Gemini trả về phản hồi không đọc được. Vui lòng thử lại.', 'AI_INVALID_RESPONSE') from error
        if not isinstance(result, dict):
            raise AIProviderError('Gemini trả về phản hồi sai cấu trúc. Vui lòng thử lại.', 'AI_INVALID_RESPONSE')

        candidates = result.get('candidates') or []
        if not isinstance(candidates, list) or not candidates:
            raise AIProviderError('Dịch vụ AI không trả về nội dung.')
        candidate = candidates[0]
        if not isinstance(candidate, dict):
            raise AIProviderError('Gemini trả về phản hồi sai cấu trúc. Vui lòng thử lại.', 'AI_INVALID_RESPONSE')
        if candidate.get('finishReason') == 'MAX_TOKENS':
            raise AIProviderError('Kết quả AI bị cắt do giới hạn độ dài. Hãy thử lại hoặc chia tệp nhỏ hơn.')
        content = candidate.get('content') or {}
        parts = content.get('parts') if isinstance(content, dict) else None
        if not isinstance(parts, list) or any(not isinstance(part, dict) for part in parts):
            raise AIProviderError('Gemini trả về phản hồi sai cấu trúc. Vui lòng thử lại.', 'AI_INVALID_RESPONSE')
        text = ''.join(part.get('text', '') for part in parts
                       if not part.get('thought') and isinstance(part.get('text', ''), str))
        if not text.strip():
            raise AIProviderError('Dịch vụ AI không trả về nội dung văn bản hợp lệ.')
        return text.strip()
