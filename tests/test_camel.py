"""Unit tests for camelCase and PascalCase utilities."""
from skillbridge.camel import (
    camel_case_dict,
    camelCaseDict,
    pascal_case_dict,
    to_camel_case,
    to_pascal_case,
    to_snake_case,
    toCamelCase,
    toPascalCase,
    toSnakeCase,
)


def test_string_conversions():
    assert to_camel_case("match_score") == "matchScore"
    assert toCamelCase("required_skills") == "requiredSkills"
    assert to_camel_case("experience-projects") == "experienceProjects"
    assert to_camel_case("Matching Skills") == "matchingSkills"

    assert to_pascal_case("match_score") == "MatchScore"
    assert toPascalCase("score_breakdown") == "ScoreBreakdown"
    assert to_pascal_case("matching skills") == "MatchingSkills"

    assert to_snake_case("matchScore") == "match_score"
    assert toSnakeCase("RequiredSkills") == "required_skills"


def test_nested_dict_camel_casing():
    data = {
        "match_score": 75,
        "score_breakdown": {
            "required_skills": 40.0,
            "experience_projects": 15.0,
        },
        "matching_skills": [
            {"skill_name": "Python", "is_demonstrated": True, "quoted_evidence": "Wrote script in Python"}
        ],
    }
    converted = camel_case_dict(data)
    assert converted["matchScore"] == 75
    assert converted["scoreBreakdown"]["requiredSkills"] == 40.0
    assert converted["scoreBreakdown"]["experienceProjects"] == 15.0
    assert converted["matchingSkills"][0]["skillName"] == "Python"
    assert converted["matchingSkills"][0]["isDemonstrated"] is True
    assert converted["matchingSkills"][0]["quotedEvidence"] == "Wrote script in Python"

    # Alias check
    assert camelCaseDict(data) == converted


def test_pascal_case_dict():
    data = {"match_score": 80, "score_breakdown": {"education": 10}}
    converted = pascal_case_dict(data)
    assert converted["MatchScore"] == 80
    assert converted["ScoreBreakdown"]["Education"] == 10

