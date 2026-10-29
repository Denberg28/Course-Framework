# Course Framework 0.1.0-rc.3 — Windows test candidate

Match the Course Framework authoring workspace to Aero Academy’s minimal white/navy/gold design. Compact left navigation follows Syllabus → Review draft → Course editor, with Engine settings alongside. File actions share a single top bar; helper text wraps; provider guidance opens on demand. Optional Streamlit headings and colors follow the same design.

Startup sizing also fits smaller supported displays (1024×768 and above) while keeping footer actions visible.

Download the Windows x64 ZIP, extract the entire folder, and run CourseFramework.exe. Course JSON and exports retain their existing format. Keys remain session-only. This update prepares visual integration; Academy accounts, subject publishing, and data synchronization are not implemented.

Verification: regression tests, native Windows navigation/minimum-window checks, source startup, Windows packaging, and packaged EXE startup must pass in the linked Actions run before this candidate is published. Real Tk UI review captures are attached to that run. Provider tests use simulated responses; no live API key or paid request is used.

Manual Windows 10/11 high-DPI/accessibility checks, direct visual comparison with the deployed Academy desktop, and live-provider validation remain pending. This is an unsigned prerelease, not a stable-readiness claim. See docs/TESTING.md and docs/KNOWN_ISSUES.md.
