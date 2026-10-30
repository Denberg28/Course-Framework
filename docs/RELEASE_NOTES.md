# Course Framework 0.3.7-rc.1 — Fix the disabled Generate button after paste

Pasting a syllabus could leave Generate disabled because Streamlit had not yet applied the textarea text and the server still saw zero modules. Users had to blur the field or press Ctrl+Enter before the button became usable.

Generate now remains available so its click submits the freshly pasted syllabus directly. It is still disabled while generating. An empty click shows a clear paste instruction and makes no provider request. Online consent and key validation remain required; completed modules, accepted material, selected models and 3.8 timeout improvements are retained.

Save your project before refreshing the Streamlit app. Paste the syllabus, select the model, check Send syllabus to this agent, then Generate. For an older unreloaded session, Ctrl+Enter applies the text as an immediate workaround.

Publication requires Linux/Windows/native tests, Chromium same-click paste/generation, desktop/mobile progress/navigation/download checks, Windows packaging and packaged startup. Tests use simulated providers and no real key. This remains an unsigned prerelease; extract the whole Windows ZIP before running CourseFramework.exe. Live provider access/latency and teaching accuracy require separate validation.
