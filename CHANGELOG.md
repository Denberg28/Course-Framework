# Changelog

## 0.1.0-rc.1 — 29 October 2026

- Add a Windows Tk course maker with syllabus import, outline review, course editing, and draft staging.
- Add session-only Gemini and OpenAI-compatible engine configuration, local compatible server support on desktop, and instructor-directed revisions.
- Separate course metadata, outcomes, topics, and references; preserve supplied week ranges and document missing information.
- Add bounded TXT/MD/DOCX/PDF import, atomic project saves, JSON reopen, Markdown/HTML/ZIP export, and overwrite/unsaved-work checks.
- Preserve accepted material after provider failures, truncated output, and discarded pending results.
- Rebuild the optional Streamlit interface around persistent session drafts and shared project exports.
- Enable normal Streamlit request protections in the dev container.
- Add automated regression, provider-adapter, Streamlit, Windows UI, and executable packaging checks.

Candidate limits: real API credentials and provider quality are not validated in automated tests. Manual Windows usability, high-DPI layout, and unsigned-download behavior remain to be checked. No live Streamlit deployment is claimed.
