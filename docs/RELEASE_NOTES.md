# Course Framework 0.3.10-rc.1 — Background generation for 3.8 Flash

Gemini 3.8 Flash submits each module to Google's background Interactions API and polls for completion. A temporary status-check failure triggers another read of the same interaction. The app shows Google queue and generation status above Generate. Flash-Lite remains the default.

3.8 Flash keeps medium reasoning, the full syllabus, the existing lesson format and the 32,768-token allowance. Google can retain the background request and result for up to 24 hours for retrieval. The app keeps completed modules and accepted course material and stages the finished draft for instructor review. It sends no automatic replacement generation request.

The exact `drone 101` and `1. drone componenta` input is covered by a local HTTP integration test. Live provider availability still depends on the configured key, model access, quota and service availability. This is an unsigned Windows prerelease. Extract the whole ZIP before running CourseFramework.exe.
