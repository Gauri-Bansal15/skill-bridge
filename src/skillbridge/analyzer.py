"""One entry point for the app, the CLI and the evaluation script."""
from __future__ import annotations

from . import offline
from .llm import GeminiClient, GeminiError, parse_json
from .privacy import anonymise
from .prompts import STRUCTURED, render
from .scoring import normalise_result


def analyse(
    resume: str,
    job: str,
    engine: str = "offline",
    prompt_version: str = "v3",
    client: GeminiClient | None = None,
    anonymise_resume: bool = True,
) -> dict:
    """Compare a resume with a job description.

    engine: "offline" (rule-based demo, no key needed) or "gemini".
    Returns a dict with the same keys for both engines (see README).
    """
    if not resume.strip() or not job.strip():
        raise ValueError("Both the resume and the job description are required.")

    privacy = {"total": 0, "counts": {}}
    clean_resume = resume
    if anonymise_resume:
        clean_resume, report = anonymise(resume)
        privacy = {"total": report.total, "counts": report.counts}

    if engine == "offline":
        result = offline.analyse(clean_resume, job)
        result.update(engine="offline-rules", prompt_version="n/a")
    elif engine == "gemini":
        client = client or GeminiClient()
        prompt = render(prompt_version, clean_resume, job)
        if prompt_version in STRUCTURED:
            raw = client.generate(prompt, json_mode=True)
            try:
                result = normalise_result(parse_json(raw), clean_resume)
            except ValueError as exc:
                raise GeminiError(f"The model did not return valid JSON: {exc}") from exc
        else:  # v1 returns free text
            result = {
                "raw_text": client.generate(prompt, json_mode=False),
                "match_score": None, "score_breakdown": None,
                "matching_skills": [], "missing_skills": [], "unverified_skills": [], "suggestions": [],
                "warnings": ["The baseline prompt returns free text, so there is no structured score or skill table."],
            }
        result.update(engine=f"gemini ({client.model})", prompt_version=prompt_version)
    else:
        raise ValueError("engine must be 'offline' or 'gemini'")

    result["privacy"] = privacy
    result["disclaimer"] = "Guidance only. This score is not a hiring decision and has not been validated against real recruiters."
    return result
