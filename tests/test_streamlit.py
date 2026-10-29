import unittest
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

    def test_direct_generate_use_edit_and_download_survive_rerun(self):
        self.assertEqual(len(self.app.tabs), 0)
        self.sample_local()
        self.click('Generate')
        self.assertEqual(self.app.session_state['content'], '')
        self.assertEqual(len(self.app.session_state['pending']['completed']), 5)
        self.click('Use draft')
        self.assertIn('## Module 1:', self.app.session_state['content'])
        self.assertIn('### Video resources', self.app.session_state['content'])
        self.app.text_area(key='content').set_value('# My edits').run()
        self.app.run()
        self.assertEqual(self.app.session_state['content'], '# My edits')
        self.assertEqual(len(self.app.get('download_button')), 2)

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
        with patch('engines.request_json', return_value=response()) as send:
            self.click('Resume')
            self.assertEqual(send.call_count, 4)
        self.click('Use draft')
        self.assertIn('## Module 5:', self.app.session_state['content'])

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
