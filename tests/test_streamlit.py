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
