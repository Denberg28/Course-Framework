# Course Framework 0.3.6-rc.1 — Gemini 3.8 reasoning requests

Investigating reported timeout/unfinished-draft symptoms found a shared 60-second HTTP timeout, a 16384-token response cap and a combined blocked/output-limit error. The 3.8 model ID and REST route match Google's documentation; the exact cause of an earlier account-side failure remains unverified.

The 3.8 Flash preset now explicitly uses medium reasoning, a 32768-token response ceiling including thinking, and a 180-second connection/read timeout. Lite remains the default with unchanged limits. The larger cap allows more tokens when used; it is not a cost or latency guarantee.

Errors distinguish client timeout/network failure, provider HTTP 503/504, token exhaustion, policy blocks, recitation and continuation. Partial modules are discarded, completed modules and accepted courses are kept, and matching jobs resume without replaying completed requests. There are no automatic retries, continuation calls or fallback model changes. Save projects before refreshing or rebooting Streamlit.

Publication requires Linux/Windows/native tests, Chromium desktop/mobile and 3.8/Lite simulated-generation checks, Windows build and packaged startup. All provider tests are simulated; no live key/account latency or teaching-quality validation is claimed. See docs/GEMINI_TROUBLESHOOTING.md for investigation evidence and recovery. This remains an unsigned prerelease; extract the entire Windows ZIP before running CourseFramework.exe.
