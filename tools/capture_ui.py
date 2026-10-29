"""Capture the actual one-workspace Tk UI on Windows or an X display."""
from pathlib import Path
import sys
import tkinter as tk

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PIL import ImageGrab
from course_core import SAMPLE
from desktop import CourseMaker
from engines import EngineConfig
from workflow import accept_job, advance, new_job


def main():
    target = Path(sys.argv[1] if len(sys.argv) > 1 else 'ui-review')
    target.mkdir(parents=True, exist_ok=True)
    root = tk.Tk()
    try:
        app = CourseMaker(root)
        app.set_source(SAMPLE)
        cfg = EngineConfig()
        job = new_job(SAMPLE, '', cfg, [0])
        job = advance(job, cfg)
        for name, size in [('syllabus', '1160x790'), ('draft', '1160x790'), ('course-minimum', '940x620')]:
            if name == 'draft':
                app.job = job
                app.refresh_draft()
            elif name == 'course-minimum':
                app.set_project(accept_job(app.project(), job))
            width, height = map(int, size.split('x'))
            width = min(width, root.winfo_screenwidth() - 40)
            height = min(height, root.winfo_screenheight() - 100)
            root.geometry(f'{width}x{height}+20+20')
            root.update()
            root.lift()
            root.update()
            x, y = root.winfo_rootx(), root.winfo_rooty()
            ImageGrab.grab(bbox=(x, y, x + root.winfo_width(), y + root.winfo_height())).save(target / f'{name}.png')
    finally:
        for timer in root.tk.call('after', 'info'):
            root.after_cancel(timer)
        root.destroy()


if __name__ == '__main__':
    main()
