# Changelog

## 0.3.3-rc.1 — Default model, branding and navigation

- Default Streamlit, native Windows and shared engine configuration to Gemini 3.5 Flash-Lite; retain 3.8 Flash for demanding work and custom model IDs. Preserve explicit session/job model choices.
- Restore the original airplane mark and favicon; add a compact white/navy/gold header with a static lesson-paper illustration that hides on narrow screens.
- Add a visible vertical page scrollbar with a stable gutter, Syllabus/Course material jump links, a return link and smooth scrolling that respects reduced-motion settings.
- Keep full-width syllabus/materials, syllabus-based references, contact hours and the teaching format intact.
- Add model-routing regression coverage and a Chromium CI gate for actual desktop/mobile navigation, overflow, offline generation/Markdown download and screenshot capture.

## 0.3.2-rc.1 — Syllabus references

- Replace the automatic agency/university/publisher catalog with the bibliography supplied in the syllabus, regardless of subject or source domain.
- Put the supplied textbook/readings into provider prompts and module reference sections with stable SYL source IDs. For AE 416, retain Paler-Calmorin, Adanza and Sevilla; add no outside agency readings.
- Preserve bibliography links from any domain while marking model-invented URLs; flag absent references without inventing replacements.
- Recognize bibliography/reading-list heading variants and distinguish bibliographic metadata from access to the actual source text.
- Preserve accepted courses and the current syllabus/layout/hours/assessment workflow. A fresh generation uses the updated reference contract.

## 0.3.1-rc.1 — Full syllabus and screen allocation

- Restore the original Streamlit reading order: paste the full syllabus, Generate, preview materials below at full content width; move optional scope to Settings & files.
- Recognize plain course code/title, course-completion outcome sentences, units/weekly hours/standing, singular Textbook headings, and lecture/lab tables copied with tabs, spaces or pipes.
- Preserve exact module lecture/lab allocations, supplied totals, outcomes and readings in prompts, course overview, headings and exports; flag inconsistent totals without inventing weeks.
- Include the supplied AE 416 syllabus as the Example and a regression fixture: five modules, three outcomes, 36 lecture/54 lab hours.
- Add direct draft/accepted Markdown downloads and keep Save/Export above the preview. Collapse course overview while keeping the teaching sequence visible.
- Retain sequential generation, failure/resume checkpoints, explicit accepted-course replacement, hosted Secrets and the five-MCQ teaching format. Start fresh generation for the updated parsing/prompt contract.

## 0.3.0-rc.1 — Focused teaching modules

- Remove video suggestions and links from new module generation.
- Restore introduction, presentation/discussion sequence, worked example, summary, and one practical activity.
- Require five numbered multiple-choice questions with A–D options and a numbered letter-only answer key.
- Collapse assessment, answer key and references in Streamlit and standalone HTML; add Windows Preview for that presentation.
- Append topic-scoped checked official/publisher references (FAA, CAAP, EASA, MIT/OpenStax); distinguish validated source locations from unverified generated content.
- Preserve existing projects; start a fresh draft for the new format. Keep one request per module and existing key/resume protections.


## 0.2.0-rc.2 — Streamlit Secrets key

- Read a server-owned Gemini key from `st.secrets["GEMINI_API_KEY"]`; hide the API-key input when configured.
- Keep the secret out of widget/session/project/export data and never use it for another provider. Manual keys remain an optional session-only fallback.
- Document the exact Secrets TOML and shared hosted quota; add regression coverage with fake secrets and no live API calls.


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
