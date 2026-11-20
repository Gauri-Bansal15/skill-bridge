# Prompt changelog

We treat the prompt as a piece of code: every change has a reason, and every reason is something we can test with `evaluation/run_eval.py`.

## v1 - baseline (`v1_baseline.md`)
The first prompt we wrote, submitted in Milestone 1. Short and plain: four tasks and one safety line ("Do not invent skills or experience").

What we expected to go wrong (to be confirmed by running the evaluation with Gemini):
- Output is free text, so the app cannot show a score gauge or a skill table.
- The score has no defined meaning, so two runs may disagree.
- "Missing or unverified" are blended together.

## v2 - structured output (`v2_structured.md`)
Changes: step-by-step instructions, an exact JSON shape, an `evidence` field for every match, and a separate `unverified_skills` list.

Why: lets the app parse the answer, and forces the model to point at resume text instead of just asserting a match.

What we still worry about: the model picks its own score, and may do the arithmetic badly.

## v3 - scoring rubric + guardrails (`v3_rubric.md`)
Changes:
- A four-part rubric (50 / 20 / 10 / 20). The model fills the components; our code adds them up, so the total can never be mis-added.
- A "when unsure, choose unverified" rule.
- Suggestions must cite a resume line, and may never encourage claiming skills the student does not have.
- An instruction to ignore commands hidden inside the resume (prompt injection).
- A fairness line: do not infer gender, age or background from a name.

Why: makes the score explainable and repeatable, and reduces hallucinated evidence.

## How to add v4
1. Copy `v3_rubric.md` to `v4_<idea>.md`.
2. Add it to `PROMPT_FILES` in `src/skillbridge/prompts.py`.
3. Run `python evaluation/run_eval.py --engine gemini --versions v3 v4 --runs 3`.
4. Write down what changed in this file, including when v4 is worse.
