from skillbridge.llm import parse_json
from skillbridge.scoring import clamp_breakdown, normalise_result, total_score


def test_total_adds_components_and_clamps():
    assert total_score({"required_skills": 50, "experience_projects": 20, "education": 10, "preferred_skills": 20}) == 100
    # a model that returns 90/50 must not inflate the total
    assert total_score({"required_skills": 90, "experience_projects": 0, "education": 0, "preferred_skills": 0}) == 50
    assert total_score({}) == 0


def test_clamp_handles_garbage():
    assert clamp_breakdown({"required_skills": "abc", "education": -4})["required_skills"] == 0


def test_parse_json_with_fences_and_noise():
    assert parse_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert parse_json('Sure! Here you go: {"a": 2} Hope it helps') == {"a": 2}


def test_invented_evidence_is_moved_to_unverified():
    resume = "Skills: Python\nProjects:\n- Built a result analysis tool in Python"
    raw = {
        "matching_skills": [
            {"skill": "Python", "evidence": "Built a result analysis tool in Python", "demonstrated": True},
            {"skill": "Kubernetes", "evidence": "Deployed a 50-node Kubernetes cluster for production traffic", "demonstrated": True},
        ],
        "score_breakdown": {"required_skills": 25, "experience_projects": 10, "education": 5, "preferred_skills": 0},
    }
    out = normalise_result(raw, resume)
    assert [m["skill"] for m in out["matching_skills"]] == ["Python"]
    assert out["unverified_skills"][0]["skill"] == "Kubernetes"
    assert out["match_score"] == 40
    assert out["warnings"]
