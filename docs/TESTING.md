# Verification and release gates

Target: **0.2.0-rc.2**, baseline `338f43b`. Evidence is automated and self-reviewed, with simulated provider responses. Live API and manual Windows/high-DPI/accessibility acceptance remain pending.

| Gate | Check |
|---|---|
| Source | `python -m compileall -q app.py desktop.py academy_theme.py course_core.py engines.py course_workflow.py hosted_keys.py tests tools`; `git diff --check` |
| Core/persistence | File parsing/bounds; atomic failure retains prior file; v1→v2 migration; accepted edits and partial checkpoints round-trip; allow-lists exclude secrets |
| Generation | One call per module; required sections; quota/truncation failure preserves previous success; resume does not replay completed modules; source/model/endpoint changes do not resume |
| Resources | Topic searches URL-encode syllabus titles; supplied video links retained; new direct video links removed; no provider call in offline mode |
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
- Review all linked videos for topic, level, captions, accuracy, and availability. The app provides searches and supplied URLs, not verified video recommendations.
- Preserve v2 project and Markdown exports before any rollback. Prior releases cannot open format 2.

Final test/commit/build/run evidence is attached to the GitHub workflow and release; this document does not claim those gates passed before they execute.

## Hosted Secrets regression

AppTest uses a fake deployment secret to verify Gemini request header placement, absence from rendered widgets/session/project data, provider isolation, manual fallback without Secrets, and sanitized invalid-secret errors. No live credential is used. The user confirmed that rebooting resolved the earlier deployed ImportError; no import-error workaround is included in this change.
