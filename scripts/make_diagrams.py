"""Draw the four Milestone 2 diagrams (matplotlib). Run: python scripts/make_diagrams.py"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

OUT = Path(__file__).resolve().parents[1] / "docs/assets/m2"
OUT.mkdir(parents=True, exist_ok=True)
NAVY, TEAL, AMBER, GREY, LIGHT, CORAL = "#1E2761", "#0F8B8D", "#F2A541", "#6B7280", "#EEF2F7", "#D95D39"


def canvas(w, h):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, w); ax.set_ylim(0, h); ax.axis("off")
    return fig, ax


def box(ax, x, y, w, h, text, fc=LIGHT, tc=NAVY, fs=9, bold=True, ec=NAVY):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08", fc=fc, ec=ec, lw=1.1))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=tc, fontweight="bold" if bold else "normal", linespacing=1.25)


def arrow(ax, x1, y1, x2, y2, color=GREY):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="-|>", color=color, lw=1.4))


def legend(ax, x, y):
    for i, (c, t) in enumerate([(TEAL, "Prompt / model step"), (NAVY, "Code step (Python)"), (LIGHT, "Data")]):
        ax.add_patch(FancyBboxPatch((x + i * 2.3, y), 0.25, 0.18, boxstyle="round,pad=0.01", fc=c, ec=NAVY, lw=0.8))
        ax.text(x + i * 2.3 + 0.35, y + 0.09, t, fontsize=8, va="center", color=GREY)


# 1 prompt workflow ------------------------------------------------------------
fig, ax = canvas(10, 3.3)
steps = [("Resume +\njob description", LIGHT, NAVY), ("1. Mask personal\ndetails\n(privacy.py)", NAVY, "white"), ("2. Prompt P1 (v3)\nfilled with resume\nand job text", TEAL, "white"),
         ("3. Gemini\nreturns JSON", TEAL, "white"), ("4. Parse JSON,\nclamp scores,\ncheck evidence", NAVY, "white"), ("5. Add up score,\nbuild report", NAVY, "white")]
w, g = 1.45, 0.2
for i, (t, fc, tc) in enumerate(steps):
    x = 0.2 + i * (w + g)
    box(ax, x, 1.2, w, 1.5, t, fc, tc, fs=8.5)
    if i < len(steps) - 1:
        arrow(ax, x + w, 1.95, x + w + g, 1.95)
ax.text(5, 3.05, "Prompt workflow: one LLM call (P1), wrapped by code steps", ha="center", fontsize=11, color=NAVY, fontweight="bold")
ax.annotate("", xy=(5.0, 1.05), xytext=(8.9, 1.05), arrowprops=dict(arrowstyle="-|>", color=CORAL, lw=1.2, linestyle="--"))
ax.text(7.0, 0.82, "if JSON is invalid or the model errors, the app shows a clear message", ha="center", fontsize=8, color=CORAL)
legend(ax, 2.2, 0.25)
fig.savefig(OUT / "d1_prompt_workflow.png", dpi=200, bbox_inches="tight", facecolor="white"); plt.close(fig)

# 2 task decomposition ----------------------------------------------------------
fig, ax = canvas(10, 4.4)
box(ax, 2.2, 3.6, 5.6, 0.6, "Task: compare a resume with a job description", NAVY, "white", fs=9.5)
subs = [("A. Read the job:\nrequired vs preferred\nskills", TEAL), ("B. Find each skill in the\nresume, quote the\nevidence", TEAL), ("C. Decide: demonstrated,\nlisted only, or\nmissing", TEAL),
        ("D. Fill the 4 rubric\ncomponents\n(50/20/10/20)", TEAL), ("E. Write suggestions\ntied to resume lines", TEAL)]
for i, (t, c) in enumerate(subs):
    x = 0.15 + i * 1.97
    box(ax, x, 1.75, 1.8, 1.15, t, c, "white", fs=8)
    arrow(ax, 5.0, 3.6, x + 0.9, 2.9)
ax.text(5, 3.0, "", fontsize=1)
box(ax, 0.15, 0.2, 3.1, 0.8, "Before: mask personal details\n(code)", NAVY, "white", fs=8.5)
box(ax, 3.45, 0.2, 3.1, 0.8, "After: check evidence is in the\nresume (code)", NAVY, "white", fs=8.5)
box(ax, 6.75, 0.2, 3.1, 0.8, "After: add up the score\n(code, never the model)", NAVY, "white", fs=8.5)
ax.text(5, 1.4, "A to E all run inside the single prompt P1, as numbered steps", ha="center", fontsize=8.5, color=GREY)
ax.text(0.15, 4.25, "Task decomposition", fontsize=11, color=NAVY, fontweight="bold")
fig.savefig(OUT / "d2_task_decomposition.png", dpi=200, bbox_inches="tight", facecolor="white"); plt.close(fig)

# 3 input-output flow ------------------------------------------------------------
fig, ax = canvas(10, 3.6)
ax.text(0.2, 3.4, "Input - output flow", fontsize=11, color=NAVY, fontweight="bold")
box(ax, 0.2, 1.95, 2.3, 0.8, "Resume text\n(or sample resume)", LIGHT, NAVY, fs=8.5)
box(ax, 0.2, 0.95, 2.3, 0.8, "Job description\n(or sample job)", LIGHT, NAVY, fs=8.5)
box(ax, 0.2, 0.1, 2.3, 0.6, "Options: engine, prompt\nversion, mask details", LIGHT, GREY, fs=7.5, bold=False)
box(ax, 3.3, 0.75, 3.1, 1.9, "Skill Bridge\nmask, prompt P1, Gemini,\nvalidate, score", TEAL, "white", fs=9)
for y in (2.35, 1.35, 0.4):
    arrow(ax, 2.5, y, 3.3, 1.7)
outs = ["Match score 0-100", "Score breakdown (4 parts)", "Matching skills + evidence quote", "Missing and listed-only skills", "Suggestions, warnings, privacy"]
for i, t in enumerate(outs):
    y = 2.85 - i * 0.62
    box(ax, 7.2, y - 0.22, 2.6, 0.5, t, LIGHT, NAVY, fs=7.8)
    arrow(ax, 6.4, 1.7, 7.2, y + 0.03)
fig.savefig(OUT / "d3_input_output_flow.png", dpi=200, bbox_inches="tight", facecolor="white"); plt.close(fig)

# 4 system architecture -----------------------------------------------------------
fig, ax = canvas(10, 5.0)
ax.text(0.2, 4.8, "System architecture", fontsize=11, color=NAVY, fontweight="bold")
box(ax, 0.2, 3.9, 3.0, 0.65, "Streamlit web app (app.py)", AMBER, NAVY, fs=9)
box(ax, 3.4, 3.9, 3.0, 0.65, "Command line (cli.py)", AMBER, NAVY, fs=9)
box(ax, 6.6, 3.9, 3.2, 0.65, "Evaluation + test scripts", AMBER, NAVY, fs=9)
box(ax, 0.2, 2.75, 9.6, 0.7, "analyzer.analyse()  -  one entry point used by all three", NAVY, "white", fs=9.5)
for x in (1.7, 4.9, 8.2):
    arrow(ax, x, 3.9, x, 3.45)
parts = [("privacy.py\nmask personal\ndetails", NAVY), ("prompts.py +\nprompts/ files\n(v1, v2, v3, final)", NAVY), ("llm.py\nGemini client,\nretry, timeout", TEAL), ("scoring.py\nclamp, add up,\ncheck evidence", NAVY), ("offline.py +\nskills.py\nrules engine", NAVY)]
for i, (t, c) in enumerate(parts):
    x = 0.2 + i * 1.97
    box(ax, x, 1.2, 1.8, 1.0, t, c, "white", fs=8)
    arrow(ax, x + 0.9, 2.75, x + 0.9, 2.2)
box(ax, 4.15, 0.1, 1.8, 0.65, "Gemini API\n(Google)", LIGHT, NAVY, fs=8.5)
arrow(ax, 5.04, 1.2, 5.05, 0.75)
box(ax, 0.2, 0.1, 3.6, 0.65, "data/ and test-data/\nsample resumes, jobs, test inputs", LIGHT, NAVY, fs=8)
box(ax, 6.3, 0.1, 3.5, 0.65, "tests/ (pytest) + GitHub Actions", LIGHT, NAVY, fs=8)
fig.savefig(OUT / "d4_architecture.png", dpi=200, bbox_inches="tight", facecolor="white"); plt.close(fig)
print("diagrams saved to", OUT)
