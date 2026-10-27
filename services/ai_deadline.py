"""One time budget shared by provider retries and meeting chunks (NFR-01)."""
from contextvars import ContextVar
from functools import wraps
import os
import time

_DEADLINE = ContextVar('ai_deadline', default=None)


def remaining_timeout(requested):
    deadline = _DEADLINE.get()
    if deadline is None:
        return requested
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        from services.gemini_service import AIProviderError
        raise AIProviderError('Yêu cầu AI đã hết thời gian xử lý. Vui lòng chia nhỏ nội dung và thử lại.', 'AI_TIMEOUT')
    return min(float(requested), remaining)


def pause_retry(seconds):
    time.sleep(remaining_timeout(seconds))
    remaining_timeout(seconds)


def with_ai_budget(function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        from services.gemini_service import AIProviderError
        try:
            seconds = max(1,min(180,int(os.getenv('AI_TOTAL_TIMEOUT_SECONDS','30'))))
        except ValueError:
            return {'success':False,'error':'AI_TOTAL_TIMEOUT_SECONDS không hợp lệ.','error_code':'AI_CONFIG'},503
        token = _DEADLINE.set(time.monotonic()+seconds)
        try:
            return function(*args, **kwargs)
        except AIProviderError as error:
            return {'success':False,'error':str(error),'error_code':error.code},503
        finally:
            _DEADLINE.reset(token)
    return wrapped
