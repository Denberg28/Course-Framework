# Aero Academy alignment and direct workflow

Reference: `Denberg28/Aeronautical-Open-Academy` main, `MainActivity.java` and `WorkspaceActivity.java`, inspected 29 October 2026. Course Framework keeps its white/navy/gold palette while simplifying authoring to **paste → select agent → Generate → review → Use draft → Save/Export**.

| Token | Value |
|---|---|
| Paper | `#ffffff` |
| Navy | `#102640` |
| Secondary text | `#536174` |
| Dividers | `#e4e9f0` |
| Fields | `#fafbfd` |
| Highlight | `#e6b844` |
| Selection tint | `#fff7df` |
| Desktop font | Segoe UI, 10 pt body, 11 pt section, 18 pt app title |

Windows uses one split workspace, with model/key/scope controls beside a draft or accepted course. Settings and File contain secondary options; Preview opens a safe HTML lesson presentation with collapsible assessments, letter keys, and references. Streamlit uses one page, a model dropdown, and Settings & files; import/outline review are optional. Draft acceptance remains explicit so new output never silently replaces accepted teaching material.

`academy_theme.py` centralizes the palette. The old left rail, four workflow pages, standalone engine page, revision instruction row, and duplicate export buttons were removed. Ctrl+O/Ctrl+S remain. Agent selection is a single model choice per generation, not an autonomous multi-agent team.

Windows CI captures actual native widgets with `python tools/capture_ui.py ui-review`. The older `docs/evidence/aero-ui-linux-preview.png` is historical rc.2 evidence and does not represent the new workspace. Manual side-by-side Academy desktop, high-DPI, keyboard, and screen-reader acceptance remain pending.

This prepares visual integration. Academy accounts, course/material import contracts, and instructor publication are not implemented.

New generated modules focus on ordered presentation/discussion, one activity, and five MCQs; video suggestions are removed. Streamlit collapses assessment, answer key, and reference details by default, while keeping discussion visible.
