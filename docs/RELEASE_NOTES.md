# Course Framework 0.4.1-rc.1 — Gemini 3.5 Flash-Lite and Gemini 4 Hydrogen

Streamlit and Windows now retain only **Gemini 3.5 Flash-Lite** (`gemini-3.5-flash-lite`, default, 16,384-token limit, 60 s timeout) and **Gemini 4 Hydrogen** (`gemini-4-hydrogen`, `medium` reasoning, 65,536-token limit, 300 s timeout) for Gemini module generation, removing other Gemini agent models.

Both models use Google's `generateContent` route with bounded HTTP 503 retries, sanitized Markdown/HTML output, and upgraded static HTML lesson presentations. Existing accepted courses and saved drafts remain readable; offline templates and the separate OpenAI-compatible provider remain under Settings.

This is an unsigned Windows prerelease. Extract the whole ZIP before running CourseFramework.exe. Live provider quality and manual Windows acceptance remain pending.
