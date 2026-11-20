"""SkillBridge - Intelligent AI Resume Analyzer & Job Matcher.

An explainable, evidence-based resume evaluator built with transparent prompt
engineering and rubric scoring. Run: streamlit run app.py
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
    page_title="SkillBridge • AI Resume & Job Intelligence",
    page_icon="🌉",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Custom CSS for Professional, Interactive UI ----------
st.markdown(
    """
<style>
  /* Header styling */
  .sb-main-title {
    font-size: 2.2rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    margin-bottom: 0.2rem;
    color: #1E293B;
  }
  .sb-subtitle {
    font-size: 1.05rem;
    color: #64748B;
    margin-bottom: 1.2rem;
  }

  /* Badge pills */
  .sb-badge-container {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 1.4rem;
  }
  .sb-badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 4px 12px;
    border-radius: 9999px;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.02em;
  }
  .sb-badge-indigo { background: #EEF2FF; color: #4338CA; border: 1px solid #C7D2FE; }
  .sb-badge-emerald { background: #ECFDF5; color: #065F46; border: 1px solid #A7F3D0; }
  .sb-badge-amber { background: #FFFBEB; color: #92400E; border: 1px solid #FDE68A; }
  .sb-badge-violet { background: #F5F3FF; color: #5B21B6; border: 1px solid #DDD6FE; }

  /* Cards */
  .sb-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 14px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
  }
  .sb-card:hover {
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
  }

  /* Status pills */
  .sb-pill {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }
  .sb-pill-demonstrated { background: #DCFCE7; color: #15803D; border: 1px solid #86EFAC; }
  .sb-pill-listed { background: #FEF3C7; color: #B45309; border: 1px solid #FCD34D; }
  .sb-pill-required { background: #FEE2E2; color: #B91C1C; border: 1px solid #FCA5A5; }
  .sb-pill-preferred { background: #F3E8FF; color: #7E22CE; border: 1px solid #D8B4FE; }
  .sb-pill-unverified { background: #F1F5F9; color: #475569; border: 1px solid #CBD5E1; }

  /* Quote block */
  .sb-quote {
    background: #F8FAFC;
    border-left: 3px solid #6366F1;
    padding: 8px 14px;
    margin-top: 6px;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    font-size: 0.83rem;
    color: #334155;
    border-radius: 0 6px 6px 0;
  }

  /* Quick stats banner */
  .sb-stat-tile {
    text-align: center;
    padding: 12px;
    border-radius: 10px;
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
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
    st.markdown("## 🌉 SkillBridge")
    st.caption("Explainable AI Resume Feedback & Transparent Rubric Scoring")

    st.markdown("### ⚙️ EngineConfiguration")
    engine_label = st.radio(
        "Evaluation Engine",
        ["Offline Demo (Rule-based, instant)", "Gemini (LLM Rubric Evaluator)"],
        help="The offline demo is deterministic, rule-based, and works offline.",
    )
    engine = "gemini" if "Gemini" in engine_label else "offline"

    version, api_key = "v3", ""
    if engine == "gemini":
        version = st.selectbox(
            "Prompt Version",
            list(LABELS),
            index=2,
            format_func=LABELS.get,
            help="v3 features the full four-part scoring rubric and hallucination guardrails.",
        )
        api_key = st.text_input(
            "Gemini API Key",
            type="password",
            help="Used for this session only. Never stored or logged.",
        )

    st.markdown("---")
    st.markdown("### 🛡️ GuardrailsAndFormatting")
    anon = st.toggle(
        "PrivacyFilterActive",
        value=True,
        help="Masks candidate names, emails, phones, URLs, and student ID numbers before evaluation.",
    )

    camel_mode = st.toggle(
        "CamelCaseModeEnabled",
        value=True,
        help="Display UI headings, metrics, tabs, and export payloads in camelCase / PascalCase.",
    )

    st.markdown("---")
    with st.expander("📖 RubricMethodology"):
        st.markdown(
            """
        **100-Point Fixed Rubric:**
        - **RequiredSkills**: 50 pts (Scaled by coverage)
        - **ExperienceProjects**: 20 pts (Evidence required)
        - **Education**: 10 pts (Related degree)
        - **PreferredSkills**: 20 pts (Bonus skills)

        *Evidence Guardrail*: Skills named only in a skills list score lower than those demonstrated with project context.
        """
        )

    st.caption("Confidentiality: Anonymise resumes before uploading real data.")

# ---------- Main Header ----------
app_title = "SkillBridge: AI Resume Analyzer & Job Matcher" if not camel_mode else "SkillBridge • ResumeAnalyzerAndJobMatcher"
st.markdown(f"<div class='sb-main-title'>{app_title}</div>", unsafe_allow_html=True)
st.markdown(
    "<div class='sb-subtitle'>Paste a resume and job description to inspect an explainable match score, verified project evidence, missing requirements, and honest improvement suggestions.</div>",
    unsafe_allow_html=True,
)

# Badges
st.markdown(
    """
<div class='sb-badge-container'>
  <span class='sb-badge sb-badge-indigo'>🔒 PrivacyFirst (AutoAnonymised)</span>
  <span class='sb-badge sb-badge-emerald'>📊 100PointRubric (NoHallucinatedScores)</span>
  <span class='sb-badge sb-badge-amber'>⚡ ZeroFakeSkillsGuardrail</span>
  <span class='sb-badge sb-badge-violet'>🐫 CamelCaseSupportEnabled</span>
</div>
""",
    unsafe_allow_html=True,
)

# ---------- Interactive Benchmark Scenarios (One-Click Testing) ----------
with st.container():
    st.markdown("##### 🚀 BenchmarkScenarios (One-Click Test Pairs)")
    scenario_labels = ["(Select a benchmark pair or input custom text below)"] + [
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

    if selected_scenario != "(Select a benchmark pair or input custom text below)":
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
                f"🎯 **Target Objective**: {matched_pair['note']} | **Expected Score Band**: {band_min} - {band_max} pts"
            )

# ---------- Input Section ----------
c1, c2 = st.columns(2)

with c1:
    resume_header = "CandidateResume" if camel_mode else "Candidate Resume"
    st.markdown(f"#### 📄 {resume_header}")
    load_sample("resume", RESUMES, "resume")

    # Live statistics & preview chips
    current_resume = st.session_state.get("resume", "")
    detected_resume_skills = find_skills(current_resume) if current_resume else []
    resume_words = len(current_resume.split()) if current_resume else 0
    st.caption(
        f"Stats: {resume_words} words | Detected skills: {', '.join(detected_resume_skills[:5]) + ('...' if len(detected_resume_skills) > 5 else '') if detected_resume_skills else 'None'}"
    )

    resume = st.text_area(
        "Resume",
        key="resume",
        height=280,
        placeholder="Paste candidate resume text here or choose a sample above...",
        label_visibility="collapsed",
    )

with c2:
    job_header = "JobDescription" if camel_mode else "Job Description"
    st.markdown(f"#### 🎯 {job_header}")
    load_sample("job", JOBS, "job description")

    current_job = st.session_state.get("job", "")
    detected_job_skills = find_skills(current_job) if current_job else []
    job_words = len(current_job.split()) if current_job else 0
    st.caption(
        f"Stats: {job_words} words | Target requirements: {', '.join(detected_job_skills[:5]) + ('...' if len(detected_job_skills) > 5 else '') if detected_job_skills else 'None'}"
    )

    job = st.text_area(
        "Job description",
        key="job",
        height=280,
        placeholder="Paste job description text here or choose a sample above...",
        label_visibility="collapsed",
    )

# ---------- Primary Action Button ----------
# NOTE: This must remain the FIRST st.button in the app to satisfy test_app.py
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

# ---------- Analysis Results Dashboard ----------
res = st.session_state.get("result")
if res:
    st.markdown("---")

    # Header summary info
    active_engine = res.get("engine", "offline")
    active_prompt = res.get("prompt_version", "v3")
    masked_total = res.get("privacy", {}).get("total", 0)

    st.caption(
        f"Evaluation Engine: **{active_engine}** | Prompt: **{active_prompt}** | Privacy Guardrail: **{masked_total} personal items masked**"
    )

    if res.get("raw_text"):
        st.subheader("Baseline Output (Free Text / Unstructured)")
        st.write(res["raw_text"])
    else:
        score = res["match_score"]

        # Score tier classification
        if score >= 85:
            score_tier, tier_color = "Exceptional Alignment", "#15803D"
        elif score >= 65:
            score_tier, tier_color = "Strong Candidate", "#1D4ED8"
        elif score >= 45:
            score_tier, tier_color = "Moderate Alignment", "#B45309"
        else:
            score_tier, tier_color = "Significant Skill Gap", "#B91C1C"

        matching_skills = res.get("matching_skills", [])
        demonstrated_count = sum(1 for m in matching_skills if m.get("demonstrated"))
        listed_only_count = sum(1 for m in matching_skills if not m.get("demonstrated"))
        missing_count = len(res.get("missing_skills", []))

        # Hero Stat Cards
        # NOTE: at.metric[0].value MUST be f"{res['match_score']} / 100" to satisfy test_app.py
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            match_metric_label = "MatchScore" if camel_mode else "Match Score"
            st.metric(match_metric_label, f"{score} / 100", delta=score_tier)
        with m2:
            dem_label = "DemonstratedSkills" if camel_mode else "Demonstrated Skills"
            st.metric(dem_label, f"{demonstrated_count} Verified", delta="Quoted Evidence")
        with m3:
            list_label = "ListedOnlySkills" if camel_mode else "Listed-Only Skills"
            st.metric(
                list_label,
                f"{listed_only_count} Unproven",
                delta="No Context" if listed_only_count else "Clean",
                delta_color="inverse" if listed_only_count else "normal",
            )
        with m4:
            miss_label = "MissingSkills" if camel_mode else "Missing Skills"
            st.metric(miss_label, f"{missing_count} Missing", delta="Rubric Gaps", delta_color="inverse")

        # Progress bar
        st.progress(score / 100)

        # Reasoning callout
        st.markdown(
            f"""
        <div class='sb-card' style='border-left: 4px solid {tier_color};'>
          <strong>💡 Rubric Evaluation Summary:</strong> {res.get("score_reasoning", "")}
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Rubric Breakdown Visuals
        breakdown = res.get("score_breakdown")
        if breakdown:
            st.markdown(f"### 📊 {'ScoreBreakdownAnalytics' if camel_mode else 'Score Breakdown Analytics'}")
            chart_col, table_col = st.columns([3, 2])

            chart_data = pd.DataFrame(
                {
                    "Component": [
                        to_pascal_case(k) if camel_mode else k.replace("_", " ").title()
                        for k in WEIGHTS
                    ],
                    "Earned": [breakdown.get(k, 0.0) for k in WEIGHTS],
                    "Max": [float(WEIGHTS[k]) for k in WEIGHTS],
                }
            )
            chart_data["Percent"] = (chart_data["Earned"] / chart_data["Max"] * 100).round(1)

            with chart_col:
                # Interactive Altair Chart
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
                            alt.Tooltip("Percent:Q", title="Percentage %"),
                        ],
                    )
                    .properties(height=200)
                )
                st.altair_chart(bar_chart, width="stretch")

            with table_col:
                display_df = chart_data.rename(
                    columns={
                        "Component": "RubricComponent" if camel_mode else "Rubric Component",
                        "Earned": "PointsEarned" if camel_mode else "Points Earned",
                        "Max": "MaxPoints" if camel_mode else "Max Points",
                        "Percent": "CompletionPercent" if camel_mode else "Completion %",
                    }
                )
                st.dataframe(display_df, hide_index=True, width="stretch")

        # ---------- Interactive Tabs ----------
        tab_names = [
            f"MatchingSkills ({len(matching_skills)})" if camel_mode else f"Matching Skills ({len(matching_skills)})",
            f"MissingSkills ({missing_count})" if camel_mode else f"Missing Skills ({missing_count})",
            "WhatIfSimulator 🔮" if camel_mode else "What-If Simulator 🔮",
            f"ActionableSuggestions ({len(res.get('suggestions', []))}) 📋"
            if camel_mode
            else f"Actionable Suggestions ({len(res.get('suggestions', []))}) 📋",
            "PrivacyAudit 🛡️" if camel_mode else "Privacy Audit 🛡️",
            "DataExportCenter 💾" if camel_mode else "Data Export Center 💾",
        ]

        t1, t2, t3, t4, t5, t6 = st.tabs(tab_names)

        # Tab 1: Matching Skills
        with t1:
            match_filter = st.radio(
                "Filter Matching Skills",
                ["All", "Demonstrated Only", "Listed Only"],
                horizontal=True,
                key="match_filter_radio",
            )
            filtered_matches = matching_skills
            if match_filter == "Demonstrated Only":
                filtered_matches = [m for m in matching_skills if m.get("demonstrated")]
            elif match_filter == "Listed Only":
                filtered_matches = [m for m in matching_skills if not m.get("demonstrated")]

            if not filtered_matches:
                st.info("No matching skills meet the current filter criteria.")

            for m in filtered_matches:
                is_dem = m.get("demonstrated", False)
                pill_class = "sb-pill-demonstrated" if is_dem else "sb-pill-listed"
                pill_text = (
                    ("DemonstratedInProject" if camel_mode else "Demonstrated in Project")
                    if is_dem
                    else ("ListedOnlyUnproven" if camel_mode else "Listed Only (Not Proven)")
                )

                st.markdown(
                    f"""
                <div class='sb-card'>
                  <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <span style='font-size: 1.1rem; font-weight: 700; color: #0F172A;'>{m['skill']}</span>
                    <span class='sb-pill {pill_class}'>{pill_text}</span>
                  </div>
                  <div class='sb-quote'>
                    <strong>Evidence:</strong> "{m.get('evidence', 'No quote available')}"
                  </div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

        # Tab 2: Missing & Unverified Skills
        with t2:
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
                st.success("🎉 No missing or unverified skills! Complete coverage achieved.")

            for m in missing_skills:
                is_req = m.get("importance") == "required"
                pill_class = "sb-pill-required" if is_req else "sb-pill-preferred"
                pill_text = (
                    ("RequiredSkill" if camel_mode else "Required (50pt Pool)")
                    if is_req
                    else ("PreferredSkill" if camel_mode else "Preferred (20pt Pool)")
                )

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

            # Unverified skills
            unverified_skills = res.get("unverified_skills", [])
            if unverified_skills:
                st.markdown("##### ⚠️ Unverified Skills (Invented or Unproven Evidence)")
                for u in unverified_skills:
                    st.markdown(
                        f"""
                    <div class='sb-card' style='border-left: 3px solid #F59E0B;'>
                      <div style='display: flex; justify-content: space-between;'>
                        <span style='font-weight: 700; color: #92400E;'>{u['skill']}</span>
                        <span class='sb-pill sb-pill-unverified'>Unverified</span>
                      </div>
                      <div style='font-size: 0.85rem; color: #64748B; margin-top: 4px;'>
                        {u.get('reason', 'Evidence quoted by the model was not found in the resume text.')}
                      </div>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

        # Tab 3: What-If Score Simulator (High Interactivity!)
        with t3:
            st.markdown(f"#### 🔮 {'WhatIfScoreSimulator' if camel_mode else 'What-If Score Simulator'}")
            st.caption(
                "Simulate your potential score increase by demonstrating missing skills or adding project proof for listed-only skills."
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
                            "desc": f"Add concrete project evidence for listed skill {m['skill']}",
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
                    # Compute simulated score
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
                        "SimulatedScore" if camel_mode else "Simulated Score",
                        f"{sim_score} / 100",
                        delta=f"+{delta_pts} pts" if delta_pts > 0 else "No Change",
                    )
                    st.progress(sim_score / 100)

                    if delta_pts > 0:
                        st.success(
                            f"✨ Demonstrating these {len(selected_sim_skills)} items could elevate your score from **{score}** to **{sim_score}**!"
                        )
                    else:
                        st.info("Check boxes on the left to simulate improvements.")

        # Tab 4: Actionable Suggestions (Interactive Checklist)
        with t4:
            st.markdown(f"#### 📋 {'ActionableResumeImprovementPlan' if camel_mode else 'Actionable Resume Improvement Plan'}")
            st.caption(
                "Work through these suggestions. Check them off as you update your resume. Remember: never claim skills you cannot defend in an interview."
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

        # Tab 5: Privacy Audit & Masking Inspector
        with t5:
            st.markdown(f"#### 🛡️ {'PrivacyAuditAndRedactionInspector' if camel_mode else 'Privacy Audit & Redaction Inspector'}")
            st.caption(
                "SkillBridge safeguards candidate privacy by automatically sanitizing personal contact details before model analysis."
            )

            privacy_info = res.get("privacy", {})
            counts = privacy_info.get("counts", {})
            total_masked = privacy_info.get("total", 0)

            p_cols = st.columns(5)
            types_map = [
                ("Names", "name"),
                ("Emails", "email"),
                ("Phones", "phone"),
                ("Links", "url"),
                ("IDs", "id_number"),
            ]
            for col, (label, key) in zip(p_cols, types_map):
                with col:
                    col_label = to_camel_case(label) if camel_mode else label
                    st.metric(col_label, counts.get(key, 0))

            with st.expander("🔍 View Anonymised Resume Text Passed to Engine"):
                from skillbridge.privacy import anonymise

                clean_text, _ = anonymise(resume)
                st.text_area("Anonymised Content", clean_text, height=220, disabled=True)

        # Tab 6: Data Export Center (With camelCase Support!)
        with t6:
            st.markdown(f"#### 💾 {'DataExportCenter' if camel_mode else 'Data Export Center'}")
            st.caption("Download structured evaluation results in camelCase JSON, standard JSON, or Markdown.")

            export_format = st.radio(
                "Payload Format",
                ["camelCase JSON", "Standard snake_case JSON", "Markdown Summary Report"],
                horizontal=True,
                key="export_format_radio",
            )

            # Build export payloads
            camel_res = camel_case_dict(res)
            camel_json_str = json.dumps(camel_res, indent=2, ensure_ascii=False)
            std_json_str = json.dumps(res, indent=2, ensure_ascii=False)

            md_report = f"""# SkillBridge Analysis Report

**Match Score**: {res.get('match_score', 0)} / 100
**Evaluation Engine**: {res.get('engine', 'offline')} (Prompt: {res.get('prompt_version', 'n/a')})

## Rubric Breakdown
- **Required Skills**: {breakdown.get('required_skills', 0) if breakdown else 'N/A'} / 50
- **Experience & Projects**: {breakdown.get('experience_projects', 0) if breakdown else 'N/A'} / 20
- **Education**: {breakdown.get('education', 0) if breakdown else 'N/A'} / 10
- **Preferred Skills**: {breakdown.get('preferred_skills', 0) if breakdown else 'N/A'} / 20

## Summary Reasoning
{res.get('score_reasoning', '')}

## Matching Skills ({len(matching_skills)})
{chr(10).join(f"- **{m['skill']}** ({'demonstrated' if m.get('demonstrated') else 'listed only'}): {m.get('evidence', '')}" for m in matching_skills)}

## Missing Skills ({len(res.get('missing_skills', []))})
{chr(10).join(f"- **{m['skill']}** [{m.get('importance', 'required')}]: {m.get('note', '')}" for m in res.get('missing_skills', []))}

## Suggestions
{chr(10).join(f"- [{s.get('section', 'General')}] {s.get('suggestion', '')}" for s in res.get('suggestions', []))}

---
*{res.get('disclaimer', '')}*
"""

            if export_format == "camelCase JSON":
                st.json(camel_res)
            elif export_format == "Standard snake_case JSON":
                st.json(res)
            else:
                st.markdown(md_report)

            down_c1, down_c2, down_c3 = st.columns(3)
            with down_c1:
                st.download_button(
                    "Download camelCase JSON",
                    camel_json_str,
                    "skillBridgeAnalysis_camelCase.json",
                    "application/json",
                    width="stretch",
                )
            with down_c2:
                st.download_button(
                    "Download Standard JSON",
                    std_json_str,
                    "skillbridge_result.json",
                    "application/json",
                    width="stretch",
                )
            with down_c3:
                st.download_button(
                    "Download Markdown Report",
                    md_report,
                    "skillBridgeReport.md",
                    "text/markdown",
                    width="stretch",
                )

    # Warnings and Disclaimer
    for w in res.get("warnings", []):
        st.warning(w)

    st.markdown("---")
    st.caption(
        f"⚖️ **Disclaimer**: {res.get('disclaimer', 'Guidance only. This score is not a hiring decision.')}"
    )
