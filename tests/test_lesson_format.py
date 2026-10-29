import unittest
from course_core import CourseError, SAMPLE, export_html
from course_workflow import new_job, advance, draft_text
from engines import EngineConfig
from lesson_format import presentation_parts, section_body, validate_lesson
from reference_catalog import select_references
from test_workflow import MODULE, response


class LessonFormatTests(unittest.TestCase):
    def test_sequence_and_five_mcqs_with_letter_key(self):
        validate_lesson(MODULE)
        self.assertEqual(section_body(MODULE, 'Answer key').splitlines(), ['1. A', '2. B', '3. C', '4. D', '5. A'])
        for bad in [MODULE.replace('5. A', '5. Z'), MODULE.replace('D. The page margin', 'C. Repeated option'),
                    MODULE.replace('### Assessment', '### Quiz'), MODULE.replace('#### Worked example', '#### Example'),
                    MODULE.replace('5. What makes', '6. What makes')]:
            with self.subTest(bad=bad[:40]), self.assertRaises(CourseError):
                validate_lesson(bad)

    def test_collapse_parts_separate_questions_key_and_sources(self):
        cfg = EngineConfig('Google AI Studio (Gemini)', 'fake-key')
        job = advance(new_job(SAMPLE, '', cfg, [0]), cfg, transport=lambda *a: response())
        parts = presentation_parts(draft_text(job))
        module = next(p for p in parts if p['title'])
        self.assertIn('#### Presentation sequence', module['body'])
        self.assertNotIn('1. A', module['body'])
        self.assertIn('A. The applied load', module['assessment'])
        self.assertEqual(module['key'].splitlines()[0], '1. A')
        self.assertIn('faa.gov', module['references'])

    def test_html_has_closed_assessment_and_key_and_escapes_content(self):
        text = '## Module 1: Load paths\n' + MODULE + '\n<script>bad()</script>\n'
        page = export_html('A <course>', text).decode()
        self.assertIn('<details><summary>Assessment', page)
        self.assertIn('<details><summary>Answer key', page)
        self.assertNotIn('<details open', page)
        self.assertNotIn('<script>', page)
        self.assertIn('&lt;course&gt;', page)
        self.assertIn('<h4>Presentation sequence</h4>', page)

    def test_reference_selection_is_topic_scoped_and_not_regulatory_approval(self):
        refs = select_references('Course Name: Aviation regulation, FAA, CAAP and EASA', 'Certification')
        ids = {r['id'] for r in refs}
        self.assertTrue({'FAA-HANDBOOKS','CAAP-PCAR','EASA-EAR'} <= ids)
        self.assertEqual(select_references('Course Name: Intro to Python', 'Loops'), [])
        ids = {r['id'] for r in select_references('Course Name: Strength of Materials', 'Stress and strain')}
        self.assertIn('MIT-MATERIALS', ids)
        self.assertNotIn('CAAP-PCAR', ids)
