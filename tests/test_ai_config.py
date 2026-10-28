"""Configuration and admin diagnostics without contacting DeepSeek or production MySQL."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app import app
from services.ai_config import key_is_configured, resolve_ai_setting
from services.ai_deadline import remaining_timeout, with_ai_budget
from services.openai_service import OpenAIService


class TestAiConfig(unittest.TestCase):
    def test_live_file_budget_overrides_stale_process_timeout(self):
        with tempfile.TemporaryDirectory() as directory:
            env_file = Path(directory) / '.env'
            env_file.write_text('AI_TOTAL_TIMEOUT_SECONDS=180\n', encoding='utf-8')

            @with_ai_budget
            def call():
                return remaining_timeout(1000)

            with patch.dict(os.environ, {'AI_CONFIG_SOURCE': 'env_file', 'AI_TOTAL_TIMEOUT_SECONDS': '30'}), \
                    patch('services.ai_config.ENV_FILE', env_file), \
                    patch('services.ai_deadline.time.monotonic', side_effect=[100, 110]):
                self.assertEqual(call(), 170)

    def test_admin_openai_diagnostics_report_generation_probe_without_key(self):
        with tempfile.TemporaryDirectory() as directory:
            env_file = Path(directory) / '.env'
            env_file.write_text(
                'AI_PROVIDER=openai\nOPENAI_API_KEY=file_openai_test_secret\n'
                'OPENAI_MODEL=deepseek-v4.1-flash-1017\n'
                'OPENAI_MEETING_MODEL=deepseek-v4.1-flash-1017\n',
                encoding='utf-8',
            )
            with patch.dict(os.environ, {'AI_CONFIG_SOURCE': 'env_file'}), \
                    patch('services.ai_config.ENV_FILE', env_file), \
                    patch.object(OpenAIService, 'probe_model', return_value=(True, 'OK')) as probe:
                admin = app.test_client()
                with admin.session_transaction() as session:
                    session.update(user_id=1, role='admin')
                status = admin.get('/api/admin/ai-status').get_json()
                self.assertEqual(status['provider'], 'deepseek')
                self.assertTrue(status['configured'])
                self.assertFalse(status['api_checked'])
                probe.assert_not_called()
                response = admin.get('/api/admin/ai-status?probe=1')
                checked = response.get_json()
                self.assertEqual(checked['model'], 'deepseek-v4.1-flash-1017')
                self.assertEqual(checked['meeting_model'], checked['model'])
                self.assertEqual(checked['probe_scope'], 'chat_completion')
                self.assertTrue(checked['api_reachable'])
                self.assertNotIn('file_openai_test_secret', response.get_data(as_text=True))
                probe.assert_called_once()

    def test_blank_process_key_uses_project_env_file(self):
        with tempfile.TemporaryDirectory() as directory:
            env_file = Path(directory) / '.env'
            env_file.write_text('OPENAI_API_KEY=file_test_key\n', encoding='utf-8')
            value, source = resolve_ai_setting(
                'OPENAI_API_KEY', environ={'OPENAI_API_KEY': ''}, env_file=env_file
            )
        self.assertEqual((value, source), ('file_test_key', 'env_file'))

    def test_nonblank_process_key_wins_and_missing_key_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            env_file = Path(directory) / '.env'
            env_file.write_text('OPENAI_API_KEY=file_test_key\n', encoding='utf-8')
            self.assertEqual(resolve_ai_setting(
                'OPENAI_API_KEY', environ={'OPENAI_API_KEY': 'process_test_key'},
                env_file=env_file
            ), ('process_test_key', 'process'))
            self.assertEqual(resolve_ai_setting(
                'OPENAI_API_KEY', environ={'OPENAI_API_KEY': ''},
                env_file=Path(directory) / 'missing.env'
            ), ('', 'default'))
        self.assertFalse(key_is_configured('khoa_api_openai_cua_ban'))

    def test_admin_diagnostics_require_admin_and_never_return_key(self):
        with tempfile.TemporaryDirectory() as directory:
            env_file = Path(directory) / '.env'
            env_file.write_text('OPENAI_API_KEY=file_test_secret\n', encoding='utf-8')
            with patch.dict(os.environ, {'OPENAI_API_KEY': '', 'OPENAI_MEETING_MODEL': 'deepseek-v4.1-flash-1017', 'AI_PROVIDER': 'deepseek'}), \
                    patch('services.ai_config.ENV_FILE', env_file), \
                    patch.object(OpenAIService, 'probe_model',
                                 return_value=(True, 'DeepSeek reachable')) as probe:
                anonymous = app.test_client()
                self.assertEqual(anonymous.get('/api/admin/ai-status').status_code, 401)

                member = app.test_client()
                self.assertEqual(member.post('/api/auth/login', json={
                    'username_or_email': 'member_my', 'password': 'Password123!'
                }).status_code, 200)
                self.assertEqual(member.get('/api/admin/ai-status').status_code, 403)

                admin = app.test_client()
                self.assertEqual(admin.post('/api/auth/login', json={
                    'username_or_email': 'admin', 'password': 'Password123!'
                }).status_code, 200)
                status = admin.get('/api/admin/ai-status')
                self.assertEqual(status.status_code, 200)
                self.assertTrue(status.get_json()['configured'])
                self.assertFalse(status.get_json()['api_checked'])
                self.assertEqual(status.get_json()['meeting_model'], OpenAIService().meeting_model)
                self.assertNotIn('file_test_secret', status.get_data(as_text=True))
                self.assertNotIn('key_source', status.get_data(as_text=True))
                probe.assert_not_called()

                checked = admin.get('/api/admin/ai-status?probe=1')
                self.assertEqual(checked.status_code, 200)
                self.assertTrue(checked.get_json()['api_reachable'])
                self.assertNotIn('file_test_secret', checked.get_data(as_text=True))
                self.assertEqual(probe.call_count, 1)


if __name__ == '__main__':
    unittest.main()
