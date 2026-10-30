import json
import io
import zipfile
from pathlib import Path
import unittest
from unittest.mock import patch

from course_core import (CourseError, SAMPLE, load_project, make_project, project_bytes,
                         validate_pending, export_bundle)
from engines import EngineConfig, generate_course
from course_workflow import (accept_job, advance, can_resume, draft_text, is_complete, new_job,
                      remove_video_sections)

MODULE = """### Discussion and presentation
#### Introduction
The learning objective is to describe a load path and explain why each structural connection must transfer the applied force through the assembly.
#### Presentation sequence
1. Begin with a diagram of an airframe and identify where an external load is introduced.
2. Follow the force through the connected members, stating assumptions and asking learners to compare two possible paths.
3. Discuss how a discontinuity changes the explanation, and distinguish a classroom model from an approved maintenance procedure.
#### Worked example
Use a simplified diagram with a labelled applied load and trace it to the supports. State the assumptions before drawing a conclusion.
#### Summary
A consistent explanation identifies the input load, connected members, supports, assumptions and limitations.
### Activity
Annotate a supplied structural diagram. Identify the load, trace its path and submit a justified explanation after twenty minutes.
### Assessment
1. Which item begins a load-path explanation?
A. The applied load
B. The paint colour
C. The calendar date
D. The page margin
2. What should be stated before interpreting the diagram?
A. A random preference
B. The assumptions
C. An unrelated rule
D. The file extension
3. What is the expected activity deliverable?
A. An empty sheet
B. An unlabelled sketch
C. An annotated diagram
D. A video suggestion
4. Which conclusion requires verification against approved data?
A. The diagram has labels
B. The explanation has words
C. The activity uses paper
D. A maintenance approval claim
5. What makes the explanation reviewable?
A. Evidence and explicit assumptions
B. Unrelated details
C. An invented reference
D. A missing load
### Answer key
1. A
2. B
3. C
4. D
5. A
"""


def response(text=MODULE):
    return {'candidates': [{'finishReason': 'STOP', 'content': {'parts': [{'text': text}]}}]}


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.config = EngineConfig('Google AI Studio (Gemini)', 'fake-secret', 'gemini-3.8-flash')

    def test_full_syllabus_hours_reach_prompt_draft_and_project_export(self):
        source = Path('examples/AE416-syllabus.txt').read_text(encoding='utf-8')
        prompts = []
        def transport(url, headers, payload):
            prompts.append(payload['contents'][0]['parts'][0]['text'])
            return response()
        job = new_job(source, '', self.config)
        while not is_complete(job):
            job = advance(job, self.config, transport=transport)
        self.assertEqual(len(prompts), 5)
        self.assertTrue(all(source in prompt for prompt in prompts))
        self.assertIn('"lecture_hours": 6.0, "lab_hours": 6.0', prompts[0])
        self.assertIn('"lecture_hours": 8.0, "lab_hours": 15.0', prompts[-1])
        text = draft_text(job)
        self.assertEqual(text.count('## Module '), 5)
        self.assertIn('Lecture: 8 h · Lab: 15 h', text)
        self.assertIn('| Selected total | | 36 | 54 |', text)
        self.assertIn('Paler-Calmorin, Laurentina.', text)
        self.assertIn('Know how to collect, evaluate, and transform data', text)
        saved = accept_job(make_project(source, '', ''), job)
        self.assertEqual(load_project(project_bytes(saved))['syllabus'], source)
        with zipfile.ZipFile(io.BytesIO(export_bundle(saved))) as archive:
            self.assertEqual(archive.read('syllabus.txt').decode(), source)
            self.assertIn(b'Lecture: 8 h', archive.read('course.md'))
        cfg = EngineConfig()
        local = advance(new_job(source, '', cfg, [4]), cfg)
        self.assertEqual(draft_text(local).count('**Allocation:**'), 1)
        self.assertIn('[Add instructor-verified', draft_text(local))

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
        self.assertIn('### Activity', accepted['content'])
        self.assertNotIn('### Video resources', accepted['content'])
        self.assertIn('### References', accepted['content'])
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

    def test_video_suggestions_removed_and_syllabus_references_appended(self):
        syllabus = SAMPLE + '\nhttps://youtu.be/realSourceID\n'
        bad = MODULE + '\n### Video resources\n[Suggestion](https://youtu.be/inventedID)\n'
        job = advance(new_job(syllabus, '', self.config, [0]), self.config, transport=lambda *args: response(bad))
        text = draft_text(job)
        self.assertNotIn('youtu.be', text)
        self.assertNotIn('Video resources', text)
        self.assertNotIn('https://www.faa.gov/', text)
        self.assertIn('Instructor-supplied aircraft structural manual', text)
        self.assertIn('### References', text)

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
        self.assertIn('### Activity', text)
        self.assertNotIn('### Video resources', text)
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
