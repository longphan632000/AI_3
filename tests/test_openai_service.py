"""OpenAI-compatible defaults and wire contract without external API calls."""

import json
import os
import ssl
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import httpx
from openai import OpenAI

from services.ai_config import key_is_configured
from services.ai_errors import AIProviderError
from services.ai_provider_service import AIProviderService
from services.openai_service import OpenAIService


class TestOpenAIService(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.env_file = Path(directory.name) / '.env'
        file_patch = patch('services.ai_config.ENV_FILE', self.env_file)
        file_patch.start()
        self.addCleanup(file_patch.stop)
        env_patch = patch.dict(os.environ, {
            'AI_CONFIG_SOURCE': 'process',
            'AI_PROVIDER': 'deepseek',
            'OPENAI_API_KEY': 'test_openai_key',
            'KIRA_API_KEY': 'test_legacy_key',
            'KIRA_BASE_URL': 'https://legacy.invalid/v1',
            'KIRA_MODEL': 'legacy-model',
        }, clear=True)
        env_patch.start()
        self.addCleanup(env_patch.stop)

    def client(self, service, handler):
        client = OpenAI(
            api_key=service.api_key, base_url=service.base_url, max_retries=0,
            http_client=httpx.Client(transport=httpx.MockTransport(handler)),
        )
        self.addCleanup(client.close)
        return client

    @staticmethod
    def response(content='OK', **message_fields):
        return httpx.Response(200, json={
            'id': 'test', 'object': 'chat.completion', 'created': 0,
            'model': 'deepseek-v4.1-flash-1017',
            'choices': [{'index': 0, 'finish_reason': 'stop',
                         'message': {'role': 'assistant', 'content': content, **message_fields}}],
        })

    def test_default_provider_uses_deepseek_and_openai_settings(self):
        provider = AIProviderService()
        self.assertEqual(provider.provider_name, 'deepseek')
        self.assertIsInstance(provider.provider, OpenAIService)
        self.assertEqual(provider.provider.model, 'deepseek-v4.1-flash-1017')
        self.assertEqual(provider.provider.meeting_model, provider.provider.model)
        self.assertEqual(provider.provider.base_url, 'https://discovery-api.intern-ai.org.cn/v1')
        self.assertEqual(provider.provider.api_key, 'test_openai_key')

    def test_real_sdk_posts_to_configured_endpoint_with_bearer_auth(self):
        captured = []

        def handle(request):
            captured.append(request)
            return self.response('  Kết nối thành công.  ')

        service = OpenAIService()
        with patch.object(service, '_get_client', return_value=self.client(service, handle)):
            result = service.generate_content('Kiểm tra', max_output_tokens=64)
        self.assertEqual(result, 'Kết nối thành công.')
        self.assertEqual(len(captured), 1)
        request = captured[0]
        self.assertEqual(request.method, 'POST')
        self.assertEqual(str(request.url), 'https://discovery-api.intern-ai.org.cn/v1/chat/completions')
        self.assertEqual(request.headers['authorization'], 'Bearer test_openai_key')
        payload = json.loads(request.content)
        self.assertEqual(payload['model'], 'deepseek-v4.1-flash-1017')
        self.assertEqual(payload['messages'], [{'role': 'user', 'content': 'Kiểm tra'}])
        self.assertEqual(payload['max_tokens'], 64)
        self.assertNotIn('response_format', payload)

    def test_json_uses_meeting_model_and_excludes_reasoning(self):
        captured = []

        def handle(request):
            captured.append(json.loads(request.content))
            return self.response('{"items": []}', reasoning_content='Private reasoning')

        service = OpenAIService()
        with patch.object(service, '_get_client', return_value=self.client(service, handle)):
            result = service.generate_content('Return JSON', json_output=True)
        self.assertEqual(json.loads(result), {'items': []})
        self.assertNotIn('Private reasoning', result)
        self.assertEqual(captured[0]['model'], 'deepseek-v4.1-flash-1017')
        self.assertEqual(captured[0]['response_format'], {'type': 'json_object'})
        self.assertEqual(captured[0]['reasoning_effort'], 'none')

    def test_live_file_switch_overrides_stale_provider_and_cleared_key(self):
        config = (
            'AI_PROVIDER=openai\nOPENAI_MODEL=deepseek-v4.1-flash-1017\n'
            'OPENAI_API_KEY=\n'
        )
        self.env_file.write_text(config, encoding='utf-8')
        with patch.dict(os.environ, {'AI_CONFIG_SOURCE': 'env_file', 'AI_PROVIDER': 'kira'}):
            first = AIProviderService()
            self.assertEqual(first.provider_name, 'deepseek')
            self.assertFalse(first.provider.configured)
            self.env_file.write_text(config.replace('OPENAI_API_KEY=\n', 'OPENAI_API_KEY=new_test_key\n'), encoding='utf-8')
            second = AIProviderService()
            self.assertTrue(second.provider.configured)
            self.assertEqual(second.provider.api_key, 'new_test_key')

    def test_legacy_key_cannot_configure_openai_provider(self):
        with patch.dict(os.environ, {'OPENAI_API_KEY': ''}):
            service = OpenAIService()
        self.assertFalse(service.configured)
        with patch.object(service, '_get_client') as client:
            with self.assertRaises(AIProviderError) as raised:
                service.generate_content('Hello')
            client.assert_not_called()
        self.assertEqual(raised.exception.code, 'AI_KEY_MISSING')
        self.assertNotIn('Kira', str(raised.exception))
        self.assertFalse(key_is_configured('your_openai_api_key'))

    def test_removed_providers_are_rejected_before_calling_sdk(self):
        with patch.object(OpenAIService, '_get_client') as client:
            for provider in ('kira', 'qwen', 'unknown'):
                with self.subTest(provider=provider), self.assertRaises(AIProviderError) as raised:
                    AIProviderService(provider)
                self.assertEqual(raised.exception.code, 'AI_CONFIG')
            client.assert_not_called()

    def test_other_models_are_rejected_for_general_and_meeting_tasks(self):
        for field in ('OPENAI_MODEL', 'OPENAI_MEETING_MODEL'):
            with self.subTest(field=field), patch.dict(os.environ, {field: 'gemini-3.8-flash'}):
                with self.assertRaises(AIProviderError) as raised:
                    OpenAIService()
                self.assertEqual(raised.exception.code, 'AI_CONFIG')

    def test_probe_requires_nonempty_text(self):
        service = OpenAIService()
        client = self.client(service, lambda request: self.response(''))
        with patch.object(service, '_get_client', return_value=client):
            ok, _ = service.probe_model()
        self.assertFalse(ok)
        self.assertEqual(service.last_probe_error_code, 'AI_INVALID_RESPONSE')
        self.assertEqual(service.probe_scope, 'chat_completion')

    def test_authentication_errors_do_not_expose_upstream_secrets(self):
        service = OpenAIService()
        def client_factory(**kwargs):
            return self.client(service, lambda request: httpx.Response(
                401, json={'error': {'message': 'test_openai_key private upstream details'}}))

        with patch.object(service, '_get_client', side_effect=client_factory):
            ok, message = service.probe_model()
            self.assertFalse(ok)
            self.assertEqual(service.last_probe_error_code, 'AI_KEY_REJECTED')
            self.assertEqual(service.last_probe_diagnostics, {'http_status': 401})
            self.assertNotIn('test_openai_key', message)
            with self.assertRaises(AIProviderError) as raised:
                service.generate_content('Hello')
        self.assertEqual(raised.exception.code, 'AI_KEY_REJECTED')
        self.assertNotIn('private upstream details', str(raised.exception))

    def test_interrupted_tls_connection_retries_without_ignoring_certificates(self):
        service = OpenAIService()
        attempts = []

        def handle(request):
            attempts.append(request)
            if len(attempts) == 1:
                raise httpx.ConnectError('private transport detail', request=request) from ssl.SSLEOFError()
            return self.response('OK')

        with patch.object(service, '_get_client', return_value=self.client(service, handle)), \
                patch('services.openai_service.pause_retry') as retry:
            self.assertEqual(service.generate_content('Test'), 'OK')
        self.assertEqual(len(attempts), 2)
        retry.assert_called_once_with(1)


if __name__ == '__main__':
    unittest.main()
