# Gemini 3.8 Flash generation

The exact input `drone 101` followed by `1. drone componenta` is recognized as one module. The earlier streaming design still depended on Google sending the initial response before the connection timed out.

From 0.3.10-rc.1, 3.8 Flash submits the full prompt with medium reasoning and the existing 32,768-token allowance using Google's background Interactions API. Once Google acknowledges the request, the app shows queue or generation status and checks the same interaction about every five seconds. A temporary connection or server error during a status check can be retried without submitting a second module. Google can keep the background request and result for up to 24 hours for retrieval.

If the app stops during submission, check the displayed HTTP, quota, access or connection error. An unacknowledged submission can still have reached Google. If the background wait reaches fifteen minutes, the provider may continue processing. The app retains completed modules in the pending draft. Save the project before closing or refreshing. Reopening a project can resume from completed checkpoints. The in-flight request ID is held only during generation, so a manual retry can create another request for that module.

Check the deployed version in **Settings & files**. Use **3.8 Flash**, allow syllabus transmission and generate the one-module outline. The displayed Google status should transition to **Draft ready · 1/1 complete** when the result is received. Review it before selecting **Use draft**.

- [Google background execution documentation](https://ai.google.dev/gemini-api/docs/background-execution)
- [Google Interactions response format](https://ai.google.dev/gemini-api/docs/interactions-breaking-changes-may-2026)
