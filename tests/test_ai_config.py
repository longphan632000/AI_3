"""Configuration and admin diagnostics without contacting Gemini or production MySQL."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app import app
from services.ai_config import key_is_configured, resolve_ai_setting
from services.gemini_service import GeminiService


class TestAiConfig(unittest.TestCase):
    def test_blank_process_key_uses_project_env_file(self):
        with tempfile.TemporaryDirectory() as directory:
            env_file = Path(directory) / '.env'
            env_file.write_text('GEMINI_API_KEY=file_test_key\n', encoding='utf-8')
            value, source = resolve_ai_setting(
                'GEMINI_API_KEY', environ={'GEMINI_API_KEY': ''}, env_file=env_file
            )
        self.assertEqual((value, source), ('file_test_key', 'env_file'))

    def test_nonblank_process_key_wins_and_missing_key_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            env_file = Path(directory) / '.env'
            env_file.write_text('GEMINI_API_KEY=file_test_key\n', encoding='utf-8')
            self.assertEqual(resolve_ai_setting(
                'GEMINI_API_KEY', environ={'GEMINI_API_KEY': 'process_test_key'},
                env_file=env_file
            ), ('process_test_key', 'process'))
            self.assertEqual(resolve_ai_setting(
                'GEMINI_API_KEY', environ={'GEMINI_API_KEY': ''},
                env_file=Path(directory) / 'missing.env'
            ), ('', 'default'))
        self.assertFalse(key_is_configured('khoa_api_gemini_cua_ban'))

    def test_admin_diagnostics_require_admin_and_never_return_key(self):
        with tempfile.TemporaryDirectory() as directory:
            env_file = Path(directory) / '.env'
            env_file.write_text('GEMINI_API_KEY=file_test_secret\n', encoding='utf-8')
            with patch.dict(os.environ, {'GEMINI_API_KEY': '', 'GEMINI_MEETING_MODEL': 'gemini-3.5-flash-lite', 'AI_PROVIDER': 'gemini'}), \
                    patch('services.ai_config.ENV_FILE', env_file), \
                    patch.object(GeminiService, 'probe_model',
                                 return_value=(True, 'Gemini reachable')) as probe:
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
                self.assertEqual(status.get_json()['meeting_model'], GeminiService().meeting_model)
                self.assertNotIn('file_test_secret', status.get_data(as_text=True))
                self.assertNotIn('key_source', status.get_data(as_text=True))
                probe.assert_not_called()

                checked = admin.get('/api/admin/ai-status?probe=1')
                self.assertEqual(checked.status_code, 200)
                self.assertTrue(checked.get_json()['api_reachable'])
                self.assertNotIn('file_test_secret', checked.get_data(as_text=True))
                self.assertEqual(probe.call_count, 2)


if __name__ == '__main__':
    unittest.main()
