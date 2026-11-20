# Evaluation

`data/eval_pairs.json` holds six resume/job pairs with hand-written answers ("gold labels"): which skills match, which are missing, which are only listed, and a score range a sensible reviewer would accept.

```bash
# Offline engine - no key needed, runs in CI
python evaluation/run_eval.py --engine offline

# Gemini - compare prompt versions, 3 repeats each to measure consistency
export GEMINI_API_KEY=...
python evaluation/run_eval.py --engine gemini --versions v2 v3 --runs 3
```

## Metrics
| Metric | Meaning |
|---|---|
| in-band | Share of runs whose score fell inside the accepted range |
| match F1 | Precision/recall of the skills the engine called "matching" |
| missing recall | Share of truly missing skills the engine noticed |
| unverified recall | Share of "listed only" skills the engine caught |
| score std | Spread of the score across repeated runs (lower = more consistent) |
| valid rate | Share of runs that returned usable structured output |
| evidence warnings | Times the model quoted resume text that is not in the resume |

## Be careful how you read the offline numbers
The offline engine scores 100% on this set. That is a **sanity check, not a result**: the sample data is small, written by us, and uses the same skill list as the engine. The interesting numbers are the Gemini ones, and the bigger question is whether the pairs are realistic - add more, and add messy ones.

## Adding a pair
Add a resume to `data/resumes/`, a job to `data/jobs/`, then a new entry in `data/eval_pairs.json`. Write the gold labels *before* you run the engine, otherwise you will be tempted to fit them to the output.
