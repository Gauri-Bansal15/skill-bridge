from streamlit.testing.v1 import AppTest

from conftest import ROOT


def test_app_runs_and_analyses_offline():
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
    assert not at.exception
    at.session_state["resume"] = (ROOT / "data/resumes/aarav_mehta.txt").read_text()
    at.session_state["job"] = (ROOT / "data/jobs/ai_ml_intern.txt").read_text()
    at.button[0].click().run()
    assert not at.exception
    assert at.metric[0].value == "62 / 100"


def test_empty_input_shows_error():
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
    at.button[0].click().run()
    assert at.error


def test_app_interactive_features_and_camel_case():
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
    at.session_state["resume"] = (ROOT / "data/resumes/aarav_mehta.txt").read_text()
    at.session_state["job"] = (ROOT / "data/jobs/ai_ml_intern.txt").read_text()
    at.button[0].click().run()
    assert not at.exception
    assert len(at.tabs) == 6
    assert at.metric[0].label == "MatchScore"
    assert at.metric[0].value == "62 / 100"
