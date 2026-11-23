import io
import json
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from course_core import CourseError
from course_workflow import advance, new_job
from engines import EngineConfig, ProviderUnavailable, generate_course
from test_workflow import MODULE, response


SOURCE = 'drone 101\n1. drone componenta'
URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-4-hydrogen:generateContent'


class GeminiFlashTests(unittest.TestCase):
    def setUp(self):
        self.config = EngineConfig('Google AI Studio (Gemini)', 'fake-secret', 'gemini-4-hydrogen')

    def test_uncertain_submission_is_not_replayed(self):
        for error in (TimeoutError('fake-secret'), HTTPError(URL, 504, 'fake-secret', {}, io.BytesIO())):
            with self.subTest(error=type(error)), patch('engines.build_opener') as opener:
                send = opener.return_value.open
                send.side_effect = error
                with self.assertRaises(CourseError) as caught:
                    generate_course(SOURCE, '', self.config)
                self.assertNotIn('fake-secret', str(caught.exception))
                send.assert_called_once()

    def test_explicit_http_503_retries_identical_direct_request(self):
        overloaded = HTTPError(URL, 503, 'fake-secret', {'Retry-After': '15'}, io.BytesIO())
        success = io.BytesIO(json.dumps(response(MODULE)).encode())
        progress = []
        with patch('engines.build_opener') as opener, patch('engines.time.sleep') as sleep:
            send = opener.return_value.open
            send.side_effect = [overloaded, success]
            job = advance(new_job(SOURCE, '', self.config), self.config, on_progress=progress.append)
        self.assertEqual(len(job['completed']), 1)
        self.assertEqual(progress, ['retrying'])
        sleep.assert_called_once_with(15)
        first, second = [c.args[0] for c in send.call_args_list]
        self.assertEqual(first.data, second.data)
        payload = json.loads(second.data)
        self.assertEqual(first.full_url, URL)
        self.assertEqual(second.full_url, URL)
        self.assertEqual(payload['generationConfig']['maxOutputTokens'], 65536)
        self.assertEqual(payload['generationConfig']['thinkingConfig']['thinkingLevel'], 'medium')
        self.assertIn(SOURCE, payload['contents'][0]['parts'][0]['text'])
        self.assertIn('## Module 1: drone componenta', job['completed'][0])

    def test_retry_budget_and_long_retry_after_stop_without_extra_calls(self):
        for wait, calls, delays in [(0, 3, [10, 30]), (90, 1, [])]:
            with self.subTest(wait=wait), patch('engines.time.sleep') as sleep, \
                    patch('engines.request_json', side_effect=ProviderUnavailable('HTTP 503', wait)) as send:
                with self.assertRaisesRegex(CourseError, 'HTTP 503'):
                    generate_course(SOURCE, '', self.config)
                self.assertEqual(send.call_count, calls)
                self.assertEqual([c.args[0] for c in sleep.call_args_list], delays)

    def test_flash_lite_also_recovers_from_http_503_without_thinking_config(self):
        url = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent'
        cfg = EngineConfig('Google AI Studio (Gemini)', 'fake-secret', 'gemini-3.5-flash-lite')
        overloaded = HTTPError(url, 503, 'fake-secret', {'Retry-After': '12'}, io.BytesIO())
        success = io.BytesIO(json.dumps(response(MODULE)).encode())
        progress = []
        with patch('engines.build_opener') as opener, patch('engines.time.sleep') as sleep:
            send = opener.return_value.open
            send.side_effect = [overloaded, success]
            job = advance(new_job(SOURCE, '', cfg), cfg, on_progress=progress.append)
        self.assertEqual(len(job['completed']), 1)
        self.assertEqual(progress, ['retrying'])
        sleep.assert_called_once_with(12)
        req = send.call_args_list[-1].args[0]
        payload = json.loads(req.data)
        self.assertEqual(req.full_url, url)
        self.assertEqual(payload['generationConfig'], {'maxOutputTokens': 16384})
