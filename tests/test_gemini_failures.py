"""Provider failures must be classified without leaking prompts or credentials."""

import io
import http.client
import json
import os
import errno
import socket
import ssl
import unittest
import urllib.error
from unittest.mock import patch

from services.gemini_service import AIProviderError, GeminiService


def _response(text='Xin chào'):
    payload = {'candidates': [{'content': {'parts': [{'text': text}]}}]}
    return io.BytesIO(json.dumps(payload).encode('utf-8'))


def _http_error(status):
    return urllib.error.HTTPError('https://example.invalid', status, 'failure', {}, None)


class TestGeminiFailures(unittest.TestCase):
    def setUp(self):
        self.key_patch = patch.dict(os.environ, {
            'AI_CONFIG_SOURCE': 'process',
            'GEMINI_API_KEY': 'test_secret_key',
            'GEMINI_MODEL': 'general_test_model',
            'GEMINI_MEETING_MODEL': 'meeting_test_model',
            'AI_TIMEOUT_SECONDS': '30',
            'AI_MEETING_TIMEOUT_SECONDS': '90',
        })
        self.key_patch.start()
        self.addCleanup(self.key_patch.stop)
        self.service = GeminiService()

    def test_timeout_retries_then_succeeds_with_meeting_timeout(self):
        with patch('services.gemini_service.urllib.request.urlopen',
                   side_effect=[TimeoutError(), _response()]) as urlopen, \
                patch('services.ai_deadline.time.sleep') as sleep:
            self.assertEqual(self.service.generate_content('meeting', json_output=True), 'Xin chào')
        self.assertEqual(urlopen.call_count, 2)
        self.assertEqual(urlopen.call_args.kwargs['timeout'], 90)
        self.assertIn('/models/meeting_test_model:generateContent', urlopen.call_args.args[0].full_url)
        sleep.assert_called_once_with(1)

    def test_other_ai_modes_keep_the_general_model(self):
        with patch('services.gemini_service.urllib.request.urlopen', return_value=_response()) as urlopen:
            self.service.generate_content('weekly report')
        self.assertIn('/models/general_test_model:generateContent', urlopen.call_args.args[0].full_url)

    def test_persistent_timeout_returns_specific_safe_error(self):
        with patch('services.gemini_service.urllib.request.urlopen',
                   side_effect=TimeoutError()) as urlopen, \
                patch('services.ai_deadline.time.sleep'):
            with self.assertRaises(AIProviderError) as caught:
                self.service.generate_content('private meeting text')
        self.assertEqual(caught.exception.code, 'AI_TIMEOUT')
        self.assertEqual(urlopen.call_count, 3)
        self.assertNotIn('private meeting text', str(caught.exception))
        self.assertNotIn('test_secret_key', str(caught.exception))

    def test_connection_failure_and_invalid_json_are_distinct(self):
        with patch('services.gemini_service.urllib.request.urlopen',
                   side_effect=urllib.error.URLError('dns failure')), \
                patch('services.ai_deadline.time.sleep'):
            with self.assertRaises(AIProviderError) as caught:
                self.service.generate_content('meeting')
        self.assertEqual(caught.exception.code, 'AI_CONNECTION')

        with patch('services.gemini_service.urllib.request.urlopen',
                   return_value=io.BytesIO(b'<html>proxy error</html>')) as urlopen:
            with self.assertRaises(AIProviderError) as caught:
                self.service.generate_content('meeting')
        self.assertEqual(caught.exception.code, 'AI_INVALID_RESPONSE')
        urlopen.assert_called_once()

        with patch('services.gemini_service.urllib.request.urlopen',
                   side_effect=http.client.IncompleteRead(b'partial')), \
                patch('services.ai_deadline.time.sleep'):
            with self.assertRaises(AIProviderError) as caught:
                self.service.generate_content('meeting')
        self.assertEqual(caught.exception.code, 'AI_CONNECTION')

    def test_service_unavailable_retries_and_rate_limit_is_separate(self):
        with patch('services.gemini_service.urllib.request.urlopen',
                   side_effect=[_http_error(503), _response()]) as urlopen, \
                patch('services.ai_deadline.time.sleep'):
            self.assertEqual(self.service.generate_content('meeting'), 'Xin chào')
        self.assertEqual(urlopen.call_count, 2)

        with patch('services.gemini_service.urllib.request.urlopen',
                   side_effect=_http_error(429)), \
                patch('services.ai_deadline.time.sleep'):
            with self.assertRaises(AIProviderError) as caught:
                self.service.generate_content('meeting')
        self.assertEqual(caught.exception.code, 'AI_RATE_LIMIT')

    def test_network_denied_is_not_retried_and_secrets_are_not_logged(self):
        denied=PermissionError(errno.EACCES,'test_secret_key private meeting text')
        denied.winerror=10013
        for error in [denied,urllib.error.URLError(denied),OSError(10013,'test_secret_key')]:
            with self.subTest(wrapped=type(error).__name__), \
                    patch('services.gemini_service.urllib.request.urlopen',side_effect=error) as network, \
                    patch('services.ai_deadline.time.sleep') as sleep, \
                    self.assertLogs('services.gemini_service',level='WARNING') as logs:
                with self.assertRaises(AIProviderError) as caught:
                    self.service.generate_content('private meeting text')
                self.assertEqual(caught.exception.code,'AI_NETWORK_DENIED')
                self.assertFalse(caught.exception.retryable)
                network.assert_called_once();sleep.assert_not_called()
                for text in [str(caught.exception),' '.join(logs.output)]:
                    self.assertNotIn('test_secret_key',text)
                    self.assertNotIn('private meeting text',text)

    def test_tls_failures_keep_verification_and_do_not_retry(self):
        for error,code in [(ssl.SSLCertVerificationError(1,'test_secret_key'),'AI_TLS_CERTIFICATE'),
                           (ssl.SSLError(1,'handshake'),'AI_TLS_ERROR')]:
            with self.subTest(code=code), \
                    patch('services.gemini_service.urllib.request.urlopen',side_effect=urllib.error.URLError(error)) as network, \
                    patch('services.ai_deadline.time.sleep') as sleep:
                with self.assertRaises(AIProviderError) as caught:
                    self.service.generate_content('note')
                self.assertEqual(caught.exception.code,code)
                network.assert_called_once();sleep.assert_not_called()

    def test_permanent_dns_failure_is_separate_from_connection(self):
        with patch('services.gemini_service.urllib.request.urlopen',side_effect=urllib.error.URLError(socket.gaierror(socket.EAI_NONAME,'host not found'))) as network, \
                patch('services.ai_deadline.time.sleep') as sleep:
            with self.assertRaises(AIProviderError) as caught:
                self.service.generate_content('note')
        self.assertEqual(caught.exception.code,'AI_DNS')
        network.assert_called_once();sleep.assert_not_called()

    def test_temporary_dns_failure_can_recover(self):
        with patch('services.gemini_service.urllib.request.urlopen',side_effect=[urllib.error.URLError(socket.gaierror(socket.EAI_AGAIN,'temporary')),_response()]) as network, \
                patch('services.ai_deadline.time.sleep') as sleep:
            self.assertEqual(self.service.generate_content('note'),'Xin chào')
        self.assertEqual(network.call_count,2)
        sleep.assert_called_once_with(1)

    def test_http_errors_are_distinct_and_never_echo_provider_body(self):
        for status,code in [(400,'AI_HTTP_ERROR'),(401,'AI_KEY_REJECTED'),(403,'AI_KEY_REJECTED'),
                            (404,'AI_MODEL_UNAVAILABLE'),(429,'AI_RATE_LIMIT'),(503,'AI_SERVICE_UNAVAILABLE')]:
            with self.subTest(status=status),patch('services.gemini_service.urllib.request.urlopen',side_effect=_http_error(status)) as network,patch('services.ai_deadline.time.sleep'):
                with self.assertRaises(AIProviderError) as caught:
                    self.service.generate_content('note')
                self.assertEqual(caught.exception.code,code)
                self.assertEqual(network.call_count,3 if status in (429,503) else 1)
        body=json.dumps({'error':{'message':'test_secret_key','details':[{'reason':'API_KEY_INVALID'}]}}).encode()
        invalid=urllib.error.HTTPError('https://example.invalid',400,'bad',{},io.BytesIO(body))
        with patch('services.gemini_service.urllib.request.urlopen',side_effect=invalid):
            with self.assertRaises(AIProviderError) as caught:
                self.service.generate_content('note')
        self.assertEqual(caught.exception.code,'AI_KEY_REJECTED')
        self.assertNotIn('test_secret_key',str(caught.exception))

    def test_probe_uses_same_transport_classifier_and_clears_old_error(self):
        denied=PermissionError(errno.EACCES,'secret')
        denied.winerror=10013
        with patch('services.gemini_service.urllib.request.urlopen',side_effect=urllib.error.URLError(denied)):
            ok,message=self.service.probe_model()
        self.assertFalse(ok)
        self.assertEqual(self.service.last_probe_error_code,'AI_NETWORK_DENIED')
        self.assertEqual(self.service.last_probe_diagnostics['winerror'],10013)
        self.assertNotIn('secret',message)
        with patch('services.gemini_service.urllib.request.urlopen',return_value=_response('OK')) as network:
            self.assertTrue(self.service.probe_model()[0])
        self.assertEqual(network.call_args.args[0].method, 'POST')
        self.assertEqual(self.service.probe_scope, 'generate_content')
        self.assertIsNone(self.service.last_probe_error_code)
        self.assertEqual(self.service.last_probe_diagnostics,{})


if __name__ == '__main__':
    unittest.main()
