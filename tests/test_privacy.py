from skillbridge.privacy import anonymise


def test_masks_contact_details():
    text = "Jane Doe\nEmail: jane.doe@example.com  Phone: +91 98765 43210\nGitHub: github.com/janedoe\nID S24CSEU0778"
    clean, report = anonymise(text)
    assert "jane.doe@example.com" not in clean
    assert "98765" not in clean
    assert "github.com/janedoe" not in clean
    assert "S24CSEU0778" not in clean
    assert clean.splitlines()[0] == "[CANDIDATE NAME]"
    assert report.total >= 5


def test_does_not_touch_years_or_scores():
    clean, _ = anonymise("Name\nB.Tech 2024-2028, reached 98% accuracy, 2020-2023", redact_first_line=False)
    assert "2024-2028" in clean and "98%" in clean and "2020-2023" in clean


def test_first_line_is_masked_only_when_it_is_a_name():
    # regression found by M2 test T7: "Skills: Python" used to be masked as a name
    clean, report = anonymise("Skills: Python")
    assert clean == "Skills: Python" and "name" not in report.counts
    clean, report = anonymise("Gauri Test\nSkills: Python")
    assert clean.splitlines()[0] == "[CANDIDATE NAME]" and report.counts["name"] == 1
    clean, _ = anonymise("Education\nB.Tech CSE")
    assert clean.startswith("Education")
