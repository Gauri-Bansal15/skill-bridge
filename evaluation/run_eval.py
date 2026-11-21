"""Evaluate an engine / prompt version against the hand-labelled pairs.

Examples
  python evaluation/run_eval.py --engine offline
  python evaluation/run_eval.py --engine gemini --versions v2 v3 --runs 3
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics as st
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from skillbridge.analyzer import analyse  # noqa: E402
from skillbridge.llm import GeminiClient  # noqa: E402
from skillbridge.skills import canonical  # noqa: E402


def prf(pred: set[str], gold: set[str]) -> tuple[float, float, float]:
    tp = len(pred & gold)
    p = tp / len(pred) if pred else (1.0 if not gold else 0.0)
    r = tp / len(gold) if gold else 1.0
    f = 2 * p * r / (p + r) if (p + r) else 0.0
    return p, r, f


def recall(pred: set[str], gold: set[str]) -> float:
    return len(pred & gold) / len(gold) if gold else 1.0


def lower(items) -> set[str]:
    return {canonical(i) for i in items}


def run_one(pair: dict, engine: str, version: str, client) -> dict:
    resume = (ROOT / "data/resumes" / pair["resume"]).read_text(encoding="utf-8")
    job = (ROOT / "data/jobs" / pair["job"]).read_text(encoding="utf-8")
    gold = pair["gold"]
    try:
        res = analyse(resume, job, engine=engine, prompt_version=version, client=client)
        valid = res.get("match_score") is not None
    except Exception as exc:  # invalid JSON, API error...
        return {"valid": False, "error": str(exc)[:120]}
    if not valid:
        return {"valid": False, "error": "free text, no structured output"}
    # "matching" = skills the resume claims: demonstrated ones plus listed-only ones
    pred_match = lower(m["skill"] for m in res["matching_skills"]) | lower(m["skill"] for m in res["unverified_skills"])
    pred_miss = lower(m["skill"] for m in res["missing_skills"])
    pred_unv = lower(m["skill"] for m in res["unverified_skills"])
    p, r, f = prf(pred_match, lower(gold["matching"]))
    lo, hi = gold["score_band"]
    return {
        "valid": True, "score": res["match_score"], "in_band": lo <= res["match_score"] <= hi,
        "match_p": p, "match_r": r, "match_f1": f,
        "missing_recall": recall(pred_miss, lower(gold["missing"])),
        "unverified_recall": recall(pred_unv, lower(gold["unverified"])),
        "evidence_warnings": sum("evidence" in w.lower() for w in res.get("warnings", [])),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", choices=["offline", "gemini"], default="offline")
    ap.add_argument("--versions", nargs="+", default=["v3"])
    ap.add_argument("--runs", type=int, default=1, help="repeats per pair (use >=3 with Gemini to measure consistency)")
    ap.add_argument("--delay", type=float, default=15.0, help="seconds between Gemini calls (free tier: 5 per minute)")
    ap.add_argument("--pairs", nargs="*", help="only these pair ids, e.g. P1 P5")
    ap.add_argument("--tag", default="", help="suffix for the results file")
    a = ap.parse_args()

    pairs = json.loads((ROOT / "data/eval_pairs.json").read_text())
    if a.pairs:
        pairs = [p for p in pairs if p["id"] in a.pairs]
    client = GeminiClient() if a.engine == "gemini" else None
    versions = a.versions if a.engine == "gemini" else ["n/a"]

    rows = []
    for v in versions:
        for pair in pairs:
            runs = []
            for k in range(a.runs):
                r = run_one(pair, a.engine, v, client)
                runs.append(r)
                print(f"[{v}] {pair['id']} run {k+1}/{a.runs}: " + (f"score {r['score']}" if r["valid"] else "FAILED: " + r.get("error", "")), flush=True)
                if a.engine == "gemini":
                    time.sleep(a.delay)
            ok = [r for r in runs if r["valid"]]
            row = {"engine": a.engine, "version": v, "pair": pair["id"], "note": pair["note"],
                   "valid_rate": len(ok) / len(runs)}
            if ok:
                scores = [r["score"] for r in ok]
                row.update(
                    score=round(st.mean(scores), 1),
                    score_std=round(st.pstdev(scores), 2) if len(scores) > 1 else 0.0,
                    gold_band=f"{pair['gold']['score_band'][0]}-{pair['gold']['score_band'][1]}",
                    in_band=round(st.mean(r["in_band"] for r in ok), 2),
                    match_f1=round(st.mean(r["match_f1"] for r in ok), 2),
                    missing_recall=round(st.mean(r["missing_recall"] for r in ok), 2),
                    unverified_recall=round(st.mean(r["unverified_recall"] for r in ok), 2),
                    evidence_warnings=sum(r["evidence_warnings"] for r in ok),
                )
            rows.append(row)

    out = ROOT / "evaluation/results"
    out.mkdir(exist_ok=True)
    tag = (a.engine if a.engine == "offline" else "gemini_" + "_".join(versions)) + (("_" + a.tag) if a.tag else "")
    fields = ["engine", "version", "pair", "note", "valid_rate", "score", "score_std", "gold_band", "in_band",
              "match_f1", "missing_recall", "unverified_recall", "evidence_warnings"]
    with open(out / f"{tag}.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    print(f"{'ver':<5}{'pair':<5}{'score':>7}{'band':>9}{'inBand':>8}{'F1':>6}{'missR':>7}{'unvR':>6}{'valid':>7}")
    for r in rows:
        print(f"{r['version']:<5}{r['pair']:<5}{r.get('score','-'):>7}{r.get('gold_band','-'):>9}{r.get('in_band','-'):>8}"
              f"{r.get('match_f1','-'):>6}{r.get('missing_recall','-'):>7}{r.get('unverified_recall','-'):>6}{r['valid_rate']:>7}")
    good = [r for r in rows if "score" in r]
    if good:
        print(f"\nMEAN  in-band={st.mean(r['in_band'] for r in good):.2f}  match-F1={st.mean(r['match_f1'] for r in good):.2f}  "
              f"missing-recall={st.mean(r['missing_recall'] for r in good):.2f}  "
              f"unverified-recall={st.mean(r['unverified_recall'] for r in good):.2f}")
    print(f"\nSaved to evaluation/results/{tag}.csv")


if __name__ == "__main__":
    main()
