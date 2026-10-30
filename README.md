# Course Framework

Paste a syllabus, choose an agent model, and generate modules with presentation/discussion, a practical activity, and a five-question assessment. The Windows and Streamlit editions share the same generation and project format, with a compact Aero Academy white/navy/gold design.

## Use it

1. **Paste the full course syllabus** as supplied: course heading, description, units, outcomes, lecture/lab topic table, and readings. The included [AE 416 example](examples/AE416-syllabus.txt) is detected as five modules, three outcomes, 36 lecture hours and 54 laboratory hours without relabeling it. Labelled and weekly outlines remain supported.
2. **Choose an agent model** and enter its API key if not configured in Streamlit Secrets. **Gemini 3.5 Flash-Lite** (`gemini-3.5-flash-lite`) is the default; choose **3.8 Flash** (`gemini-3.8-flash`) for demanding work, or select/type a custom model ID. Availability and quotas depend on your provider account.
3. Select **all modules** or **one module**, allow sending the syllabus to the agent, then **Generate**. Each selected module uses one request; there is no automatic paid retry.
4. **Review** the generated material below the syllabus and **Download Markdown** directly, including an unfinished draft if needed. **Use draft** accepts a complete course for editing/package export; existing accepted material stays intact until then.
5. **Save project** to keep the syllabus, accepted edits, and unfinished modules. **Export course** produces a ZIP with Markdown, a collapsible HTML lesson presentation, the source syllabus, and a reopenable project.

The supplied [AE 417 OJT table](examples/AE417-syllabus.md) is supported as a Markdown table, a tab-separated browser/spreadsheet paste, a space-separated copy, or an imported Word table. It contains **13 modules, seven objectives, eight bibliography entries and 54 lecture hours** (declared lab total: zero). Blank leading columns, `<br>` headings, dash/empty hour cells and Laboratory/Equipment rows do not create extra modules. Missing per-module lab values remain unspecified; weeks are not invented. Check the detected module count before generating. After updating, generate a fresh draft for previously misread tables; accepted material remains available.

If a request fails, completed modules remain in the pending draft. With the same syllabus, title, module selection, provider, model, and endpoint, **Generate/Resume** continues from the next unfinished module. Reopen a saved project, re-enter the session key, and configure the original compatible endpoint if applicable. Changing the engine or syllabus starts a new draft; previously accepted content remains safe. Streamlit work is session-local until downloaded; Windows work is held in memory until saved. Save before closing or reloading.

A Windows **Pause** finishes and retains the current module, then stops before the next request. It does not cancel provider processing or billing. In Streamlit, a provider failure stops the sequence and exposes Resume; generation otherwise runs through the selected modules. Do not start overlapping browser requests or tabs expecting shared persistence.

Each new module follows **Discussion and presentation → Activity → Assessment → Answer key → References**. Discussion contains an introduction, 3–5 teaching/discussion segments, a worked example, and a summary. The activity includes steps, a deliverable, and suggested time. Assessment contains exactly five multiple-choice questions numbered 1–5, each with A–D options; the key contains five numbered letters such as `1. B`. Streamlit collapses assessment, answer key, and references separately. Windows **Preview** opens a standalone HTML presentation with the same collapsible sections; the native editor remains Markdown.

Video suggestions and links are removed from new module creation. **References follow the syllabus textbook and reading list**, for any subject, author, publisher or agency. No FAA/CAAP/EASA, university or publisher bibliography is added automatically. Listed readings receive stable source IDs (SYL-1, SYL-2, …) in prompts and module reference sections; instructors confirm which readings support each module. For AE 416 these are Paler-Calmorin (1995), Adanza (1995), and Sevilla (1992), as supplied.

A syllabus bibliography is not the source text. The app does not retrieve or claim to verify book contents, page numbers or generated explanations/answers. Model instructions prohibit invented citations and outside reading suggestions; supplied HTTP(S) reference links can use any domain, while model-created URLs absent from the bibliography are marked for verification. If no references are supplied, the module marks the gap. Add the actual readings or check them before teaching. Existing accepted material is not rewritten; generate a fresh draft to apply this reference policy.

Lecture/lab tables pasted with tabs, spaces or pipes retain topic hours in the outline, generation prompt, module headings and exported Markdown. Units, weekly hours, standing requirement, outcomes and syllabus readings are retained; conflicting totals produce an outline warning rather than being silently corrected. Hours alone do not imply a week schedule. The prompt asks the model to scope discussion/lab activities to these allocations, but the app does not verify whether content fills every contact hour.

Output validation checks the presentation subsections, discussion length, the five A–D question structures, and the five-letter answer key. This is structural validation, not pedagogical or factual approval. Offline mode produces explicit placeholders, including questions and answer letters that an instructor must complete; it never invents a correct answer.

Generation still uses one sequential AI request per module. The previous original AI app made one shorter Flash-Lite request for the whole course, so removing locally generated video suggestions alone does not eliminate that latency difference. This release asks for compact, focused module content but does not claim a measured live-provider speed improvement.

## Windows

Download the latest Windows x64 ZIP from [GitHub Releases](https://github.com/Denberg28/Course-Framework/releases), extract the **entire folder**, and run `CourseFramework.exe`. No Python installation is required for the packaged app. Target: Windows 10/11 x64, display 1024×768 or larger. The app fits the available screen, with a 940×620 workspace minimum. Distribution is unsigned and remains a test candidate pending manual Windows and live-provider acceptance.

One workspace contains the syllabus and agent controls beside the draft/course editor. **Settings** holds the provider, optional custom endpoint, and title. **File** holds New/Open/Save as/Export; Save remains visible. Ctrl+O opens a project; Ctrl+S saves. Import and outline review are optional.

## Streamlit

Deployment configuration: repository **Denberg28/Course-Framework**, branch **main**, entrypoint **app.py**, Python **3.12**. The browser interface restores the original airplane branding with a compact navy/gold header and a small static lesson illustration. A wider vertical scrollbar starts below the Streamlit toolbar, with a contrasting track and a minimum thumb size in Chromium/Safari. Syllabus/Course material jump links and a return link support long courses; scrolling respects reduced-motion settings. The illustration hides on narrow screens, and no animation or remote asset is required. The original top-to-bottom allocation remains: full-width syllabus input, compact model/key and Generate controls, then a full-width materials preview. The reading area is capped at 1100 px. Settings & files contains import/open/provider and optional module scope; all modules are selected by default. Course overview, assessment, key and references collapse separately; save/download actions stay above the preview. This repository does not establish or verify a public deployment.

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
py -3.12 -m compileall -q app.py desktop.py academy_theme.py course_core.py engines.py course_workflow.py hosted_keys.py lesson_format.py reference_catalog.py tests tools
py -3.12 desktop.py --smoke-test
py -3.12 -m pip install -r requirements-build.txt
py -3.12 -m PyInstaller --noconfirm --clean --windowed --onedir --name CourseFramework desktop.py
```

Build Windows packages **on Windows**. CI requires Linux/Windows regression tests, native startup, packaging, and packaged EXE startup before publishing a new prerelease on `main`. Windows workflow artifacts retain real native UI captures. Live-provider calls never run in CI.

Input limits: 8 MB per file, 100 PDF pages, 180,000 source characters, 80 detected modules. Accepted course and pending draft each have a 400,000-character bound. Scanned PDFs require OCR; complex tables may need source cleanup. Each request uses a bounded response and 60-second socket timeout; this is not a strict whole-course deadline.

New saves use **project format 2**, including a pending-draft checkpoint and selected model metadata. Format 1 projects open without losing accepted material. Older app versions cannot open format 2; keep Markdown exports if reverting. API keys and endpoints are never serialized. Export packages contain accepted material only; Save project keeps unfinished work. Schema migration does not introduce an Aero Academy account or publication integration.

See [testing](docs/TESTING.md), [architecture](docs/ARCHITECTURE.md), [UI alignment](docs/UI_ALIGNMENT.md), and [known issues](docs/KNOWN_ISSUES.md). Roll back via a focused revert after preserving project and Markdown exports.

The new lesson contract has a different generation fingerprint. Completed/accepted older projects remain readable; older unfinished drafts are preserved in the project but require a fresh draft to use the new presentation/MCQ format.

New sessions, native startup and switching back to Gemini default to 3.5 Flash-Lite. A saved pending job restores its original model, and an explicit 3.8 choice survives reruns; changing defaults does not silently switch an existing request/job. No model speed or free-quota guarantee is implied.

Generation progress appears immediately above Generate/Resume, including the actual completed/selected module count and stopped/ready status. The button is disabled while the request runs. Work is queued by the click callback and executed in the normal page layout, so progress is not prepended off-screen. Settings/editor widgets are registered before rerunning; completed checkpoints and selected settings remain intact.
