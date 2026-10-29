import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from course_core import SAMPLE, build_course_markdown, load_project, make_project


@unittest.skipUnless(os.name == 'nt' or os.environ.get('DISPLAY'), 'Requires Windows desktop or X display')
class DesktopTests(unittest.TestCase):
    def setUp(self):
        import tkinter as tk
        from desktop import CourseMaker
        self.root = tk.Tk()
        self.app = CourseMaker(self.root)
        self.root.update()

    def tearDown(self):
        self.root.destroy()

    def test_editor_save_and_reopen_exclude_api_key(self):
        self.app.set_project(make_project(SAMPLE, 'Structures', build_course_markdown(SAMPLE)))
        self.app.key.set('fake-secret')
        self.root.update()
        with tempfile.TemporaryDirectory() as directory:
            self.app.path = Path(directory) / 'course.json'
            self.assertTrue(self.app.save())
            self.assertNotIn('fake-secret', self.app.path.read_text())
            restored = load_project(self.app.path.read_bytes())
            self.app.set_project(restored, self.app.path)
            self.assertIn('## Module 1:', self.app.text(self.app.editor))
            self.assertIn('5 modules', self.app.text(self.app.outline))
            self.assertFalse(self.app.dirty)

    def test_failed_worker_keeps_course_and_clears_busy(self):
        self.app.replace(self.app.editor, 'Keep this draft')
        self.app.busy = True
        self.app.results.put((False, 'Quota reached', 'Google AI Studio (Gemini)', SAMPLE, 'Course'))
        with patch('desktop.messagebox.showerror'):
            self.app.poll()
        self.assertEqual(self.app.text(self.app.editor), 'Keep this draft')
        self.assertFalse(self.app.busy)

    def test_worker_stages_then_accepts_source_snapshot(self):
        self.app.replace(self.app.source, 'Changed syllabus')
        self.app.results.put((True, '# Generated Course', 'Google AI Studio (Gemini)', SAMPLE, 'Structures'))
        self.app.poll()
        self.assertEqual(self.app.text(self.app.editor), '')
        self.assertTrue(self.app.unaccepted)
        with patch('desktop.messagebox.askyesno', return_value=True):
            self.app.apply_draft()
        self.assertEqual(self.app.text(self.app.editor), '# Generated Course')
        self.assertEqual(self.app.text(self.app.source), SAMPLE)
        self.assertFalse(self.app.unaccepted)

    def test_discard_pending_result_preserves_editor(self):
        self.app.replace(self.app.editor, 'Keep this draft')
        self.app.discard_result = True
        self.app.results.put((True, 'Discard me', 'Local template', SAMPLE, 'Course'))
        self.app.poll()
        self.assertEqual(self.app.text(self.app.editor), 'Keep this draft')
        self.assertEqual(self.app.text(self.app.candidate), '')


if __name__ == '__main__':
    unittest.main()
