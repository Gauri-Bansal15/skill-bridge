"""CamelCase conversion utilities for SkillBridge.

Provides helpers to convert strings, dictionary keys, and complex nested data
structures between snake_case, camelCase, and PascalCase.
"""
from __future__ import annotations

import re
from typing import Any


def to_camel_case(s: str) -> str:
    """Convert snake_case, kebab-case, or space-separated string to lowerCamelCase.

    Examples:
        to_camel_case("match_score") -> "matchScore"
        to_camel_case("required_skills") -> "requiredSkills"
        to_camel_case("Matching Skills") -> "matchingSkills"
    """
    if not s:
        return s
    # If already strict camelCase (starts with lowercase, no separators, has uppercase):
    if not any(c in s for c in "_ -") and s[0].islower():
        return s
    words = [w for w in re.split(r"[\s_\-]+", s) if w]
    if not words:
        return s
    return words[0].lower() + "".join(w.capitalize() for w in words[1:])


# CamelCase alias
toCamelCase = to_camel_case


def to_pascal_case(s: str) -> str:
    """Convert snake_case, kebab-case, or space-separated string to UpperCamelCase / PascalCase.

    Examples:
        to_pascal_case("match_score") -> "MatchScore"
        to_pascal_case("required_skills") -> "RequiredSkills"
        to_pascal_case("matching skills") -> "MatchingSkills"
    """
    if not s:
        return s
    words = [w for w in re.split(r"[\s_\-]+", s) if w]
    if not words:
        return s
    return "".join(w.capitalize() for w in words)


# PascalCase alias
toPascalCase = to_pascal_case


def to_snake_case(s: str) -> str:
    """Convert camelCase or PascalCase string to snake_case.

    Examples:
        to_snake_case("matchScore") -> "match_score"
        to_snake_case("RequiredSkills") -> "required_skills"
    """
    if not s:
        return s
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", s)
    s2 = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1)
    return re.sub(r"[\s\-]+", "_", s2).lower()


# SnakeCase alias
toSnakeCase = to_snake_case


def camel_case_dict(data: Any) -> Any:
    """Recursively convert all dictionary keys to camelCase.

    Accepts dicts, lists, and primitives, returning a new data structure
    where every dict key is converted to lowerCamelCase.
    """
    if isinstance(data, dict):
        return {to_camel_case(str(k)): camel_case_dict(v) for k, v in data.items()}
    if isinstance(data, list):
        return [camel_case_dict(item) for item in data]
    return data


# CamelCaseDict alias
camelCaseDict = camel_case_dict


def pascal_case_dict(data: Any) -> Any:
    """Recursively convert all dictionary keys to PascalCase (UpperCamelCase)."""
    if isinstance(data, dict):
        return {to_pascal_case(str(k)): pascal_case_dict(v) for k, v in data.items()}
    if isinstance(data, list):
        return [pascal_case_dict(item) for item in data]
    return data


# PascalCaseDict alias
pascalCaseDict = pascal_case_dict

