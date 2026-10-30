import unittest
from pathlib import Path
from course_core import CourseError, SAMPLE, export_html
from course_workflow import new_job, advance, draft_text
from engines import EngineConfig
from lesson_format import presentation_parts, section_body, validate_lesson
from reference_catalog import reference_context, reference_section, restrict_generated_reference_links, select_references
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
        self.assertIn('Instructor-supplied aircraft structural manual', module['references'])
        self.assertNotIn('faa.gov', module['references'])

    def test_html_has_closed_assessment_and_key_and_escapes_content(self):
        text = '## Module 1: Load paths\n' + MODULE + '\n<script>bad()</script>\n'
        page = export_html('A <course>', text).decode()
        self.assertIn('<details><summary>Assessment', page)
        self.assertIn('<details><summary>Answer key', page)
        self.assertNotIn('<details open', page)
        self.assertNotIn('<script>', page)
        self.assertIn('&lt;course&gt;', page)
        self.assertIn('<h4>Presentation sequence</h4>', page)

    def test_model_invented_reference_url_is_not_published(self):
        cfg = EngineConfig('Google AI Studio (Gemini)', 'fake-key')
        fake = MODULE.replace('#### Summary', '[Invented citation](https://fabricated.example/faa-rule)\n#### Summary')
        job = advance(new_job(SAMPLE, '', cfg, [0]), cfg, transport=lambda *a: response(fake))
        text = draft_text(job)
        self.assertNotIn('fabricated.example', text)
        self.assertIn('source link needs verification', text)
        self.assertNotIn('https://www.faa.gov/', text)
        self.assertIn('Instructor-supplied aircraft structural manual', text)

    def test_aviation_context_does_not_inject_external_sources(self):
        refs = select_references('Course Name: Aviation regulation, FAA, CAAP and EASA', 'Certification')
        self.assertEqual(refs, [])
        self.assertEqual(select_references('Course Name: Intro to Python', 'Loops'), [])
        self.assertEqual(select_references('Course Name: Strength of Materials', 'Stress and strain'), [])

    def test_ae416_modules_use_the_three_syllabus_readings(self):
        source = Path('examples/AE416-syllabus.txt').read_text(encoding='utf-8')
        refs = select_references(source, 'Research Design')
        self.assertEqual([r['id'] for r in refs], ['SYL-1', 'SYL-2', 'SYL-3'])
        for author in ('Paler-Calmorin', 'Adanza', 'Sevilla'):
            self.assertIn(author, reference_context(source, 'Research Design'))
        cfg = EngineConfig('Google AI Studio (Gemini)', 'fake-key')
        payloads = []
        def transport(url, headers, payload):
            payloads.append(payload)
            return response()
        job = advance(new_job(source, '', cfg, [3]), cfg, transport=transport)
        part = next(p for p in presentation_parts(draft_text(job)) if p['title'])
        for author in ('Paler-Calmorin', 'Adanza', 'Sevilla'):
            self.assertIn(author, part['references'])
        for agency in ('FAA', 'CAAP', 'EASA', 'OpenStax', 'MIT'):
            self.assertNotIn(agency, part['references'])
        system = payloads[0]['systemInstruction']['parts'][0]['text']
        self.assertIn('syllabus-listed textbook and references', system)
        self.assertIn('Do not add outside books', system)
        self.assertNotIn('catalog', str(payloads))
        self.assertNotIn('independently verified source locations', part['references'])

    def test_supplied_links_from_any_domain_survive_but_invented_links_do_not(self):
        source = ('Course Name: Research\nWeek 1: Design\nReferences:\n'
                  'Journal article https://journal.example/paper\n'
                  '[Library reading](https://library.example/book)\n'
                  'Official guide https://www.faa.gov/guide\n')
        text = ('[Article](https://journal.example/paper)\n'
                'https://library.example/book.\nhttps://www.faa.gov/guide\n'
                '[Invented](https://invented.example/book)\n'
                'https://www.faa.gov/regulations_policies/handbooks_manuals/aviation')
        cleaned = restrict_generated_reference_links(text, source)
        for url in ('https://journal.example/paper', 'https://library.example/book.', 'https://www.faa.gov/guide'):
            self.assertIn(url, cleaned)
        self.assertNotIn('invented.example', cleaned)
        self.assertNotIn('handbooks_manuals', cleaned)
        self.assertIn('source link needs verification', cleaned)
        self.assertIn('https://www.faa.gov/guide', reference_section(source, 'Design'))

    def test_missing_references_are_marked_without_inventing_replacements(self):
        source = 'Course Name: Aviation Research\nWeek 1: Design'
        section = reference_section(source, 'Design')
        self.assertIn('No references supplied in the syllabus', section)
        self.assertNotIn('https://', section)
        self.assertIn('do not invent', reference_context(source, 'Design'))

    def test_reading_heading_aliases_are_kept_as_references(self):
        for heading in ('Reference', 'Bibliography', 'Reading list', 'Required readings',
                        'Recommended readings', 'Textbooks and references'):
            with self.subTest(heading=heading):
                source = f'Course Name: Research\nWeek 1: Design\n{heading}\nAuthor. Research book. 1995.'
                self.assertEqual(select_references(source, 'Design')[0]['title'], 'Author. Research book. 1995.')
