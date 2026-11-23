# Gemini agent models and troubleshooting

Starting with **0.4.1-rc.1**, Streamlit and Windows support **Gemini 3.5 Flash-Lite** and **Gemini 4 Hydrogen** through the shared `generateContent` endpoint:

| Model ID | Tier / Role | Reasoning | Token ceiling (thinking + output) | Timeout |
|---|---|---|---|---|
| `gemini-3.5-flash-lite` | Default · fast, low-cost (Free/Paid) | Default | 16,384 | 60 s |
| `gemini-4-hydrogen` | Balanced Gemini 4 teaching agent (Free/Paid) | `medium` | 65,536 | 300 s |

Check the deployed version in **Settings & files**. Both models are available on Google's Free and Paid Gemini API tiers, subject to Google's current quotas and account access.

The app retries an explicit HTTP 503 overload response up to twice with minimum delays of 10 and 30 seconds and respects a `Retry-After` value of up to 60 seconds. A connection timeout, HTTP 504, quota error (HTTP 429), or persistent overload stops the sequence without replaying uncertain requests. **Resume** continues at the first unfinished module. Save the project before closing or refreshing to keep completed checkpoints. When the draft is ready, review it and select **Use draft**.

- [Google Gemini API models](https://ai.google.dev/gemini-api/docs/models)
- [Google Generate Content thinking configuration](https://ai.google.dev/gemini-api/docs/generate-content/thinking)
- [Google Gemini API errors](https://ai.google.dev/gemini-api/docs/api-errors)
