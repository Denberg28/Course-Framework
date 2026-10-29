import json
import io
import zipfile
import unittest
from unittest.mock import patch

from course_core import (CourseError, SAMPLE, load_project, make_project, project_bytes,
                         validate_pending, export_bundle)
from engines import EngineConfig, generate_course
from workflow import (accept_job, advance, can_resume, draft_text, is_complete, new_job,
                      video_resources)

MODULE = '''### Learning objectives
Explain the source topic and apply it to a case.
### Lesson content
A substantive explanation with a worked example and its assumptions.
### Learning activities
1. Inspect the case. Submit an annotated explanation after 20 minutes.
2. Compare two alternatives and justify a decision in a short report.
### Assessment
Explain the reasoning. Answer guide: identify assumptions and use evidence.
Rubric: accuracy 40%, reasoning 40%, clarity 20%.
'''


def response(text=MODULE):
    return {'candidates': [{'finishReason': 'STOP', 'content': {'parts': [{'text': text}]}}]}


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.config = EngineConfig('Google AI Studio (Gemini)', 'fake-secret', 'gemini-3.8-flash')

    def test_partial_job_roundtrip_resumes_only_failed_module(self):
        calls = []
        def transport(url, headers, payload):
            calls.append(payload['contents'][0]['parts'][0]['text'])
            if len(calls) == 2:
                raise CourseError('Quota reached')
            return response()
        job = new_job(SAMPLE, '', self.config, [0, 1])
        job = advance(job, self.config, transport=transport)
        with self.assertRaises(CourseError):
            advance(job, self.config, transport=transport)
        self.assertEqual(len(job['completed']), 1)
        saved = make_project(SAMPLE, 'Structures', 'Keep accepted material', pending=job)
        saved['pending']['api_key'] = 'fake-secret'
        data = project_bytes(saved)
        self.assertNotIn(b'fake-secret', data)
        restored = load_project(data)
        self.assertEqual(restored['content'], 'Keep accepted material')
        resumed = advance(restored['pending'], self.config, transport=transport)
        self.assertTrue(is_complete(resumed))
        self.assertIn('ONLY module 2', calls[-1])
        self.assertEqual(resumed['completed'][0], job['completed'][0])
        accepted = accept_job(restored, resumed)
        self.assertIn('### Learning activities', accepted['content'])
        self.assertIn('### Video resources', accepted['content'])
        self.assertIsNone(accepted['pending'])

    def test_changed_source_model_or_endpoint_does_not_resume(self):
        job = new_job(SAMPLE, '', self.config)
        self.assertTrue(can_resume(job, SAMPLE, '', self.config))
        self.assertFalse(can_resume(job, SAMPLE + '\nExtra topic', '', self.config))
        other = EngineConfig(self.config.provider, 'replacement-key', 'gemini-3.5-flash-lite')
        self.assertFalse(can_resume(job, SAMPLE, '', other))
        replacement_key = EngineConfig(self.config.provider, 'replacement-key', self.config.model)
        self.assertTrue(can_resume(job, SAMPLE, '', replacement_key))
        compatible = EngineConfig('OpenAI-compatible', 'fake', 'm', 'https://one.example/v1', True)
        other = EngineConfig('OpenAI-compatible', 'fake', 'm', 'https://two.example/v1', True)
        self.assertFalse(can_resume(new_job(SAMPLE, '', compatible), SAMPLE, '', other))
        with self.assertRaises(CourseError):
            advance(job, other)

    def test_complete_only_acceptance_and_checkpoint_validation(self):
        job = new_job(SAMPLE, '', self.config)
        with self.assertRaises(CourseError):
            accept_job(make_project('', '', ''), job)
        for change in ({'indices': [0, 0]}, {'indices': [True]}, {'indices': [90]},
                       {'completed': ['']}, {'completed': ['x'] * 6}, {'profile': 'invalid'}):
            with self.subTest(change=change), self.assertRaises(CourseError):
                validate_pending({**job, **change})

    def test_video_resources_are_deterministic_searches_or_supplied_links(self):
        syllabus = SAMPLE + '\nhttps://youtu.be/realSourceID\nhttps://[broken\n'
        text = video_resources(syllabus, 'Lift & drag', 'Flight Theory')
        self.assertIn('Lift+%26+drag', text)
        self.assertIn('https://youtu.be/realSourceID', text)
        bad = MODULE + '\n### Video resources\n[Imaginary](https://youtu.be/inventedID)\n'
        job = advance(new_job(syllabus, '', self.config, [0]), self.config, transport=lambda *args: response(bad))
        self.assertNotIn('inventedID', draft_text(job))
        self.assertIn('youtube.com/results?search_query=', draft_text(job))

    def test_missing_sections_and_truncated_output_preserve_checkpoint(self):
        job = new_job(SAMPLE, '', self.config)
        for bad in (response('# Too short'), {'candidates': [{'finishReason': 'MAX_TOKENS'}]}):
            with self.assertRaises(CourseError):
                advance(job, self.config, transport=lambda *args: bad)
            self.assertEqual(job['completed'], [])

    def test_local_module_generation_never_uses_network(self):
        cfg = EngineConfig()
        with patch('engines.request_json', side_effect=AssertionError('must stay offline')):
            job = advance(new_job(SAMPLE, '', cfg, [2]), cfg)
        text = draft_text(job)
        self.assertIn('## Module 3:', text)
        self.assertNotIn('## Module 1:', text)
        self.assertIn('### Learning activities', text)
        self.assertIn('### Video resources', text)
        self.assertIn('[Add instructor-verified', text)

    def test_course_export_keeps_accepted_source_and_excludes_pending(self):
        job = new_job(SAMPLE, '', self.config, [0])
        saved = make_project('Week 1: New source', 'Edited title', 'Accepted material',
                             pending=job, accepted_syllabus=SAMPLE)
        with zipfile.ZipFile(io.BytesIO(export_bundle(saved))) as archive:
            self.assertEqual(archive.read('syllabus.txt').decode(), SAMPLE)
            self.assertIsNone(load_project(archive.read('project.json'))['pending'])
            self.assertEqual(archive.read('course.md').decode(), 'Accepted material')

    def test_v1_projects_migrate_without_losing_edits(self):
        old = {'schema_version': 1, 'title': 'Old course', 'syllabus': SAMPLE,
               'content': '# My edited lesson', 'engine': 'Imported', 'api_key': 'discard-me'}
        saved = load_project(json.dumps(old).encode())
        self.assertEqual(saved['schema_version'], 2)
        self.assertEqual(saved['content'], old['content'])
        self.assertNotIn('api_key', saved)
        self.assertIsNone(saved['pending'])


if __name__ == '__main__':
    unittest.main()
