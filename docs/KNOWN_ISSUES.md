# Known issues and validation limits

- **Academy alignment:** visual tokens are based on the current Academy source; real Windows side-by-side comparison, high-DPI, and screen-reader acceptance remain pending. No Academy account/content integration is implemented.
- **Live providers not tested:** no user key is available. API shapes, auth placement, refusal/truncation handling, and failures are covered with deterministic simulated responses. Account/model access and teaching quality still require a user-run check.
- **Candidate release:** Windows automated UI and packaged-executable checks run in GitHub Actions. Manual Windows 10/11 use, high-DPI layout, keyboard/screen-reader accessibility, and long-session behavior need real desktop validation before stable promotion.
- **Input parsing:** format detection is heuristic, not semantic extraction. Complex tables, merged cells, and scanned PDFs may need manual cleanup/OCR. Imported week labels remain source values; calendar conflicts are not automatically resolved.
- **Long courses:** single-request generation may exceed provider context/output limits. Split the syllabus into smaller sections; output-limit responses do not overwrite the accepted course.
- **Generic provider support:** Gemini and Chat Completions compatible APIs are implemented. Native formats such as Anthropic Messages, Azure deployment auth, and proprietary engines require another adapter.
- **Persistence:** API keys and pending drafts are session-only. Accept pending drafts before saving. Streamlit sessions and cloud local disks are not a durable project store; download JSON to retain work.
- **Preview:** native editing and HTML export show Markdown text rather than a rich Word/LMS layout. No DOCX/PDF export, SCORM package, or LMS integration is claimed.
- **Cancellation:** discarding a result does not terminate the provider's request or refund it. The app waits for the worker before starting another; the socket timeout is not a strict whole-request deadline against a slowly streaming server.
- **Distribution:** the Windows package is unsigned; no signing identity was created or changed.

There are no known critical/high defects after the documented candidate checks. Missing verification is kept explicit and does not imply stable readiness.
