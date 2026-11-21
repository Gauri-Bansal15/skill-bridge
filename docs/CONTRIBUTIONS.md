<!-- TEAM: make sure this matches what each person really did, then run scripts/contrib_stats.sh once everyone has pushed commits. -->
# Individual contributions

Team **Skill Bridge** - 4 members. Each member owned a clear area, and every pull request was reviewed by a teammate.

| Member | Role | Main ownership |
|---|---|---|
| **Gauri Bansal** (Team Leader) | Project lead, app and integration | Problem definition, Milestone 1 proposal, baseline prompt (v1), Streamlit app, scoring and validation, README, final report, release |
| **Garima Pandey** | Prompt engineer and backend | Prompts v2 and v3, JSON schema, scoring rubric, Gemini integration, offline engine, evaluation script |
| **Bhumika Singh** | Data and evaluation support | Sample resumes and job descriptions, gold labels, running the evaluation and recording results |
| **Shashank Choudhary** | Privacy and testing | Privacy filter, unit tests, CI workflow |

## In more detail

### Gauri Bansal - project lead, app and integration
- Chose problem C9 with the team and wrote the problem statement (`docs/PROBLEM_STATEMENT.md`).
- Wrote the baseline prompt `prompts/v1_baseline.md`.
- Built `app.py` (Streamlit interface), `src/skillbridge/cli.py`, `scoring.py` and `analyzer.py`.
- Wrote `README.md`, `docs/DEMO.md` and the report; prepared the presentation.
- Reviewed pull requests, kept the milestone checklist and tagged the release.

### Garima Pandey - prompt engineering and backend
- Designed prompts `v2_structured.md` and `v3_rubric.md` and wrote `prompts/CHANGELOG.md` explaining each change.
- Defined the four-part scoring rubric (50/20/10/20) and the JSON schema.
- Built `llm.py` (Gemini client), `prompts.py`, `skills.py` and the offline engine `offline.py`.
- Wrote `evaluation/run_eval.py` and `evaluation/README.md`.

### Bhumika Singh - data and evaluation support
- Wrote the synthetic resumes and job descriptions in `data/` and the six labelled pairs in `data/eval_pairs.json`.
- Ran the evaluation and recorded the results in `evaluation/results/`.
- Collected the NACE reference used in the problem statement.

### Shashank Choudhary - privacy and testing
- Wrote the privacy filter `src/skillbridge/privacy.py`.
- Wrote the tests in `tests/` and the CI workflow `.github/workflows/ci.yml`.

## Shared work
All four members took part in choosing the problem, reviewing prompt outputs, and preparing the demo.

## How to check this against git
```bash
./scripts/contrib_stats.sh
```
It prints commits, lines changed and files touched per author. For this to be accurate, each member should commit from their own account (`git config user.name "Your Name"`).
