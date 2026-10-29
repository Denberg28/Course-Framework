"""Capture the real Tk workspace on an interactive Windows/X display for review."""
from pathlib import Path
import sys
import tkinter as tk

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PIL import ImageGrab
from course_core import SAMPLE, build_course_markdown, make_project
from desktop import CourseMaker


def main():
    target = Path(sys.argv[1] if len(sys.argv) > 1 else 'ui-review')
    target.mkdir(parents=True, exist_ok=True)
    root = tk.Tk()
    try:
        app = CourseMaker(root)
        app.set_project(make_project(SAMPLE, 'Aircraft Structures', build_course_markdown(SAMPLE)))
        for name, page, size in [('syllabus', app.source_tab, '1160x790'),
                                 ('course', app.editor_tab, '1160x790'),
                                 ('engine-minimum', app.settings_tab, '940x620')]:
            width, height = map(int, size.split("x"))
            width = min(width, root.winfo_screenwidth() - 40)
            height = min(height, root.winfo_screenheight() - 100)
            root.geometry(f"{width}x{height}+20+20")
            app.tabs.select(page)
            root.update()
            root.lift()
            root.update()
            x, y = root.winfo_rootx(), root.winfo_rooty()
            ImageGrab.grab(bbox=(x, y, x + root.winfo_width(), y + root.winfo_height())).save(target / f'{name}.png')
    finally:
        root.destroy()


if __name__ == '__main__':
    main()
