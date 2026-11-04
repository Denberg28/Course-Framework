import io
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from course_core import CourseError
from course_workflow import advance, new_job
from engines import INTERACTIONS_URL, EngineConfig, TransientEngineError, generate_course
from test_workflow import MODULE, background_response


SOURCE = 'drone 101\n1. drone componenta'


class GeminiBackgroundTests(unittest.TestCase):
    def setUp(self):
        self.config = EngineConfig('Google AI Studio (Gemini)', 'fake-secret', 'gemini-3.8-flash')

    def test_single_post_and_real_http_poll_for_the_exact_drone_outline(self):
        requests = []

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def reply(self, result):
                body = json.dumps(result).encode()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_POST(self):
                data = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                requests.append((self.command, self.path, self.headers['x-goog-api-key'], data))
                self.reply({'id': 'int_drone', 'status': 'queued'})

            def do_GET(self):
                requests.append((self.command, self.path, self.headers['x-goog-api-key'],
                                 self.headers.get('Content-Length')))
                if len(requests) == 2:
                    self.reply({'id': 'int_drone', 'status': 'in_progress'})
                else:
                    result = background_response(MODULE)
                    result['steps'][:0] = [{'type': 'user_input', 'content': [{'type': 'text', 'text': SOURCE}]},
                                           {'type': 'thought', 'content': [{'type': 'text', 'text': 'Private summary'}]}]
                    self.reply(result)

            def do_DELETE(self):
                requests.append((self.command, self.path, self.headers['x-goog-api-key'], None))
                self.send_response(204)
                self.end_headers()

        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, kwargs={'poll_interval': .01}, daemon=True)
        thread.start()
        progress = []
        try:
            with patch('engines.INTERACTIONS_URL', f'http://127.0.0.1:{server.server_port}/v1beta/interactions'), \
                    patch('engines.FLASH_POLL_INTERVAL', .01):
                job = advance(new_job(SOURCE, '', self.config), self.config, on_progress=progress.append)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(2)

        self.assertEqual(progress, ['queued', 'in_progress'])
        self.assertEqual([request[0] for request in requests], ['POST', 'GET', 'GET', 'DELETE'])
        self.assertIn(SOURCE, requests[0][3]['input'])
        self.assertIn('ONLY module 1: drone componenta', requests[0][3]['input'])
        self.assertEqual(requests[1:], [('GET', '/v1beta/interactions/int_drone', 'fake-secret', None)] * 2
                         + [('DELETE', '/v1beta/interactions/int_drone', 'fake-secret', None)])
        self.assertEqual(len(job['completed']), 1)
        self.assertIn('## Module 1: drone componenta', job['completed'][0])
        self.assertNotIn('Private summary', job['completed'][0])

    def test_transient_poll_failure_checks_the_same_interaction_without_reposting(self):
        replies = [{'id': 'int_drone', 'status': 'in_progress'}, TransientEngineError('timeout'),
                   background_response('Finished lesson'), TransientEngineError('cleanup timed out')]
        progress = []
        with patch('engines.request_json', side_effect=replies) as send, patch('engines.time.sleep'), \
                patch('engines.time.monotonic', side_effect=[0, 5, 200]):
            text = generate_course(SOURCE, '', self.config, on_progress=progress.append)
        self.assertEqual(text, 'Finished lesson\n')
        self.assertEqual(progress, ['in_progress', 'reconnecting'])
        self.assertEqual([c.args[0] for c in send.call_args_list],
                         [INTERACTIONS_URL, *[f'{INTERACTIONS_URL}/int_drone'] * 3])
        self.assertEqual(send.call_args.kwargs['method'], 'DELETE')
        self.assertTrue(all(c.args[2] is None for c in send.call_args_list[1:]))

    def test_failed_or_uncertain_submission_is_not_replayed(self):
        for result in (TransientEngineError('timeout'), {'id': '../unexpected', 'status': 'queued'},
                       {'id': 'fake-secret', 'status': 'in_progress'}):
            with self.subTest(result=result), patch('engines.request_json', side_effect=[result]) as send:
                with self.assertRaises(CourseError) as error:
                    generate_course(SOURCE, '', self.config)
                self.assertNotIn('fake-secret', str(error.exception))
                self.assertEqual(send.call_count, 1)

    def test_incomplete_unexpected_and_empty_results_do_not_become_modules(self):
        for result in (background_response('Partial lesson', 'incomplete'),
                       background_response('Partial lesson', 'fake-secret'),
                       background_response('fake-secret'), background_response('x' * 400001),
                       {'status': 'completed', 'steps': [{'type': 'thought'}]}):
            with self.subTest(status=result['status']), patch('engines.request_json', return_value=result):
                job = new_job(SOURCE, '', self.config)
                with self.assertRaises(CourseError) as error:
                    advance(job, self.config)
                self.assertNotIn('fake-secret', str(error.exception))
                self.assertEqual(job['completed'], [])

    def test_background_wait_is_bounded_without_resubmission(self):
        with patch('engines.request_json', return_value={'id': 'int_drone', 'status': 'queued'}) as send, \
                patch('engines.time.monotonic', side_effect=[0, 901]), \
                self.assertRaisesRegex(CourseError, '15-minute'):
            generate_course(SOURCE, '', self.config)
        self.assertEqual(send.call_count, 1)

    def test_live_style_storage_rejection_is_distinguished_and_sanitized(self):
        body = io.BytesIO(b'{"error":{"message":"Background interactions require store=true. fake-secret"}}')
        failure = HTTPError(INTERACTIONS_URL, 400, 'fake-secret', {}, body)
        with patch('engines.build_opener') as opener:
            opener.return_value.open.side_effect = failure
            with self.assertRaisesRegex(CourseError, 'storage settings.*HTTP 400') as error:
                generate_course(SOURCE, '', self.config)
            self.assertNotIn('fake-secret', str(error.exception))
            self.assertEqual(opener.return_value.open.call_count, 1)
