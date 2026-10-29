# Course Framework project instructions

Based on [Denberg28/Agents_md AGENTS.md v1.1](https://github.com/Denberg28/Agents_md/blob/main/AGENTS.md), reviewed 29 October 2026. Preserve the priorities and proportionate workflow below.

## Context and workflow

- Follow Define → Baseline → Design → Implement → Review → Verify → Package → Deliver. Repository evidence is the source of truth; do not invent test results or stable readiness.
- Preserve unrelated work. Do not reset, clean, force-push, overwrite user edits, or republish an existing version to hide a regression.
- Prefer free-first, lightweight, maintainable solutions. Windows desktop is the primary target; Streamlit is optional. Both use the same course model, adapters, and project format.
- Choose reversible defaults and complete authorized work without repeated approval. Ask only for material ambiguity, missing access, spending, destructive actions, signing/identity changes, or unapproved publication.

## Boundaries

- Keep UI, generation adapters, and file/persistence logic separate. Never access Tk widgets from a worker thread.
- Preserve accepted material when generation/revision fails. Stage generated output for explicit review before replacement.
- Manual/desktop API keys are session-only. The hosted Gemini key may be read from Streamlit Secrets, as explicitly requested by the user; keep it server-side and never prefill widgets or copy it into session/project state. Never commit, log, export, or put API keys in URLs. Use explicit project-field allow-lists and sanitized errors.
- Treat syllabus files and provider responses as untrusted data. Bound file/text/response sizes, validate schemas, refuse credential-forwarding redirects, and use normal TLS verification.
- Do not invent factual teaching material in local template mode. Identify placeholders and instructor-review requirements.

## Verification and delivery

- Python 3.12; requirements files constrain direct dependencies. Commands and gates live in `docs/TESTING.md`.
- Run syntax/whitespace checks and the critical regression suite. Windows native and packaged smoke tests are required for candidate publication. Live API tests use only explicitly supplied credentials and never run in CI.
- Source changes invalidate affected test evidence. Fix failures instead of weakening gates. Label simulated, build-verified, and manual observations separately.
- Keep releases as prereleases until manual Windows and live-provider gates pass. Never claim that startup/build proves usability or teaching accuracy.
- Keep README, architecture, testing, known issues, and changelog current. Report changes, version/commit/artifact, check results, and material verification limits.
- Roll back via a focused revert; preserve user project/Markdown exports first. No hardware gate applies unless a future feature controls physical equipment.
