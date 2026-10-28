"""Unit and integration tests for Kira AI provider adapter."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from services.ai_errors import AIProviderError
from services.ai_provider_service import AIProviderService
from services.kira_service import KiraAIService


class TestKiraService(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        file_patch = patch('services.ai_config.ENV_FILE', Path(directory.name) / 'missing.env')
        file_patch.start()
        self.addCleanup(file_patch.stop)
        env_patch = patch.dict(os.environ, {'AI_CONFIG_SOURCE': 'process'})
        env_patch.start()
        self.addCleanup(env_patch.stop)

    def test_kira_service_init_and_configured(self):
        with patch.dict(os.environ, {
            'AI_PROVIDER': 'kira',
            'KIRA_API_KEY': 'kira_test_key_123',
            'KIRA_BASE_URL': 'https://kiraai.vn/api/v1',
            'KIRA_MODEL': 'qwen3.8-flash-next-free',
        }):
            service = KiraAIService()
            self.assertTrue(service.configured)
            self.assertEqual(service.model, 'qwen3.8-flash-next-free')
            self.assertEqual(service.base_url, 'https://kiraai.vn/api/v1')

    def test_kira_service_unconfigured_raises_on_generate(self):
        with tempfile.TemporaryDirectory() as directory, \
                patch('services.ai_config.ENV_FILE', Path(directory) / 'missing.env'), \
                patch.dict(os.environ, {'KIRA_API_KEY': ''}):
            service = KiraAIService()
            self.assertFalse(service.configured)
            with self.assertRaises(AIProviderError) as ctx:
                service.generate_content('Hello')
            self.assertEqual(ctx.exception.code, 'AI_KEY_MISSING')

    def test_probe_model_success(self):
        with patch.dict(os.environ, {'KIRA_API_KEY': 'kira_test_key_123'}):
            service = KiraAIService()
            mock_client = MagicMock()
            mock_choice = MagicMock()
            mock_choice.message.content = 'pong'
            mock_client.chat.completions.create.return_value = MagicMock(choices=[mock_choice])
            with patch.object(service, '_get_client', return_value=mock_client):
                ok, msg = service.probe_model()
                self.assertTrue(ok)
                self.assertIn('sẵn sàng', msg)

    def test_generate_content_success(self):
        with patch.dict(os.environ, {'KIRA_API_KEY': 'kira_test_key_123'}):
            service = KiraAIService()
            mock_client = MagicMock()
            mock_choice = MagicMock()
            mock_choice.message.content = 'Báo cáo tiến độ hoàn thành tốt.'
            mock_choice.finish_reason = 'stop'
            mock_client.chat.completions.create.return_value = MagicMock(choices=[mock_choice])
            with patch.object(service, '_get_client', return_value=mock_client):
                res = service.generate_content('Viết báo cáo')
                self.assertEqual(res, 'Báo cáo tiến độ hoàn thành tốt.')
                mock_client.chat.completions.create.assert_called_once()
                kwargs = mock_client.chat.completions.create.call_args[1]
                self.assertEqual(kwargs['model'], 'qwen3.8-flash-next-free')
                self.assertEqual(kwargs['messages'], [{'role': 'user', 'content': 'Viết báo cáo'}])

    def test_generate_content_json_output(self):
        with patch.dict(os.environ, {'KIRA_API_KEY': 'kira_test_key_123'}):
            service = KiraAIService()
            mock_client = MagicMock()
            mock_choice = MagicMock()
            mock_choice.message.content = '{"items": []}'
            mock_choice.finish_reason = 'stop'
            mock_client.chat.completions.create.return_value = MagicMock(choices=[mock_choice])
            with patch.object(service, '_get_client', return_value=mock_client):
                res = service.generate_content('Trả về JSON', json_output=True)
                self.assertEqual(res, '{"items": []}')
                kwargs = mock_client.chat.completions.create.call_args[1]
                self.assertEqual(kwargs['response_format'], {'type': 'json_object'})

    def test_ai_provider_service_routing(self):
        for provider in ('kira', 'unknown'):
            with self.subTest(provider=provider), patch.dict(os.environ, {'AI_PROVIDER': provider}):
                with self.assertRaises(AIProviderError) as raised:
                    AIProviderService()
                self.assertEqual(raised.exception.code, 'AI_CONFIG')


if __name__ == '__main__':
    unittest.main()
