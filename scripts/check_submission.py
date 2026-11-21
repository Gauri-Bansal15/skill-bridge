#!/usr/bin/env python3
"""Pre-submission checklist for Milestone 2. Run from the repo root:  python scripts/check_submission.py

Checks the things the guidelines say lose marks: wrong folder layout, visible API keys, leftover placeholders,
missing real test runs, missing screenshots, bad file names, numbers that do not match, no team commits.
"""
from __future__ import annotations

import glob
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ok_count, bad = 0, []


def check(cond: bool, msg: str, fix: str = "") -> None:
    global ok_count
    if cond:
        ok_count += 1
        print(f"  ok    {msg}")
    else:
        bad.append(msg)
        print(f"  FAIL  {msg}" + (f"\n          -> {fix}" if fix else ""))


def read(p: str) -> str:
    return (ROOT / p).read_text(encoding="utf-8", errors="ignore")


print("1. Folder layout required by the guidelines")
for d in ("prompts/v1", "prompts/v2", "prompts/v3", "prompts/final", "code", "test-data", "docs"):
    check((ROOT / d).is_dir() and any((ROOT / d).iterdir()), f"{d}/ exists and is not empty")
for f in ("README.md", "CHANGELOG.md"):
    check((ROOT / f).is_file(), f"{f} exists")
check(read("prompts/final/P1_resume_analysis.md") == read("prompts/v3/v3_rubric.md"), "final prompt P1 is identical to v3")

print("\n2. Secrets (an API key anywhere = 0 for the repository)")
leaks = []
for p in ROOT.rglob("*"):
    if p.is_file() and not any(x in p.parts for x in (".git", ".venv", "__pycache__", ".pytest_cache", "node_modules")) and p.suffix not in (".png", ".pdf", ".pptx", ".docx", ".zip"):
        try:
            txt = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if re.search(r"AIza[0-9A-Za-z_\-]{30,}", txt):
            leaks.append(str(p.relative_to(ROOT)))
        if p.name != ".env.example" and re.search(r"GEMINI_API_KEY\s*=\s*['\"]?[A-Za-z0-9_\-]{20,}", txt):
            leaks.append(str(p.relative_to(ROOT)))
check(not leaks, "no API key found in any file", f"remove it from: {', '.join(sorted(set(leaks)))} and revoke the key in AI Studio")
check(not (ROOT / ".env").exists() or ".env" in read(".gitignore"), ".env is git-ignored")

print("\n3. Placeholders")
for f in ("README.md", "docs/m2_config.json", "CHANGELOG.md", "docs/DEMO.md"):
    if (ROOT / f).exists():
        t = read(f)
        check(not re.search(r"FILL_ME|PROTOTYPE_URL_HERE|<your-username>|commit count: ADD", t), f"no placeholders left in {f}", "replace FILL_ME / PROTOTYPE_URL_HERE / <your-username> / '(commit count: ADD)'")

print("\n4. Real test runs and counts")
cfg = json.loads(read("docs/m2_config.json"))
rows = {}
for f in sorted(glob.glob(str(ROOT / "test-data/outputs/tests_*.json")), key=lambda p: Path(p).stat().st_mtime):
    for r in json.loads(Path(f).read_text()):
        if str(r.get("engine", "")).startswith("gemini"):
            rows[r["id"]] = r
check(len(rows) >= 10, f"{len(rows)} tests have real Gemini results (need >= 10; the table has 12)", "python evaluation/run_tests.py --engine gemini --tag mine")
check(sum(r["type"] == "Edge" for r in rows.values()) >= 3, "at least 3 edge cases have real results")
check(any(r["type"] == "Invalid" for r in rows.values()), "at least 1 invalid-input test has a real result")
it = []
for f in glob.glob(str(ROOT / "test-data/outputs/iteration_*.json")):
    d = json.loads(Path(f).read_text())
    if d.get("engine") == "gemini":
        it += d["records"]
for v in ("v1", "v2", "v3"):
    check(any(r["version"] == v and r["ok"] for r in it), f"iteration log has real Gemini runs for {v}", "python evaluation/run_iteration_log.py --tag mine")
check(len(list((ROOT / "test-data/inputs").glob("*.txt"))) >= 8, "test inputs are saved in test-data/inputs/")

print("\n5. Config, reel and contribution table")
check(cfg["team_id"] not in ("", "FILL_ME"), "team id is set")
check(cfg["faculty"] not in ("", "FILL_ME"), "faculty name is set")
check(all(v not in ("", "FILL_ME") for v in cfg["links"].values()), "prototype, repository and reel links are set")
check(90 <= cfg["reel_seconds"] <= 150, f"reel length {cfg['reel_seconds']} s is within 90-150")
check(sum(m["percent"] for m in cfg["members"]) == 100, "contribution percentages add up to 100")
check(all(m["tasks"].strip() and m["evidence"].strip() for m in cfg["members"]), "every member has a task and evidence")

print("\n6. Screenshots and PDFs")
check(len(list((ROOT / "docs/assets/m2").glob("shot_T*.png"))) >= 2, "at least 2 test screenshots (docs/assets/m2/shot_T<n>.png)")
check((ROOT / "docs/assets/m2/repo.png").exists(), "repository screenshot docs/assets/m2/repo.png (taken after the restructure)")
m2 = ROOT / f"docs/M2_{cfg['team_id']}_{cfg['file_title']}.pdf"
bmc = ROOT / f"docs/{cfg['file_title']}_BMC.pdf"
for p in (m2, bmc):
    check(p.exists() and p.stat().st_size < 10 * 1024 * 1024, f"{p.name} exists and is under 10 MB", "python docs/build_m2.py")

print("\n7. Git history (progress since Milestone 1, and who did what)")
try:
    log = subprocess.run(["git", "-C", str(ROOT), "shortlog", "-sne", "--no-merges", "HEAD"], capture_output=True, text=True, check=True).stdout
    authors = [l for l in log.splitlines() if l.strip()]
    check(len(authors) >= len(cfg["members"]), f"{len(authors)} different commit authors (team has {len(cfg['members'])})", "every member must push real commits from their own account")
    ncommits = int(subprocess.run(["git", "-C", str(ROOT), "rev-list", "--count", "HEAD"], capture_output=True, text=True).stdout.strip() or 0)
    check(ncommits >= 8, f"{ncommits} commits so far")
    status = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain"], capture_output=True, text=True).stdout.strip()
    check(not status, "everything is committed (nothing left uncommitted)", "git add . && git commit && git push")
except Exception:  # noqa: BLE001
    check(False, "git history readable")
check(len(re.findall(r"^## .*20\d\d-\d\d-\d\d", read("CHANGELOG.md"), re.M)) >= 3, "CHANGELOG.md has at least 3 dated entries")

print(f"\n{ok_count} checks passed, {len(bad)} failed.")
if bad:
    print("Fix the FAIL items above, then run this again. Do not submit until it is clean.")
    sys.exit(1)
print("All clear. Now open every link in a private/incognito window one last time.")
