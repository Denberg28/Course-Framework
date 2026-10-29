import os
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from course_core import CourseError, SAMPLE, load_project, make_project
from engines import EngineConfig, PROVIDERS
from course_workflow import advance, new_job


@unittest.skipUnless(os.name == 'nt' or os.environ.get('DISPLAY'), 'Requires Windows desktop or X display')
class DesktopTests(unittest.TestCase):
    def setUp(self):
        import tkinter as tk
        from desktop import CourseMaker
        self.root = tk.Tk()
        self.app = CourseMaker(self.root)
        self.root.update()

    def tearDown(self):
        for timer in self.root.tk.call('after', 'info'):
            self.root.after_cancel(timer)
        self.root.destroy()

    def wait_worker(self):
        end = time.monotonic() + 5
        while self.app.busy and time.monotonic() < end:
            self.root.update()
            time.sleep(.01)
        self.root.update()
        self.assertFalse(self.app.busy)

    def local_sample(self):
        self.app.set_source(SAMPLE)
        self.app.provider.set(PROVIDERS[0])
        self.app.provider_changed()
        self.root.update()

    def test_direct_offline_generation_stages_then_accepts(self):
        self.local_sample()
        self.app.start()
        self.wait_worker()
        self.assertEqual(self.app.text(self.app.editor), '')
        self.assertEqual(len(self.app.job['completed']), 5)
        self.assertIn('### Video resources', self.app.text(self.app.candidate))
        self.app.apply_draft()
        self.root.update()
        self.assertIn('## Module 5:', self.app.text(self.app.editor))
        self.assertIsNone(self.app.job)
        self.assertEqual(self.app.view.get(), 'Course')

    def test_failure_checkpoint_save_and_reopen_preserve_course(self):
        self.local_sample()
        self.app.replace(self.app.editor, 'Keep accepted course')
        one = advance(new_job(SAMPLE, '', EngineConfig()), EngineConfig())
        with patch('desktop.advance', side_effect=[one, CourseError('Quota reached')]), patch('desktop.messagebox.showerror'):
            self.app.start()
            self.wait_worker()
        self.assertEqual(self.app.text(self.app.editor), 'Keep accepted course')
        self.assertEqual(len(self.app.job['completed']), 1)
        self.app.key.set('fake-key-never-save')
        with tempfile.TemporaryDirectory() as directory:
            self.app.path = Path(directory) / 'course.json'
            self.assertTrue(self.app.save())
            data = self.app.path.read_bytes()
            self.assertNotIn(b'fake-key-never-save', data)
            self.app.set_project(load_project(data), self.app.path)
            self.assertEqual(len(self.app.job['completed']), 1)
            self.assertEqual(self.app.text(self.app.editor), 'Keep accepted course')
            self.assertFalse(self.app.dirty)
        self.app.start()
        self.wait_worker()
        self.assertEqual(len(self.app.job['completed']), 5)

    def test_pause_keeps_active_module_and_stops_next_request(self):
        self.local_sample()
        started, release = threading.Event(), threading.Event()
        real_advance = advance
        def slow_step(job, cfg):
            started.set()
            release.wait(timeout=3)
            return real_advance(job, cfg)
        with patch('desktop.advance', side_effect=slow_step) as call:
            self.app.start()
            self.assertTrue(started.wait(timeout=1))
            self.app.pause()
            release.set()
            self.wait_worker()
            self.assertEqual(call.call_count, 1)
        self.assertEqual(len(self.app.job['completed']), 1)
        self.assertEqual(str(self.app.apply_button.cget('state')), 'disabled')

    def test_model_selection_and_online_consent_prevent_accidental_call(self):
        self.app.set_source(SAMPLE)
        self.app.model.set('gemini-3.5-flash-lite')
        self.app.key.set('fake-key')
        with patch('desktop.advance', side_effect=AssertionError('not allowed')), patch('desktop.messagebox.showerror'):
            self.app.start()
        self.assertFalse(self.app.busy)
        self.assertEqual(self.app.config().model, 'gemini-3.5-flash-lite')
        self.app.provider.set(PROVIDERS[2])
        self.app.provider_changed()
        self.assertEqual(self.app.key.get(), '')
        self.assertFalse(self.app.consent.get())

    def test_minimum_window_and_startup_controls_fit(self):
        self.assertLessEqual(self.root.winfo_width(), self.root.winfo_screenwidth() - 40)
        self.assertLessEqual(self.root.winfo_height(), self.root.winfo_screenheight() - 100)
        self.root.geometry('940x620')
        self.root.update()
        for widget in (self.app.source, self.app.model_picker, self.app.key_entry,
                       self.app.generate_button, self.app.pause_button, self.app.editor):
            self.assertTrue(widget.winfo_viewable())
            self.assertGreater(widget.winfo_height(), 20)
            self.assertLessEqual(widget.winfo_rootx() + widget.winfo_width(),
                                 self.root.winfo_rootx() + self.root.winfo_width())
            self.assertLessEqual(widget.winfo_rooty() + widget.winfo_height(),
                                 self.root.winfo_rooty() + self.root.winfo_height())

    def test_settings_do_not_displace_primary_controls(self):
        self.root.geometry('940x620')
        self.root.update()
        before = self.app.generate_button.winfo_rooty()
        self.app.toggle_settings()
        self.root.update()
        self.assertTrue(self.app.settings.winfo_viewable())
        self.assertEqual(self.app.generate_button.winfo_rooty(), before)
        self.app.settings.destroy()

    def test_acceptance_restores_source_snapshot_only_after_confirmation(self):
        self.local_sample()
        self.app.scope.set('1. Airframe components and load paths')
        self.app.start()
        self.wait_worker()
        self.app.replace(self.app.source, 'Week 1: Changed source')
        with patch('desktop.messagebox.askyesno', return_value=False):
            self.app.apply_draft()
        self.assertIsNotNone(self.app.job)
        self.assertEqual(self.app.text(self.app.editor), '')
        with patch('desktop.messagebox.askyesno', return_value=True):
            self.app.apply_draft()
        self.assertEqual(self.app.text(self.app.source), SAMPLE)
        self.assertIsNone(self.app.job)


if __name__ == '__main__':
    unittest.main()
