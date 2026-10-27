"""Shared input rules for FR-02..09, with errors safe for users."""
import math
import re
from datetime import date, datetime, timezone, timedelta
from flask import request
from werkzeug.exceptions import BadRequest

LOCAL_TIMEZONE = timezone(timedelta(hours=7))


class ValidationError(ValueError):
    pass


def json_object():
    try:
        value = request.get_json()
    except BadRequest as error:
        raise ValidationError('JSON không hợp lệ.') from error
    if not isinstance(value, dict):
        raise ValidationError('Nội dung yêu cầu phải là một đối tượng JSON.')
    return value


def text(value, label, maximum, required=False):
    if value is None:
        value = ''
    if not isinstance(value, str):
        raise ValidationError(f'{label} phải là văn bản.')
    value = value.strip()
    if required and not value:
        raise ValidationError(f'{label} không được để trống.')
    if len(value) > maximum:
        raise ValidationError(f'{label} không được vượt quá {maximum} ký tự.')
    return value


def number(value, label, minimum=0, maximum=9999.99):
    if isinstance(value, bool):
        raise ValidationError(f'{label} phải là số hợp lệ.')
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValidationError(f'{label} phải là số hợp lệ.') from error
    if not math.isfinite(result) or not minimum <= result <= maximum:
        raise ValidationError(f'{label} phải trong khoảng {minimum} đến {maximum}.')
    return result


def integer(value, label, minimum=0, maximum=2147483647, optional=False):
    if optional and value in (None, ''):
        return None
    if isinstance(value, bool) or not re.fullmatch(r'\d+', str(value)):
        raise ValidationError(f'{label} phải là số nguyên hợp lệ.')
    result = int(value)
    if not minimum <= result <= maximum:
        raise ValidationError(f'{label} phải trong khoảng {minimum} đến {maximum}.')
    return result


def choice(value, allowed, label):
    if not isinstance(value, str) or value not in allowed:
        raise ValidationError(f'{label} không hợp lệ.')
    return value


def iso_date(value, label, required=False):
    if (value is None or value == '') and not required:
        return None
    try:
        return date.fromisoformat(str(value)).isoformat()
    except (ValueError, TypeError) as error:
        raise ValidationError(f'{label} phải là ngày hợp lệ YYYY-MM-DD.') from error


def local_datetime(value):
    if value is None or value == '':
        return None
    try:
        parsed = value if isinstance(value, datetime) else datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        if parsed.tzinfo is not None:
            parsed = parsed.astimezone(LOCAL_TIMEZONE).replace(tzinfo=None)
        return parsed
    except (ValueError, TypeError) as error:
        raise ValidationError('Hạn hoàn thành phải là ngày giờ hợp lệ.') from error


def availability_percent(value):
    raw = str(value if value is not None else '100').strip()
    if raw.lower() in ('full-time', 'toàn thời gian'):
        return 100.0
    match = re.match(r'^(\d+(?:\.\d+)?)\s*%?(?:\s*\([^)]*\))?$', raw)
    if not match:
        raise ValidationError('Mức sẵn sàng phải là tỷ lệ từ 0 đến 100%.')
    return number(match.group(1), 'Mức sẵn sàng', maximum=100)
