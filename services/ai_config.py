"""Resolve AI settings, with opt-in live .env configuration for local servers."""

import os
from pathlib import Path

from dotenv import dotenv_values

ENV_FILE = Path(__file__).resolve().parents[1] / '.env'
PLACEHOLDER_KEYS = {
    'your_gemini_api_key', 'khoa_api_gemini_cua_ban',
    'your_kira_api_key', 'khoa_api_kira_cua_ban',
    'your_openai_api_key', 'khoa_api_openai_cua_ban',
}


def resolve_ai_setting(name, default='', *, environ=None, env_file=None):
    """Process settings win by default; AI_CONFIG_SOURCE=env_file selects live file values."""
    source_env = os.environ if environ is None else environ
    path = ENV_FILE if env_file is None else env_file
    file_settings = dotenv_values(path)
    config_source = source_env.get('AI_CONFIG_SOURCE') or file_settings.get('AI_CONFIG_SOURCE')
    # Local installations explicitly opt in to live file configuration. In particular,
    # a cleared key must not resurrect a secret inherited by an older server process.
    if config_source == 'env_file' and name in file_settings:
        return (file_settings[name] or '').strip(), 'env_file'
    process_value = source_env.get(name)
    if isinstance(process_value, str) and process_value.strip():
        return process_value.strip(), 'process'

    file_value = file_settings.get(name)
    if isinstance(file_value, str) and file_value.strip():
        return file_value.strip(), 'env_file'
    return default, 'default'


def key_is_configured(value):
    return bool(value and value.strip() and value.strip().lower() not in PLACEHOLDER_KEYS)
