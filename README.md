# Course Framework

A Windows course maker that turns a syllabus into an editable teaching draft. Import or paste a syllabus, review the detected outline, generate a course with a local template or your own API engine, then edit and export it. An optional Streamlit interface shares the same core and project format.

## Windows download

Download the Windows x64 ZIP from [GitHub Releases](https://github.com/Denberg28/Course-Framework/releases), extract the **entire folder**, and run `CourseFramework.exe`. Python is not needed for the packaged app. Target: Windows 10/11 x64. The first release is a **test candidate**, pending manual Windows usability checks and live provider validation.

The application is unsigned. This project does not claim publisher verification or stable readiness.

## Workflow

1. **Syllabus:** paste text or import `.txt`, `.md`, `.docx`, or a text-based `.pdf`. Load the built-in aircraft structures example to try the workflow.
2. **Review outline:** check the detected course metadata, outcomes, module topics, subtopics, week ranges, and references. Correct parsing by editing the syllabus. Explicit `Week 1: Topic` lines are the most predictable format. Unassigned weeks remain unassigned.
3. **Engine settings:** select a local template, Gemini, or an OpenAI-compatible API. Enter your key, model, and endpoint as appropriate.
4. **Generate course:** generation produces a separate draft. Review it and select **Use this draft** to populate the course editor. Existing course material is preserved on failed requests and until replacement is accepted.
5. **Edit/revise:** edit Markdown directly, or request an API revision using plain-language instructions. Revisions are staged for review too.
6. **Save project:** save a JSON project containing the syllabus, accepted course, title, and engine name. Save as a new file to retain a previous version. Unsaved changes prompt on close/new/open; writes use an atomic replacement.
7. **Export:** choose Markdown, a safe printable HTML **text view** of the Markdown, or a ZIP containing both, the source syllabus, and the editable project.

Pending generated drafts are session-only until accepted. Accept a draft before saving it. Scanned PDFs need OCR before import. Complex or merged tables may need manual cleanup. File import limit: 8 MB; PDF limit: 100 pages; source limit: 180,000 characters; generated/edited course limit: 400,000 characters; local outline limit: 80 modules.

## API engines

| Engine | Required configuration | Protocol |
|---|---|---|
| Local template | None | Offline; creates teaching structure and explicit placeholders, not researched lesson content |
| Google AI Studio (Gemini) | Gemini API key and an available Gemini model ID | Google `generateContent`; fixed Google endpoint |
| OpenAI-compatible | Provider key, model ID, and API base URL | `POST {base}/chat/completions` |
| Local compatible server (Windows app) | Local model ID and base URL, e.g. `http://localhost:1234/v1`; key optional | OpenAI Chat Completions compatible |

Create a Gemini key in [Google AI Studio](https://aistudio.google.com/apikey). The model field is editable because model availability varies by account/provider. The initial Gemini model ID is `gemini-2.5-flash-lite`; change it if unavailable in your account. When switching to an OpenAI-compatible provider, also change the model ID and base URL to that provider's values.

An arbitrary API key does **not** identify its provider or make incompatible APIs work. Anthropic's native Messages API and Azure's deployment-specific authentication are not implemented. A compatible gateway may expose them through Chat Completions.

The desktop asks before sending online requests. Keys are masked, held only in memory, omitted from projects/exports, and never placed in the Gemini URL. Clear the key or exit to remove the app's reference to it; no secure memory-erasure claim is made. The source syllabus and, for revisions, the current draft are sent to the selected provider. Provider fees, quota, and privacy policies apply. There is no automatic retry after an error. Output limits, blocked responses, and malformed responses produce a failure without overwriting the course. Large courses may need to be generated as separate syllabus sections.

The engine uses a 60-second socket timeout and bounded response size. Discarding a pending result does not cancel provider processing or billing; another desktop request is blocked until the previous worker returns. Model content requires instructor review, including answer keys and references. The app cannot verify factual accuracy or guarantee a model preserved every requested section.

## Run from source

Python **3.12** is the tested build target. The Windows Python installer includes Tk; Linux development needs a Tk-enabled Python and a display for desktop tests.

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -r requirements-desktop.txt
.venv\Scripts\python desktop.py
```

Optional Streamlit:

```powershell
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m streamlit run app.py
```

Streamlit Community Cloud configuration: repository `Denberg28/Course-Framework`, branch `main`, entrypoint `app.py`, Python 3.12. No server API secret is required: users supply session keys. Download project JSON regularly; browser reloads, server restarts, and cloud filesystem changes are not durable storage. This change does not establish or verify a public Streamlit deployment. The hosted interface permits public HTTPS compatible endpoints only; local servers are supported in the desktop edition.

## Build and verify

```powershell
py -3.12 -m pip install -r requirements.txt -r requirements-build.txt
py -3.12 -m unittest discover -s tests -v
py -3.12 desktop.py --smoke-test
py -3.12 -m PyInstaller --noconfirm --clean --windowed --onedir --name CourseFramework desktop.py
```

Build Windows executables **on Windows**. `.github/workflows/verify-and-package.yml` tests Linux/Windows, exercises the native UI on Windows, builds the Windows package, checks the packaged executable, and publishes a versioned prerelease after a successful run on `main`. Pull requests produce build artifacts without publishing a release. See [testing and review evidence](docs/TESTING.md), [architecture](docs/ARCHITECTURE.md), and [known issues](docs/KNOWN_ISSUES.md).

Repository: [Denberg28/Course-Framework](https://github.com/Denberg28/Course-Framework), public. Baseline before this work: `66f3d9f5f3f43c17d488a281cce34e206cb93c91`. Revert the feature commit(s) to restore the prior Streamlit entrypoint; preserve exported JSON/Markdown first. New JSON projects are not supported by the old app, but exported Markdown remains readable.
