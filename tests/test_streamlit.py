import unittest
from unittest.mock import patch
from streamlit.testing.v1 import AppTest


class StreamlitTests(unittest.TestCase):
    def setUp(self):
        self.app = AppTest.from_file('app.py', default_timeout=20).run()

    def click(self, label):
        next(button for button in self.app.button if button.label == label).click().run()
        self.assertFalse(self.app.exception)

    def test_generate_accept_edit_and_rerun_keeps_draft_and_downloads(self):
        self.click('Load example')
        self.click('Generate course')
        self.assertTrue(self.app.session_state['candidate'])
        self.assertEqual(self.app.session_state['content'], '')
        self.click('Use this draft')
        self.assertIn('## Module 1:', self.app.session_state['content'])
        self.app.text_area(key='content').set_value('# Edited Course\nCustom lesson').run()
        self.app.run()
        self.assertEqual(self.app.session_state['content'], '# Edited Course\nCustom lesson')
        self.assertEqual(len(self.app.get('download_button')), 3)
        self.assertFalse(self.app.exception)

    def test_empty_input_and_online_consent_leave_draft_intact(self):
        self.app.text_area(key='content').set_value('Keep this lesson').run()
        self.click('Generate course')
        self.assertTrue(self.app.error)
        self.assertEqual(self.app.session_state['content'], 'Keep this lesson')
        self.click('Load example')
        self.app.selectbox(key='provider').select('Google AI Studio (Gemini)').run()
        with patch('engines.request_json', side_effect=AssertionError('must not call without consent')):
            self.click('Generate course')
        self.assertTrue(self.app.error)
        self.assertEqual(self.app.session_state['content'], 'Keep this lesson')

    def test_revision_is_staged_and_does_not_overwrite(self):
        self.click('Load example')
        self.app.text_area(key='content').set_value('Original course').run()
        self.app.text_input(key='revision_instructions').set_value('Add an example').run()
        self.app.selectbox(key='provider').select('Google AI Studio (Gemini)').run()
        self.app.text_input(key='api_key').set_value('fake-key').run()
        self.app.checkbox(key='online_consent').check().run()
        response = {'candidates': [{'finishReason': 'STOP', 'content': {'parts': [{'text': '# Revised Course'}]}}]}
        with patch('engines.request_json', return_value=response):
            self.click('Revise with engine')
        self.assertEqual(self.app.session_state['candidate'], '# Revised Course\n')
        self.assertEqual(self.app.session_state['content'], 'Original course')
        self.click('Use this draft')
        self.assertEqual(self.app.session_state['content'], 'Original course')
        self.app.checkbox(key='replace_draft').check().run()
        self.click('Use this draft')
        self.assertEqual(self.app.session_state['content'], '# Revised Course\n')


if __name__ == '__main__':
    unittest.main()
