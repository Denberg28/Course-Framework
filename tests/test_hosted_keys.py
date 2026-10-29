import unittest
from course_core import CourseError
from hosted_keys import gemini_secret


class HostedKeyTests(unittest.TestCase):
    def test_missing_optional_and_trimmed_secret(self):
        self.assertEqual(gemini_secret({}), '')
        self.assertEqual(gemini_secret({'GEMINI_API_KEY': ' fake-secret '}), 'fake-secret')
        class Missing:
            def get(self, *args):
                raise FileNotFoundError('No secrets configured')
        self.assertEqual(gemini_secret(Missing()), '')

    def test_invalid_secret_does_not_echo_value(self):
        for value in (123, {'key': 'fake-secret'}, 'fake-secret\n', 'fake-secret🔑'):
            with self.subTest(value=type(value)), self.assertRaises(CourseError) as raised:
                gemini_secret({'GEMINI_API_KEY': value})
            self.assertNotIn('fake-secret', str(raised.exception))
