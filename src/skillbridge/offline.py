"""Offline demo engine: a transparent, rule-based analyser.

It needs no API key and no internet, so the app can be demoed anywhere and the
test-suite can run in CI. It also gives us a deterministic baseline to compare
the language model against.
"""
from __future__ import annotations

import re

from .scoring import WEIGHTS, normalise_result, total_score
from .skills import SKILLS, find_skills, mentions

_HEADER = re.compile(r"^\s*(required|must[- ]have|preferred|nice[- ]to[- ]have|good[- ]to[- ]have|bonus)[^:]*:", re.I)
_RELATED = re.compile(r"computer|information technology|\bIT\b|\bCSE\b|engineering|data science|artificial intelligence|software", re.I)
_DEGREE = re.compile(r"b\.?\s?tech|b\.?\s?e\b|b\.?\s?sc|bca|m\.?\s?tech|m\.?\s?sc|bachelor|master|degree", re.I)


def split_job(job: str) -> tuple[list[str], list[str]]:
    """Return (required, preferred) skills found in a job description."""
    required: list[str] = []
    preferred: list[str] = []
    found_header = False
    for line in job.splitlines():
        m = _HEADER.match(line)
        if not m:
            continue
        found_header = True
        bucket = required if m.group(1).lower().startswith(("required", "must")) else preferred
        for s in find_skills(line):
            if s not in bucket:
                bucket.append(s)
    if not found_header:
        required = find_skills(job)
    return required, preferred


def _is_skills_line(line: str) -> bool:
    return line.strip().lower().startswith(("skills", "technical skills", "key skills"))


def _locate(resume: str, skill: str) -> tuple[str | None, bool]:
    """(evidence_line, demonstrated). Evidence is None if the skill is absent."""
    listed_line = None
    for raw in resume.splitlines():
        line = raw.strip(" -*\t")
        if not line or not mentions(line, skill):
            continue
        if _is_skills_line(line):
            listed_line = listed_line or line
        else:
            return line, True
    return listed_line, False


def analyse(resume: str, job: str) -> dict:
    required, preferred = split_job(job)
    matching, missing, unverified = [], [], []
    states: dict[str, tuple[str | None, bool]] = {}

    for skill, importance in [(s, "required") for s in required] + [(s, "preferred") for s in preferred]:
        evidence, demonstrated = _locate(resume, skill)
        states[skill] = (evidence, demonstrated)
        if evidence is None:
            missing.append({"skill": skill, "importance": importance, "note": f"'{skill}' is not mentioned anywhere in the resume."})
            continue
        matching.append({"skill": skill, "evidence": evidence, "demonstrated": demonstrated})
        if not demonstrated:
            unverified.append({"skill": skill, "reason": "Only appears in the skills list; no project or experience line shows it being used."})

    present_req = [s for s in required if states[s][0] is not None]
    shown_req = [s for s in required if states[s][1]]
    present_pref = [s for s in preferred if states[s][0] is not None]

    has_degree = bool(_DEGREE.search(resume))
    related = has_degree and bool(_RELATED.search(resume))

    breakdown = {
        "required_skills": WEIGHTS["required_skills"] * len(present_req) / len(required) if required else 0,
        "experience_projects": WEIGHTS["experience_projects"] * len(shown_req) / len(required) if required else 0,
        "education": 10 if related else (5 if has_degree else 0),
        "preferred_skills": WEIGHTS["preferred_skills"] * len(present_pref) / len(preferred) if preferred else 0,
    }

    parts = [f"{len(present_req)} of {len(required)} required skills appear in the resume"]
    parts.append(f"{len(shown_req)} of them are shown in a project or experience line")
    if preferred:
        parts.append(f"{len(present_pref)} of {len(preferred)} preferred skills appear")
    reasoning = "; ".join(parts) + "."

    suggestions = []
    for m in missing:
        if m["importance"] == "required":
            suggestions.append({
                "section": "Skills / Projects",
                "suggestion": f"The job asks for {m['skill']}. Add it only if you really have it; otherwise learn it and build a small project you can describe.",
                "based_on": "Job description requirement not found in the resume",
            })
    for u in unverified:
        suggestions.append({
            "section": "Projects",
            "suggestion": f"You list {u['skill']} but never show it in action. Add a project or experience bullet that explains what you built with it and the result.",
            "based_on": "Skills line",
        })
    if not suggestions and missing:
        suggestions.append({"section": "Skills", "suggestion": "You cover every required skill. Consider picking up the preferred skills listed in the job description.", "based_on": "Preferred skills not found"})

    raw = {
        "matching_skills": matching, "missing_skills": missing, "unverified_skills": unverified,
        "score_breakdown": breakdown, "score_reasoning": reasoning, "suggestions": suggestions[:5],
    }
    result = normalise_result(raw, resume)
    result["match_score"] = total_score(result["score_breakdown"])
    return result
