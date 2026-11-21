"""Run the Milestone 2 test table (test-data/test_cases.json) and save real outputs.

  python evaluation/run_tests.py --engine gemini --prompt final --delay 15 --tag mine
  python evaluation/run_tests.py --engine gemini --only T1 T5 --tag part2
  python evaluation/run_tests.py --engine offline          # dry run, no key needed

Each test's full output is saved to test-data/outputs/<id>.json and a summary to
test-data/outputs/tests_<tag>.json. The M2 PDF builder reads those files.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from skillbridge.analyzer import analyse  # noqa: E402
from skillbridge.llm import GeminiClient, is_quota_error  # noqa: E402
from skillbridge.skills import canonical  # noqa: E402

TD = ROOT / "test-data"


def names(items) -> set[str]:
    return {canonical(i.get("skill", "")) for i in items or []}


def evaluate(case: dict, result: dict | None, error: str | None) -> tuple[bool, list[str], str]:
    """Return (passed, problems, short actual-output text)."""
    checks = case["checks"]
    if checks.get("expect_error"):
        ok = bool(error) and "required" in error.lower()
        return ok, ([] if ok else ["no error was raised"]), f"Error shown: {error}" if error else "No error shown"
    if error or result is None:
        return False, [f"run failed: {error}"], f"Run failed: {(error or '')[:90]}"

    matching = names(result["matching_skills"])
    unverified = names(result["unverified_skills"]) | {canonical(m["skill"]) for m in result["matching_skills"] if not m.get("demonstrated", True)}
    claimed = matching | names(result["unverified_skills"])
    score = result["match_score"]
    problems: list[str] = []

    lo_hi = checks.get("score_range")
    if lo_hi and not (lo_hi[0] <= score <= lo_hi[1]):
        problems.append(f"score {score} outside {lo_hi[0]}-{lo_hi[1]}")
    for s in checks.get("must_match", []):
        if canonical(s) not in claimed:
            problems.append(f"did not match '{s}'")
    for s in checks.get("must_miss", []):
        if canonical(s) in claimed:
            problems.append(f"wrongly matched '{s}'")
    for s in checks.get("must_unverified", []):
        if canonical(s) not in unverified:
            problems.append(f"'{s}' not flagged listed-only")
    if checks.get("must_not_match_any") and claimed:
        problems.append("matched skills in nonsense text: " + ", ".join(sorted(claimed)))
    if "privacy_min" in checks and result["privacy"]["total"] < checks["privacy_min"]:
        problems.append(f"only {result['privacy']['total']} personal details masked")
    blob = json.dumps(result)
    for pii in checks.get("pii_strings", []):
        if pii in blob:
            problems.append(f"personal detail '{pii}' leaked into output")

    shown = sorted(s for s in (names(result["matching_skills"])))
    miss = sorted(names(result["missing_skills"]))
    short = f"Score {score}. Matched: {', '.join(shown) or 'none'}. Missing: {', '.join(miss[:4]) or 'none'}."
    if unverified:
        short += f" Listed-only: {', '.join(sorted(unverified)[:4])}."
    if checks.get("privacy_min"):
        short += f" Masked {result['privacy']['total']} personal details."
    return not problems, problems, short[:230]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", choices=["offline", "gemini"], default="gemini")
    ap.add_argument("--prompt", default="final", choices=["v1", "v2", "v3", "final"])
    ap.add_argument("--only", nargs="*", help="run only these test ids, e.g. T1 T5")
    ap.add_argument("--delay", type=float, default=15.0, help="seconds between Gemini calls (free tier: 5 per minute)")
    ap.add_argument("--tag", default="run1")
    a = ap.parse_args()

    cases = json.loads((TD / "test_cases.json").read_text())
    if a.only:
        cases = [c for c in cases if c["id"] in a.only]
    client = GeminiClient() if a.engine == "gemini" else None
    (TD / "outputs").mkdir(exist_ok=True)

    rows = []
    for case in cases:
        resume = case.get("resume_inline")
        if resume is None:
            resume = (TD / "inputs" / case["resume"]).read_text(encoding="utf-8")
        job = (TD / "inputs" / case["job"]).read_text(encoding="utf-8")
        result, error = None, None
        try:
            result = analyse(resume, job, engine=a.engine, prompt_version=a.prompt, client=client)
        except Exception as exc:  # noqa: BLE001 - we want to record every failure
            error = str(exc)
        passed, problems, short = evaluate(case, result, error)
        row = {"id": case["id"], "type": case["type"], "input_short": case["input_short"], "expected": case["expected"],
               "actual_short": short, "pass": passed, "problems": problems,
               "engine": (result or {}).get("engine", a.engine), "prompt_version": a.prompt,
               "score": (result or {}).get("match_score"), "evidence_warnings": sum("evidence" in w.lower() for w in (result or {}).get("warnings", []))}
        rows.append(row)
        (TD / "outputs" / f"{case['id']}.json").write_text(json.dumps({"case": case, "result": result, "error": error, "row": row}, indent=2, ensure_ascii=False))
        print(f"{case['id']:<4}{case['type']:<8}{'PASS' if passed else 'FAIL':<6}{short}")
        for p in problems:
            print(f"        - {p}")
        if error and is_quota_error(error):
            print("\nStopped: Gemini quota used up. Wait for the daily reset (or use another key) and rerun with --only for the remaining tests.")
            break
        if a.engine == "gemini" and case["id"] != "T12":
            time.sleep(a.delay)

    (TD / "outputs" / f"tests_{a.tag}.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False))
    print(f"\n{sum(r['pass'] for r in rows)}/{len(rows)} passed. Saved to test-data/outputs/tests_{a.tag}.json")


if __name__ == "__main__":
    main()
