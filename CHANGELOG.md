# Changelog

## 0.2.0-rc.1 — Direct syllabus workflow

- One workspace in Windows and Streamlit: paste syllabus, choose an agent model, Generate, review, Use draft, Save/Export. Move import, provider configuration, and project opening into Settings/File controls.
- Add Gemini model presets and custom model IDs; preserve Chat Completions compatible and offline providers. Provider changes clear the key and online consent.
- Generate all modules or one selected module, one request per module, with required objectives, lesson content, activities, and assessment sections.
- Keep completed modules after failures; Resume skips them with matching source/model/endpoint. Windows Pause finishes the active request before stopping.
- Version-2 projects retain accepted edits and unfinished drafts without credentials. Version-1 projects migrate on load.
- Add deterministic video searches and syllabus-supplied video links; no verified video-discovery claim.


## 0.1.0-rc.3 — Fit smaller Windows displays

- Fit the initial window within the display with room for window chrome and the taskbar; retain the 940×620 minimum workspace.
- Bound automated Windows captures to the display so footer controls remain visible on 1024×768 runners.
- Add a native startup-size regression check. Windows desktop target: displays of at least 1024×768.


## 0.1.0-rc.2 — Aero Academy UI alignment

- Match the Academy white/navy/gold palette with compact Segoe UI typography, light dividers, and restrained headings.
- Replace the desktop tab strip with synchronized left navigation ordered Syllabus → Review draft → Course editor, plus Engine settings.
- Consolidate file actions in the top bar; wrap helper text and simplify provider guidance for smaller windows.
- Align optional Streamlit colors/headings; preserve generation review, project format, persistence, and session-only keys.
- Add native navigation/minimum-size regression checks and real UI captures to Windows CI. Future Academy data integration remains unimplemented.


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
