"""Command line interface:  python -m skillbridge.cli --resume R.txt --job J.txt"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .analyzer import analyse
from .camel import camel_case_dict


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Skill Bridge - compare a resume with a job description")
    p.add_argument("--resume", required=True, type=Path)
    p.add_argument("--job", required=True, type=Path)
    p.add_argument("--engine", choices=["offline", "gemini"], default="offline")
    p.add_argument("--prompt", choices=["v1", "v2", "v3"], default="v3")
    p.add_argument("--json", action="store_true", help="print raw JSON")
    p.add_argument("--camel", action="store_true", help="format JSON output keys in camelCase")
    a = p.parse_args(argv)

    res = analyse(a.resume.read_text(encoding="utf-8"), a.job.read_text(encoding="utf-8"), a.engine, a.prompt)
    if a.json:
        payload = camel_case_dict(res) if a.camel else res
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    print(f"Engine: {res['engine']}   Prompt: {res['prompt_version']}")
    if res.get("raw_text"):
        print(res["raw_text"])
        return 0
    print(f"\nMATCH SCORE: {res['match_score']}/100")
    for k, v in (res.get("score_breakdown") or {}).items():
        print(f"  {k:<20} {v}")
    print(f"Why: {res['score_reasoning']}")
    print("\nMatching skills:")
    for m in res["matching_skills"]:
        tag = "demonstrated" if m["demonstrated"] else "listed only"
        print(f"  + {m['skill']} ({tag})")
    print("Missing skills:")
    for m in res["missing_skills"]:
        print(f"  - {m['skill']} [{m['importance']}]")
    print("Suggestions:")
    for s in res["suggestions"]:
        print(f"  * [{s['section']}] {s['suggestion']}")
    print(f"\n{res['disclaimer']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
