# Course Framework

Paste a syllabus, choose an agent model, and generate modules with lesson content, learning activities, assessments, and video resources. The Windows and Streamlit editions share the same generation and project format, with a compact Aero Academy white/navy/gold design.

## Use it

1. **Paste** your syllabus. Topics such as `Week 1: Aircraft loads` give the most predictable module boundaries.
2. **Choose an agent model** and enter its API key if not configured in Streamlit Secrets. Gemini presets are `gemini-3.8-flash` and `gemini-3.5-flash-lite`; select/type a custom model ID when needed. Availability and quotas depend on your provider account.
3. Select **all modules** or **one module**, allow sending the syllabus to the agent, then **Generate**. Each selected module uses one request; there is no automatic paid retry.
4. **Review → Use draft.** Accepted material stays intact until you accept a complete draft. Edit the accepted course if needed.
5. **Save project** to keep the syllabus, accepted edits, and unfinished modules. **Export course** produces a ZIP with Markdown, a printable HTML text view, the source syllabus, and a reopenable project.

If a request fails, completed modules remain in the pending draft. With the same syllabus, title, module selection, provider, model, and endpoint, **Generate/Resume** continues from the next unfinished module. Reopen a saved project, re-enter the session key, and configure the original compatible endpoint if applicable. Changing the engine or syllabus starts a new draft; previously accepted content remains safe. Streamlit work is session-local until downloaded; Windows work is held in memory until saved. Save before closing or reloading.

A Windows **Pause** finishes and retains the current module, then stops before the next request. It does not cancel provider processing or billing. In Streamlit, a provider failure stops the sequence and exposes Resume; generation otherwise runs through the selected modules. Do not start overlapping browser requests or tabs expecting shared persistence.

Each AI module is checked for nonempty **Learning objectives**, **Lesson content**, **Learning activities**, and **Assessment** sections. This validates structure, not factual accuracy, activity quality, or syllabus coverage. Video resources include topic-based YouTube search links and supplied YouTube/Vimeo links. The app does not discover, watch, rank, or verify specific videos; review relevance, accuracy, captions, and availability before teaching. Offline mode produces labeled scaffolding and placeholders, not researched lesson content.

## Windows

Download the latest Windows x64 ZIP from [GitHub Releases](https://github.com/Denberg28/Course-Framework/releases), extract the **entire folder**, and run `CourseFramework.exe`. No Python installation is required for the packaged app. Target: Windows 10/11 x64, display 1024×768 or larger. The app fits the available screen, with a 940×620 workspace minimum. Distribution is unsigned and remains a test candidate pending manual Windows and live-provider acceptance.

One workspace contains the syllabus and agent controls beside the draft/course editor. **Settings** holds the provider, optional custom endpoint, and title. **File** holds New/Open/Save as/Export; Save remains visible. Ctrl+O opens a project; Ctrl+S saves. Import and outline review are optional.

## Streamlit

Deployment configuration: repository **Denberg28/Course-Framework**, branch **main**, entrypoint **app.py**, Python **3.12**. The browser interface has one page with no workflow tabs; Settings & files contains import/open/provider controls. This repository does not establish or verify a public deployment.

You can configure a deployment-owned Gemini key under **Manage app → Settings → Secrets**:

```toml
GEMINI_API_KEY = "PASTE_YOUR_GEMINI_API_KEY_HERE"
```

Save and reboot the app if needed. The app reads the key on the server and displays **Gemini key configured in Secrets** instead of an API-key input. It does not copy the key into widgets, session state, project files, exports, or URLs. This deployment key is used only for Google AI Studio (Gemini), never a custom provider. Everyone with access to the hosted app can use its quota; choose app access accordingly. Do not put a real key in GitHub. `.streamlit/secrets.toml` is ignored for local development.

Without a configured Gemini secret, you can enter a manual key in the app; manual/desktop keys remain session-only. No key is required for offline scaffolding. Switching providers clears the entered key and consent. Hosted compatible endpoints require public HTTPS; desktop compatible engines can use HTTP on localhost with an optional key. Syllabi and generated text are sent only after the explicit online consent and Generate action. Provider costs, quotas, and privacy policies apply.

| Provider | Configuration |
|---|---|
| Google AI Studio (Gemini) | Gemini key and an available model ID; fixed Google endpoint |
| OpenAI-compatible | Provider key, model ID, and Chat Completions base URL |
| Local compatible server (Windows) | Local model ID and localhost URL, such as `http://localhost:1234/v1`; key optional |
| Local template | Offline scaffolding; no key or online consent needed |

An arbitrary key cannot identify its provider or support incompatible protocols. Native Anthropic Messages and Azure deployment-specific APIs require an additional adapter or compatible gateway.

## Run and verify

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m streamlit run app.py
```

For the Windows app, install `requirements-desktop.txt` and run `desktop.py`. Tk comes with Windows Python; Linux development requires a Tk-enabled Python and display for native tests.

```powershell
py -3.12 -m unittest discover -s tests -v
py -3.12 -m compileall -q app.py desktop.py academy_theme.py course_core.py engines.py course_workflow.py hosted_keys.py tests tools
py -3.12 desktop.py --smoke-test
py -3.12 -m pip install -r requirements-build.txt
py -3.12 -m PyInstaller --noconfirm --clean --windowed --onedir --name CourseFramework desktop.py
```

Build Windows packages **on Windows**. CI requires Linux/Windows regression tests, native startup, packaging, and packaged EXE startup before publishing a new prerelease on `main`. Windows workflow artifacts retain real native UI captures. Live-provider calls never run in CI.

Input limits: 8 MB per file, 100 PDF pages, 180,000 source characters, 80 detected modules. Accepted course and pending draft each have a 400,000-character bound. Scanned PDFs require OCR; complex tables may need source cleanup. Each request uses a bounded response and 60-second socket timeout; this is not a strict whole-course deadline.

New saves use **project format 2**, including a pending-draft checkpoint and selected model metadata. Format 1 projects open without losing accepted material. Older app versions cannot open format 2; keep Markdown exports if reverting. API keys and endpoints are never serialized. Export packages contain accepted material only; Save project keeps unfinished work. Schema migration does not introduce an Aero Academy account or publication integration.

See [testing](docs/TESTING.md), [architecture](docs/ARCHITECTURE.md), [UI alignment](docs/UI_ALIGNMENT.md), and [known issues](docs/KNOWN_ISSUES.md). Roll back via a focused revert after preserving project and Markdown exports.
