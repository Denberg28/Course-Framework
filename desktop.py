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
from academy_theme import FIELD, INK, LINE, MUTED, PAPER, WARM, apply_desktop_theme


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
        width = min(1160, max(940, root.winfo_screenwidth() - 40))
        height = min(790, max(620, root.winfo_screenheight() - 100))
        root.geometry(f"{width}x{height}+20+20")
        root.minsize(940, 620)
        self.style = apply_desktop_theme(root)
        header = ttk.Frame(root, padding=(18, 12))
        header.pack(fill="x")
        ttk.Label(header, text="Course Framework", style="Title.TLabel").pack(side="left")
        toolbar = ttk.Frame(header)
        toolbar.pack(side="right")
        for label, action in (("New", self.new), ("Open", self.open_project),
                              ("Save", self.save), ("Save as…", lambda: self.save(True)),
                              ("Export…", self.export)):
            ttk.Button(toolbar, text=label, command=action).pack(side="left", padx=(4, 0))
        ttk.Separator(root).pack(fill="x")
        shell = ttk.Frame(root)
        shell.pack(fill="both", expand=True)
        rail = ttk.Frame(shell, style="Rail.TFrame", padding=(12, 18), width=196)
        rail.pack(side="left", fill="y")
        rail.pack_propagate(False)
        ttk.Label(rail, text="COURSE MAKER", style="Brand.TLabel").pack(anchor="w", padx=12)
        ttk.Label(rail, text="Authoring workspace", style="Rail.TLabel").pack(anchor="w", padx=12, pady=(3, 18))
        ttk.Separator(shell, orient="vertical").pack(side="left", fill="y")
        workspace = ttk.Frame(shell, padding=(18, 14))
        workspace.pack(side="left", fill="both", expand=True)
        title_row = ttk.Frame(workspace)
        title_row.pack(fill="x", pady=(0, 14))
        ttk.Label(title_row, text="Course title", style="Muted.TLabel").pack(side="left", padx=(0, 12))
        self.title = tk.StringVar()
        ttk.Entry(title_row, textvariable=self.title).pack(side="left", fill="x", expand=True)
        self.title.trace_add("write", lambda *_: self.mark_dirty())
        self.tabs = ttk.Notebook(workspace, style="Workspace.TNotebook")
        self.tabs.pack(fill="both", expand=True)
        self.source_tab = ttk.Frame(self.tabs)
        self.editor_tab = ttk.Frame(self.tabs)
        self.draft_tab = ttk.Frame(self.tabs)
        self.settings_tab = ttk.Frame(self.tabs)
        self.navigation = tk.StringVar(value="0")
        self.nav_buttons = []
        for index, (label, tab) in enumerate((("1   Syllabus", self.source_tab),
                                             ("2   Review draft", self.draft_tab),
                                             ("3   Course editor", self.editor_tab),
                                             ("Engine settings", self.settings_tab))):
            self.tabs.add(tab, text=label)
            button = ttk.Radiobutton(rail, text=label, variable=self.navigation, value=str(index),
                                     style="Nav.TRadiobutton", command=lambda page=tab: self.tabs.select(page))
            button.pack(fill="x", pady=(0, 4))
            self.nav_buttons.append(button)
            root.bind(f"<Alt-Key-{index + 1}>", lambda event, page=tab: self.tabs.select(page))
        self.tabs.bind("<<NotebookTabChanged>>", self.sync_navigation)
        ttk.Label(rail, text=f"{VERSION}\nSyllabus → draft → course", style="Rail.TLabel",
                  justify="left").pack(side="bottom", anchor="w", padx=12)
        bar = ttk.Frame(self.source_tab)
        bar.pack(fill="x", pady=(0, 10))
        ttk.Button(bar, text="Import syllabus…", command=self.import_syllabus).pack(side="left", padx=(0, 6))
        ttk.Button(bar, text="Load example", command=self.example).pack(side="left")
        ttk.Button(bar, text="Review outline", command=self.review).pack(side="right")
        panes = ttk.Panedwindow(self.source_tab, orient="horizontal")
        panes.pack(fill="both", expand=True)
        left, right = ttk.Frame(panes, padding=(0, 0, 10, 0)), ttk.Frame(panes, padding=(10, 0, 0, 0))
        panes.add(left, weight=3)
        panes.add(right, weight=2)
        ttk.Label(left, text="Syllabus", style="Section.TLabel").pack(anchor="w", pady=(0, 6))
        self.wrapped_label(left, "Paste text or import TXT, MD, DOCX, or a text-based PDF.")
        self.source = self.textbox(left)
        ttk.Label(right, text="Detected outline", style="Section.TLabel").pack(anchor="w", pady=(0, 6))
        self.wrapped_label(right, "Review topics and weeks before generating.")
        self.outline = self.textbox(right, editable=False)
        ttk.Label(self.editor_tab, text="Course editor", style="Section.TLabel").pack(anchor="w", pady=(0, 6))
        self.wrapped_label(self.editor_tab, "Edit your accepted course in Markdown. Save to retain the syllabus and course.")
        self.editor = self.textbox(self.editor_tab)
        revision = ttk.Frame(self.editor_tab)
        revision.pack(fill="x", pady=(10, 0))
        self.instructions = tk.StringVar()
        ttk.Entry(revision, textvariable=self.instructions).pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.revise_button = ttk.Button(revision, text="Revise with engine", command=lambda: self.start(True))
        self.revise_button.pack(side="right")
        self.wrapped_label(self.editor_tab, "Revision instructions, e.g. Add a worked example to module 2 and preserve the other modules.")
        draft_bar = ttk.Frame(self.draft_tab)
        draft_bar.pack(fill="x", pady=(0, 10))
        ttk.Label(draft_bar, text="Review draft", style="Section.TLabel").pack(side="left")
        self.apply_button = ttk.Button(draft_bar, text="Use this draft", style="Accent.TButton", command=self.apply_draft, state="disabled")
        self.apply_button.pack(side="right")
        self.wrapped_label(self.draft_tab, "Review before accepting. Use this draft replaces the accepted course after confirmation.")
        self.candidate = self.textbox(self.draft_tab)
        self.setup_engine()
        ttk.Separator(root).pack(fill="x")
        footer = ttk.Frame(root, padding=(18, 10))
        footer.pack(fill="x")
        self.status = tk.StringVar(value="Ready · Local template mode · No API key required")
        status_label = ttk.Label(footer, textvariable=self.status, style="Muted.TLabel")
        status_label.pack(side="left", fill="x", expand=True, padx=(0, 12))
        status_label.bind("<Configure>", lambda event: status_label.configure(wraplength=max(140, event.width)))
        self.cancel_button = ttk.Button(footer, text="Discard pending result", command=self.cancel, state="disabled")
        self.cancel_button.pack(side="right", padx=(6, 0))
        self.generate_button = ttk.Button(footer, text="Generate course", style="Accent.TButton", command=self.start)
        self.generate_button.pack(side="right")
        root.bind("<Control-s>", lambda e: self.save())
        root.bind("<Control-o>", lambda e: self.open_project())
        root.protocol("WM_DELETE_WINDOW", self.close)
        root.after(150, self.poll)

    def sync_navigation(self, event=None):
        self.navigation.set(str(self.tabs.index(self.tabs.select())))

    @staticmethod
    def wrapped_label(parent, text):
        label = ttk.Label(parent, text=text, style="Muted.TLabel", justify="left", wraplength=300)
        label.pack(fill="x", pady=(0, 8))
        label.bind("<Configure>", lambda event: label.configure(wraplength=max(100, event.width)))
        return label

    def textbox(self, parent, editable=True):
        box = ScrolledText(parent, wrap="word", undo=True, font=("Segoe UI", 10), width=1, height=1,
                           background=PAPER if editable else FIELD, foreground=INK,
                           insertbackground=INK, selectbackground=WARM, selectforeground=INK,
                           relief="flat", borderwidth=0, highlightthickness=1,
                           highlightbackground=LINE, highlightcolor=INK, padx=12, pady=10)
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
        heading = ttk.Label(self.settings_tab, text="Engine settings", style="Section.TLabel")
        heading.pack(anchor="w", pady=(0, 6))
        self.wrapped_label(self.settings_tab, "Choose the engine used to generate and revise course drafts.")
        form = ttk.Frame(self.settings_tab)
        form.pack(fill="x")
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
            ttk.Label(form, text=label).grid(row=row, column=0, sticky="w", padx=(0, 20), pady=6)
            widget.grid(row=row, column=1, sticky="ew", pady=6)
        ttk.Button(form, text="Clear key", command=lambda: self.key.set("")).grid(row=4, column=1, sticky="w", pady=8)
        ttk.Button(form, text="Provider guide…", command=self.provider_guide).grid(row=4, column=1, sticky="e", pady=8)
        self.wrapped_label(self.settings_tab,
            "Keys stay in this session and are excluded from saved projects. Online generation sends your syllabus "
            "and, for revisions, your course to the selected provider. Charges and quotas may apply.")
        self.wrapped_label(self.settings_tab, "Review generated facts, answers, coverage, and references before use.")

    def provider_guide(self):
        messagebox.showinfo("Provider guide",
            "Google AI Studio: enter a Gemini key and available model ID. The Google endpoint is fixed.\n\n"
            "OpenAI-compatible: enter a key, model ID, and Chat Completions base URL. "
            "A key alone cannot identify a provider or support every API format.\n\n"
            "For a local server, use its localhost URL; a key may be omitted.", parent=self.root)

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
