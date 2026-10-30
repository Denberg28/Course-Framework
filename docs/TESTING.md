# Verification and release gates

Target: **0.3.5-rc.1**, baseline `e0901c7`. Evidence is automated and self-reviewed, with simulated provider responses. Live API and manual Windows/high-DPI/accessibility acceptance remain pending.

| Gate | Check |
|---|---|
| Source | `python -m compileall -q app.py desktop.py academy_theme.py course_core.py engines.py course_workflow.py hosted_keys.py lesson_format.py reference_catalog.py tests tools`; `git diff --check` |
| Core/persistence | File parsing/bounds; atomic failure retains prior file; v1→v2 migration; accepted edits and partial checkpoints round-trip; allow-lists exclude secrets |
| Generation | One call per module; required sections; quota/truncation failure preserves previous success; resume does not replay completed modules; source/model/endpoint changes do not resume |
| Teaching format | Ordered discussion/presentation subsections; five questions/options A–D; letter-only answer keys; malformed/missing items rejected; video sections/URLs removed; syllabus-listed bibliography without automatic source additions |
| Streamlit | No workflow tabs; model/custom selection; consent; selected/all modules; draft acceptance; editor/download persistence; failure/resume; provider change clears credentials |
| Native Windows | Single-workspace minimum/startup bounds; offline worker; pause after active module; accepted course preservation; partial save/reopen/resume; changed-source acceptance |
| Package | Windows build; source `desktop.py --smoke-test`; packaged `CourseFramework.exe --smoke-test`; ZIP and SHA256 |

Run `python -m unittest discover -s tests -v`. The local headless environment skips native Tk tests; Windows CI runs them with Python 3.12. AppTest is an event simulation, not browser visual acceptance. `python tools/capture_ui.py ui-review` captures the actual native syllabus/draft/minimum-course views; Windows CI retains those images for inspection.

No user key, real paid API call, or live model availability probe is part of tests or CI. Fresh source changes require the corresponding CI gates before publication. Publish as a prerelease only after Linux/Windows tests, native startup, Windows build, and packaged startup pass. Build/startup does not prove teaching quality or usability.

## Manual acceptance before stable promotion

- Windows 10/11: 1024×768 and larger screens, 100/125/150% scaling, keyboard focus/editing, resizing and dialogs; inspect the single workspace and settings at minimum size.
- Real PDF/Word syllabi: confirm topic/week/outcome detection and retained policies; clean ambiguous text and OCR scanned documents.
- Actual Gemini and compatible providers: choose an available model; generate selected/all modules; inspect substantive explanations, examples, activity steps/deliverables/time, assessment and references. Confirm the key/model/endpoint in use.
- Quota/offline failure: preserve accepted content and completed modules; Save project, reopen, re-enter key and original endpoint, Resume; verify only unfinished modules are requested.
- Pause during an active native request; verify its result is kept and the next request does not start. Save before closing/reloading. Confirm key exclusion in project and course ZIP.
- Check discussion sequence, worked-example units/assumptions, activity instructions/time, and correctness of all five MCQs and their letter keys. Confirm assessment/key expansion in Streamlit and Windows HTML Preview.
- Verify the relevant official/publisher text, chapter, jurisdiction and revision. Catalog location checks do not establish claim correctness. No video recommendations should be generated.
- Preserve v2 project and Markdown exports before any rollback. Prior releases cannot open format 2.

Final test/commit/build/run evidence is attached to the GitHub workflow and release; this document does not claim those gates passed before they execute.

## Hosted Secrets regression

AppTest uses a fake deployment secret to verify Gemini request header placement, absence from rendered widgets/session/project data, provider isolation, manual fallback without Secrets, and sanitized invalid-secret errors. No live credential is used. The user confirmed that rebooting resolved the earlier deployed ImportError; no import-error workaround is included in this change.

## Presentation checks

Regression tests reject duplicate/missing MCQ choices, missing question numbers and invalid answer letters. HTML tests verify closed assessment/key details and escaped untrusted markup. Native tests verify Preview output without launching a real browser in CI. Existing saved content remains readable; the new contract fingerprint starts fresh for unfinished old drafts. The syllabus reference policy and its limits are recorded in docs/REFERENCE_CATALOG.md.

## Full syllabus and screen allocation regression

The supplied `examples/AE416-syllabus.txt` must parse unchanged as five topics, three outcomes and three readings; each module keeps its lecture/lab pair `(6,6), (6,9), (8,12), (8,12), (8,15)`, summing to 36/54. Tests cover tab/space/pipe copies, fractional/reversed hour columns, conflicting declared totals, full-syllabus prompts, deterministic headings/allocation table, raw-source project/export round trips, direct paste/generate/download and vertical Streamlit containers. Native Windows coverage checks summary/outline/generation with that same file. Existing weekly outlines, consent, Secrets, partial failures/resume, accepted-material replacement and MCQ structure remain required.

Local Python 3.12: 63 tests discovered, 54 passed and 9 native-display tests skipped; syntax/whitespace checks pass. Providers are simulated; no real API key or paid request is used. Browser visual acceptance remains pending because the local Chromium download failed. GitHub Linux/Windows, native and package results must be checked for the final commit before publication.

## Syllabus references regression

AE 416 provider prompts and module References must contain Paler-Calmorin, Adanza and Sevilla, with SYL-1/2/3 IDs, and no injected agencies/publishers. Tests check aviation/strength-of-materials topics do not infer references, supplied bibliography URLs survive across arbitrary domains, invented URLs (including former catalog URLs) are marked, absent readings are flagged, and bibliography heading aliases are recognized. Existing lesson/key, full-syllabus/hour, Secrets, checkpoint and persistence tests remain required. All provider responses are simulated; real-book content and live teaching quality are unverified. Check final Linux/Windows/native/package CI before publication.

## Default model and Streamlit browser gate

The shared adapter and fresh Streamlit/native sessions default to 3.5 Flash-Lite. A simulated request verifies its actual endpoint, then selects 3.8 Flash and verifies that endpoint and preserved selection. Provider resets return to Lite; saved jobs keep their model. Existing consent/Secrets/generation/outline/reference/persistence tests remain required.

The `streamlit-browser` CI job installs Playwright 1.62.1 only as test tooling, starts the real app, verifies model selection, pastes AE 416, generates offline without credentials and downloads Markdown. It checks desktop/mobile horizontal overflow, the main scroll container, anchor navigation, closed assessment, hidden mobile illustration and reduced-motion scrolling. Desktop/mobile PNGs and the explicitly offline placeholder draft are retained as `CourseFramework-Streamlit-review`. Windows packaging waits for both the source/native regression job and this browser job. Browser checks do not validate live model quality or manual accessibility; inspect the final-run screenshots for visual review.

Local checks: `node --check tools/capture_streamlit.cjs`, compileall, git diff --check and the Python suite. For local browser capture with Playwright/Chromium available, run `node tools/capture_streamlit.cjs streamlit-review` from the repository root. Source changes require fresh affected CI evidence before publication.

## Hosted scrollbar and in-flight generation regression

The scroll viewport must start below the 60 px Streamlit toolbar and end inside the browser viewport, retain a visible gutter, and apply a 56 px minimum WebKit thumb. Test the actual geometry at desktop/mobile sizes and inspect screenshots, including long generated courses. Standard Firefox/OS scrollbar rendering still needs manual acceptance.

Progress must be inside the generation controls above Generate/Resume, not in pre-page callback output. Unit/AppTest coverage checks partial-failure counts, unchanged accepted content, settings persistence and no repeated requests after rerun. The Chromium runner uses the CI-only streamlit_ui_fixture.py entry point, which runs the actual app with delayed simulated provider transport. It verifies the disabled in-flight action and progress placement within the visible viewport on desktop/mobile, and saves generation screenshots alongside the prior navigation/offline-download captures. All provider requests remain simulated; production entry is app.py. Python/Node syntax, whitespace, Linux/Windows/native/browser/package checks must pass for the final candidate commit.

## AE 417 field/value table regression

examples/AE417-syllabus.md reproduces the supplied OJT curriculum, including its title spelling. Before this fix a browser-style tab/space copy detected two modules: the first topic with following numbered rows as subtopics, then Laboratory/Equipment. Corrected Markdown, clipboard tabs/spaces, decorated nonbreaking-space/HTML and imported Word variants must yield identical 13 titles, seven objectives, eight bibliography entries, lecture allocations [3,3,6,6,6,6,3,3,3,6,3,3,3] and declared totals 54/0. Dash/empty module lab cells stay absent. Reversed columns and missing first/second hour cells must not shift values. Plain indented subtopics and AE 416 remain required.

Shared workflow and Streamlit tests simulate all 13 module responses, check exactly 13 requests (also after rerun), progress 13/13, the final heading, source/project preservation and old-contract checkpoint rejection. The Streamlit scenario starts with an existing completed draft and accepted material, changes the syllabus and generates all 13 modules while preserving the accepted text; replacement approval resets before widget registration. Windows verifies 13 offline modules in the native worker. Chromium pastes the tab-separated table over the previous course, checks the summary and completed 13-module Markdown download and captures its course view. Browser offline material is explicitly placeholder content, not live AI teaching-quality evidence.

Local Python 3.12: 69 tests discovered, 59 passed and 10 native-display tests skipped. Final affected GitHub Linux/Windows/native/browser/package checks must pass before prerelease publication. No real credential or paid request is used.
