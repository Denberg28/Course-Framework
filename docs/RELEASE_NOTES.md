# Course Framework 0.3.4-rc.1 — Visible scrollbar and progress placement

The main scrollbar now starts below Streamlit's fixed toolbar, so a short thumb is not hidden behind the app menu. The scroll viewport fits the remaining screen; Chromium/WebKit has a contrasting 16 px track and a 56 px minimum thumb for long courses. Native scrolling, section links and reduced-motion support remain.

After Generate/Resume is clicked, progress appears directly above the action with the actual completed/selected module count. The action is disabled while running; ready/stopped status and sanitized errors stay in the same area. Generation runs in the normal page layout instead of pre-page callback output. Every successful module is checkpointed, settings/editor state is preserved before rerunning, and reruns do not repeat API requests.

Gemini 3.5 Flash-Lite remains the default with optional 3.8 Flash. Syllabus-based references, full-width materials, lecture/lab allocations, collapsible assessments/keys, saved projects and hosted Secrets are retained.

Publication requires Linux/Windows/native regression checks, actual Chromium desktop/mobile navigation/download/scrollbar and delayed simulated in-flight generation checks, Windows packaging and packaged startup. Screenshots are retained for review. Provider responses are simulated; live teaching quality and manual browser/OS/accessibility acceptance remain pending. This is an unsigned prerelease. Extract the whole Windows ZIP before running CourseFramework.exe. Streamlit: main/app.py, Python 3.12. Save your project before rebooting a deployment.
