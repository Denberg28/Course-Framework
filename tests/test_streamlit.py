import unittest
from pathlib import Path
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
from course_core import CourseError
from test_workflow import response


class StreamlitTests(unittest.TestCase):
    def setUp(self):
        self.app = AppTest.from_file('app.py', default_timeout=30).run()

    def click(self, label):
        next(b for b in self.app.button if b.label == label).click().run()
        self.assertFalse(self.app.exception)

    def sample_local(self):
        self.click('Example')
        self.app.selectbox(key='provider').select('Local template').run()

    def test_ae417_clipboard_table_generates_thirteen_modules(self):
        self.sample_local()
        self.click('Generate')
        self.app.session_state['content'] = 'Keep accepted material'
        self.app.run()
        source = Path('examples/AE417-syllabus.md').read_text(encoding='utf-8')
        # Browser table copies have tabs, blank leading cells and indented rows.
        source = '\n'.join('\t'.join(c.strip() for c in line[1:-1].split('|'))
                           for line in source.splitlines() if not line.startswith('|---'))
        self.app.text_area(key='source').set_value(source).run()
        self.app.selectbox(key='provider').select('Google AI Studio (Gemini)').run()
        self.assertIn('13 modules · 7 outcomes', ' '.join(c.value for c in self.app.caption))
        self.assertIn('54 lecture h · 0 lab h · 54 total h', ' '.join(c.value for c in self.app.caption))
        self.app.text_input(key='api_key').set_value('fake-key').run()
        self.app.checkbox(key='online_consent').check().run()
        with patch('engines.request_json', return_value=response()) as send:
            self.click('Generate')
            self.assertEqual(send.call_count, 13)
            self.app.run()
            self.assertEqual(send.call_count, 13)
        self.assertEqual(self.app.session_state['pending']['indices'], list(range(13)))
        self.assertEqual(self.app.session_state['generation_status']['completed'], 13)
        self.assertEqual(self.app.session_state['generation_status']['total'], 13)
        self.assertEqual(self.app.session_state['content'], 'Keep accepted material')
        self.assertFalse(self.app.session_state['replace_course'])
        self.app.checkbox(key='replace_course').check().run()
        self.click('Use draft')
        self.assertEqual(self.app.session_state['content'].count('## Module '), 13)
        self.assertIn('## Module 13: Pre-Deployment Seminar and Internship Requirements', self.app.session_state['content'])
        self.assertEqual(self.app.session_state['source'], source)

    def test_default_lite_and_selected_flash_route_to_the_right_model(self):
        self.assertEqual(self.app.session_state['model_choice'], 'gemini-3.5-flash-lite')
        self.click('Example')
        self.app.text_input(key='api_key').set_value('fake-key').run()
        self.app.checkbox(key='online_consent').check().run()
        self.app.selectbox(key='module_scope').select(0).run()
        with patch('engines.request_json', return_value=response()) as send:
            self.click('Generate')
            self.assertIn('/gemini-3.5-flash-lite:generateContent', send.call_args.args[0])
        self.app.selectbox(key='model_choice').select('gemini-3.8-flash').run()
        with patch('engines.request_json', return_value=response()) as send:
            self.click('Generate')
            self.assertIn('/gemini-3.8-flash:generateContent', send.call_args.args[0])
            self.assertEqual(send.call_args.kwargs['timeout'], 180)
            self.assertEqual(send.call_args.args[2]['generationConfig']['thinkingConfig'], {'thinkingLevel': 'medium'})
        self.assertEqual(self.app.session_state['pending']['model'], 'gemini-3.8-flash')
        self.app.run()
        self.assertEqual(self.app.session_state['model_choice'], 'gemini-3.8-flash')

    def test_flash_timeout_or_token_limit_keeps_checkpoint_and_resume(self):
        self.click('Example')
        self.app.selectbox(key='model_choice').select('gemini-3.8-flash').run()
        self.app.text_input(key='api_key').set_value('fake-key').run()
        self.app.checkbox(key='online_consent').check().run()
        self.app.session_state['content'] = 'Keep accepted material'
        self.app.run()
        cutoff = {'candidates': [{'finishReason': 'MAX_TOKENS', 'content': {'parts': [{'text': 'Partial lesson'}]}}]}
        for failure in (CourseError('The engine did not respond within the 180-second connection/read timeout.'), cutoff):
            # Each attempt starts fresh after the preceding test job finished.
            with self.subTest(failure=type(failure)), patch('engines.request_json', side_effect=[response(), failure]) as send:
                self.click('Generate')
                self.assertEqual(send.call_count, 2)
            self.assertEqual(self.app.session_state['generation_status']['completed'], 1)
            self.assertEqual(self.app.session_state['generation_status']['total'], 5)
            self.assertEqual(len(self.app.session_state['pending']['completed']), 1)
            self.assertNotIn('Partial lesson', self.app.session_state['pending']['completed'][0])
            self.assertEqual(self.app.session_state['content'], 'Keep accepted material')
            with patch('engines.request_json', return_value=response()) as send:
                self.click('Resume')
                self.assertEqual(send.call_count, 4)
                self.assertTrue(all(c.kwargs['timeout'] == 180 for c in send.call_args_list))
                self.app.run()
                self.assertEqual(send.call_count, 4)
            self.assertEqual(self.app.session_state['generation_status']['completed'], 5)
            self.assertEqual(self.app.session_state['content'], 'Keep accepted material')

    def test_direct_generate_use_edit_and_download_survive_rerun(self):
        self.assertEqual(len(self.app.tabs), 0)
        self.sample_local()
        self.click('Generate')
        self.assertEqual(self.app.session_state['content'], '')
        self.assertEqual(len(self.app.session_state['pending']['completed']), 5)
        self.click('Use draft')
        self.assertIn('## Module 1:', self.app.session_state['content'])
        self.assertNotIn('### Video resources', self.app.session_state['content'])
        self.assertIn('### Discussion and presentation', self.app.session_state['content'])
        self.app.text_area(key='content').set_value('# My edits').run()
        self.app.run()
        self.assertEqual(self.app.session_state['content'], '# My edits')
        self.assertEqual(len(self.app.get('download_button')), 3)

    def test_full_syllabus_direct_paste_has_full_width_output_and_correct_allocation(self):
        source = Path('examples/AE416-syllabus.txt').read_text(encoding='utf-8')
        self.app.text_area(key='source').set_value(source).run()
        self.app.selectbox(key='provider').select('Local template').run()
        self.assertIn('36 lecture h · 54 lab h · 90 total h', ' '.join(c.value for c in self.app.caption))
        # Main-page blocks are sequential, never columns reserving space beside output.
        blocks = [b for b in self.app.main.children.values() if b.type == 'flex_container']
        self.assertEqual(len(blocks), 2)
        self.assertTrue(blocks[0].text_area)
        self.assertFalse(blocks[1].text_area)
        self.assertTrue(all(b.proto.flex_container.direction == b.proto.flex_container.VERTICAL for b in blocks))
        self.click('Generate')
        self.assertEqual(self.app.session_state['pending']['indices'], [0, 1, 2, 3, 4])
        self.assertEqual(self.app.session_state['pending']['title'], 'RESEARCH METHODS AND APPLICATION')
        self.assertEqual(self.app.session_state['source'], source)
        self.assertTrue(any(b.label == 'Download Markdown' for b in self.app.get('download_button')))
        self.click('Use draft')
        self.assertIn('| Selected total | | 36 | 54 |', self.app.session_state['content'])

    def test_assessment_and_answer_key_are_collapsed(self):
        self.click('Example')
        self.app.text_input(key='api_key').set_value('fake-key').run()
        self.app.checkbox(key='online_consent').check().run()
        self.app.selectbox(key='module_scope').select(0).run()
        with patch('engines.request_json', return_value=response()):
            self.click('Generate')
        labels = [e.label for e in self.app.expander]
        self.assertIn('Assessment', labels)
        self.assertIn('Answer key', labels)
        assessment = next(e for e in self.app.expander if e.label == 'Assessment')
        self.assertIn('A. The applied load  \nB.', assessment.markdown[0].value)
        for expander in self.app.expander:
            if expander.label in {'Assessment', 'Answer key'}:
                self.assertFalse(expander.proto.expanded)

    def test_model_selector_custom_and_provider_change_clear_credentials(self):
        self.app.selectbox(key='model_choice').select('gemini-3.5-flash-lite').run()
        self.assertEqual(self.app.session_state['model_choice'], 'gemini-3.5-flash-lite')
        self.app.selectbox(key='model_choice').select('Custom model…').run()
        self.app.text_input(key='custom_model').set_value('my-model').run()
        self.app.text_input(key='api_key').set_value('fake-key').run()
        self.app.checkbox(key='online_consent').check().run()
        self.app.selectbox(key='provider').select('OpenAI-compatible').run()
        self.assertEqual(self.app.session_state['api_key'], '')
        self.assertFalse(self.app.session_state['online_consent'])
        self.assertFalse(self.app.exception)
        self.app.selectbox(key='provider').select('Google AI Studio (Gemini)').run()
        self.assertEqual(self.app.session_state['model_choice'], 'gemini-3.5-flash-lite')

    def test_no_consent_does_not_call_provider_or_overwrite(self):
        self.click('Example')
        self.app.session_state['content'] = 'Accepted material'
        with patch('engines.request_json', side_effect=AssertionError('must not send')):
            self.click('Generate')
        self.assertTrue(self.app.error)
        self.assertEqual(self.app.session_state['content'], 'Accepted material')

    def test_failure_preserves_completed_module_and_resume_skips_it(self):
        self.click('Example')
        self.app.text_input(key='api_key').set_value('fake-key').run()
        self.app.checkbox(key='online_consent').check().run()
        with patch('engines.request_json', side_effect=[response(), CourseError('Quota reached')]) as send:
            self.click('Generate')
            self.assertEqual(send.call_count, 2)
        self.assertEqual(len(self.app.session_state['pending']['completed']), 1)
        self.assertEqual(self.app.session_state['content'], '')
        self.assertEqual(self.app.session_state['generation_status']['completed'], 1)
        self.assertEqual(self.app.session_state['generation_status']['total'], 5)
        self.assertIn('Stopped', self.app.session_state['generation_status']['text'])
        with patch('engines.request_json', return_value=response()) as send:
            self.click('Resume')
            self.assertEqual(send.call_count, 4)
        self.click('Use draft')
        self.assertIn('## Module 5:', self.app.session_state['content'])

    def test_progress_is_in_generation_controls_and_rerun_does_not_repeat_requests(self):
        self.click('Example')
        self.app.text_input(key='api_key').set_value('fake-key').run()
        self.app.checkbox(key='online_consent').check().run()
        with patch('engines.request_json', return_value=response()) as send:
            self.click('Generate')
            self.app.run()
            self.assertEqual(send.call_count, 5)
        self.assertFalse(self.app.session_state['generation_requested'])
        self.assertEqual(self.app.session_state['generation_status']['text'], 'Draft ready · 5/5 complete')
        controls = next(b for b in self.app.main if getattr(b, 'type', '') == 'flex_container'
                        and b.proto.id.endswith('-generation_controls'))
        self.assertEqual(len(controls.get('progress')), 1)
        self.assertEqual(len(self.app.main.get('progress')), 1)
        self.app.text_area(key='source').set_value('Week 1: Changed topic').run()
        self.assertIsNone(self.app.session_state['generation_status'])

    def test_hosted_gemini_secret_used_without_display_or_session_copy(self):
        from course_core import project_bytes, make_project
        app = AppTest.from_file('app.py', default_timeout=30)
        app.secrets['GEMINI_API_KEY'] = 'fake-server-secret'
        app.run()
        self.assertFalse(app.exception)
        self.assertFalse(any(w.key == 'api_key' for w in app.text_input))
        self.assertIn('configured in Secrets', ' '.join(c.value for c in app.caption))
        next(b for b in app.button if b.label == 'Example').click().run()
        app.selectbox(key='module_scope').select(0).run()
        app.checkbox(key='online_consent').check().run()
        with patch('engines.request_json', return_value=response()) as send:
            next(b for b in app.button if b.label == 'Generate').click().run()
            self.assertEqual(send.call_args.args[1]['x-goog-api-key'], 'fake-server-secret')
        self.assertFalse(app.exception)
        self.assertNotIn('fake-server-secret', str(app.main))
        self.assertNotIn('fake-server-secret', str(app.session_state.filtered_state))
        data = project_bytes(make_project(app.session_state['source'], '', '', pending=app.session_state['pending']))
        self.assertNotIn(b'fake-server-secret', data)

    def test_hosted_secret_never_used_for_compatible_provider(self):
        app = AppTest.from_file('app.py', default_timeout=30)
        app.secrets['GEMINI_API_KEY'] = 'fake-server-secret'
        app.run()
        next(b for b in app.button if b.label == 'Example').click().run()
        app.selectbox(key='provider').select('OpenAI-compatible').run()
        app.text_input(key='custom_model').set_value('provider-model').run()
        app.checkbox(key='online_consent').check().run()
        with patch('engines.request_json') as send:
            next(b for b in app.button if b.label == 'Generate').click().run()
            send.assert_not_called()
        self.assertTrue(app.error)
        self.assertEqual(app.session_state['content'], '')
        self.assertFalse(app.exception)

    def test_selected_module_and_existing_course_replacement_gate(self):
        self.sample_local()
        self.app.selectbox(key='module_scope').select(2).run()
        self.click('Generate')
        self.click('Use draft')
        self.assertIn('## Module 3:', self.app.session_state['content'])
        self.assertNotIn('## Module 1:', self.app.session_state['content'])
        original = self.app.session_state['content']
        self.app.selectbox(key='module_scope').select(0).run()
        self.click('Generate')
        self.click('Use draft')
        self.assertEqual(self.app.session_state['content'], original)
        self.app.checkbox(key='replace_course').check().run()
        self.click('Use draft')
        self.assertIn('## Module 1:', self.app.session_state['content'])


if __name__ == '__main__':
    unittest.main()
