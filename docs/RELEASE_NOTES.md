# Course Framework 0.4.0-rc.1 — Gemini 4 agent models, sanitization, and presentation upgrade

Streamlit and Windows now offer Google's Gemini 4 agent models (`gemini-4-hydrogen`, `gemini-4-neon`, `gemini-4-carbon`, `gemini-4-argon`), `gemini-3.8-flash`, `gemini-3.5-flash-lite` (default), and custom Gemini model IDs through the shared `generateContent` adapter with bounded HTTP 503 retries and model-appropriate reasoning/token limits (65,536 tokens for Gemini 4, 32,768 for 3.8 Flash, 16,384 for Flash-Lite/custom).

Untrusted provider responses are sanitized before saving or previewing, and standalone HTML lesson presentations now render Markdown tables, lists, blockquotes, inline formatting, and static module navigation with zero scripts and full HTML escaping. Existing courses and saved partial projects remain compatible and restore their recorded Gemini model.

This is an unsigned Windows prerelease. Extract the whole ZIP before running CourseFramework.exe. Live provider quality and manual Windows acceptance remain pending.
