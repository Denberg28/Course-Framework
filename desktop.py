"""Windows-first Tk course maker. Network work never touches the Tk thread."""
from __future__ import annotations

import queue
from pathlib import Path
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from course_core import (CourseError, SAMPLE, VERSION, analyze_syllabus, atomic_write,
                         export_bundle, export_html, extract_text, load_project,
                         make_project, project_bytes, read_file)
from engines import EngineConfig, PROVIDERS, generate_course


class CourseMaker:
    def __init__(self, root):
        self.root = root
        self.path = None
        self.dirty = False
        self.loading = False
        self.engine_used = "Local template"
        self.candidate_engine = "Local template"
        self.candidate_source = ""
        self.candidate_title = ""
        self.unaccepted = False
        self.busy = False
        self.discard_result = False
        self.results = queue.Queue(maxsize=1)
        root.title(f"Course Framework {VERSION}")
        root.geometry("1160x790")
        root.minsize(940, 620)
        root.configure(bg="#f3f5f9")
        style = ttk.Style(root)
        style.theme_use("clam")
        style.configure(".", font=("Segoe UI", 10), background="#f3f5f9", foreground="#172b49")
        style.configure("TButton", padding=(12, 7))
        style.configure("TNotebook.Tab", padding=(18, 10))
        style.configure("Title.TLabel", font=("Segoe UI", 21, "bold"))
        style.configure("Accent.TButton", background="#203d65", foreground="white")
        shell = ttk.Frame(root, padding=20)
        shell.pack(fill="both", expand=True)
        header = ttk.Frame(shell)
        header.pack(fill="x")
        ttk.Label(header, text="Course Framework", style="Title.TLabel").pack(side="left")
        ttk.Label(header, text="Syllabus → teachable course draft").pack(side="right")
        toolbar = ttk.Frame(shell, padding=(0, 16, 0, 12))
        toolbar.pack(fill="x")
        for label, action in (("New", self.new), ("Open project", self.open_project),
                              ("Save project", self.save), ("Save as…", lambda: self.save(True)),
                              ("Export…", self.export)):
            ttk.Button(toolbar, text=label, command=action).pack(side="left", padx=(0, 6))
        ttk.Button(toolbar, text="Engine settings", command=lambda: self.tabs.select(self.settings_tab)).pack(side="right")
        title_row = ttk.Frame(shell)
        title_row.pack(fill="x", pady=(0, 12))
        ttk.Label(title_row, text="Course title", width=13).pack(side="left")
        self.title = tk.StringVar()
        ttk.Entry(title_row, textvariable=self.title).pack(side="left", fill="x", expand=True)
        self.title.trace_add("write", lambda *_: self.mark_dirty())
        self.tabs = ttk.Notebook(shell)
        self.tabs.pack(fill="both", expand=True)
        self.source_tab = ttk.Frame(self.tabs, padding=12)
        self.editor_tab = ttk.Frame(self.tabs, padding=12)
        self.draft_tab = ttk.Frame(self.tabs, padding=12)
        self.settings_tab = ttk.Frame(self.tabs, padding=20)
        for label, tab in (("1  Syllabus", self.source_tab), ("2  Course editor", self.editor_tab),
                           ("3  Generated draft", self.draft_tab), ("Engine", self.settings_tab)):
            self.tabs.add(tab, text=label)
        bar = ttk.Frame(self.source_tab)
        bar.pack(fill="x", pady=(0, 10))
        ttk.Button(bar, text="Import syllabus…", command=self.import_syllabus).pack(side="left", padx=(0, 6))
        ttk.Button(bar, text="Load example", command=self.example).pack(side="left")
        ttk.Button(bar, text="Review outline", command=self.review).pack(side="right")
        panes = ttk.Panedwindow(self.source_tab, orient="horizontal")
        panes.pack(fill="both", expand=True)
        left, right = ttk.Frame(panes), ttk.Frame(panes)
        panes.add(left, weight=3)
        panes.add(right, weight=2)
        ttk.Label(left, text="Paste or import TXT, MD, DOCX, or a text-based PDF").pack(anchor="w", pady=(0, 6))
        self.source = self.textbox(left)
        ttk.Label(right, text="Detected course structure · review before generating").pack(anchor="w", padx=(12, 0), pady=(0, 6))
        self.outline = self.textbox(right, editable=False)
        ttk.Label(self.editor_tab, text="Edit your accepted course in Markdown. Save the project to retain both source and draft.").pack(anchor="w", pady=(0, 8))
        self.editor = self.textbox(self.editor_tab)
        revision = ttk.Frame(self.editor_tab)
        revision.pack(fill="x", pady=(10, 0))
        self.instructions = tk.StringVar()
        ttk.Entry(revision, textvariable=self.instructions).pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.revise_button = ttk.Button(revision, text="Revise with engine", command=lambda: self.start(True))
        self.revise_button.pack(side="right")
        ttk.Label(self.editor_tab, text="Revision instructions, e.g. Add a worked example to module 2 and preserve the other modules.").pack(anchor="w", pady=(6, 0))
        draft_bar = ttk.Frame(self.draft_tab)
        draft_bar.pack(fill="x", pady=(0, 10))
        ttk.Label(draft_bar, text="Review the generated draft. Your accepted course stays unchanged until you use it.").pack(side="left")
        self.apply_button = ttk.Button(draft_bar, text="Use this draft", command=self.apply_draft, state="disabled")
        self.apply_button.pack(side="right")
        self.candidate = self.textbox(self.draft_tab)
        self.setup_engine()
        footer = ttk.Frame(shell, padding=(0, 12, 0, 0))
        footer.pack(fill="x")
        self.status = tk.StringVar(value="Ready · Local template mode · No API key required")
        ttk.Label(footer, textvariable=self.status, wraplength=700).pack(side="left", fill="x", expand=True)
        self.cancel_button = ttk.Button(footer, text="Discard pending result", command=self.cancel, state="disabled")
        self.cancel_button.pack(side="right", padx=(6, 0))
        self.generate_button = ttk.Button(footer, text="Generate course", style="Accent.TButton", command=self.start)
        self.generate_button.pack(side="right")
        root.bind("<Control-s>", lambda e: self.save())
        root.bind("<Control-o>", lambda e: self.open_project())
        root.protocol("WM_DELETE_WINDOW", self.close)
        root.after(150, self.poll)

    def textbox(self, parent, editable=True):
        box = ScrolledText(parent, wrap="word", undo=True, font=("Segoe UI", 11),
                           background="white", foreground="#172b49", relief="flat", padx=12, pady=10)
        box.pack(fill="both", expand=True)
        if editable:
            box.bind("<<Modified>>", lambda e: self.changed(box))
        else:
            box.configure(state="disabled")
        return box

    def changed(self, box):
        if box.edit_modified():
            if box in (self.source, self.editor):
                self.mark_dirty()
            box.edit_modified(False)

    def mark_dirty(self):
        if not self.loading:
            self.dirty = True
            self.root.title(f"* Course Framework {VERSION}" + (f" — {self.path.name}" if self.path else ""))

    @staticmethod
    def text(box):
        return box.get("1.0", "end-1c")

    @staticmethod
    def replace(box, value):
        state = box.cget("state")
        box.configure(state="normal")
        box.delete("1.0", "end")
        box.insert("1.0", value)
        box.edit_modified(False)
        box.configure(state=state)

    def setup_engine(self):
        form = self.settings_tab
        form.columnconfigure(1, weight=1)
        self.provider = tk.StringVar(value=PROVIDERS[0])
        self.model = tk.StringVar(value="gemini-2.5-flash-lite")
        self.endpoint = tk.StringVar(value="https://api.openai.com/v1")
        self.key = tk.StringVar()
        fields = [("Provider", ttk.Combobox(form, values=PROVIDERS, textvariable=self.provider, state="readonly")),
                  ("API key", ttk.Entry(form, textvariable=self.key, show="•")),
                  ("Model ID", ttk.Entry(form, textvariable=self.model)),
                  ("API base URL", ttk.Entry(form, textvariable=self.endpoint))]
        for row, (label, widget) in enumerate(fields):
            ttk.Label(form, text=label).grid(row=row, column=0, sticky="w", padx=(0, 20), pady=9)
            widget.grid(row=row, column=1, sticky="ew", pady=9)
        ttk.Button(form, text="Clear key", command=lambda: self.key.set("")).grid(row=4, column=1, sticky="w", pady=8)
        ttk.Label(form, justify="left", wraplength=740, text=(
            "Google AI Studio: paste a Gemini API key and an available Gemini model ID. The Google endpoint is fixed.\n\n"
            "OpenAI-compatible: enter the provider's API key, model ID, and base URL ending in /v1 if required by that provider. "
            "The app uses Chat Completions. A key alone cannot identify a provider or support every API format.\n\n"
            "Local engines: select OpenAI-compatible and use a localhost base URL. A key may be omitted for a local server.\n\n"
            "Keys stay in this session and are never written to projects. Online generation sends your syllabus and, for revision, "
            "your draft to the selected engine. Provider charges and quotas may apply.\n\n"
            "AI output is an editable draft. Review facts, answer keys, coverage, and references before use."
        )).grid(row=5, column=0, columnspan=2, sticky="nw", pady=15)

    def project(self):
        return make_project(self.text(self.source), self.title.get(), self.text(self.editor), self.engine_used)

    def confirm_leave(self):
        if self.unaccepted and not messagebox.askyesno("Unaccepted draft", "The generated draft has not been accepted or saved. Discard it and continue?", parent=self.root):
            return False
        if not self.dirty:
            return True
        answer = messagebox.askyesnocancel("Unsaved course", "Save your current project before continuing?", parent=self.root)
        return self.save() if answer else answer is False

    def set_project(self, project, path=None):
        self.loading = True
        self.title.set(project["title"])
        self.replace(self.source, project["syllabus"])
        self.replace(self.editor, project["content"])
        self.replace(self.candidate, "")
        self.apply_button.configure(state="disabled")
        self.unaccepted = False
        self.engine_used = project["engine"]
        self.path, self.dirty = path, False
        self.loading = False
        self.root.title(f"Course Framework {VERSION}" + (f" — {path.name}" if path else ""))
        self.review()

    def new(self):
        if self.busy:
            return messagebox.showinfo("Engine busy", "Wait for the pending request before opening another project.")
        if self.confirm_leave():
            project = make_project("", "", "")
            project["title"] = ""
            self.set_project(project)
            self.status.set("New project")
            self.tabs.select(self.source_tab)

    def open_project(self):
        if self.busy:
            return messagebox.showinfo("Engine busy", "Wait for the pending request before opening another project.")
        if not self.confirm_leave():
            return
        path = filedialog.askopenfilename(filetypes=[("Course project", "*.json")])
        if path:
            try:
                project = load_project(read_file(path))
                self.set_project(project, Path(path))
                self.status.set("Project opened")
                self.tabs.select(self.editor_tab if project["content"] else self.source_tab)
            except (CourseError, OSError) as error:
                self.error(error)

    def save(self, save_as=False):
        path = self.path if self.path and not save_as else filedialog.asksaveasfilename(
            defaultextension=".json", initialfile="course-project.json", filetypes=[("Course project", "*.json")])
        if not path:
            return False
        try:
            atomic_write(path, project_bytes(self.project()))
            self.path, self.dirty = Path(path), False
            self.root.title(f"Course Framework {VERSION} — {self.path.name}")
            self.status.set("Project saved · API keys are excluded")
            return True
        except (CourseError, OSError) as error:
            self.error(error)
            return False

    def import_syllabus(self):
        path = filedialog.askopenfilename(filetypes=[("Syllabus", "*.txt *.md *.docx *.pdf")])
        if path:
            try:
                text = extract_text(path, read_file(path))
                self.set_source(text)
            except (CourseError, OSError) as error:
                self.error(error)

    def set_source(self, text):
        if self.text(self.source).strip() and not messagebox.askyesno("Replace syllabus", "Replace the current syllabus text? The course editor will be preserved."):
            return
        self.replace(self.source, text)
        self.mark_dirty()
        self.review()

    def example(self):
        self.set_source(SAMPLE)

    def review(self):
        source = self.text(self.source)
        if not source.strip():
            self.replace(self.outline, "Paste a syllabus or load the example, then review its outline.")
            return
        try:
            plan = analyze_syllabus(source)
            if not self.title.get().strip() and plan["metadata"].get("title"):
                self.title.set(plan["metadata"]["title"])
            lines = [f"{len(plan['topics'])} modules · {len(plan['outcomes'])} course outcomes", ""]
            lines += [f"{key.title()}: {value}" for key, value in plan["metadata"].items()]
            lines += ["", "COURSE OUTCOMES"] + plan["outcomes"]
            lines += ["", "MODULES"]
            for i, topic in enumerate(plan["topics"], 1):
                lines += [f"{i}. {topic['title']} — Week(s): {topic['schedule'] or 'unassigned'}"]
                lines += [f"   • {sub}" for sub in topic["subtopics"]]
            lines += ["", "REVIEW NOTES"] + plan["warnings"]
            self.replace(self.outline, "\n".join(lines))
        except CourseError as error:
            self.error(error)

    def start(self, revise=False):
        if self.busy:
            return
        if self.unaccepted and not messagebox.askyesno("Unaccepted draft", "Replace the pending generated draft if this new request succeeds?"):
            return
        source, title = self.text(self.source), self.title.get()
        draft = self.text(self.editor) if revise else ""
        instructions = self.instructions.get() if revise else ""
        try:
            analyze_syllabus(source)
            self.project()  # Validate all editor bounds before starting a paid call.
            if revise and (not draft.strip() or not instructions.strip()):
                raise CourseError("Enter a course draft and revision instructions first.")
            config = EngineConfig(self.provider.get(), self.key.get(), self.model.get().strip(), self.endpoint.get().strip(), True)
            if config.provider != "Local template":
                if not messagebox.askyesno("Send to engine", f"Send the syllabus{' and course draft' if revise else ''} to {config.provider}?\n\nModel: {config.model}\nEndpoint: {'Google Gemini API' if config.provider == PROVIDERS[1] else config.base_url}\n\nProvider charges and quotas may apply."):
                    return
            self.busy, self.discard_result = True, False
            self.generate_button.configure(state="disabled")
            self.revise_button.configure(state="disabled")
            self.cancel_button.configure(state="normal")
            self.status.set("Generating a review draft… Your existing course is preserved.")
            def worker():
                try:
                    result = generate_course(source, title, config, draft=draft, instructions=instructions)
                    self.results.put((True, result, config.provider, source, title))
                except CourseError as error:
                    self.results.put((False, str(error), config.provider, source, title))
                except Exception:
                    self.results.put((False, "Unexpected engine failure. Your current draft is unchanged.", config.provider, source, title))
            threading.Thread(target=worker, daemon=True).start()
        except CourseError as error:
            self.error(error)

    def cancel(self):
        self.discard_result = True
        self.cancel_button.configure(state="disabled")
        self.status.set("Pending result will be discarded. Waiting for the request to finish; provider billing may still apply.")

    def poll(self):
        try:
            success, value, provider, source, title = self.results.get_nowait()
            self.busy = False
            self.generate_button.configure(state="normal")
            self.revise_button.configure(state="normal")
            self.cancel_button.configure(state="disabled")
            if self.discard_result:
                self.status.set("Pending result discarded · Current course unchanged")
            elif success:
                self.replace(self.candidate, value)
                self.candidate_engine = provider
                self.candidate_source, self.candidate_title = source, title
                self.unaccepted = True
                self.apply_button.configure(state="normal")
                self.tabs.select(self.draft_tab)
                self.status.set("Draft ready · Review it, then select Use this draft")
            else:
                self.status.set("Generation failed · Current course unchanged")
                self.error(CourseError(value))
        except queue.Empty:
            pass
        self.root.after(150, self.poll)

    def apply_draft(self):
        if self.text(self.editor).strip() and not messagebox.askyesno("Replace accepted course", "Replace the course editor with this draft? Save a project copy first if you need the previous version."):
            return
        if (self.text(self.source) != self.candidate_source or self.title.get() != self.candidate_title) and not messagebox.askyesno(
                "Syllabus changed", "Restore the syllabus and title used to generate this draft? The current source has changed since generation."):
            return
        self.replace(self.source, self.candidate_source)
        self.title.set(self.candidate_title)
        self.replace(self.editor, self.text(self.candidate))
        self.engine_used = self.candidate_engine
        self.unaccepted = False
        self.mark_dirty()
        self.tabs.select(self.editor_tab)
        self.status.set("Draft accepted · Edit and save your course project")

    def export(self):
        try:
            project = self.project()
            if not project["content"].strip():
                raise CourseError("Generate and accept a draft, or write course material in the editor first.")
            path = filedialog.asksaveasfilename(defaultextension=".zip", initialfile="course-package.zip",
                filetypes=[("Complete course package", "*.zip"), ("Markdown material", "*.md"), ("Printable HTML text view", "*.html")])
            if not path:
                return
            suffix = Path(path).suffix.lower()
            data = (project["content"].encode("utf-8") if suffix == ".md" else
                    export_html(project["title"], project["content"]) if suffix == ".html" else export_bundle(project))
            atomic_write(path, data)
            self.status.set("Course exported · Save the project separately to keep editing later")
        except (CourseError, OSError) as error:
            self.error(error)

    def error(self, error):
        messagebox.showerror("Course Framework", str(error) if isinstance(error, CourseError) else "Could not read or save this file. Check its location and permissions.", parent=self.root)

    def close(self):
        if self.busy and not messagebox.askyesno("Engine request pending", "Close the app and discard the pending result? Provider billing may still apply."):
            return
        if self.confirm_leave():
            self.key.set("")
            self.root.destroy()


def main():
    root = tk.Tk()
    app = CourseMaker(root)
    if "--smoke-test" in sys.argv:
        from course_core import build_course_markdown
        app.set_project(make_project(SAMPLE, "Smoke Test", build_course_markdown(SAMPLE)))
        root.update()
        assert "Module 1:" in app.text(app.editor)
        assert "5 modules" in app.text(app.outline)
        assert not app.key.get()
        root.destroy()
        return
    root.mainloop()


if __name__ == "__main__":
    main()
