"""Remove personal details from a resume before it is sent to any AI service."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

_RULES: list[tuple[str, re.Pattern, str]] = [
    ("email", re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+"), "[EMAIL]"),
    ("url", re.compile(r"(?:https?://|www\.)\S+|(?:linkedin|github)\.com/\S*", re.I), "[LINK]"),
    ("phone", re.compile(r"(?<![\d-])(?:\+\d{1,3}[\s-]?)?(?:\d{5}[\s-]?\d{5}|\d{3}[\s-]\d{3}[\s-]\d{4})(?![\d-])"), "[PHONE]"),
    ("id_number", re.compile(r"\b[A-Za-z]\d{2}[A-Za-z]{3,8}\d{3,5}\b"), "[ID]"),
]


@dataclass
class RedactionReport:
    counts: dict[str, int] = field(default_factory=dict)

    @property
    def total(self) -> int:
        return sum(self.counts.values())


def anonymise(text: str, redact_first_line: bool = True) -> tuple[str, RedactionReport]:
    """Return (clean_text, report).

    Emails, links, phone numbers and student/admission IDs are masked. By
    default the first line (usually the candidate's name) is masked too.
    """
    report = RedactionReport()
    for name, pattern, token in _RULES:
        text, n = pattern.subn(token, text)
        if n:
            report.counts[name] = n
    if redact_first_line:
        lines = text.splitlines()
        if lines and lines[0].strip() and not lines[0].strip().startswith("["):
            lines[0] = "[CANDIDATE NAME]"
            report.counts["name"] = 1
            text = "\n".join(lines)
    return text, report
