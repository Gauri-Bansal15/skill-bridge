"""Scoring rubric and sanity checks.

The language model fills in component scores; this module adds them up. That
way the total can never be mis-added, and a model that returns 60 out of 50
for one component gets clamped instead of inflating the result.
"""
from __future__ import annotations

import re
from typing import Any

from .skills import SKILLS, mentions

WEIGHTS = {
    "required_skills": 50,
    "experience_projects": 20,
    "education": 10,
    "preferred_skills": 20,
}


def total_score(breakdown: dict[str, float]) -> int:
    """Sum clamped components -> integer 0-100."""
    total = 0.0
    for key, cap in WEIGHTS.items():
        try:
            value = float(breakdown.get(key, 0))
        except (TypeError, ValueError):
            value = 0.0
        total += max(0.0, min(cap, value))
    return int(round(total))


def clamp_breakdown(breakdown: dict[str, Any]) -> dict[str, float]:
    out = {}
    for key, cap in WEIGHTS.items():
        try:
            value = float(breakdown.get(key, 0))
        except (TypeError, ValueError):
            value = 0.0
        out[key] = round(max(0.0, min(cap, value)), 1)
    return out


def _words(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9+#.]{2,}", text.lower()))


def evidence_in_resume(evidence: str, skill: str, resume: str) -> bool:
    """Is the quoted evidence really in the resume?

    We accept it if most of its words occur in the resume. If the model gave no
    evidence at all we fall back to checking that the skill itself is mentioned.
    """
    evidence = (evidence or "").strip()
    if not evidence:
        return mentions(resume, skill) if skill in SKILLS else skill.lower() in resume.lower()
    ev, rs = _words(evidence), _words(resume)
    if not ev:
        return False
    return len(ev & rs) / len(ev) >= 0.6


def normalise_result(raw: dict[str, Any], resume: str) -> dict[str, Any]:
    """Clean up a model answer: fill gaps, clamp scores, flag invented evidence."""
    warnings: list[str] = []
    result: dict[str, Any] = {
        "matching_skills": [],
        "missing_skills": list(raw.get("missing_skills") or []),
        "unverified_skills": list(raw.get("unverified_skills") or []),
        "score_reasoning": str(raw.get("score_reasoning") or ""),
        "suggestions": list(raw.get("suggestions") or [])[:5],
    }

    for item in raw.get("matching_skills") or []:
        skill = str(item.get("skill", "")).strip()
        if not skill:
            continue
        evidence = str(item.get("evidence", ""))
        if not evidence_in_resume(evidence, skill, resume):
            warnings.append(f"Could not find evidence for '{skill}' in the resume, so it was moved to 'unverified'.")
            result["unverified_skills"].append({"skill": skill, "reason": "Evidence quoted by the model was not found in the resume text."})
            continue
        result["matching_skills"].append(
            {"skill": skill, "evidence": evidence, "demonstrated": bool(item.get("demonstrated", True))}
        )

    if isinstance(raw.get("score_breakdown"), dict):
        result["score_breakdown"] = clamp_breakdown(raw["score_breakdown"])
        result["match_score"] = total_score(result["score_breakdown"])
    else:
        try:
            result["match_score"] = int(max(0, min(100, round(float(raw.get("match_score", 0))))))
        except (TypeError, ValueError):
            result["match_score"] = 0
            warnings.append("The model did not return a usable score.")
        result["score_breakdown"] = None
        warnings.append("No score breakdown returned; the score is the model's own number.")

    result["warnings"] = warnings
    return result
