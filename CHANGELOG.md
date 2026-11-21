# Changelog

Dated list of changes since Milestone 1 (submitted 9 October 2026). Newest first.

## 2026-11-21
- Restructured the repository to the Milestone 2 layout: `prompts/v1`, `v2`, `v3`, `final`, `test-data/`, `code/`, `docs/`.
- Added the 12-case test table (`test-data/test_cases.json`, 6 normal, 4 edge, 2 invalid) and its runner `evaluation/run_tests.py`.
- Added `evaluation/run_iteration_log.py`, which measures prompt versions v1, v2 and v3 on the same inputs.
- **Bug found by dry-running test T7 and fixed:** the privacy filter always masked the first line of a resume as a name, so a resume whose first line was `Skills: Python` lost its only content. The first line is now masked only when it looks like a name (regression test added).
- Hit the Gemini free-tier limit (20 requests per day). Gemini client now retries timeouts but never retries a quota error; the app shows a clear "quota used up" message and the offline engine still works.
- Added `docs/build_m2.py` (builds the Milestone 2 PDF and the Business Model Canvas) and `scripts/check_submission.py`.
- Tested prompts v1 and v3 with Gemini on the T1 input. v1 returned free text (60/100, no rubric); v3 returned 62/100 with the breakdown 37.5 / 15 / 10 / 0.

## 2026-11-20
- First working prototype pushed to GitHub: Streamlit app, command-line tool, Gemini client, offline rules engine.
- Prompt versions v1 (baseline), v2 (structured JSON) and v3 (rubric and guardrails).
- Privacy filter, validator that checks quoted evidence against the resume, scoring rubric (50/20/10/20).
- Synthetic resumes and job descriptions, six labelled pairs, automated tests and a GitHub Actions workflow.
