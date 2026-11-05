# Gemini 3.8 Flash generation

From 0.3.15, Antigravity Preview replaces 3.8 Flash in the preset list. It uses the existing Gemini API key and pins Gemini 3.5 Flash-Lite under the agent. Google manages a separate preview agent service with its own access and quota constraints. Older 3.8 projects can still be opened. The following 3.8 notes apply to legacy jobs.

From 0.3.14-rc.1, select **3.8 Flash**, allow syllabus transmission, and click **Generate**. Both Gemini presets use Google's `generateContent` endpoint. 3.8 Flash uses high reasoning, the full teaching prompt, a 32,768-token allowance, and a 300-second connection/read timeout. Check the version in **Settings & files**.

The exact input `drone 101` followed by `1. drone componenta` produces one module. The earlier live run on the Interactions route returned Google HTTP 503. The current generation path has been tested with simulated provider responses.

The app retries an explicit HTTP 503 up to twice with minimum delays of 10 and 30 seconds and respects a Retry-After value of up to 60 seconds. A connection timeout, quota error or persistent overload stops the sequence. **Resume** starts at the first unfinished module. Save the project before closing or refreshing to keep the completed checkpoints. When the result is ready, review it and select **Use draft**.

- [Google Generate Content thinking configuration](https://ai.google.dev/gemini-api/docs/generate-content/thinking)
- [Google Gemini API errors](https://ai.google.dev/gemini-api/docs/api-errors)
