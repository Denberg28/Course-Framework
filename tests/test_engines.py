import io
import json
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from course_core import CourseError, SAMPLE
from engines import EngineConfig, NoRedirect, generate_course, request_json, validate_endpoint


class EngineTests(unittest.TestCase):
    def test_local_never_calls_network(self):
        with patch('engines.request_json', side_effect=AssertionError('network')):
            self.assertIn('## Module 1:', generate_course(SAMPLE, 'Course', EngineConfig()))

    def test_gemini_header_and_response(self):
        def send(url, headers, payload):
            self.assertIn('/gemini-3.5-flash-lite:generateContent', url)
            self.assertNotIn('fake-secret', url)
            self.assertEqual(headers['x-goog-api-key'], 'fake-secret')
            self.assertIn('generateContent', url)
            self.assertIn('systemInstruction', payload)
            return {'candidates': [{'finishReason': 'STOP', 'content': {'parts': [{'text': '# Course\nLesson content'}]}}]}
        config = EngineConfig('Google AI Studio (Gemini)', 'fake-secret')
        self.assertNotIn('fake-secret', repr(config))
        self.assertIn('Lesson content', generate_course(SAMPLE, 'Course', config, transport=send))

    def test_flash_reasoning_settings_reach_the_request_wrapper(self):
        answer = {'candidates': [{'finishReason': 'STOP', 'content': {'parts': [{'text': 'Final lesson'}]}}]}
        for model in ('gemini-3.8-flash', 'models/gemini-3.8-flash', 'gemini-3.5-flash-lite', 'custom-model'):
            with self.subTest(model=model), patch('engines.request_json', return_value=answer) as send:
                generate_course(SAMPLE, '', EngineConfig('Google AI Studio (Gemini)', 'fake-secret', model))
                is_flash = model.removeprefix('models/') == 'gemini-3.8-flash'
                self.assertEqual(send.call_args.kwargs['timeout'], 180 if is_flash else 60)
                settings = send.call_args.args[2]['generationConfig']
                self.assertEqual(settings['maxOutputTokens'], 32768 if is_flash else 16384)
                if is_flash:
                    self.assertEqual(settings['thinkingConfig'], {'thinkingLevel': 'medium', 'includeThoughts': True})
                    self.assertIn(':streamGenerateContent?alt=sse', send.call_args.args[0])
                    self.assertTrue(send.call_args.kwargs['stream'])
                    self.assertEqual(send.call_args.args[1]['Accept'], 'text/event-stream')
                else:
                    self.assertNotIn('thinkingConfig', settings)
                    self.assertNotIn('stream', send.call_args.kwargs)
                self.assertNotIn('fake-secret', send.call_args.args[0])

    def test_extended_timeout_is_applied_once_and_errors_are_distinct(self):
        for error in (TimeoutError('fake-secret'), URLError(TimeoutError('fake-secret')),
                      URLError('fake-secret'), HTTPError('https://fake-secret', 504, 'fake-secret', {}, io.BytesIO())):
            with self.subTest(error=type(error)), patch('engines.build_opener') as opener:
                opener.return_value.open.side_effect = error
                with self.assertRaises(CourseError) as raised:
                    request_json('https://example.com', {}, {}, timeout=180)
                self.assertEqual(opener.return_value.open.call_count, 1)
                self.assertEqual(opener.return_value.open.call_args.kwargs['timeout'], 180)
                message = str(raised.exception)
                self.assertNotIn('fake-secret', message)
                if isinstance(error, HTTPError):
                    self.assertIn('HTTP 504', message)
                elif isinstance(error, TimeoutError) or isinstance(error.reason, TimeoutError):
                    self.assertIn('180-second', message)
                else:
                    self.assertIn('Could not connect', message)

    def test_gemini_finish_reasons_do_not_conflate_limits_and_blocks(self):
        cfg = EngineConfig('Google AI Studio (Gemini)', 'fake-secret', 'gemini-3.8-flash')
        for reason, expected in [('MAX_TOKENS', '32,768-token'), ('CONTINUATION', 'Automatic extra requests are off'),
                                 ('SAFETY', 'content policy'), ('RECITATION', 'source recitation'),
                                 ('fake-secret', 'stopped before completing')]:
            answer = {'candidates': [{'finishReason': reason, 'content': {'parts': [{'text': 'Incomplete content'}]}}]}
            with self.subTest(reason=reason), self.assertRaises(CourseError) as raised:
                generate_course(SAMPLE, '', cfg, transport=lambda *a: answer)
            self.assertIn(expected, str(raised.exception))
            self.assertNotIn('fake-secret', str(raised.exception))

    def test_openai_compatible_and_revision(self):
        def send(url, headers, payload):
            self.assertEqual(url, 'http://localhost:1234/v1/chat/completions')
            self.assertEqual(headers, {})
            self.assertIn('Add an example', payload['messages'][1]['content'])
            self.assertIn('<draft>', payload['messages'][1]['content'])
            self.assertEqual(payload['model'], 'local-model')
            return {'choices': [{'finish_reason': 'stop', 'message': {'content': '# Revised course'}}]}
        result = generate_course(SAMPLE, 'Course', EngineConfig('OpenAI-compatible', '', 'local-model', 'http://localhost:1234/v1', True),
                                 draft='Old course', instructions='Add an example', transport=send)
        self.assertIn('Revised', result)

    def test_reject_missing_key_invalid_model_and_local_revision(self):
        for config, draft in [(EngineConfig('Google AI Studio (Gemini)'), ''),
                              (EngineConfig('Google AI Studio (Gemini)', 'fake', 'bad model'), ''),
                              (EngineConfig('Google AI Studio (Gemini)', 'invalid🔑'), ''),
                              (EngineConfig(), 'Draft')]:
            with self.subTest(config=config), self.assertRaises(CourseError):
                generate_course(SAMPLE, 'Course', config, draft=draft)

    def test_incomplete_or_malformed_provider_output_rejected(self):
        for response in [{}, {'candidates': []}, {'candidates': [{'finishReason': 'MAX_TOKENS'}]},
                         {'candidates': [{'finishReason': 'STOP', 'content': {'parts': [{'text': 'fake-secret'}]}}]}]:
            with self.subTest(response=response), self.assertRaises(CourseError):
                generate_course(SAMPLE, 'Course', EngineConfig('Google AI Studio (Gemini)', 'fake-secret'), transport=lambda *a: response)
        for reason in ('length', 'content_filter', None):
            with self.assertRaises(CourseError):
                generate_course(SAMPLE, 'Course', EngineConfig('OpenAI-compatible', 'fake', 'model', 'https://example.com/v1', True),
                                transport=lambda *a: {'choices': [{'finish_reason': reason, 'message': {'content': 'partial'}}]})

    def test_endpoint_credential_and_insecure_url_rejected(self):
        for url in ['http://example.com/v1', 'https://user:secret@example.com/v1', 'https://example.com?key=secret',
                    'https://example.com#fragment', 'https://example.com:bad/v1', 'not-a-url',
                    'https://example.com/bad path', 'https://例子.com/v1']:
            with self.subTest(url=url), self.assertRaises(CourseError):
                validate_endpoint(url, True)
        with self.assertRaises(CourseError):
            validate_endpoint('https://127.0.0.1/v1', False)
        self.assertEqual(validate_endpoint('http://localhost:1234/v1/', True), 'http://localhost:1234/v1')

    def test_http_and_network_errors_are_sanitized(self):
        for error in [HTTPError('https://fake-secret', 429, 'fake-secret', {}, io.BytesIO(b'fake-secret')),
                      URLError('fake-secret')]:
            with patch('engines.build_opener') as opener:
                opener.return_value.open.side_effect = error
                with self.assertRaises(CourseError) as raised:
                    request_json('https://example.com', {}, {})
                self.assertNotIn('fake-secret', str(raised.exception))

    def test_redirects_are_not_followed(self):
        self.assertIsNone(NoRedirect().redirect_request(None, None, 302, '', {}, 'https://elsewhere.example'))

    def test_provider_response_size_is_bounded(self):
        with patch('engines.build_opener') as opener:
            opener.return_value.open.return_value.__enter__.return_value.read.return_value = b'x' * (2 * 1024 * 1024 + 1)
            with self.assertRaisesRegex(CourseError, '2 MB'):
                request_json('https://example.com', {}, {})


if __name__ == '__main__':
    unittest.main()
