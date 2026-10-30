# Course Framework 0.3.5-rc.1 — Detect every curriculum table module

Fix AE 417 OJT syllabus copies generating only two modules. Blank leading columns and row indentation previously collapsed topics 2–13 into the first topic's subtopics; dash/empty lab-hour cells did not match the hour parser, and Laboratory/Equipment became another module.

Markdown tables, browser/spreadsheet tab or space copies and Word tables now detect all **13 modules, seven objectives, eight supplied bibliography entries and 54 lecture hours**, with the supplied zero lab total. Field/value metadata, HTML line breaks and nonbreaking spaces are normalized for parsing. Empty/dash module hours remain unspecified, reversed columns retain their positions, and no weeks are inferred. Original source, accepted material, syllabus-only references, model choices and the fixed scrollbar/progress placement remain intact.

Generating a changed syllabus over an earlier draft also continues past the first module: replacement approval now resets before Streamlit registers that checkbox, with accepted material still preserved until approval.

After updating, save your project, refresh Streamlit and paste the full syllabus again. Check **13 modules · 7 outcomes**, choose All modules and Generate a fresh draft. Older incomplete jobs start fresh under the changed parser contract; accepted material is not overwritten without Use draft/replacement approval.

Publication requires Linux/Windows/native regression checks, actual Chromium desktop/mobile navigation/download/scrollbar and simulated in-flight generation checks, an AE 417 clipboard-to-13-module download check, Windows packaging and packaged startup. Provider responses are simulated; live teaching quality and manual Windows/browser/OS/accessibility acceptance remain pending. This is an unsigned prerelease. Extract the whole Windows ZIP before running CourseFramework.exe. Streamlit: main/app.py, Python 3.12.
