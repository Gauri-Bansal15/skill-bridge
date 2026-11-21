"""Measure prompt versions v1, v2, v3 on the same inputs (for the Milestone 2 iteration log).

  python evaluation/run_iteration_log.py --pairs P1 P5 --runs 2 --delay 15 --tag mine
  python evaluation/run_iteration_log.py --versions v2 v3 --pairs P1 --runs 2 --tag extra

Free-tier note: this makes len(versions) x len(pairs) x runs Gemini calls (default 3 x 2 x 2 = 12).
Results go to test-data/outputs/iteration_<tag>.json; v1's raw free-text answers are saved too.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from skillbridge.analyzer import analyse  # noqa: E402
from skillbridge.llm import GeminiClient, is_quota_error  # noqa: E402
from skillbridge.skills import canonical  # noqa: E402

TD = ROOT / "test-data"


def score_from_text(text: str) -> int | None:
    """v1 answers in free text: pull out the first 'NN / 100' (or 'NN/100')."""
    m = re.search(r"(\d{1,3})\s*(?:/|out of)\s*100", text)
    return int(m.group(1)) if m else None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", choices=["offline", "gemini"], default="gemini")
    ap.add_argument("--versions", nargs="+", default=["v1", "v2", "v3"])
    ap.add_argument("--pairs", nargs="+", default=["P1", "P5"])
    ap.add_argument("--runs", type=int, default=2)
    ap.add_argument("--delay", type=float, default=15.0)
    ap.add_argument("--tag", default="run1")
    a = ap.parse_args()

    pairs = {p["id"]: p for p in json.loads((ROOT / "data/eval_pairs.json").read_text())}
    client = GeminiClient() if a.engine == "gemini" else None
    out_dir = TD / "outputs"
    out_dir.mkdir(exist_ok=True)
    records, stop = [], False

    for v in a.versions:
        for pid in a.pairs:
            pair = pairs[pid]
            resume = (ROOT / "data/resumes" / pair["resume"]).read_text(encoding="utf-8")
            job = (ROOT / "data/jobs" / pair["job"]).read_text(encoding="utf-8")
            lo, hi = pair["gold"]["score_band"]
            for k in range(a.runs):
                rec = {"version": v, "pair": pid, "run": k + 1, "ok": False, "score": None, "in_band": False,
                       "structured": False, "evidence_warnings": 0, "unverified_found": None, "error": None}
                try:
                    res = analyse(resume, job, engine=a.engine, prompt_version=v, client=client)
                    if res.get("raw_text") is not None:  # v1 free text
                        (out_dir / f"v1_raw_{pid}_run{k+1}_{a.tag}.txt").write_text(res["raw_text"], encoding="utf-8")
                        rec.update(ok=True, score=score_from_text(res["raw_text"]), structured=False)
                    else:
                        unv = {canonical(s["skill"]) for s in res["unverified_skills"]}
                        gold_unv = {canonical(s) for s in pair["gold"]["unverified"]}
                        rec.update(ok=True, score=res["match_score"], structured=True,
                                   evidence_warnings=sum("evidence" in w.lower() for w in res.get("warnings", [])),
                                   unverified_found=(len(unv & gold_unv) / len(gold_unv)) if gold_unv else None)
                    rec["in_band"] = rec["score"] is not None and lo <= rec["score"] <= hi
                except Exception as exc:  # noqa: BLE001
                    rec["error"] = str(exc)[:160]
                    stop = is_quota_error(exc)
                records.append(rec)
                print(f"[{v}] {pid} run {k+1}/{a.runs}: " + (f"score {rec['score']}  structured={rec['structured']}  in_band={rec['in_band']}" if rec["ok"] else f"FAILED {rec['error']}"), flush=True)
                if stop:
                    break
                if a.engine == "gemini":
                    time.sleep(a.delay)
            if stop:
                break
        if stop:
            print("\nStopped: Gemini quota used up. Rerun later with --versions / --pairs for the missing ones and a new --tag.")
            break

    model = getattr(client, "model", "offline-rules")
    (out_dir / f"iteration_{a.tag}.json").write_text(json.dumps({"engine": a.engine, "model": model, "records": records}, indent=2))
    print(f"\nSaved test-data/outputs/iteration_{a.tag}.json  ({sum(r['ok'] for r in records)}/{len(records)} runs OK)")


if __name__ == "__main__":
    main()
