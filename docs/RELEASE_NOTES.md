# Course Framework 0.2.0-rc.1 — Direct course workflow

Paste a syllabus, choose an agent model, and Generate in one workspace. Review modules with lesson content, activities, assessments, and video resources, then Use draft and Save/Export. Streamlit no longer has workflow tabs; Windows places the syllabus/agent controls beside the course. File/provider options are secondary.

Choose all modules or one module. Requests run one module at a time; failures retain completed modules and the accepted course. Resume continues unfinished work with the same syllabus/model/endpoint. Windows Pause finishes the current module before stopping. Save project keeps unfinished drafts; re-enter your session key when reopening. Preset Gemini models and custom IDs are selectable; availability depends on your provider account.

Video resources are topic search links and supplied YouTube/Vimeo URLs. Specific videos are not discovered or verified. Review all teaching content and resources before use. Offline generation produces explicit scaffolding/placeholders.

Download the Windows x64 ZIP, extract the entire folder, and run CourseFramework.exe. Windows 10/11 x64, display 1024×768 or larger. Streamlit deployment: main/app.py, Python 3.12.

Projects now use format 2 and include unfinished work plus model metadata, never API keys/endpoints. Format 1 projects migrate without losing accepted edits. Older app versions cannot open format 2; keep Markdown exports for rollback. Course export includes accepted content only.

Required Linux/Windows tests, native startup, Windows packaging, packaged EXE startup, and UI captures must pass before publication. Provider tests use simulated responses. This is an unsigned prerelease; manual Windows/high-DPI/accessibility and live-provider acceptance remain pending. See docs/TESTING.md and docs/KNOWN_ISSUES.md.
