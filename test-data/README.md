# test-data/

Inputs and saved outputs for the Milestone 2 test table.

- `test_cases.json` - the 12 tests (6 normal, 4 edge, 2 invalid): input, expected output and the automatic pass/fail checks.
- `inputs/` - the resume and job description texts used by the tests. All people and companies are made up.
- `outputs/` - real outputs saved by the runners: `T1.json` ... `T12.json` (one per test), `tests_<tag>.json` (summary) and `iteration_<tag>.json` (prompt-version experiment).

Reproduce:
```bash
export GEMINI_API_KEY=...
python evaluation/run_tests.py --engine gemini --tag mine           # the 12-test table
python evaluation/run_iteration_log.py --pairs P1 P5 --runs 2 --tag mine   # v1 vs v2 vs v3
```
The free tier allows about 5 requests a minute and 20 a day, so use `--delay 15` (the default) and split the work with `--only` or `--pairs` if needed.
