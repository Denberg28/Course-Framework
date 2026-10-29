"""Single-workspace Windows course authoring. Workers never access Tk widgets."""
from __future__ import annotations

from pathlib import Path
import queue
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from academy_theme import FIELD, INK, LINE, PAPER, WARM, apply_desktop_theme
from course_core import (CourseError, SAMPLE, VERSION, analyze_syllabus, atomic_write,
                         export_bundle, export_html, extract_text, load_project,
                         make_project, project_bytes, read_file)
from engines import EngineConfig, PROVIDERS
from workflow import GEMINI_MODELS, accept_job, advance, can_resume, draft_text, is_complete, new_job


class CourseMaker:
    def __init__(self, root):
        self.root, self.path = root, None
        self.dirty = self.loading = self.busy = False
        self.job = None
        self.engine_used, self.model_used, self.accepted_source = 'Local template', '', ''
        self.results = queue.Queue(maxsize=1)
        self.pause_event = threading.Event()
        self.review_timer = None
        self.poll_timer = None
        self.plan = None
        self.style = apply_desktop_theme(root)
        root.title(f'Course Framework {VERSION}')
        root.geometry(f'{min(1160, max(940, root.winfo_screenwidth() - 40))}x{min(790, max(620, root.winfo_screenheight() - 100))}+20+20')
        root.minsize(940, 620)
        self.title = tk.StringVar()
        self.provider = tk.StringVar(value=PROVIDERS[1])
        self.model = tk.StringVar(value=GEMINI_MODELS[0])
        self.key = tk.StringVar()
        self.endpoint = tk.StringVar(value='https://api.openai.com/v1')
        self.consent = tk.BooleanVar(value=False)
        self.scope = tk.StringVar(value='All modules')
        self.view = tk.StringVar(value='Course')
        self.summary = tk.StringVar(value='Paste a syllabus to begin.')
        self.status = tk.StringVar(value='Ready')
        self.settings_open = tk.BooleanVar(value=False)
        self.title.trace_add('write', lambda *_: self.mark_dirty())

        header = ttk.Frame(root, padding=(18, 12))
        header.pack(fill='x')
        ttk.Label(header, text='Course Framework', style='Title.TLabel').pack(side='left')
        ttk.Button(header, text='Save', command=self.save).pack(side='right')
        menu_button = ttk.Menubutton(header, text='File')
        menu_button.pack(side='right', padx=6)
        menu = tk.Menu(menu_button, tearoff=False)
        for label, command in [('New', self.new), ('Open…', self.open_project),
                               ('Save as…', lambda: self.save(True)), ('Export…', self.export)]:
            menu.add_command(label=label, command=command)
        menu_button.configure(menu=menu)
        ttk.Separator(root).pack(fill='x')
        shell = ttk.Frame(root, padding=(18, 14))
        shell.pack(fill='both', expand=True)
        panes = ttk.Panedwindow(shell, orient='horizontal')
        panes.pack(fill='both', expand=True)
        self.input_panel = ttk.Frame(panes, padding=(0, 0, 12, 0))
        self.output_panel = ttk.Frame(panes, padding=(12, 0, 0, 0))
        panes.add(self.input_panel, weight=2)
        panes.add(self.output_panel, weight=3)
        self.input_panel.columnconfigure(0, weight=1)

        bar = ttk.Frame(self.input_panel)
        bar.pack(fill='x', pady=(0, 6))
        ttk.Label(bar, text='Syllabus', style='Section.TLabel').pack(side='left')
        ttk.Button(bar, text='Import…', command=self.import_syllabus).pack(side='right')
        self.source = self.textbox(self.input_panel)
        self.source.configure(height=1)
        details = ttk.Frame(self.input_panel)
        details.pack(fill='x', pady=(6, 8))
        label = ttk.Label(details, textvariable=self.summary, style='Muted.TLabel')
        label.pack(side='left', fill='x', expand=True)
        label.bind('<Configure>', lambda e: label.configure(wraplength=max(80, e.width)))
        ttk.Button(details, text='Outline', command=self.show_outline).pack(side='right')
        ttk.Label(self.input_panel, text='Agent model', style='Muted.TLabel').pack(anchor='w')
        self.model_picker = ttk.Combobox(self.input_panel, textvariable=self.model, values=GEMINI_MODELS)
        self.model_picker.pack(fill='x', pady=(3, 8))
        ttk.Label(self.input_panel, text='API key', style='Muted.TLabel').pack(anchor='w')
        self.key_entry = ttk.Entry(self.input_panel, textvariable=self.key, show='•')
        self.key_entry.pack(fill='x', pady=(3, 5))
        ttk.Checkbutton(self.input_panel, text='Settings', variable=self.settings_open, command=self.toggle_settings).pack(anchor='w')
        self.settings = ttk.Frame(self.input_panel)
        self.settings.columnconfigure(1, weight=1)
        for row, (label_text, widget) in enumerate([
            ('Provider', ttk.Combobox(self.settings, textvariable=self.provider, values=PROVIDERS, state='readonly')),
            ('Base URL', ttk.Entry(self.settings, textvariable=self.endpoint)),
            ('Title', ttk.Entry(self.settings, textvariable=self.title))]):
            ttk.Label(self.settings, text=label_text, style='Muted.TLabel').grid(row=row, column=0, sticky='w', padx=(0, 8))
            widget.grid(row=row, column=1, sticky='ew', pady=3)
            if row == 0:
                widget.bind('<<ComboboxSelected>>', self.provider_changed)
        ttk.Button(self.settings, text='Clear key', command=lambda: self.key.set('')).grid(row=3, column=1, sticky='w')
        self.scope_picker = ttk.Combobox(self.input_panel, textvariable=self.scope, state='readonly', values=['All modules'])
        self.scope_picker.pack(fill='x', pady=(6, 4))
        ttk.Checkbutton(self.input_panel, text='Send syllabus to agent · fees/quota may apply', variable=self.consent).pack(anchor='w', pady=(0, 5))
        actions = ttk.Frame(self.input_panel)
        actions.pack(fill='x')
        self.generate_button = ttk.Button(actions, text='Generate', style='Accent.TButton', command=self.start)
        self.generate_button.pack(side='left', fill='x', expand=True)
        self.pause_button = ttk.Button(actions, text='Pause', state='disabled', command=self.pause)
        self.pause_button.pack(side='right', padx=(6, 0))

        result_bar = ttk.Frame(self.output_panel)
        result_bar.pack(fill='x', pady=(0, 8))
        ttk.Label(result_bar, text='Course', style='Section.TLabel').pack(side='left')
        self.apply_button = ttk.Button(result_bar, text='Use draft', style='Accent.TButton', command=self.apply_draft, state='disabled')
        self.apply_button.pack(side='right')
        views = ttk.Frame(self.output_panel)
        views.pack(fill='x', pady=(0, 6))
        self.draft_radio = ttk.Radiobutton(views, text='Draft', value='Draft', variable=self.view, command=self.show_view, state='disabled')
        self.draft_radio.pack(side='left')
        ttk.Radiobutton(views, text='Accepted course', value='Course', variable=self.view, command=self.show_view).pack(side='left', padx=8)
        self.result_host = ttk.Frame(self.output_panel)
        self.result_host.pack(fill='both', expand=True)
        self.editor_frame, self.candidate_frame = ttk.Frame(self.result_host), ttk.Frame(self.result_host)
        self.editor = self.textbox(self.editor_frame)
        self.candidate = self.textbox(self.candidate_frame, editable=False)
        self.editor_frame.pack(fill='both', expand=True)
        foot = ttk.Frame(root, padding=(18, 9))
        foot.pack(fill='x')
        status_label = ttk.Label(foot, textvariable=self.status, style='Muted.TLabel')
        status_label.pack(fill='x')
        status_label.bind('<Configure>', lambda e: status_label.configure(wraplength=max(140, e.width)))
        root.bind('<Control-s>', lambda e: self.save())
        root.bind('<Control-o>', lambda e: self.open_project())
        root.protocol('WM_DELETE_WINDOW', self.close)
        self.poll_timer = root.after(120, self.poll)

    @staticmethod
    def text(box):
        return box.get('1.0', 'end-1c')

    @staticmethod
    def replace(box, text):
        state = box.cget('state')
        box.configure(state='normal')
        box.delete('1.0', 'end')
        box.insert('1.0', text)
        box.edit_modified(False)
        box.configure(state=state)

    def textbox(self, parent, editable=True):
        box = ScrolledText(parent, wrap='word', undo=True, font=('Segoe UI', 10), width=1, height=1,
                           background=PAPER if editable else FIELD, foreground=INK, insertbackground=INK,
                           selectbackground=WARM, selectforeground=INK, relief='flat', borderwidth=0,
                           highlightthickness=1, highlightbackground=LINE, highlightcolor=INK, padx=10, pady=8)
        box.pack(fill='both', expand=True)
        if editable:
            box.bind('<<Modified>>', lambda e: self.changed(box))
        else:
            box.configure(state='disabled')
        return box

    def changed(self, box):
        if not box.edit_modified():
            return
        box.edit_modified(False)
        self.mark_dirty()
        if box is self.source:
            if self.review_timer:
                self.root.after_cancel(self.review_timer)
            self.review_timer = self.root.after(300, self.review)

    def mark_dirty(self):
        if not self.loading:
            self.dirty = True
            self.root.title(f'* Course Framework {VERSION}')

    def toggle_settings(self):
        if self.settings_open.get():
            self.settings.pack(fill='x', before=self.scope_picker)
        else:
            self.settings.pack_forget()

    def provider_changed(self, event=None):
        self.key.set('')
        self.consent.set(False)
        if self.provider.get() == PROVIDERS[1]:
            self.model_picker.configure(values=GEMINI_MODELS)
            self.model.set(GEMINI_MODELS[0])
        elif self.provider.get() == PROVIDERS[0]:
            self.model_picker.configure(values=['Offline template'])
            self.model.set('Offline template')
        else:
            self.model_picker.configure(values=[])
            self.model.set('')

    def show_view(self):
        self.editor_frame.pack_forget()
        self.candidate_frame.pack_forget()
        (self.candidate_frame if self.view.get() == 'Draft' else self.editor_frame).pack(fill='both', expand=True)

    def review(self):
        self.review_timer = None
        try:
            self.plan = analyze_syllabus(self.text(self.source))
            choices = ['All modules'] + [f"{i + 1}. {t['title']}" for i, t in enumerate(self.plan['topics'])]
            self.scope_picker.configure(values=choices)
            if self.scope.get() not in choices:
                self.scope.set(choices[0])
            self.summary.set(f"{len(self.plan['topics'])} modules · {len(self.plan['outcomes'])} outcomes")
        except CourseError:
            self.plan = None
            self.summary.set('Paste a syllabus to begin.')
            self.scope.set('All modules')
            self.scope_picker.configure(values=['All modules'])

    def show_outline(self):
        self.review()
        if self.plan:
            lines = [f"{i + 1}. {t['title']} · {t['schedule'] or 'Week unassigned'}" for i, t in enumerate(self.plan['topics'])]
            lines += ['', *self.plan['warnings']]
            messagebox.showinfo('Outline', '\n'.join(lines), parent=self.root)

    def config(self):
        return EngineConfig(self.provider.get(), self.key.get(), self.model.get().strip(), self.endpoint.get().strip(), True)

    def indices(self):
        if self.scope.get() == 'All modules':
            return None
        return [int(self.scope.get().split('.', 1)[0]) - 1]

    def project(self):
        title = self.title.get().strip()
        if not title and self.text(self.source).strip():
            title = analyze_syllabus(self.text(self.source))['metadata'].get('title', '')
        return make_project(self.text(self.source), title, self.text(self.editor), self.engine_used,
                            model=self.model_used, pending=self.job, accepted_syllabus=self.accepted_source or self.text(self.source))

    def refresh_draft(self):
        self.replace(self.candidate, draft_text(self.job) if self.job else '')
        self.apply_button.configure(state='normal' if is_complete(self.job) else 'disabled')
        self.draft_radio.configure(state='normal' if self.job else 'disabled')
        if self.job:
            self.view.set('Draft')
        self.show_view()

    def set_project(self, project, path=None):
        self.loading = True
        self.replace(self.source, project['syllabus'])
        self.title.set(project['title'])
        self.replace(self.editor, project['content'])
        self.engine_used, self.model_used, self.job = project['engine'], project.get('model', ''), project.get('pending')
        self.accepted_source = project.get('accepted_syllabus', project['syllabus'])
        self.path, self.dirty = path, False
        if self.job and self.job['provider'] in PROVIDERS:
            self.provider.set(self.job['provider'])
            self.provider_changed()
            self.model.set(self.job['model'] or 'Offline template')
        self.view.set('Draft' if self.job else 'Course')
        self.refresh_draft()
        self.review()
        self.loading = False
        self.root.title(f'Course Framework {VERSION}')

    def confirm_leave(self):
        if not self.dirty:
            return True
        answer = messagebox.askyesnocancel('Save project', 'Save your course and unfinished draft before continuing?', parent=self.root)
        return self.save() if answer else answer is False

    def new(self):
        if self.busy:
            return self.status.set('Pause and wait for the active request before opening another project.')
        if self.confirm_leave():
            project = make_project('', '', '')
            project['title'] = ''
            self.set_project(project)

    def open_project(self):
        if self.busy or not self.confirm_leave():
            return
        path = filedialog.askopenfilename(filetypes=[('Course project', '*.json')], parent=self.root)
        if path:
            try:
                self.set_project(load_project(read_file(path)), Path(path))
                self.status.set('Project opened · enter your session key to resume a draft')
            except (CourseError, OSError) as error:
                self.error(error)

    def save(self, save_as=False):
        path = self.path if self.path and not save_as else filedialog.asksaveasfilename(
            defaultextension='.json', initialfile='course-project.json', filetypes=[('Course project', '*.json')], parent=self.root)
        if not path:
            return False
        try:
            atomic_write(path, project_bytes(self.project()))
            self.path, self.dirty = Path(path), False
            self.root.title(f'Course Framework {VERSION} — {self.path.name}')
            self.status.set('Project saved · includes unfinished modules · no API key')
            return True
        except (CourseError, OSError) as error:
            self.error(error)
            return False

    def import_syllabus(self):
        path = filedialog.askopenfilename(filetypes=[('Syllabus', '*.txt *.md *.docx *.pdf')], parent=self.root)
        if path:
            try:
                self.set_source(extract_text(path, read_file(path)))
            except (CourseError, OSError) as error:
                self.error(error)

    def set_source(self, text):
        if self.text(self.source).strip() and not messagebox.askyesno('Replace syllabus', 'Replace the current syllabus?', parent=self.root):
            return
        self.replace(self.source, text)
        self.title.set('')
        self.mark_dirty()
        self.review()

    def start(self):
        if self.busy:
            return
        try:
            self.review()
            self.project()
            cfg = self.config()
            if cfg.provider != PROVIDERS[0] and not self.consent.get():
                raise CourseError('Allow sending the syllabus to the selected agent first.')
            source, title, indices = self.text(self.source), self.title.get(), self.indices()
            job = self.job if can_resume(self.job, source, title, cfg, indices) else new_job(source, title, cfg, indices)
            self.busy = True
            self.pause_event.clear()
            self.generate_button.configure(state='disabled')
            self.pause_button.configure(state='normal')
            self.status.set(f"Generating · {len(job['indices']) - len(job['completed'])} module request(s) remaining")
            def worker():
                current = job
                try:
                    while not is_complete(current) and not self.pause_event.is_set():
                        current = advance(current, cfg)
                        self.results.put(('progress', current))
                    self.results.put(('done', None))
                except CourseError as error:
                    self.results.put(('error', str(error)))
                except Exception:
                    self.results.put(('error', 'Request stopped unexpectedly. Completed modules are preserved.'))
            threading.Thread(target=worker, daemon=True).start()
        except CourseError as error:
            self.error(error)

    def pause(self):
        self.pause_event.set()
        self.pause_button.configure(state='disabled')
        self.status.set('Pausing after the active module. Its request may still be billed.')

    def poll(self):
        try:
            kind, value = self.results.get_nowait()
            if kind == 'progress':
                self.job = value
                self.refresh_draft()
                self.mark_dirty()
                self.status.set(f"Draft · {len(value['completed'])}/{len(value['indices'])} modules · {value['model'] or 'Offline template'}")
            else:
                self.busy = False
                self.generate_button.configure(state='normal')
                self.pause_button.configure(state='disabled')
                self.status.set('Draft ready · Review and use draft' if is_complete(self.job) else 'Paused · Generate resumes completed work with the same syllabus and model')
                if kind == 'error':
                    self.error(CourseError(value))
        except queue.Empty:
            pass
        self.poll_timer = self.root.after(120, self.poll)

    def apply_draft(self):
        try:
            if not is_complete(self.job):
                raise CourseError('Finish the selected modules before using this draft.')
            if self.text(self.editor).strip() and not messagebox.askyesno('Replace course', 'Replace the accepted course with this draft?', parent=self.root):
                return
            if (self.text(self.source) != self.job['syllabus'] or (self.title.get().strip() and self.title.get() != self.job['title'])) and not messagebox.askyesno(
                    'Restore syllabus', 'Use the syllabus and title that generated this draft?', parent=self.root):
                return
            saved = accept_job(self.project(), self.job)
            self.set_project(saved, self.path)
            self.mark_dirty()
            self.status.set('Course ready · edit and save')
        except CourseError as error:
            self.error(error)

    def export(self):
        try:
            project = {**self.project(), 'pending': None}
            if not project['content'].strip():
                raise CourseError('Review and use a complete draft before exporting. Save project keeps unfinished work.')
            path = filedialog.asksaveasfilename(defaultextension='.zip', initialfile='course-package.zip',
                filetypes=[('Course package', '*.zip'), ('Markdown', '*.md'), ('HTML text view', '*.html')], parent=self.root)
            if path:
                suffix = Path(path).suffix.lower()
                data = (project['content'].encode() if suffix == '.md' else export_html(project['title'], project['content'])
                        if suffix == '.html' else export_bundle(project))
                atomic_write(path, data)
                self.status.set('Course exported')
        except (CourseError, OSError) as error:
            self.error(error)

    def error(self, error):
        text = str(error) if isinstance(error, CourseError) else 'Could not read or save this file. Check its location and permissions.'
        self.status.set(text)
        messagebox.showerror('Course Framework', text, parent=self.root)

    def close(self):
        if self.busy and not messagebox.askyesno('Request active', 'Close after saving completed work? The active provider request may still be billed.', parent=self.root):
            return
        if self.confirm_leave():
            self.pause_event.set()
            self.key.set('')
            for timer in self.root.tk.call('after', 'info'):
                self.root.after_cancel(timer)
            self.root.destroy()


def main():
    root = tk.Tk()
    app = CourseMaker(root)
    if '--smoke-test' in sys.argv:
        from course_core import build_course_markdown
        app.set_project(make_project(SAMPLE, 'Smoke Test', build_course_markdown(SAMPLE)))
        root.update()
        assert 'Module 1:' in app.text(app.editor)
        assert '5 modules' in app.summary.get()
        assert not app.key.get()
        root.destroy()
        return
    root.mainloop()


if __name__ == '__main__':
    main()
