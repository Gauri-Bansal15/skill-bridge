#!/usr/bin/env python3
"""Build the Milestone 2 PDF and the supporting document (Business Model Canvas).

  pip install reportlab
  python docs/build_m2.py            # final build (refuses to run if anything is still FILL_ME)
  python docs/build_m2.py --draft    # preview with a DRAFT banner and warnings

Reads: docs/m2_config.json, prompts/, test-data/outputs/*.json (real Gemini runs), docs/assets/m2/*.png
Writes: docs/M2_<TeamID>_<Title>.pdf and docs/<Title>_BMC.pdf
"""
from __future__ import annotations

import argparse
import glob
import json
import re
import statistics as st
import sys
import textwrap
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (BaseDocTemplate, Frame, Image, KeepTogether, NextPageTemplate, PageBreak, PageTemplate,
                                Paragraph, Preformatted, Spacer, Table, TableStyle)

ROOT = Path(__file__).resolve().parents[1]
DOCS, ASSETS, TD = ROOT / "docs", ROOT / "docs/assets/m2", ROOT / "test-data"
NAVY, TEAL, GREY, LIGHT, RED = colors.HexColor("#1E2761"), colors.HexColor("#0F8B8D"), colors.HexColor("#6B7280"), colors.HexColor("#EEF2F7"), colors.HexColor("#B42318")

ss = getSampleStyleSheet()
BASE = ParagraphStyle("b", parent=ss["Normal"], fontName="Helvetica", fontSize=9.5, leading=13, spaceAfter=5)
SMALL = ParagraphStyle("s", parent=BASE, fontSize=8, leading=10, spaceAfter=0)
TINY = ParagraphStyle("t", parent=BASE, fontSize=7, leading=8.6, spaceAfter=0)
CAP = ParagraphStyle("c", parent=BASE, fontSize=8, leading=10, textColor=GREY, alignment=TA_CENTER, spaceAfter=8)
H1S = ParagraphStyle("h1", parent=BASE, fontName="Helvetica-Bold", fontSize=15, leading=19, textColor=NAVY, spaceBefore=4, spaceAfter=8)
H2S = ParagraphStyle("h2", parent=BASE, fontName="Helvetica-Bold", fontSize=11, leading=14, textColor=TEAL, spaceBefore=8, spaceAfter=4)
H3S = ParagraphStyle("h3", parent=BASE, fontName="Helvetica-Bold", fontSize=9.5, leading=12, textColor=NAVY, spaceBefore=6, spaceAfter=3)
CODE = ParagraphStyle("code", fontName="Courier", fontSize=6.8, leading=8.2, backColor=colors.HexColor("#F3F5F8"), borderPadding=3)
TITLE = ParagraphStyle("title", parent=BASE, fontName="Helvetica-Bold", fontSize=24, leading=28, textColor=NAVY, spaceAfter=6)

REPL = {"\u2013": "-", "\u2014": "-", "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"', "\u2192": "->", "\u2265": ">=", "\u2264": "<=", "\u2022": "-", "\u00a0": " ", "\u2713": "ok"}


def clean(t: str) -> str:
    for k, v in REPL.items():
        t = t.replace(k, v)
    return t.encode("latin-1", "replace").decode("latin-1")


def esc(t: str) -> str:
    return clean(str(t)).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def P(t, style=BASE):
    return Paragraph(esc(t).replace("\n", "<br/>"), style)


def H1(t):
    return Paragraph(esc(t), H1S)


def H2(t):
    return Paragraph(esc(t), H2S)


def H3(t):
    return Paragraph(esc(t), H3S)


def PB(t, style=BASE):  # allows <b>..</b> marker syntax **bold**
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", esc(t))
    return Paragraph(t.replace("\n", "<br/>"), style)


def code(text: str, width=108):
    lines = []
    for line in clean(text).splitlines():
        lines += textwrap.wrap(line, width, subsequent_indent="  ", replace_whitespace=False) or [""]
    return Preformatted("\n".join(lines), CODE)


def table(data, widths, head=True, font=7.6, zebra=True):
    rows = [[c if not isinstance(c, str) else P(c, ParagraphStyle("tc", parent=SMALL, fontSize=font, leading=font + 2)) for c in r] for r in data]
    t = Table(rows, colWidths=[w * cm for w in widths], repeatRows=1 if head else 0)
    style = [("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#C9D1DC")), ("VALIGN", (0, 0), (-1, -1), "TOP"),
             ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3), ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5)]
    if head:
        style += [("BACKGROUND", (0, 0), (-1, 0), NAVY)]
        for j, c in enumerate(data[0]):
            rows[0][j] = P(c, ParagraphStyle("th", parent=SMALL, fontSize=font, leading=font + 2, textColor=colors.white, fontName="Helvetica-Bold"))
    if zebra:
        style += [("ROWBACKGROUNDS", (0, 1 if head else 0), (-1, -1), [colors.white, colors.HexColor("#F6F8FB")])]
    t = Table(rows, colWidths=[w * cm for w in widths], repeatRows=1 if head else 0)
    t.setStyle(TableStyle(style))
    return t


def image(path: Path, max_w=16.5, max_h=11.0):
    from PIL import Image as PILImage
    w, h = PILImage.open(path).size
    s = min(max_w * cm / w, max_h * cm / h)
    return Image(str(path), width=w * s, height=h * s)


# ------------------------------------------------------------------ BMC
def bmc_flowable(width_cm: float):
    def cell(title, items):
        body = "".join(f"- {esc(i)}<br/>" for i in items)
        return Paragraph(f"<font name='Helvetica-Bold' color='#1E2761' size='10'>{esc(title)}</font><br/><font size='9'>{body}</font>", ParagraphStyle("bm", parent=SMALL, leading=11.6))
    kp = cell("KEY PARTNERS", ["Google (Gemini API)", "College placement cells and career counsellors (feedback, pilots)", "GitHub and Streamlit Community Cloud (hosting)", "Employer surveys such as NACE (evidence for what recruiters want)"])
    ka = cell("KEY ACTIVITIES", ["Designing and testing prompts", "Maintaining the scoring rubric and skill list", "Evaluating on labelled resume/job pairs", "Privacy and safety checks", "Collecting student feedback"])
    kr = cell("KEY RESOURCES", ["Gemini API access", "Prompt library (v1-v3) and rubric", "Skill taxonomy and labelled test set", "Streamlit app and offline engine", "Team skills: prompting, Python, testing"])
    vp = cell("VALUE PROPOSITIONS", ["0-100 match score with a visible breakdown", "Shows which skills are demonstrated, only listed, or missing, with a quote from the resume", "Honest suggestions: never tells anyone to claim a skill they lack", "Personal details masked before analysis", "Works offline with no key for demos"])
    cr = cell("CUSTOMER RELATIONSHIPS", ["Self-service, instant feedback", "Open-source: issues and pull requests on GitHub", "Pilot sessions with placement cells (planned)"])
    ch = cell("CHANNELS", ["Web app link (Streamlit)", "GitHub repository", "Campus workshops and batch WhatsApp groups", "Placement cell mailing lists (planned)"])
    cs = cell("CUSTOMER SEGMENTS", ["College students and fresh graduates applying for internships and jobs", "Career switchers", "Placement cells and career counsellors", "Coaching institutes (later)"])
    cost = cell("COST STRUCTURE", ["Gemini API usage (free tier now; paid at scale)", "Hosting (free tier now)", "Team time for prompts, testing and data", "Creating and labelling test data"])
    rev = cell("REVENUE STREAMS (ideas, not yet tested)", ["Free for individual students", "Institutional licence for placement cells (per batch)", "Premium extras: bulk analysis, PDF export"])
    unit = width_cm / 5.0
    data = [[kp, [ka, Spacer(1, 4), kr], vp, [cr, Spacer(1, 4), ch], cs], [cost, "", "", rev, ""]]
    # merge: row 2 -> cost spans cols 0-1 (2 blocks) and revenue spans 2-4
    data[1] = [cost, "", rev, "", ""]
    t = Table(data, colWidths=[unit * cm] * 5, rowHeights=[10.9 * cm, 4.3 * cm])
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.7, NAVY), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("SPAN", (0, 1), (1, 1)), ("SPAN", (2, 1), (4, 1)),
                           ("BACKGROUND", (2, 0), (2, 0), colors.HexColor("#E6F4F4")), ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5), ("TOPPADDING", (0, 0), (-1, -1), 4)]))
    return t


def bmc_story(cfg, width_cm=26.0):
    return [Paragraph(f"Business Model Canvas: {esc(cfg['project_title'])}", ParagraphStyle("bt", parent=H1S, fontSize=14, spaceAfter=2)),
            Paragraph(esc(f"Team {cfg['team_name']} | SCSE4041 Prompt Engineering | Milestone 2 supporting document"), ParagraphStyle("bs", parent=SMALL, textColor=GREY, spaceAfter=6)),
            bmc_flowable(width_cm),
            Spacer(1, 4),
            Paragraph("Note: this canvas describes how Skill Bridge could work as a product. The prototype is a student project; revenue streams and partnerships are ideas we have not tested.", ParagraphStyle("bn", parent=SMALL, textColor=GREY))]


def build_bmc(cfg, out: Path):
    doc = BaseDocTemplate(str(out), pagesize=landscape(A4), leftMargin=1.0 * cm, rightMargin=1.0 * cm, topMargin=0.9 * cm, bottomMargin=0.8 * cm, title="Business Model Canvas", author=cfg["team_name"])
    doc.addPageTemplates([PageTemplate(id="l", frames=[Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="f", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)])])
    doc.build(bmc_story(cfg))


# ------------------------------------------------------------------ data loading
def load_tests(warn):
    best = {}
    for f in sorted(glob.glob(str(TD / "outputs/tests_*.json")), key=lambda p: Path(p).stat().st_mtime):
        for r in json.loads(Path(f).read_text()):
            if str(r.get("engine", "")).startswith("gemini"):
                best[r["id"]] = r
            elif "offline" in str(r.get("engine", "")):
                continue
    cases = json.loads((TD / "test_cases.json").read_text())
    rows = []
    for c in cases:
        r = best.get(c["id"])
        if not r:
            warn(f"test {c['id']} has no real Gemini result yet (run evaluation/run_tests.py)")
            r = {"id": c["id"], "type": c["type"], "input_short": c["input_short"], "expected": c["expected"], "actual_short": "NOT RUN YET", "pass": False, "problems": [], "engine": "none"}
        rows.append(r)
    return rows


def load_iteration(warn):
    recs, model = [], "gemini-3.5-flash"
    for f in glob.glob(str(TD / "outputs/iteration_*.json")):
        d = json.loads(Path(f).read_text())
        if d.get("engine") == "gemini":
            recs += d["records"]
            model = d.get("model", model)
    out = {}
    for v in ("v1", "v2", "v3"):
        rs = [r for r in recs if r["version"] == v and r["ok"]]
        if not rs:
            warn(f"no real Gemini iteration runs for {v} yet (run evaluation/run_iteration_log.py)")
            out[v] = None
            continue
        by_pair = {}
        for r in rs:
            by_pair.setdefault(r["pair"], []).append(r["score"])
        spreads = [max(x) - min(x) for x in by_pair.values() if len(x) > 1 and None not in x]
        unv = [r["unverified_found"] for r in rs if r["unverified_found"] is not None]
        text = f"{sum(r['structured'] for r in rs)}/{len(rs)} runs gave structured JSON. "
        text += "Scores: " + "; ".join(f"{p}: {', '.join('n/a' if s is None else str(s) for s in sc)}" for p, sc in sorted(by_pair.items())) + ". "
        text += f"In accepted score band: {sum(r['in_band'] for r in rs)}/{len(rs)}. "
        if spreads:
            text += f"Largest score spread between repeat runs: {max(spreads)} points. "
        if v != "v1":
            text += f"Evidence warnings: {sum(r['evidence_warnings'] for r in rs)}. "
        if unv:
            text += f"Listed-only skills caught (P5): {round(100 * st.mean(unv))}%."
        out[v] = text.strip()
    return out, model


# ------------------------------------------------------------------ main build
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--draft", action="store_true", help="build a preview even if things are missing")
    a = ap.parse_args()
    cfg = json.loads((DOCS / "m2_config.json").read_text())
    warnings: list[str] = []
    warn = warnings.append

    flat = json.dumps(cfg)
    if "FILL_ME" in flat:
        warn("m2_config.json still contains FILL_ME (team id, faculty name or links)")
    if cfg["reel_seconds"] == 0:
        warn("reel_seconds is 0 (must be 90-150)")
    if sum(m["percent"] for m in cfg["members"]) != 100:
        warn("member percentages do not add up to 100")
    if any("ADD" in m["evidence"] for m in cfg["members"]):
        warn("contribution evidence still says '(commit count: ADD)' - replace with the real commit counts from `git shortlog -sn`")

    tests = load_tests(warn)
    iteration, model = load_iteration(warn)
    shots = sorted(ASSETS.glob("shot_T*.png"))
    if len(shots) < 2:
        warn("fewer than 2 test screenshots (docs/assets/m2/shot_T<n>.png); take screenshots of real app runs")
    repo_img = ASSETS / "repo.png"
    if not repo_img.exists():
        warn("docs/assets/m2/repo.png missing (screenshot of the repository AFTER the restructure)")
        repo_img = ASSETS / "repo_before_m2.png"
    n_prompts = len(list((ROOT / "prompts/final").glob("*.md")))
    if not (ROOT / "prompts/final/P1_resume_analysis.md").exists():
        warn("prompts/final/P1_resume_analysis.md missing")

    if warnings and not a.draft:
        print("Cannot build the final PDF yet. Fix these first (or use --draft to preview):")
        for w in warnings:
            print("  -", w)
        sys.exit(1)

    out_bmc = DOCS / f"{cfg['file_title']}_BMC.pdf"
    build_bmc(cfg, out_bmc)
    out_m2 = DOCS / f"M2_{cfg['team_id']}_{cfg['file_title']}.pdf"

    def on_page(c, d):
        c.saveState()
        c.setFont("Helvetica", 7.5); c.setFillColor(GREY)
        c.drawString(1.8 * cm, 1.0 * cm, clean(f"M2 | {cfg['team_name']} | {cfg['project_title']}"))
        c.drawRightString(A4[0] - 1.8 * cm, 1.0 * cm, f"Page {d.page}")
        if a.draft:
            c.setFillColor(RED); c.setFont("Helvetica-Bold", 9)
            c.drawString(1.8 * cm, A4[1] - 1.0 * cm, "DRAFT - not ready to submit")
        c.restoreState()

    def on_page_l(c, d):
        c.saveState(); c.setFont("Helvetica", 7.5); c.setFillColor(GREY)
        c.drawRightString(landscape(A4)[0] - 1.8 * cm, 0.6 * cm, f"Page {d.page}"); c.restoreState()

    doc = BaseDocTemplate(str(out_m2), pagesize=A4, leftMargin=1.8 * cm, rightMargin=1.8 * cm, topMargin=1.6 * cm, bottomMargin=1.7 * cm,
                          title=f"Milestone 2 - {cfg['project_title']}", author=cfg["team_name"])
    doc.addPageTemplates([
        PageTemplate(id="p", frames=[Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="fp")], onPage=on_page),
        PageTemplate(id="l", pagesize=landscape(A4), frames=[Frame(1.0 * cm, 1.0 * cm, landscape(A4)[0] - 2.0 * cm, landscape(A4)[1] - 1.8 * cm, id="fl", leftPadding=0, rightPadding=0)], onPage=on_page_l),
    ])
    S: list = []
    L = cfg["links"]

    # ---- 1 cover
    S += [Spacer(1, 1.2 * cm), Paragraph("SCSE4041 Prompt Engineering - Mini Project", ParagraphStyle("k", parent=BASE, textColor=TEAL, fontName="Helvetica-Bold", fontSize=11)),
          Paragraph("Milestone 2", TITLE), P("Prompt design, prototype, testing and demonstration", ParagraphStyle("k2", parent=BASE, fontSize=12, textColor=GREY)), Spacer(1, 0.6 * cm),
          H1("1. Cover page"),
          table([["Team ID", cfg["team_id"]], ["Team name", cfg["team_name"]], ["Project title", cfg["project_title"]], ["Batch", cfg["batch"]], ["Faculty", cfg["faculty"]]], [4, 12.4], head=False, font=9, zebra=False),
          Spacer(1, 6), H3("Team members"),
          table([["Name", "Enrollment no.", "Role"]] + [[m["name"], m["enrollment"], m["role"]] for m in cfg["members"]], [6.5, 3.5, 6.4], font=8.5),
          Spacer(1, 6), H3("Links"),
          table([["Prototype", L["prototype"]], ["GitHub repository", L["repository"]], ["Reel", f"{L['reel']}  ({cfg['reel_seconds']} seconds)"]], [4, 12.4], head=False, font=8.5, zebra=False),
          Spacer(1, 6), P("Counts used in the submission form: final prompts = %d; test inputs = %d; prompt versions = 3." % (n_prompts, len(tests)), SMALL), PageBreak()]

    # ---- 2 design
    S += [H1("2. Prompt and solution design"), H2("2(a) Summary")]
    S += [PB("**Problem and users.** Students send one general resume to every job and cannot see how well it matches a posting, which skills are only listed and never shown, or what to improve. Skill Bridge is for college students, fresh graduates and career switchers, and can help placement cells. Employers look for evidence of skills on resumes (NACE Job Outlook 2025), so a skill that is only named in a list is weak."),
          PB("**Input and output.** Input: resume text and one job description. Output: a 0-100 match score with a four-part breakdown (required skills 50, experience/projects 20, education 10, preferred skills 20), matching skills with a quote from the resume, missing skills, skills that are only listed (unverified), and suggestions tied to resume lines."),
          PB(f"**Prompts and steps.** The final solution uses **{n_prompts} prompt** (P1) inside a five-step workflow: mask personal details (code), fill and send P1 (prompt), receive JSON from the model, validate it (code), add up the score and show the report (code). We use one prompt because the five sub-tasks depend on each other and one call keeps the evidence, the classification and the rubric consistent. The arithmetic is done in code, not by the model."),
          PB(f"**Tool and model.** {model} through the Gemini API, with a Streamlit web app and a Python backend. Gemini was chosen because the team has free access through Google AI Studio, it supports JSON output, and it handles two long free-text documents in one call. A rule-based offline engine is included so the app and tests run without a key."),
          PB("**What changed since Milestone 1.** In Milestone 1 we had one baseline prompt and a plan. Since then we built the working app, wrote two further prompt versions (v2 structured JSON, v3 rubric and guardrails), added a privacy filter, a validator that checks quoted evidence against the resume, an offline engine, a 12-test table with a runner script, and a CI workflow.")]
    S += [H2("2(b) Diagrams")]
    for name, cap in [("d1_prompt_workflow.png", "Figure 1. Prompt workflow."), ("d2_task_decomposition.png", "Figure 2. Task decomposition."),
                      ("d3_input_output_flow.png", "Figure 3. Input-output flow."), ("d4_architecture.png", "Figure 4. System architecture (app).")]:
        S += [KeepTogether([image(ASSETS / name, 15.5, 7.2), P(cap, CAP)])]
    final_text = (ROOT / "prompts/final/P1_resume_analysis.md").read_text(encoding="utf-8").strip()
    t1 = TD / "outputs/T1.json"
    sample_in, sample_out = "(run test T1 to fill this in)", "(run test T1 to fill this in)"
    if t1.exists():
        d = json.loads(t1.read_text())
        if d.get("result"):
            res = {k: v for k, v in d["result"].items() if k not in ("privacy", "disclaimer")}
            trimmed = False
            for k in ("matching_skills", "missing_skills", "unverified_skills", "suggestions"):
                if len(res.get(k, [])) > 3:
                    res[k] = res[k][:3]; trimmed = True
            sample_out = json.dumps(res, indent=1, ensure_ascii=False) + ("\n(lists shortened to 3 items; full output in test-data/outputs/T1.json)" if trimmed else "")
            sample_in = f"Resume: {d['case']['resume']} (data/resumes/aarav_mehta.txt)   Job: {d['case']['job']}\n(full texts in test-data/inputs/)"
    S += [PageBreak(), H2("2(c) Prompt sheet"), P("Prompt P1 is the only prompt in the final solution.", SMALL), Spacer(1, 4),
          table([["Field", "Value"],
                 ["Prompt ID and name", "P1 - Resume analysis against a job description (version v3, final)"],
                 ["Step in the workflow", "Step 2 of 5: after personal details are masked, before the JSON is validated"],
                 ["Purpose", "Compare one resume with one job description and return an evidence-based, rubric-scored analysis as JSON"],
                 ["Tool and model", f"Gemini API, model {model}"],
                 ["Settings", "temperature 0.2; response type application/json; request timeout 120 s"],
                 ["System prompt", "None (everything is in the user prompt)"],
                 ["Variables", "{{RESUME}}: the resume text after personal details were masked.  {{JOB_DESCRIPTION}}: the job description text as pasted."],
                 ["Number of examples included", "0 (zero-shot; the rubric and the JSON shape do the work)"],
                 ["Output format", "JSON with matching_skills, missing_skills, unverified_skills, score_breakdown (4 numbers), score_reasoning, suggestions"]], [4.2, 12.2], font=8),
          H3("Full user prompt template (text, file prompts/final/P1_resume_analysis.md)"), code(final_text),
          H3("One sample run (real input and actual output, test T1)"), code(sample_in), Spacer(1, 3), code(sample_out), PageBreak()]

    # ---- 3 implementation
    S += [H1("3. Implementation"), H2("What is built")]
    S += [PB("A working web app (Streamlit) and command-line tool that compare a resume with a job description using Gemini and prompt P1, show a rubric-based score with evidence, and run entirely offline with a rules engine when no key is available. The code is in app.py and src/skillbridge/; prompts are in prompts/; tests in tests/; test inputs and saved outputs in test-data/.")]
    S += [H2("Module status")]
    mods = [["Input form and sample loader", "Paste or load sample resume and job description; options for engine, prompt version, masking", "Working", "app.py"],
            ["Privacy filter", "Masks name, email, phone, links and ID numbers before analysis", "Working", "Name masking bug found by test T7 and fixed"],
            ["Prompt builder", "Loads prompt version v1, v2, v3 or final and fills the variables", "Working", "prompts.py"],
            ["Gemini analysis", "Sends P1 to Gemini, retries on timeouts, parses JSON", "Working", "Needs an API key; free tier allows about 20 requests a day. A quota message is shown and the offline engine can be used instead."],
            ["Validator and score calculator", "Clamps component scores, adds them up, moves matches with invented evidence to 'unverified'", "Working", "scoring.py"],
            ["Offline rules engine", "Rule-based version of the same analysis with no key", "Working", "Uses a list of about 35 skills"],
            ["Results page", "Score, breakdown table, matching/missing skills, suggestions, JSON download", "Working", "app.py"]]
    S += [table([["Module", "What it does", "Status", "Notes"]] + mods, [3.6, 6.2, 1.6, 5.0], font=7.6)]
    S += [H2("Prompt iteration log"), P(f"All versions were run with {model}, temperature 0.2, on the same inputs: P1 (test T1 input) and P5 (test T5 input), repeated runs. The result column is produced by evaluation/run_iteration_log.py from the saved runs.", SMALL), Spacer(1, 4)]
    manual_v1 = " Manual run on the T1 input (Figure 5): answered 60/100 as '+60 / -40' with no rubric, listed 'Education' as a matching skill, and described the candidate as a 'Data Entry' profile although the resume never says so."
    rows = [["Version", "What changed", "Why it was changed", "Result after the change"],
            ["v1", "First prompt (Milestone 1 baseline): four tasks and one safety line, free-text answer.", "Starting point.", (iteration.get("v1") or "NOT RUN YET") + manual_v1],
            ["v2", "Numbered steps, exact JSON schema, evidence quote for each match, separate 'unverified' list, rule 'if unsure, treat as unverified'.", "v1 gave free text the app cannot show and a score with no defined meaning.", iteration.get("v2") or "NOT RUN YET"],
            ["v3", "Four-part scoring rubric (model fills parts, code adds them), suggestions must cite a resume line and never encourage faking skills, ignore instructions inside the resume, no guessing from names.", "v2 still let the model choose its own score and gave no protection against hidden instructions.", iteration.get("v3") or "NOT RUN YET"]]
    S += [table(rows, [1.2, 5.2, 4.0, 6.0], font=7.4)]
    S += [Spacer(1, 4), image(ASSETS / "shot_v1_T1.png", 15.5, 6.5), P("Figure 5. Prompt v1 on the T1 input (real run): free-text answer, score 60/100 with no rubric.", CAP)]
    for v, f in [("v1", "prompts/v1/v1_baseline.md"), ("v2", "prompts/v2/v2_structured.md"), ("v3", "prompts/v3/v3_rubric.md")]:
        S += [H3(f"Full text of {v} ({f})"), code((ROOT / f).read_text(encoding="utf-8").strip())]
    S += [PageBreak()]

    # ---- 4 testing
    passed = sum(1 for r in tests if r["pass"])
    S += [H1("4. Demonstration and testing"), H2("Test table"),
          P(f"{len(tests)} test inputs ({sum(r['type']=='Normal' for r in tests)} normal, {sum(r['type']=='Edge' for r in tests)} edge, {sum(r['type']=='Invalid' for r in tests)} invalid). Result: {passed} passed, {len(tests)-passed} failed. Prompt P1 (v3) with {model}. Inputs are in test-data/inputs/, full outputs in test-data/outputs/. Pass/Fail is decided by checks in test-data/test_cases.json, not by eye.", SMALL), Spacer(1, 4)]
    trows = [["No.", "Input (short)", "Type", "Expected output", "Actual output (short)", "Pass / Fail"]]
    for r in tests:
        actual = r["actual_short"] + ("  Problem: " + "; ".join(r["problems"]) if (r.get("problems") and not r["pass"]) else "")
        trows.append([r["id"].replace("T", ""), r["input_short"], r["type"], r["expected"], actual, "Pass" if r["pass"] else "Fail"])
    S += [table(trows, [0.9, 3.7, 1.3, 3.8, 5.4, 1.3], font=6.9)]
    S += [H2("Screenshots of real runs")]
    for s in shots:
        tid = s.stem.replace("shot_", "")
        row = next((r for r in tests if r["id"] == tid), None)
        S += [KeepTogether([image(s, 15.5, 8.0), P(f"Test {tid.replace('T','')} ({row['input_short'] if row else ''}): real run of the app with Gemini.", CAP)])]
    S += [H2("Known limitations and what we will try next")]
    for lim, nxt in [("The test set is small (12 inputs) and written by us with synthetic resumes.", "Grow to 30+ pairs, including consented, anonymised real resumes."),
                     ("Each test was run once on a free-tier key, and model answers can vary between runs.", "Repeat each test three or more times and report the spread."),
                     ("Plain text only: no PDF resume upload; the offline engine and the evidence check know only about 35 skills.", "Add PDF parsing and a larger skill list in Milestone 3."),
                     ("The score has not been checked against real recruiters, and we have not tested for bias (for example by swapping names).", "Get feedback from a placement officer and run a name-swap test.")]:
        S += [PB(f"- {lim}  **Next:** {nxt}", SMALL), Spacer(1, 2)]
    S += [PageBreak()]

    # ---- 5 repository
    S += [H1("5. Repository"), image(repo_img, 16.4, 9.0), P("Figure 6. The GitHub repository: " + L["repository"], CAP),
          H2("What changed since Milestone 1")]
    for t in ["Built the working Streamlit app, command-line tool and Gemini integration; added an offline rules engine.",
              "Wrote prompt versions v1, v2 and v3 under prompts/ and the final prompt P1 under prompts/final/.",
              "Added a privacy filter, a validator that checks evidence, and automated tests with a GitHub Actions workflow.",
              "Added the 12-test table (test-data/), the prompt-version experiment and their runner scripts, plus a dated CHANGELOG.md.",
              "Fixed a name-masking bug that test T7 exposed (the first line of a resume was always masked)."]:
        S += [PB("- " + t, BASE)]
    S += [NextPageTemplate("l"), PageBreak()]

    # ---- 6 supporting document (landscape)
    S += [Paragraph("6. Supporting document - Business Model Canvas", ParagraphStyle("s6", parent=H1S, fontSize=12, spaceAfter=2))] + bmc_story(cfg, 27.0)[1:]
    S += [NextPageTemplate("p"), PageBreak()]

    # ---- 7 contributions
    S += [H1("7. Team contribution"),
          table([["Member", "Enrollment no.", "Role", "Tasks done in Milestone 2", "Evidence", "Contribution (%)"]] +
                [[m["name"], m["enrollment"], m["role"], m["tasks"], m["evidence"], str(m["percent"])] for m in cfg["members"]], [2.6, 2.2, 2.0, 4.6, 3.8, 1.2], font=7.2),
          Spacer(1, 6), P(f"Total: {sum(m['percent'] for m in cfg['members'])}%. Every member can explain the part listed against their name.", SMALL)]
    doc.build(S)

    print(f"\nBuilt {out_m2.name} and {out_bmc.name}")
    print("\n===== VALUES FOR THE SUBMISSION FORM =====")
    print(f"Q10 prompts in final solution : {n_prompts}")
    print(f"Q14 reel seconds              : {cfg['reel_seconds']}")
    print(f"Q17 test inputs               : {len(tests)}")
    print("Q18 prompt versions           : 3")
    print(f"Q9  model                     : {model} in Google AI Studio / Gemini API")
    print(f"Q21 upload                    : {out_m2.name}")
    print(f"Q16 upload                    : {out_bmc.name}")
    if warnings:
        print("\nDRAFT WARNINGS:")
        for w in warnings:
            print("  -", w)


if __name__ == "__main__":
    main()
