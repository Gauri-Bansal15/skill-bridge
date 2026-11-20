<!-- TEAM: the roles below are a starting draft. Edit them so they match what each person really did, then run scripts/contrib_stats.sh once everyone has pushed commits. -->
# Individual contributions

Team **Skill Bridge** - 4 members. Each member owned one area and had at least one of their pull requests reviewed by a teammate.

| Member | Role | Main ownership |
|---|---|---|
| **Gauri Bansal** (Team Leader) | Project lead and integration | Problem definition, Milestone 1 proposal, baseline prompt (v1), README and docs, final report, release |
| **Garima Pandey** | Prompt engineer | Prompts v2 and v3, JSON output schema, scoring rubric design, Gemini integration, prompt changelog |
| **Bhumika Singh** | Research and evaluation | Problem research and NACE evidence, review of existing tools, sample resumes and job descriptions, gold labels, evaluation script and metrics |
| **Shashank Choudhary** | App and quality | Streamlit app, privacy filter, scoring and validation code, tests, CI workflow |

## In more detail

### Gauri Bansal - project lead and integration
- Chose problem C9 with the team and wrote the problem statement (`docs/PROBLEM_STATEMENT.md`).
- Wrote the baseline prompt `prompts/v1_baseline.md`.
- Wrote `README.md`, `docs/DEMO.md` and the report; prepared the presentation.
- Reviewed pull requests, kept the milestone checklist and tagged the release.

### Garima Pandey - prompt engineering
- Designed prompts `v2_structured.md` and `v3_rubric.md` and wrote `prompts/CHANGELOG.md` explaining each change.
- Defined the four-part scoring rubric (50/20/10/20) and the JSON schema.
- Built `src/skillbridge/llm.py` (Gemini client, JSON parsing) and `src/skillbridge/prompts.py`.

### Bhumika Singh - research and evaluation
- Collected the evidence for the problem (NACE Job Outlook 2025) and compared Jobscan and Teal to find our gap.
- Wrote the synthetic resumes and job descriptions in `data/` and the six labelled pairs in `data/eval_pairs.json`.
- Wrote `evaluation/run_eval.py` and `evaluation/README.md`, and ran the evaluation.

### Shashank Choudhary - app and quality
- Built `app.py` (Streamlit interface) and `src/skillbridge/cli.py`.
- Wrote `privacy.py`, `scoring.py`, `skills.py` and the offline engine `offline.py`.
- Wrote the 22 tests in `tests/` and `.github/workflows/ci.yml`.

## Shared work
All four members took part in choosing the problem, reviewing prompt outputs, and preparing the demo.

## How to check this against git
```bash
./scripts/contrib_stats.sh
```
It prints commits, lines changed and files touched per author. For this to be accurate, each member should commit from their own account (`git config user.name "Your Name"`).
