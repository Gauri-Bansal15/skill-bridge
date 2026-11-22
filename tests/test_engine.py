import json

try:
    import pytest
except ImportError:
    class _PytestFallback:
        class mark:
            @staticmethod
            def parametrize(*args, **kwargs):
                def decorator(fn):
                    return fn
                return decorator

        @staticmethod
        def raises(exc):
            class _RaisesContext:
                def __enter__(self):
                    return self

                def __exit__(self, exc_type, exc_val, exc_tb):
                    return exc_type is not None and issubclass(exc_type, exc)

            return _RaisesContext()

    pytest = _PytestFallback()

from conftest import ROOT, read
from skillbridge.analyzer import analyse
from skillbridge.offline import split_job
from skillbridge.prompts import render
from skillbridge.skills import find_skills

PAIRS = json.loads((ROOT / "data/eval_pairs.json").read_text())


def test_java_is_not_javascript():
    assert find_skills("I know JavaScript") == ["JavaScript"]


def test_job_split_required_and_preferred():
    req, pref = split_job(read("jobs", "ai_ml_intern.txt"))
    assert req == ["Python", "SQL", "machine learning", "data analysis"]
    assert pref == ["TensorFlow", "PyTorch", "Git"]


@pytest.mark.parametrize("pair", PAIRS, ids=[p["id"] for p in PAIRS])
def test_offline_matches_gold_labels(pair=None):
    pairs_to_test = [pair] if pair else PAIRS
    for p in pairs_to_test:
        res = analyse(read("resumes", p["resume"]), read("jobs", p["job"]), engine="offline")
        lo, hi = p["gold"]["score_band"]
        assert lo <= res["match_score"] <= hi
        assert {m["skill"] for m in res["matching_skills"]} == set(p["gold"]["matching"])
        assert {m["skill"] for m in res["unverified_skills"]} == set(p["gold"]["unverified"])


def test_listed_only_skills_score_below_demonstrated():
    job = read("jobs", "ai_ml_intern.txt")
    honest = analyse(read("resumes", "aarav_mehta.txt"), job)
    padded = analyse(read("resumes", "meera_iyer.txt"), job)
    assert len(padded["matching_skills"]) > len(honest["matching_skills"])  # more claims...
    assert padded["match_score"] < honest["match_score"]  # ...but less proof


def test_personal_data_is_masked_before_analysis():
    resume = "Test Person\nEmail: t@x.com\nSkills: Python\nProjects:\n- Built a Python tool"
    res = analyse(resume, "Required skills: Python", engine="offline")
    assert res["privacy"]["counts"]["email"] == 1


def test_prompt_rendering_has_no_leftover_placeholders():
    for v in ("v1", "v2", "v3"):
        p = render(v, "RESUME TEXT", "JOB TEXT")
        assert "RESUME TEXT" in p and "JOB TEXT" in p and "{{" not in p


def test_empty_input_rejected():
    with pytest.raises(ValueError):
        analyse("", "job")


class FakeClient:
    model = "fake"

    def __init__(self, reply):
        self.reply = reply

    def generate(self, prompt, json_mode=True):
        return self.reply


def test_gemini_path_with_fake_client():
    reply = json.dumps({
        "matching_skills": [{"skill": "Python", "evidence": "Built a Python tool", "demonstrated": True}],
        "missing_skills": [], "unverified_skills": [],
        "score_breakdown": {"required_skills": 50, "experience_projects": 20, "education": 0, "preferred_skills": 0},
        "score_reasoning": "ok", "suggestions": [],
    })
    resume = "Name\nSkills: Python\n- Built a Python tool"
    res = analyse(resume, "Required: Python", engine="gemini", prompt_version="v3", client=FakeClient(reply))
    assert res["match_score"] == 70 and res["engine"].startswith("gemini")


def test_gemini_v1_returns_free_text():
    res = analyse("Name\nPython", "Python", engine="gemini", prompt_version="v1", client=FakeClient("blah"))
    assert res["raw_text"] == "blah" and res["match_score"] is None
