# Course Framework 0.3.9-rc.1 — Stream 3.8 modules while preserving reasoning

Gemini 3.8 Flash now uses streamed SSE responses instead of waiting for a full JSON result. It keeps **medium reasoning**, the full syllabus/lesson request and the 32768-token allowance. No lower reasoning setting, shortened syllabus or reduced lesson scope is introduced.

Provider activity is consumed while reasoning and generating. Summary content is discarded; the app displays only working/received-character progress above Generate. It finishes immediately when the model signals completion, avoiding a late timeout caused by waiting for the connection to close. Completed modules are checkpointed; interrupted output never replaces accepted material. Matching partial jobs can Resume without replaying completed requests.

The 180-second connection/idle timeout remains. A fifteen-minute response budget is checked between reads; an already blocked read can extend that by its socket timeout. Streaming cannot force a busy provider to send data or prevent server-side 504s. No automatic retry, continuation or fallback-model call is added. The deployed version appears in Settings & files; save your project before refreshing.

Publication requires Linux/Windows/native tests, a real local HTTP chunked-SSE integration check, simulated streaming/progress/rollback/resume tests, actual Chromium desktop/mobile checks, Windows packaging and packaged startup. No real Google API call or live latency/teaching-quality result is claimed. This remains an unsigned prerelease; extract the whole Windows ZIP before running CourseFramework.exe.
