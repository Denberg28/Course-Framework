import io
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading
import unittest
from unittest.mock import patch

from course_core import CourseError, SAMPLE, make_project
from course_workflow import advance, draft_text, new_job
from engines import EngineConfig, generate_course, request_json
from test_workflow import MODULE


def event(text='', finish=None, thought=False):
    candidate = {'content': {'parts': [{'text': text, 'thought': thought}]}}
    if finish:
        candidate['finishReason'] = finish
    return ('data: ' + json.dumps({'candidates': [candidate]}, ensure_ascii=False) + '\r\n\r\n').encode()


class Stream(io.BytesIO):
    def __init__(self, *blocks):
        super().__init__()
        self.blocks = iter(blocks)

    def read1(self, size):
        item = next(self.blocks, b'')
        if isinstance(item, Exception):
            raise item
        return item


class GeminiStreamTests(unittest.TestCase):
    def setUp(self):
        self.config = EngineConfig('Google AI Studio (Gemini)', 'fake-secret', 'gemini-3.8-flash')

    def generate(self, stream, progress=None):
        with patch('engines.build_opener') as opener:
            opener.return_value.open.return_value = stream
            result = generate_course('Drone components', '', self.config, on_progress=progress)
            self.assertEqual(opener.return_value.open.call_count, 1)
            request = opener.return_value.open.call_args.args[0]
            self.assertIn(':streamGenerateContent?alt=sse', request.full_url)
            self.assertNotIn('fake-secret', request.full_url)
            self.assertEqual(opener.return_value.open.call_args.kwargs['timeout'], 180)
            return result

    def test_fragmented_utf8_sse_combines_text_and_ignores_thoughts(self):
        wire = b': keepalive\r\n\r\n' + event('Internal summary', thought=True) + event('Résumé ') + event('lesson', 'STOP')
        progress = []
        stream = Stream(*[wire[i:i + 3] for i in range(0, len(wire), 3)])
        self.assertEqual(self.generate(stream, progress.append), 'Résumé lesson\n')
        self.assertEqual(progress, [0, 0, 7, 13])
        self.assertTrue(stream.closed)

    def test_chunks_arriving_beyond_old_total_wait_are_consumed_without_retry(self):
        stream = Stream(event('First '), event('second '), event('done', 'STOP'))
        with patch('engines.time.monotonic', side_effect=[0, 0, 100, 200, 250]):
            self.assertEqual(self.generate(stream), 'First second done\n')

    def test_stop_finishes_without_waiting_for_stream_connection_to_close(self):
        self.assertEqual(self.generate(Stream(event('Complete lesson', 'STOP'), TimeoutError('late close'))),
                         'Complete lesson\n')

    def test_real_http_chunked_sse_finishes_before_connection_close(self):
        release = threading.Event()
        class Handler(BaseHTTPRequestHandler):
            protocol_version = 'HTTP/1.1'
            def log_message(self, *args):
                pass
            def do_POST(self):
                self.rfile.read(int(self.headers['Content-Length']))
                self.send_response(200)
                self.send_header('Content-Type', 'text/event-stream')
                self.send_header('Transfer-Encoding', 'chunked')
                self.end_headers()
                for block in (event('Résumé '), event('lesson', 'STOP')):
                    self.wfile.write(f'{len(block):x}\r\n'.encode() + block + b'\r\n')
                    self.wfile.flush()
                # The response is complete while the HTTP connection remains open.
                release.wait(2)
                self.close_connection = True
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, kwargs={'poll_interval': .01}, daemon=True)
        thread.start()
        try:
            result = request_json(f'http://127.0.0.1:{server.server_port}/stream', {}, {}, timeout=1, stream=True)
            self.assertEqual(result['candidates'][0]['finishReason'], 'STOP')
            self.assertEqual(result['candidates'][0]['content']['parts'][0]['text'], 'Résumé lesson')
        finally:
            release.set()
            server.shutdown()
            server.server_close()
            thread.join(2)

    def test_eof_or_timeout_after_partial_text_does_not_make_a_module(self):
        for tail in (b'', TimeoutError('fake-secret')):
            with self.subTest(tail=type(tail)), self.assertRaises(CourseError) as raised:
                self.generate(Stream(event('Partial text'), tail))
            self.assertNotIn('fake-secret', str(raised.exception))

    def test_server_errors_bad_json_and_invalid_utf8_are_sanitized(self):
        for block in (b'data: {"error":{"code":504,"message":"fake-secret"}}\n\n',
                      b'data: fake-secret\n\n', b'data: \xff\n\n', b'data: []\n\n'):
            with self.subTest(block=block[:20]), self.assertRaises(CourseError) as raised:
                self.generate(Stream(block))
            self.assertNotIn('fake-secret', str(raised.exception))

    def test_stream_byte_text_and_time_limits_are_enforced(self):
        for block, expected in ((b'x' * (2 * 1024 * 1024 + 1), '2 MB'),
                                (event('x' * 400001, 'STOP'), 'text limit')):
            with self.subTest(expected=expected), self.assertRaisesRegex(CourseError, expected):
                self.generate(Stream(block))
        with patch('engines.time.monotonic', side_effect=[0, 901]), self.assertRaisesRegex(CourseError, 'fifteen-minute'):
            self.generate(Stream(event('Unused', 'STOP')))

    def test_credential_reflection_across_chunks_and_thought_only_output_are_rejected(self):
        for stream in (Stream(event('fake-'), event('secret', 'STOP')),
                       Stream(event('Internal only', 'STOP', thought=True))):
            with self.subTest(), self.assertRaises(CourseError):
                self.generate(stream)

    def test_failure_retains_checkpoint_and_resume_requests_only_unfinished_module(self):
        job = new_job(SAMPLE, '', self.config, [0, 1])
        project = make_project(SAMPLE, '', 'Keep accepted material')
        streams = [Stream(event(MODULE[:300]), event(MODULE[300:], 'STOP')),
                   Stream(event('Unfinished text'), TimeoutError('fake-secret')),
                   Stream(event(MODULE, 'STOP'))]
        with patch('engines.build_opener') as opener:
            opener.return_value.open.side_effect = streams
            job = advance(job, self.config)
            first = job['completed'][0]
            with self.assertRaisesRegex(CourseError, 'stream idle'):
                advance(job, self.config)
            self.assertEqual(job['completed'], [first])
            job = advance(job, self.config)
            self.assertEqual(opener.return_value.open.call_count, 3)
        self.assertEqual(len(job['completed']), 2)
        self.assertEqual(job['completed'][0], first)
        self.assertNotIn('Unfinished text', draft_text(job))
        self.assertEqual(project['content'], 'Keep accepted material')


if __name__ == '__main__':
    unittest.main()
