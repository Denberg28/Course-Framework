Course Framework now includes a Windows syllabus-to-course maker with session-only API engines.

- Import TXT, Markdown, DOCX, or text-based PDF syllabi and review the detected course outline.
- Generate with Google AI Studio (Gemini), an OpenAI-compatible provider, or a local teaching template. Windows also supports localhost compatible engines.
- Review generated/revised drafts before accepting them; failed requests preserve the current course.
- Edit course material, save/reopen JSON projects, and export Markdown, printable HTML text view, or a complete ZIP.
- The optional Streamlit interface shares the same core and project format.

Download the Windows x64 ZIP, extract the entire `CourseFramework` folder, then run `CourseFramework.exe`. Python is not required. API keys are entered in Engine settings and are not saved to projects. For online providers, also enter the correct model ID and, for compatible providers, base URL. An arbitrary key alone cannot identify its API protocol.

Automated publication requires Linux/Windows regression tests, native Windows startup, a PyInstaller build, and a successful packaged-executable smoke test. Provider integration is tested with simulated responses; live API accounts and model output quality are not validated. Manual Windows usability/high-DPI/accessibility and actual-provider checks remain pending, so this is a **prerelease test candidate**. The package is unsigned.

The release tag identifies the exact source commit; SHA256SUMS.txt identifies the package. Review all course content, answers, references, and syllabus alignment before teaching. Scanned PDFs require OCR and long syllabi may need smaller generation sections. Pending drafts are session-only until accepted. Save a JSON project to retain work.

Rollback: retain your exported JSON/Markdown, then use the baseline source commit `66f3d9f5f3f43c17d488a281cce34e206cb93c91` if needed. The old Streamlit app reads Markdown but cannot reopen the new project JSON. See README and docs/TESTING.md for the full workflow and validation limits.
