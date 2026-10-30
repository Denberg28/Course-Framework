# Gemini 3.8 Flash investigation — 30 October 2026

The user identified timeout/unfinished-draft symptoms. The exact original error and account-side request trace were not supplied. Code inspection found a fixed 60-second HTTP connection/read timeout and maxOutputTokens 16384 shared by both presets; all non-STOP Gemini outcomes were reported as a combined blocked/output-limit error. Those are confirmed app behaviors, not proof of which condition caused a particular live failure.

Google documents gemini-3.8-flash and the v1beta models generateContent and streamGenerateContent routes. The model defaults to medium thinking and accepts low, medium or high; minimal is unsupported. Thinking counts against the response token ceiling, so exhausting it can produce empty or truncated output.

Version 0.3.6 explicitly retains medium reasoning for demanding work, allows 32768 response tokens including thinking, and applies a 180-second connection/read timeout to this preset. These are application choices within the documented API capabilities, not Google latency guarantees. Lite remains the default with its earlier settings. A larger cap permits more tokens if used and does not establish a fixed or free cost. No automatic retry, continuation, fallback model or source reduction is performed. Existing matching completed modules remain resumable.

| Message | Meaning and next action |
|---|---|
| 180-second timeout | The client did not receive a timely connection/read. Keep the saved project; retry the unfinished module with Resume when available. |
| HTTP 504 | Google/provider timed out; the client wait cannot force a server to finish. Resume later. |
| HTTP 503 | Provider temporarily unavailable; Resume later. |
| MAX_TOKENS | The combined thinking/output allowance was exhausted. Partial output is discarded; completed modules stay. Retry the unfinished module, or explicitly choose Lite for a new job if appropriate. |
| Content policy / RECITATION | A distinct model stop rather than a network timeout; review the input and request original explanations. |
| CONTINUATION | Further generation would need another request. This app does not issue automatic continuation requests; incomplete material is rejected. |
| Access, model-not-found or quota | Check the model/key/project in Google AI Studio. Longer waits do not grant access or quota. |

To check a deployment, save the project before refreshing/rebooting. Select 3.8 Flash and one module for a small live check; allow syllabus transmission, then Generate. Inspect any exact error and the completed/selected count. Reopen a saved matching project to resume after refreshing, and configure the original provider/key/endpoint. Live calls require the deployment owner's authorized key; CI uses fake keys and simulated responses only.

Sources checked on 30 October 2026:

- https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash
- https://ai.google.dev/gemini-api/docs/generate-content/whats-new-gemini-3.8
- https://ai.google.dev/gemini-api/docs/generate-content/thinking
- https://ai.google.dev/api/generate-content

Automated request/error/checkpoint tests demonstrate the code paths, not live model latency, account access or teaching accuracy.

## Continued timeouts: quality-preserving streaming in 0.3.9

The user confirmed that 3.8 must retain its quality-oriented medium reasoning. The app now uses SSE streaming, while preserving medium, the complete syllabus, the existing 600–900-word lesson request and the 32768-token thinking/output allowance. Thought summaries are requested solely as provider activity signals; their content is discarded. Visible progress reports working/received final-text character counts, never model reasoning text. A response can continue beyond 180 seconds overall as chunks arrive; the same timeout still limits a stalled connection/idle read. A fifteen-minute budget is checked between reads, not as a strict whole-course deadline; a blocked read can extend it by up to the socket timeout.

A terminal STOP finishes the module immediately, without waiting for a proxy to close the connection. One request still generates one selected module. An interrupted stream cannot replace accepted material or replay completed modules; a matching saved partial job uses Resume for unfinished work. There is no automatic continuation/retry or quality-reducing model switch.

This change removes the app's full-response buffering path for 3.8. It does not establish the exact account-side cause of earlier timeouts or guarantee first-chunk latency. Google documents streaming and also notes that occasional slowness/timeouts can occur. Unit, simulated browser and real loopback HTTP transport checks are separate from real-key teaching/latency validation. Check v0.3.9 or later in Settings & files to confirm the deployment update.

Additional primary references:

- https://ai.google.dev/gemini-api/docs/generate-content/text-generation
- https://deepmind.google/models/model-cards/gemini-3-8-flash/
