from services.ai_deadline import remaining_timeout, pause_retry
"""Kira AI (OpenAI-compatible) adapter for Qwen and Kira models. A provider failure must not look like a real summary."""

import logging
import time
from services.ai_config import key_is_configured, resolve_ai_setting
from services.gemini_service import AIProviderError

LOGGER = logging.getLogger(__name__)
MAX_ATTEMPTS = 3


class KiraAIService:
    """
    Adapter kết nối tới Kira AI thông qua chuẩn OpenAI API.
    Hỗ trợ mô hình qwen3.8-flash-next-free và các mô hình OpenAI-compatible khác.
    """
    def __init__(self):
        self.api_key, self.key_source = resolve_ai_setting('KIRA_API_KEY')
        self.base_url = resolve_ai_setting('KIRA_BASE_URL', 'https://kiraai.vn/api/v1')[0]
        self.model = resolve_ai_setting('KIRA_MODEL', 'qwen3.8-flash-next-free')[0]
        self.meeting_model = resolve_ai_setting('KIRA_MEETING_MODEL', self.model)[0]

        timeout, _ = resolve_ai_setting('AI_TIMEOUT_SECONDS', '60')
        meeting_timeout, _ = resolve_ai_setting('AI_MEETING_TIMEOUT_SECONDS', '120')
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

    def _get_client(self, timeout=None):
        try:
            from openai import OpenAI
        except ImportError as error:
            raise AIProviderError('Thư viện openai chưa được cài đặt trên hệ thống.', 'AI_CONFIG') from error

        return OpenAI(
            base_url=self.base_url,
            api_key=self.api_key or 'unconfigured',
            timeout=timeout or self.timeout,
            max_retries=0,  # We manage application-level retries explicitly with backoff
        )

    def probe_model(self, model=None):
        """Kiểm tra kết nối và tính sẵn sàng của mô hình Kira AI cho trang Admin Diagnostics."""
        if not self.configured:
            return False, 'Chưa nạp khóa Kira AI hợp lệ.'
        target_model = model or self.model
        try:
            client = self._get_client(timeout=min(self.timeout, 15))
            # Gửi một tin nhắn ngắn để kiểm tra xác thực và mô hình
            response = client.chat.completions.create(
                model=target_model,
                messages=[{'role': 'user', 'content': 'ping'}],
                max_tokens=5,
                temperature=0.1,
            )
            if response and response.choices:
                return True, f'Kira AI ({target_model}) đã xác nhận kết nối và sẵn sàng tạo nội dung.'
            return False, f'Kira AI ({target_model}) không trả về lựa chọn phản hồi hợp lệ.'
        except Exception as error:
            error_str = str(error)
            error_type = type(error).__name__
            if 'AuthenticationError' in error_type or '401' in error_str:
                return False, 'Khóa Kira AI bị từ chối hoặc không có quyền truy cập.'
            if 'NotFoundError' in error_type or '404' in error_str:
                return False, f'Mô hình {target_model} của Kira AI không khả dụng.'
            if 'RateLimitError' in error_type or '429' in error_str:
                return False, 'Kira AI đang giới hạn số lần gọi (Rate Limit).'
            return False, 'Không kết nối được Kira AI. Hãy kiểm tra cấu hình và thử lại.'

    def generate_content(self, prompt_text, max_output_tokens=4096, json_output=False):
        """
        Gửi yêu cầu tạo nội dung tới Kira AI.
        Hỗ trợ JSON mode nếu json_output=True, có fallback tự động nếu upstream proxy lỗi 5xx với response_format.
        """
        if not self.configured:
            raise AIProviderError('Trợ lý AI chưa được cấu hình khóa Kira AI. Không thể tạo bản nháp đáng tin cậy.', 'AI_KEY_MISSING')

        target_model = self.meeting_model if json_output else self.model
        request_timeout = self.meeting_timeout if json_output else self.timeout
        client = self._get_client(timeout=request_timeout)

        messages = [{'role': 'user', 'content': prompt_text}]
        kwargs = {
            'model': target_model,
            'messages': messages,
            'temperature': 0.1,
            'max_tokens': max_output_tokens,
        }
        if json_output:
            kwargs['response_format'] = {'type': 'json_object'}

        for attempt in range(MAX_ATTEMPTS):
            try:
                timeout = remaining_timeout(request_timeout)
                response = client.chat.completions.create(timeout=timeout, **kwargs)
                choices = getattr(response, 'choices', None) or []
                if not choices:
                    raise AIProviderError('Dịch vụ AI không trả về nội dung.')

                first_choice = choices[0]
                finish_reason = getattr(first_choice, 'finish_reason', None)
                if finish_reason == 'length':
                    raise AIProviderError('Kết quả AI bị cắt do giới hạn độ dài. Hãy thử lại hoặc chia tệp nhỏ hơn.')

                message = getattr(first_choice, 'message', None)
                content = getattr(message, 'content', '') if message else ''
                if not content or not isinstance(content, str) or not content.strip():
                    raise AIProviderError('Dịch vụ AI không trả về nội dung văn bản hợp lệ.')

                return content.strip()

            except AIProviderError:
                raise
            except Exception as error:
                error_type = type(error).__name__
                error_str = str(error)

                # Kiểm tra lỗi xác thực (401 / 403)
                if 'AuthenticationError' in error_type or '401' in error_str or '403' in error_str:
                    raise AIProviderError('Khóa Kira AI bị từ chối hoặc không có quyền truy cập.', 'AI_KEY_REJECTED') from error

                # Kiểm tra mô hình không tồn tại (404)
                if 'NotFoundError' in error_type or '404' in error_str:
                    raise AIProviderError(f'Mô hình {target_model} của Kira AI không khả dụng. Hãy kiểm tra KIRA_MODEL.', 'AI_MODEL_UNAVAILABLE') from error

                # Rate limit (429)
                if 'RateLimitError' in error_type or '429' in error_str:
                    LOGGER.warning('Kira AI RateLimit, attempt %s/%s', attempt + 1, MAX_ATTEMPTS)
                    if attempt < MAX_ATTEMPTS - 1:
                        pause_retry(2 ** attempt)
                        continue
                    raise AIProviderError('Kira AI đang giới hạn số lần gọi. Vui lòng thử lại sau.', 'AI_RATE_LIMIT') from error

                # Lỗi server nội bộ (500, 502, 503, 504)
                if any(code in error_str for code in ('500', '502', '503', '504')) or 'InternalServerError' in error_type:
                    LOGGER.warning('Kira AI server error, attempt %s/%s', attempt + 1, MAX_ATTEMPTS)
                    # Nếu đang bật response_format json_object mà upstream lỗi 5xx, thử bỏ constraint để Qwen sinh JSON tự nhiên
                    if 'response_format' in kwargs:
                        LOGGER.info('Retrying Kira AI request without response_format constraint')
                        del kwargs['response_format']
                    if attempt < MAX_ATTEMPTS - 1:
                        pause_retry(2 ** attempt)
                        continue
                    raise AIProviderError('Dịch vụ Kira AI tạm thời không khả dụng. Vui lòng thử lại sau.', 'AI_SERVICE_UNAVAILABLE') from error

                # Timeout
                if 'Timeout' in error_type or 'timeout' in error_str.lower():
                    LOGGER.warning('Kira AI timeout, attempt %s/%s', attempt + 1, MAX_ATTEMPTS)
                    if attempt < MAX_ATTEMPTS - 1:
                        pause_retry(2 ** attempt)
                        continue
                    raise AIProviderError('Kira AI xử lý quá thời gian chờ. Hãy thử lại hoặc chia tệp nhỏ hơn.', 'AI_TIMEOUT') from error

                # Lỗi kết nối mạng
                if 'ConnectionError' in error_type or 'APIConnectionError' in error_type:
                    LOGGER.warning('Kira AI connection error, attempt %s/%s', attempt + 1, MAX_ATTEMPTS)
                    if attempt < MAX_ATTEMPTS - 1:
                        pause_retry(2 ** attempt)
                        continue
                    raise AIProviderError('Không kết nối được Kira AI. Hãy kiểm tra mạng hoặc URL rồi thử lại.', 'AI_CONNECTION') from error

                LOGGER.warning('Kira AI unexpected error (%s)', error_type)
                raise AIProviderError('Dịch vụ Kira AI trả về lỗi không xác định. Vui lòng thử lại.', 'AI_PROVIDER_ERROR') from error
