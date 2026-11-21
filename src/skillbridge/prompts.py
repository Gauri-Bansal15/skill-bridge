"""Load prompt templates from the /prompts folder."""
from __future__ import annotations

from pathlib import Path

PROMPT_DIR = Path(__file__).resolve().parents[2] / "prompts"

PROMPT_FILES = {
    "v1": "v1/v1_baseline.md",
    "v2": "v2/v2_structured.md",
    "v3": "v3/v3_rubric.md",
    "final": "final/P1_resume_analysis.md",  # identical to v3; a test keeps them in sync
}
STRUCTURED = {"v2", "v3", "final"}
LABELS = {
    "v1": "v1 - baseline (free text)",
    "v2": "v2 - structured JSON",
    "v3": "v3 - rubric + guardrails (recommended)",
}


def load_template(version: str) -> str:
    if version not in PROMPT_FILES:
        raise ValueError(f"Unknown prompt version '{version}'. Choose from {list(PROMPT_FILES)}")
    return (PROMPT_DIR / PROMPT_FILES[version]).read_text(encoding="utf-8")


def render(version: str, resume: str, job: str) -> str:
    # str.replace (not str.format) because the templates contain JSON braces.
    return load_template(version).replace("{{RESUME}}", resume.strip()).replace("{{JOB_DESCRIPTION}}", job.strip())
