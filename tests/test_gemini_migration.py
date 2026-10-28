"""Gemini as the primary provider, without touching production data or real keys."""

import io
import json
import os
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch
from uuid import uuid4

from services.ai_errors import AIProviderError
from services.ai_provider_service import AIProviderService
from services.gemini_service import GeminiService
from services.openai_service import OpenAIService


def response(text='OK', **candidate_fields):
    return io.BytesIO(json.dumps({'candidates': [{'finishReason': 'STOP',
        'content': {'parts': [{'text': text}]}, **candidate_fields}]}).encode('utf-8'))


class GeminiCase(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.env_file = Path(directory.name) / '.env'
        config = patch('services.ai_config.ENV_FILE', self.env_file)
        config.start()
        self.addCleanup(config.stop)
        env = patch.dict(os.environ, {
            'AI_CONFIG_SOURCE': 'process', 'AI_PROVIDER': 'gemini', 'GEMINI_API_KEY': 'gemini_test_secret',
            'GEMINI_MODEL': 'gemini-3.8-flash', 'GEMINI_MEETING_MODEL': 'gemini-3.8-flash',
            'OPENAI_API_KEY': 'legacy_deepseek_secret', 'AI_LOCAL_FALLBACK_ENABLED': 'true',
            'LOCAL_AI_MODEL_ENABLED': 'false', 'LOCAL_AI_AUTOSTART': 'false',
            'AI_TOTAL_TIMEOUT_SECONDS': '180', 'AI_PRIMARY_BUDGET_SECONDS': '30',
        })
        env.start()
        self.addCleanup(env.stop)


class TestGeminiMigration(GeminiCase):
    def test_primary_provider_is_gemini_and_does_not_create_deepseek_client(self):
        with patch.object(OpenAIService, '_get_client') as legacy:
            provider = AIProviderService()
            with patch('services.gemini_service.urllib.request.urlopen', return_value=response()):
                self.assertEqual(provider.generate_response('Reply OK'), 'OK')
        self.assertIsInstance(provider.provider, GeminiService)
        legacy.assert_not_called()
        self.assertEqual(provider.execution_metadata()['primary'], 'gemini')
        self.assertEqual(provider.execution_metadata()['used_providers'], ['gemini'])

    def test_default_provider_is_gemini(self):
        with patch.dict(os.environ, {'AI_PROVIDER': ''}):
            self.assertEqual(AIProviderService().provider_name, 'gemini')

    def test_default_model_uses_verified_gemini_flash(self):
        with patch.dict(os.environ, {'GEMINI_MODEL': '', 'GEMINI_MEETING_MODEL': ''}):
            service = GeminiService()
        self.assertEqual(service.model, 'gemini-3.6-flash')
        self.assertEqual(service.meeting_model, service.model)

    def test_wire_request_uses_google_endpoint_and_key_header(self):
        service = GeminiService()
        with patch('services.gemini_service.urllib.request.urlopen', return_value=response('{"items":[]}')) as network:
            service.generate_content('Nguồn kiểm thử', json_output=True)
        request = network.call_args.args[0]
        self.assertEqual(request.full_url, 'https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent')
        self.assertEqual(request.get_header('X-goog-api-key'), 'gemini_test_secret')
        self.assertNotIn('gemini_test_secret', request.full_url)
        payload = json.loads(request.data)
        self.assertEqual(payload['generationConfig']['responseMimeType'], 'application/json')
        self.assertEqual(payload['generationConfig']['thinkingConfig'], {'thinkingLevel': 'low', 'includeThoughts': False})

    def test_live_file_overrides_stale_provider_and_key(self):
        self.env_file.write_text('AI_PROVIDER=gemini\nGEMINI_API_KEY=first_file_key\n', encoding='utf-8')
        with patch.dict(os.environ, {'AI_CONFIG_SOURCE': 'env_file', 'AI_PROVIDER': 'deepseek'}):
            first = AIProviderService()
            self.assertEqual(first.provider.api_key, 'first_file_key')
            self.env_file.write_text('AI_PROVIDER=gemini\nGEMINI_API_KEY=second_file_key\n', encoding='utf-8')
            self.assertEqual(AIProviderService().provider.api_key, 'second_file_key')
            self.env_file.write_text('AI_PROVIDER=gemini\nGEMINI_API_KEY=\n', encoding='utf-8')
            cleared = AIProviderService()
            self.assertEqual(cleared.primary_provider_name, 'gemini')
            self.assertFalse(cleared.provider.configured)

    def test_missing_gemini_key_never_reuses_deepseek_key(self):
        with patch.dict(os.environ, {'GEMINI_API_KEY': 'your_gemini_api_key'}):
            provider = AIProviderService()
        provider.bind_context({'task_type': 'weekly_summary'}, {
            'week_start': '2026-10-26', 'week_end': '2026-11-01', 'tasks': []})
        with patch('services.gemini_service.urllib.request.urlopen') as google, patch.object(OpenAIService, '_get_client') as legacy:
            text = provider.generate_response('Nguồn')
        google.assert_not_called()
        legacy.assert_not_called()
        self.assertIn('Không có nhiệm vụ', text)
        self.assertEqual(provider.execution_metadata()['primary'], 'gemini')
        self.assertEqual(provider.provider_name, 'local_rules')

    def test_probe_requires_successful_content_generation(self):
        service = GeminiService()
        with patch('services.gemini_service.urllib.request.urlopen', return_value=io.BytesIO(
                b'{"supportedGenerationMethods":["generateContent"]}')):
            ok, _ = service.probe_model()
        self.assertFalse(ok)
        self.assertEqual(service.last_probe_error_code, 'AI_INVALID_RESPONSE')
        with patch('services.gemini_service.urllib.request.urlopen', return_value=response()) as network:
            self.assertTrue(service.probe_model()[0])
        self.assertEqual(network.call_args.args[0].method, 'POST')
        self.assertEqual(service.probe_scope, 'generate_content')

    def test_probe_of_different_meeting_model_uses_that_model(self):
        with patch.dict(os.environ, {'GEMINI_MEETING_MODEL': 'gemini-3.8-pro'}):
            service = GeminiService()
        with patch('services.gemini_service.urllib.request.urlopen', return_value=response()) as network:
            self.assertTrue(service.probe_model(service.meeting_model)[0])
        self.assertIn('/gemini-3.8-pro:generateContent', network.call_args.args[0].full_url)

    def test_model_name_cannot_inject_a_url_or_query(self):
        for name in ('../secrets', 'gemini?key=secret', 'https://other.invalid/model'):
            with self.subTest(name=name), patch.dict(os.environ, {'GEMINI_MODEL': name}), self.assertRaises(AIProviderError) as raised:
                GeminiService()
            self.assertEqual(raised.exception.code, 'AI_CONFIG')

    def test_model_prefix_is_normalized(self):
        with patch.dict(os.environ, {'GEMINI_MODEL': 'models/gemini-3.8-flash'}):
            self.assertEqual(GeminiService().model, 'gemini-3.8-flash')

    def test_truncation_and_safety_blocks_are_controlled_errors(self):
        for finish, code in (('MAX_TOKENS', 'AI_INVALID_RESPONSE'), ('SAFETY', 'AI_CONTENT_BLOCKED')):
            with self.subTest(finish=finish), patch('services.gemini_service.urllib.request.urlopen',
                    return_value=response('Không dùng nội dung chưa hoàn chỉnh', finishReason=finish)), self.assertRaises(AIProviderError) as raised:
                GeminiService().generate_content('Nguồn')
            self.assertEqual(raised.exception.code, code)

    def test_thought_parts_are_not_returned_to_user(self):
        payload = {'candidates': [{'finishReason': 'STOP', 'content': {'parts': [
            {'text': 'private reasoning', 'thought': True}, {'text': 'Nội dung cuối'}]}}]}
        with patch('services.gemini_service.urllib.request.urlopen', return_value=io.BytesIO(json.dumps(payload).encode())):
            self.assertEqual(GeminiService().generate_content('Nguồn'), 'Nội dung cuối')

    def test_meeting_json_schema_limits_items_to_source_ids(self):
        from services.local_brain_service import meeting_source_passages
        source = [{'id': 7, 'text': 'Cuộc họp.'}, {'id': 8, 'text': 'Chưa chốt.'}]
        with meeting_source_passages(source), patch('services.gemini_service.urllib.request.urlopen', return_value=response('{"items":[]}')) as network:
            GeminiService().generate_content('NGUỒN:\n[7] Cuộc họp.\n[8] Chưa chốt.', json_output=True)
        schema = json.loads(network.call_args.args[0].data)['generationConfig']['responseJsonSchema']
        items = schema['properties']['items']
        self.assertEqual(items['minItems'], 2)
        self.assertEqual(items['maxItems'], 2)
        self.assertEqual(items['items']['properties']['id']['enum'], [7, 8])

    def test_weekly_outline_numbers_are_not_treated_as_statistics(self):
        from services.ai_response_validator import validate_ai_response
        data = {'tasks': [{'task_id': 8, 'status': 'done'}, {'task_id': 9, 'status': 'todo'}]}
        text = ('Tóm tắt (FR-12)\n### 1. Tổng quan\nHoàn thành 1/2 nhiệm vụ, 50%. [Task #8]\n'
                '### 2. Rủi ro\n[Task #9] cần kiểm tra.\n### 3. Ưu tiên\n**4. Dữ liệu thiếu**')
        result = validate_ai_response(text, {'task_type': 'weekly_summary'}, {'tasks': [8, 9]}, data)
        self.assertTrue(result['is_valid'], result['warnings'])

    def test_real_wrong_statistics_still_fail_even_inside_numbered_sections(self):
        from services.ai_response_validator import validate_ai_response
        data = {'tasks': [{'task_id': 8, 'status': 'done'}, {'task_id': 9, 'status': 'todo'}]}
        for claim in ('Hoàn thành 999 nhiệm vụ', 'Tỷ lệ hoàn thành 100%'):
            with self.subTest(claim=claim):
                result = validate_ai_response('### 3. Tổng quan\n' + claim + ' [Task #8]',
                    {'task_type': 'weekly_summary'}, {'tasks': [8, 9]}, data)
                self.assertFalse(result['is_valid'])


class TestGeminiSQLite(GeminiCase):
    def setUp(self):
        super().setUp()
        from app import app
        from services.project_service import create_project
        self.client = app.test_client()
        with self.client.session_transaction() as session:
            session.update(user_id=2, role='leader')
        ok, message, self.project_id = create_project(2, 'Gemini migration QA', '',
            initial_member_ids=[3, 4], project_code='GEM-' + uuid4().hex[:10])
        self.assertTrue(ok, message)
        result = self.client.post(f'/api/projects/{self.project_id}/tasks', json={
            'title': 'Kiểm thử Gemini Python', 'estimated_hours': 2, 'labels': 'Python', 'due_date': '2026-10-30'})
        self.assertEqual(result.status_code, 201, result.get_json())
        self.task_id = result.get_json()['task_id']

    def request(self, task_type):
        data = {'project_id': self.project_id, 'task_type': task_type}
        if task_type == 'weekly_summary':
            data.update(week_start='2026-10-26', week_end='2026-11-01')
        elif task_type == 'meeting_minutes':
            data.update(raw_notes='Đã thống nhất kiểm thử SQLite.\nLong sẽ kiểm thử trước 30/10/2026.')
        else:
            data.update(task_id=self.task_id)
        return self.client.post('/api/ai', json=data)

    def google(self, request, timeout=None):
        prompt = json.loads(request.data)['contents'][0]['parts'][0]['text']
        if 'NGUỒN:\n' in prompt:
            identifiers = re.findall(r'^\[(\d+)\]', prompt.split('NGUỒN:\n')[-1], re.MULTILINE)
            return response(json.dumps({'items': [[int(identifier), ['discussion'], 'Theo nguồn cuộc họp'] for identifier in identifiers]}))
        if 'Gợi ý 1 đến 3' in prompt:
            member = re.findall(r'\[User #(\d+)\]', prompt)[0]
            return response(f'Đề xuất [User #{member}] cho [Task #{self.task_id}] vì kỹ năng và mức sẵn sàng phù hợp.')
        return response(f'Đối chiếu tiến độ [Task #{self.task_id}] theo dữ liệu nguồn.')

    def test_three_features_use_gemini_and_save_correct_history(self):
        from database.connection import query_db
        with patch('services.gemini_service.urllib.request.urlopen', side_effect=self.google), \
                patch.object(OpenAIService, '_get_client') as legacy:
            for kind in ('weekly_summary', 'meeting_minutes', 'assignment_suggestion'):
                with self.subTest(kind=kind):
                    result = self.request(kind)
                    data = result.get_json()
                    self.assertEqual(result.status_code, 200, data)
                    self.assertEqual(data['engine']['used_providers'], ['gemini'])
                    self.assertFalse(data['engine']['fallback_used'])
                    history = query_db('SELECT * FROM ai_history WHERE draft_id=%s', (data['draft_id'],), one=True)
                    self.assertEqual(history['model_provider'], 'gemini')
        legacy.assert_not_called()

    def test_three_features_keep_working_when_gemini_key_is_missing(self):
        with patch.dict(os.environ, {'GEMINI_API_KEY': 'your_gemini_api_key'}), \
                patch('services.gemini_service.urllib.request.urlopen') as network:
            for kind in ('weekly_summary', 'meeting_minutes', 'assignment_suggestion'):
                with self.subTest(kind=kind):
                    result = self.request(kind)
                    data = result.get_json()
                    self.assertEqual(result.status_code, 200, data)
                    self.assertEqual(data['engine']['primary'], 'gemini')
                    self.assertIn('AI_KEY_MISSING', data['engine']['failure_codes'])
                    self.assertEqual(data['engine']['used_providers'], ['local_rules'])
        network.assert_not_called()

    def test_admin_page_reports_gemini_and_generation_probe_without_exposing_keys(self):
        with self.client.session_transaction() as session:
            session.update(user_id=1, role='admin')
        with patch('services.gemini_service.urllib.request.urlopen', return_value=response()):
            result = self.client.get('/api/admin/ai-status?probe=1')
        data = result.get_json()
        self.assertEqual(data['provider'], 'gemini')
        self.assertTrue(data['api_reachable'])
        self.assertEqual(data['probe_scope'], 'generate_content')
        for secret in ('gemini_test_secret', 'legacy_deepseek_secret'):
            self.assertNotIn(secret, result.get_data(as_text=True))
        html = self.client.get('/admin').get_data(as_text=True)
        self.assertIn("data.provider === 'gemini'", html)

    def test_invalid_gemini_configuration_keeps_provider_name_in_diagnostics(self):
        with self.client.session_transaction() as session:
            session.update(user_id=1, role='admin')
        with patch.dict(os.environ, {'GEMINI_MODEL': 'bad/model'}):
            data = self.client.get('/api/admin/ai-status').get_json()
        self.assertEqual(data['provider'], 'gemini')
        self.assertEqual(data['error_code'], 'AI_CONFIG')
        self.assertTrue(data['fallback']['domain_brain_ready'])


if __name__ == '__main__':
    unittest.main()
