"""AI Resume Analyzer and Job Matcher.

An explainable, evidence-based resume evaluator built by Team Skill Bridge with
transparent prompt engineering, rubric scoring, and native CamelCase data schemas.
Run: streamlit run app.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import altair as alt
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from skillbridge.analyzer import analyse  # noqa: E402
from skillbridge.camel import camel_case_dict, to_camel_case, to_pascal_case  # noqa: E402
from skillbridge.llm import GeminiClient, GeminiError  # noqa: E402
from skillbridge.prompts import LABELS  # noqa: E402
from skillbridge.scoring import WEIGHTS  # noqa: E402
from skillbridge.skills import find_skills  # noqa: E402

st.set_page_config(
    page_title="AI Resume Analyzer and Job Matcher • Team Skill Bridge",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Custom Modern CSS Design System ----------
st.markdown(
    """
<style>
  /* Base font & typography enhancements */
  html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  }

  /* Header typography */
  .sb-header-title {
    font-size: 2.3rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    color: #0F172A;
    margin-bottom: 0.25rem;
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .sb-header-subtitle {
    font-size: 1.05rem;
    color: #475569;
    margin-bottom: 1.1rem;
    line-height: 1.5;
  }

  /* Badge container */
  .sb-badge-container {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 1.3rem;
  }
  .sb-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 5px 13px;
    border-radius: 9999px;
    font-size: 0.8rem;
    font-weight: 600;
    letter-spacing: 0.02em;
    box-shadow: 0 1px 2px rgba(0,0,0,0.03);
  }
  .sb-badge-indigo { background: #EEF2FF; color: #4338CA; border: 1px solid #C7D2FE; }
  .sb-badge-emerald { background: #ECFDF5; color: #065F46; border: 1px solid #A7F3D0; }
  .sb-badge-amber { background: #FFFBEB; color: #92400E; border: 1px solid #FDE68A; }
  .sb-badge-purple { background: #FAF5FF; color: #6B21A8; border: 1px solid #E9D5FF; }

  /* Interactive cards */
  .sb-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 18px 22px;
    margin-bottom: 14px;
    box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
    transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
  }
  .sb-card:hover {
    box-shadow: 0 6px 16px rgba(15, 23, 42, 0.08);
    border-color: #CBD5E1;
  }

  /* Status pills */
  .sb-pill {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 3px 10px;
    border-radius: 6px;
    font-size: 0.74rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    text-transform: none;
  }
  .sb-pill-demonstrated { background: #DCFCE7; color: #15803D; border: 1px solid #86EFAC; }
  .sb-pill-listed { background: #FEF3C7; color: #B45309; border: 1px solid #FCD34D; }
  .sb-pill-required { background: #FEE2E2; color: #B91C1C; border: 1px solid #FCA5A5; }
  .sb-pill-preferred { background: #F3E8FF; color: #7E22CE; border: 1px solid #D8B4FE; }
  .sb-pill-unverified { background: #F1F5F9; color: #475569; border: 1px solid #CBD5E1; }

  /* Evidence quotation callout */
  .sb-quote {
    background: #F8FAFC;
    border-left: 3px solid #6366F1;
    padding: 10px 16px;
    margin-top: 8px;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    font-size: 0.84rem;
    color: #334155;
    border-radius: 0 8px 8px 0;
    line-height: 1.45;
  }

  /* Benchmark scenario banner */
  .sb-scenario-box {
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 14px 18px;
    margin-bottom: 16px;
  }
</style>
""",
    unsafe_allow_html=True,
)

RESUMES = sorted((ROOT / "data/resumes").glob("*.txt"))
JOBS = sorted((ROOT / "data/jobs").glob("*.txt"))
PAIRS_FILE = ROOT / "data/eval_pairs.json"
PAIRS = json.loads(PAIRS_FILE.read_text(encoding="utf-8")) if PAIRS_FILE.exists() else []


def pretty(p: Path) -> str:
    words = p.stem.replace("_", " ").title().split()
    return " ".join({"Ai": "AI", "Ml": "ML"}.get(w, w) for w in words)


def load_sample(key: str, path_list: list[Path], label: str) -> None:
    choice = st.selectbox(
        f"Load a sample {label}",
        ["(none)"] + [pretty(p) for p in path_list],
        key=f"{key}_sel",
    )
    if choice != "(none)" and st.session_state.get(f"{key}_loaded") != choice:
        path = next(p for p in path_list if pretty(p) == choice)
        st.session_state[key] = path.read_text(encoding="utf-8")
        st.session_state[f"{key}_loaded"] = choice


# ---------- Sidebar Configuration ----------
with st.sidebar:
    st.markdown("## 📄 Resume Analyzer")
    st.caption("**Project**: AI Resume Analyzer and Job Matcher\n\n**Team**: Skill Bridge (SCSE4041)")

    st.markdown("### ⚙️ Engine Configuration")
    engine_label = st.radio(
        "Evaluation Engine",
        ["Offline Demo (Rule-based, instant)", "Gemini (LLM Rubric Evaluator)"],
        help="The offline demo runs transparent rules without internet or API key.",
    )
    engine = "gemini" if "Gemini" in engine_label else "offline"

    version, api_key = "v3", ""
    if engine == "gemini":
        version = st.selectbox(
            "Prompt Version",
            list(LABELS),
            index=2,
            format_func=LABELS.get,
            help="v3 features the full four-part scoring rubric and anti-hallucination guardrails.",
        )
        api_key = st.text_input(
            "Gemini API Key",
            type="password",
            help="Used for this session only. Never stored or logged.",
        )

    st.markdown("---")
    st.markdown("### 🛡️ Guardrails & Privacy")
    anon = st.toggle(
        "Auto Privacy Masking",
        value=True,
        help="Masks candidate names, emails, phone numbers, links, and student ID numbers before evaluation.",
    )

    with st.expander("📖 Rubric Methodology"):
        st.markdown(
            """
        **100-Point Fixed Rubric:**
        - **Required Skills**: 50 pts (Coverage & proof)
        - **Experience & Projects**: 20 pts (Evidence required)
        - **Education**: 10 pts (Relevant qualification)
        - **Preferred Skills**: 20 pts (Bonus competencies)

        *Evidence Guardrail*: Skills named only in a skills list receive lower credit than those proven with project context.
        """
        )

    st.caption("Confidentiality: Anonymise resumes before uploading real data.")

# ---------- Main Header ----------
st.markdown(
    """
<div class='sb-header-title'>
  <span>📄 AI Resume Analyzer and Job Matcher</span>
</div>
<div class='sb-header-subtitle'>
  Developed by <strong>Team Skill Bridge</strong> • SCSE4041 Prompt Engineering, Bennett University.<br>
  Compare candidate resumes against job descriptions with transparent 100-point rubric scoring, verified project evidence, and privacy-preserving guardrails.
</div>
<div class='sb-badge-container'>
  <span class='sb-badge sb-badge-indigo'>👥 Team: Skill Bridge</span>
  <span class='sb-badge sb-badge-emerald'>📊 Explainable Rubric (100-Point Total)</span>
  <span class='sb-badge sb-badge-amber'>🔒 Privacy Preserving (Auto-Masked)</span>
  <span class='sb-badge sb-badge-purple'>⚡ Zero-Hallucination Guardrail</span>
</div>
""",
    unsafe_allow_html=True,
)

# ---------- Interactive Benchmark Scenarios (One-Click Testing) ----------
with st.container():
    st.markdown("##### 🚀 Benchmark Scenarios (One-Click Evaluation Pairs)")
    scenario_labels = ["(Select a benchmark pair or enter custom text below)"] + [
        f"{p['id']}: {pretty(Path(p['resume']))} + {pretty(Path(p['job']))} — {p['note']}"
        for p in PAIRS
    ]
    selected_scenario = st.selectbox(
        "Benchmark Pair Selector",
        scenario_labels,
        index=0,
        label_visibility="collapsed",
        key="scenario_selector",
    )

    if selected_scenario != "(Select a benchmark pair or enter custom text below)":
        pair_id = selected_scenario.split(":")[0]
        matched_pair = next((p for p in PAIRS if p["id"] == pair_id), None)
        if matched_pair:
            resume_content = (ROOT / "data/resumes" / matched_pair["resume"]).read_text(encoding="utf-8")
            job_content = (ROOT / "data/jobs" / matched_pair["job"]).read_text(encoding="utf-8")
            if st.session_state.get("active_pair_id") != pair_id:
                st.session_state["resume"] = resume_content
                st.session_state["job"] = job_content
                st.session_state["active_pair_id"] = pair_id

            band_min, band_max = matched_pair["gold"]["score_band"]
            st.info(
                f"🎯 **Benchmark Objective**: {matched_pair['note']} | **Gold Target Band**: {band_min} - {band_max} pts"
            )

# ---------- Two-Column Inputs ----------
c1, c2 = st.columns(2)

with c1:
    st.markdown("#### 📄 Candidate Resume")
    load_sample("resume", RESUMES, "resume")

    # Real-time text statistics & detected skill chips
    current_resume = st.session_state.get("resume", "")
    detected_resume_skills = find_skills(current_resume) if current_resume else []
    resume_words = len(current_resume.split()) if current_resume else 0
    skills_preview = (
        ", ".join(detected_resume_skills[:5]) + ("..." if len(detected_resume_skills) > 5 else "")
        if detected_resume_skills
        else "None detected yet"
    )
    st.caption(f"Stats: **{resume_words} words** | Detected skills: *{skills_preview}*")

    resume = st.text_area(
        "Resume",
        key="resume",
        height=280,
        placeholder="Paste candidate resume text here or choose a sample from above...",
        label_visibility="collapsed",
    )

with c2:
    st.markdown("#### 🎯 Target Job Description")
    load_sample("job", JOBS, "job description")

    current_job = st.session_state.get("job", "")
    detected_job_skills = find_skills(current_job) if current_job else []
    job_words = len(current_job.split()) if current_job else 0
    req_preview = (
        ", ".join(detected_job_skills[:5]) + ("..." if len(detected_job_skills) > 5 else "")
        if detected_job_skills
        else "None detected yet"
    )
    st.caption(f"Stats: **{job_words} words** | Target requirements: *{req_preview}*")

    job = st.text_area(
        "Job description",
        key="job",
        height=280,
        placeholder="Paste target job description text here or choose a sample from above...",
        label_visibility="collapsed",
    )

# ---------- Primary Action Button ----------
# NOTE: Must remain the FIRST st.button in app.py to satisfy automated test suite
if st.button("Analyse Resume Against Job", type="primary", width="stretch"):
    try:
        client = GeminiClient(api_key=api_key or None) if engine == "gemini" else None
        with st.spinner("Executing explainable evaluation rubric..."):
            st.session_state["result"] = analyse(
                resume,
                job,
                engine=engine,
                prompt_version=version,
                client=client,
                anonymise_resume=anon,
            )
    except (ValueError, GeminiError) as exc:
        st.session_state.pop("result", None)
        st.error(str(exc))

# ---------- Results Dashboard ----------
res = st.session_state.get("result")
if res:
    st.markdown("---")

    active_engine = res.get("engine", "offline")
    active_prompt = res.get("prompt_version", "v3")
    masked_total = res.get("privacy", {}).get("total", 0)

    # Safely extract common fields regardless of prompt version (v1 free text vs v2/v3 structured)
    breakdown = res.get("score_breakdown") or {}
    matching_skills = res.get("matching_skills") or []
    missing_skills = res.get("missing_skills") or []
    suggestions = res.get("suggestions") or []

    st.caption(
        f"Evaluation Engine: **{active_engine}** | Prompt Version: **{active_prompt}** | Privacy Guardrail: **{masked_total} personal details sanitized**"
    )

    if res.get("raw_text"):
        st.subheader("Baseline Output (Free Text / Unstructured)")
        st.write(res["raw_text"])
    else:
        score = res.get("match_score", 0) or 0

        # Score tier classification
        if score >= 85:
            score_tier, tier_color = "Exceptional Alignment", "#15803D"
        elif score >= 65:
            score_tier, tier_color = "Strong Candidate", "#1D4ED8"
        elif score >= 45:
            score_tier, tier_color = "Moderate Alignment", "#B45309"
        else:
            score_tier, tier_color = "Significant Skill Gap", "#B91C1C"

        demonstrated_count = sum(1 for m in matching_skills if m.get("demonstrated"))
        listed_only_count = sum(1 for m in matching_skills if not m.get("demonstrated"))
        missing_count = len(missing_skills)

        # Hero Stat Cards with spaces between words
        # NOTE: at.metric[0].label must be "Match Score" and value "62 / 100" to satisfy test_app.py
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Match Score", f"{score} / 100", delta=score_tier)
        with m2:
            st.metric("Demonstrated Skills", f"{demonstrated_count} Verified", delta="Quoted Evidence")
        with m3:
            st.metric(
                "Listed-Only Skills",
                f"{listed_only_count} Unproven",
                delta="No Project Context" if listed_only_count else "Clean",
                delta_color="inverse" if listed_only_count else "normal",
            )
        with m4:
            st.metric("Missing Skills", f"{missing_count} Missing", delta="Rubric Gaps", delta_color="inverse")

        # Visual progress bar
        st.progress(score / 100)

        # Reasoning callout card
        st.markdown(
            f"""
        <div class='sb-card' style='border-left: 4px solid {tier_color};'>
          <strong>💡 Rubric Evaluation Reasoning:</strong> {res.get("score_reasoning", "")}
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Rubric Breakdown Analytics
        breakdown = res.get("score_breakdown")
        if breakdown:
            st.markdown("### 📊 Score Breakdown Analytics")
            chart_col, table_col = st.columns([3, 2])

            def clean_label(k: str) -> str:
                return {
                    "required_skills": "Required Skills",
                    "experience_projects": "Experience & Projects",
                    "education": "Education",
                    "preferred_skills": "Preferred Skills",
                }.get(k, k.replace("_", " ").title())

            chart_data = pd.DataFrame(
                {
                    "Component": [clean_label(k) for k in WEIGHTS],
                    "Earned": [breakdown.get(k, 0.0) for k in WEIGHTS],
                    "Max": [float(WEIGHTS[k]) for k in WEIGHTS],
                }
            )
            chart_data["Percent"] = (chart_data["Earned"] / chart_data["Max"] * 100).round(1)

            with chart_col:
                bar_chart = (
                    alt.Chart(chart_data)
                    .mark_bar(cornerRadius=6, height=22)
                    .encode(
                        x=alt.X("Earned:Q", scale=alt.Scale(domain=[0, 50]), title="Points Earned"),
                        y=alt.Y("Component:N", sort=None, title=None),
                        color=alt.Color(
                            "Earned:Q",
                            scale=alt.Scale(scheme="blues"),
                            legend=None,
                        ),
                        tooltip=[
                            alt.Tooltip("Component:N", title="Rubric Component"),
                            alt.Tooltip("Earned:Q", title="Points Earned"),
                            alt.Tooltip("Max:Q", title="Max Available"),
                            alt.Tooltip("Percent:Q", title="Completion %"),
                        ],
                    )
                    .properties(height=200)
                )
                st.altair_chart(bar_chart, width="stretch")

            with table_col:
                display_df = chart_data.rename(
                    columns={
                        "Component": "Rubric Component",
                        "Earned": "Points Earned",
                        "Max": "Max Points",
                        "Percent": "Completion %",
                    }
                )
                st.dataframe(display_df, hide_index=True, width="stretch")

        # ---------- Interactive Tabs (4 Tabs: MatchingSkills and DataExportCenter deleted) ----------
        tab_names = [
            f"Missing Skills ({missing_count})",
            "What-If Simulator 🔮",
            f"Action Plan ({len(res.get('suggestions', []))}) 📋",
            "Privacy Audit 🛡️",
        ]

        t1, t2, t3, t4 = st.tabs(tab_names)

        # Tab 1: Missing Skills
        with t1:
            miss_filter = st.radio(
                "Filter Missing Skills",
                ["All Missing", "Required Skills Only", "Preferred Skills Only"],
                horizontal=True,
                key="miss_filter_radio",
            )
            missing_skills = res.get("missing_skills", [])
            if miss_filter == "Required Skills Only":
                missing_skills = [m for m in missing_skills if m.get("importance") == "required"]
            elif miss_filter == "Preferred Skills Only":
                missing_skills = [m for m in missing_skills if m.get("importance") == "preferred"]

            if not missing_skills and not res.get("unverified_skills"):
                st.success("🎉 Full competency coverage! No required or preferred skills missing.")

            for m in missing_skills:
                is_req = m.get("importance") == "required"
                pill_class = "sb-pill-required" if is_req else "sb-pill-preferred"
                pill_text = "Missing Required (50-pt Pool)" if is_req else "Missing Preferred (20-pt Pool)"

                st.markdown(
                    f"""
                <div class='sb-card'>
                  <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <span style='font-size: 1.1rem; font-weight: 700; color: #0F172A;'>{m['skill']}</span>
                    <span class='sb-pill {pill_class}'>{pill_text}</span>
                  </div>
                  <div style='margin-top: 8px; font-size: 0.88rem; color: #475569;'>
                    {m.get('note', 'Skill absent from candidate resume.')}
                  </div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

            # Unverified skills (hallucination rejection)
            unverified_skills = res.get("unverified_skills", [])
            if unverified_skills:
                st.markdown("##### ⚠️ Unverified Skills (Quoted Evidence Failed Sanity Check)")
                for u in unverified_skills:
                    st.markdown(
                        f"""
                    <div class='sb-card' style='border-left: 3px solid #F59E0B;'>
                      <div style='display: flex; justify-content: space-between;'>
                        <span style='font-weight: 700; color: #92400E;'>{u['skill']}</span>
                        <span class='sb-pill sb-pill-unverified'>Unverified Evidence</span>
                      </div>
                      <div style='font-size: 0.85rem; color: #64748B; margin-top: 4px;'>
                        {u.get('reason', 'Evidence quoted by the model was not found in the resume text.')}
                      </div>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

        # Tab 2: What-If Simulator (Dynamic Score Improvement Projector)
        with t2:
            st.markdown("#### 🔮 What-If Score Simulator")
            st.caption(
                "Simulate your potential score increase by selecting skills to demonstrate in projects or by adding project proof for listed-only skills."
            )

            all_sim_candidates = []
            for m in res.get("missing_skills", []):
                all_sim_candidates.append(
                    {
                        "skill": m["skill"],
                        "type": "missing",
                        "importance": m.get("importance", "required"),
                        "desc": f"Build a project demonstrating {m['skill']}",
                    }
                )
            for m in matching_skills:
                if not m.get("demonstrated"):
                    all_sim_candidates.append(
                        {
                            "skill": m["skill"],
                            "type": "unproven",
                            "importance": "required",
                            "desc": f"Add project proof for listed skill {m['skill']}",
                        }
                    )

            if not all_sim_candidates:
                st.info("Your resume already demonstrates all required and preferred skills!")
            else:
                sim_col1, sim_col2 = st.columns([3, 2])

                with sim_col1:
                    st.markdown("##### Select Skills to Demonstrate:")
                    selected_sim_skills = []
                    for idx, item in enumerate(all_sim_candidates):
                        gain_est = 12 if item["importance"] == "required" and item["type"] == "missing" else (
                            6 if item["type"] == "unproven" else 5
                        )
                        label = f"{item['desc']} (+~{gain_est} pts)"
                        if st.checkbox(label, key=f"sim_skill_{idx}"):
                            selected_sim_skills.append(item)

                with sim_col2:
                    sim_score = score
                    for item in selected_sim_skills:
                        if item["importance"] == "required" and item["type"] == "missing":
                            sim_score += 12
                        elif item["type"] == "unproven":
                            sim_score += 6
                        else:
                            sim_score += 5
                    sim_score = min(100, sim_score)
                    delta_pts = sim_score - score

                    st.markdown("##### 📈 Projected Score Impact")
                    st.metric(
                        "Simulated Score",
                        f"{sim_score} / 100",
                        delta=f"+{delta_pts} pts" if delta_pts > 0 else "No Change",
                    )
                    st.progress(sim_score / 100)

                    if delta_pts > 0:
                        st.success(
                            f"✨ Demonstrating these {len(selected_sim_skills)} competencies elevates your projected score from **{score}** to **{sim_score}**!"
                        )
                    else:
                        st.info("Check boxes on the left to simulate project additions.")

        # Tab 3: Action Plan (Interactive To-Do Checklist)
        with t3:
            st.markdown("#### 📋 Actionable Resume Improvement Plan")
            st.caption(
                "Work through these suggestions. Check them off as you refine your resume. Remember: never claim skills you cannot defend in an interview."
            )

            suggestions = res.get("suggestions", [])
            if not suggestions:
                st.success("No critical suggestions needed. Profile is well aligned!")

            completed_count = 0
            for idx, s in enumerate(suggestions):
                checked = st.checkbox(
                    f"**[{s.get('section', 'General')}]** {s.get('suggestion', '')}",
                    key=f"suggestion_check_{idx}",
                )
                if checked:
                    completed_count += 1
                if s.get("based_on"):
                    st.caption(f"↳ Based on: {s['based_on']}")

            if suggestions:
                st.markdown("---")
                completion_rate = completed_count / len(suggestions)
                st.write(f"Checklist Progress: **{completed_count} of {len(suggestions)} items completed**")
                st.progress(completion_rate)

        # Tab 4: Privacy Audit (Inspection)
        with t4:
            st.markdown("#### 🛡️ Privacy Audit & Sanitization Inspector")
            st.caption(
                "SkillBridge safeguards candidate confidentiality by automatically sanitizing personal contact identifiers before passing text to any engine."
            )

            privacy_info = res.get("privacy", {})
            counts = privacy_info.get("counts", {})

            p_cols = st.columns(5)
            types_map = [
                ("Candidate Names", "name"),
                ("Email Addresses", "email"),
                ("Phone Numbers", "phone"),
                ("Profile URLs", "url"),
                ("Student IDs", "id_number"),
            ]
            for col, (label, key) in zip(p_cols, types_map):
                with col:
                    st.metric(label, counts.get(key, 0))

            with st.expander("🔍 View Anonymised Resume Text Passed to Engine"):
                from skillbridge.privacy import anonymise

                clean_text, _ = anonymise(resume)
                st.text_area("Anonymised Content", clean_text, height=220, disabled=True)

    # Optional Compact Download Expander
    with st.expander("💾 Download Evaluation Reports (camelCase JSON / Standard / Markdown)"):
        camel_res = camel_case_dict(res)
        camel_json_str = json.dumps(camel_res, indent=2, ensure_ascii=False)
        std_json_str = json.dumps(res, indent=2, ensure_ascii=False)

        if res.get("raw_text"):
            md_report = f"""# AI Resume Analyzer and Job Matcher - Baseline Evaluation Report

**Project**: AI Resume Analyzer and Job Matcher
**Team**: Skill Bridge (SCSE4041)
**Evaluation Engine**: {res.get('engine', 'offline')} (Prompt: {res.get('prompt_version', 'n/a')})

## Baseline Output
{res.get('raw_text')}

---
*{res.get('disclaimer', '')}*
"""
        else:
            md_report = f"""# AI Resume Analyzer and Job Matcher - Evaluation Report

**Project**: AI Resume Analyzer and Job Matcher
**Team**: Skill Bridge (SCSE4041)
**Match Score**: {res.get('match_score', 0)} / 100
**Evaluation Engine**: {res.get('engine', 'offline')} (Prompt: {res.get('prompt_version', 'n/a')})

## Rubric Breakdown
- **Required Skills**: {breakdown.get('required_skills', 'N/A') if breakdown else 'N/A'} / 50
- **Experience & Projects**: {breakdown.get('experience_projects', 'N/A') if breakdown else 'N/A'} / 20
- **Education**: {breakdown.get('education', 'N/A') if breakdown else 'N/A'} / 10
- **Preferred Skills**: {breakdown.get('preferred_skills', 'N/A') if breakdown else 'N/A'} / 20

## Summary Reasoning
{res.get('score_reasoning', '')}

## Missing Skills ({len(missing_skills)})
{chr(10).join(f"- **{m['skill']}** [{m.get('importance', 'required')}]: {m.get('note', '')}" for m in missing_skills) if missing_skills else "None"}

## Suggestions
{chr(10).join(f"- [{s.get('section', 'General')}] {s.get('suggestion', '')}" for s in suggestions) if suggestions else "None"}

---
*{res.get('disclaimer', '')}*
"""
        d_c1, d_c2, d_c3 = st.columns(3)
        with d_c1:
            st.download_button(
                "Download camelCase JSON",
                camel_json_str,
                "ai_resume_analyzer_camelCase.json",
                "application/json",
                width="stretch",
            )
        with d_c2:
            st.download_button(
                "Download Standard JSON",
                std_json_str,
                "ai_resume_analyzer_standard.json",
                "application/json",
                width="stretch",
            )
        with d_c3:
            st.download_button(
                "Download Markdown Report",
                md_report,
                "ai_resume_analyzer_report.md",
                "text/markdown",
                width="stretch",
            )

    # Warnings and Disclaimer
    for w in res.get("warnings", []):
        st.warning(w)

    st.markdown("---")
    st.caption(
        f"⚖️ **Disclaimer**: {res.get('disclaimer', 'Guidance only. This score is not a hiring decision.')} | **Project**: AI Resume Analyzer and Job Matcher • **Team**: Skill Bridge"
    )
