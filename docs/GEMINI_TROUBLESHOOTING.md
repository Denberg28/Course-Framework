# Gemini agent models and troubleshooting

Starting with **0.4.0-rc.1**, Streamlit and Windows support Google's Gemini 4 and 3.x models through the shared `generateContent` endpoint:

| Model ID | Tier / Role | Reasoning | Token ceiling (thinking + output) | Timeout |
|---|---|---|---|---|
| `gemini-3.5-flash-lite` | Default · fast, low-cost (Free/Paid) | Default | 16,384 | 60 s |
| `gemini-4-hydrogen` | Balanced Gemini 4 teaching agent (Free/Paid) | `medium` | 65,536 | 300 s |
| `gemini-4-neon` | Fast frontier STEM & knowledge work (Paid) | `medium` | 65,536 | 300 s |
| `gemini-4-carbon` | Deepest reasoning & verification (Paid) | `high` | 65,536 | 300 s |
| `gemini-4-argon` | Efficient Gemini 4 frontier reasoning (Paid) | `medium` | 65,536 | 300 s |
| `gemini-3.8-flash` | Reasoning Flash model | `high` | 32,768 | 300 s |
| Custom model ID | User-supplied model ID | Model default | 16,384 | 60 s |

Check the deployed version in **Settings & files**. Paid-tier models (`gemini-4-neon`, `gemini-4-carbon`, `gemini-4-argon`) require a paid Gemini API key; free-tier accounts can use `gemini-3.5-flash-lite` and `gemini-4-hydrogen` subject to Google's current quotas.

The app retries an explicit HTTP 503 overload response up to twice with minimum delays of 10 and 30 seconds and respects a `Retry-After` value of up to 60 seconds. A connection timeout, HTTP 504, quota error (HTTP 429), or persistent overload stops the sequence without replaying uncertain requests. **Resume** continues at the first unfinished module. Save the project before closing or refreshing to keep completed checkpoints. When the draft is ready, review it and select **Use draft**.

- [Google Gemini API models](https://ai.google.dev/gemini-api/docs/models)
- [Google Generate Content thinking configuration](https://ai.google.dev/gemini-api/docs/generate-content/thinking)
- [Google Gemini API errors](https://ai.google.dev/gemini-api/docs/api-errors)
