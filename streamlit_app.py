from __future__ import annotations
import tempfile
from pathlib import Path

import streamlit as st

from matchrai.parsing import parse_resume, parse_job_description
from matchrai.skills import build_skill_taxonomy, keyword_gaps
from matchrai.scoring import compute_match, score_to_percent
from matchrai.explain import build_summary, recommendation_text

st.set_page_config(page_title="MatchrAI – Resume Analyzer & Job Matcher", layout="wide")

st.title("MatchrAI – Resume Analyzer & Job Match System (Phase-2 PoC)")
st.caption("Upload a resume + paste a job description → get match score, ATS score, and skill gaps.")

SKILLS_PATH = Path("data/skills_taxonomy.txt")
taxonomy = build_skill_taxonomy(SKILLS_PATH)

with st.sidebar:
    st.header("Settings")
    fresher_mode = st.toggle("Fresher / Student Mode", value=True, help="Weights semantic match higher for fresher resumes.")
    show_raw = st.toggle("Show extracted text", value=False)
    st.markdown("---")
    st.write("Tip: Expand `data/skills_taxonomy.txt` to improve skill extraction.")

col1, col2 = st.columns(2)

with col1:
    st.subheader("1) Upload Resume (PDF/DOCX)")
    resume_file = st.file_uploader("Resume file", type=["pdf", "docx"])

with col2:
    st.subheader("2) Job Description")
    jd_text = st.text_area("Paste job description here", height=220, placeholder="Paste the job description text...")

run = st.button("Analyze Match", type="primary", use_container_width=True)

if run:
    if resume_file is None:
        st.error("Please upload a resume (PDF or DOCX).")
        st.stop()
    if not jd_text.strip():
        st.error("Please paste the job description text.")
        st.stop()

    # Save uploaded resume to temp file
    suffix = "." + resume_file.name.split(".")[-1].lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(resume_file.getbuffer())
        tmp_path = tmp.name

    parsed = parse_resume(tmp_path)
    jd_clean = parse_job_description(jd_text)

    # Compute scores
    scores = compute_match(
        resume_text=parsed.raw_text,
        jd_text=jd_clean,
        years_exp=parsed.years_experience_estimate,
        fresher_mode=fresher_mode,
    )

    # Skill gaps
    gaps = keyword_gaps(parsed.raw_text, jd_clean, taxonomy)
    summary = build_summary(scores, gaps, parsed.cgpa)

    st.markdown("---")
    topA, topB, topC = st.columns(3)
    topA.metric("Final Match Score", summary["final"])
    topB.metric("Semantic Similarity", summary["semantic"])
    topC.metric("ATS Keyword Score", summary["ats"])

    st.caption(f"Weighting used: semantic={scores.breakdown['weights']['semantic']:.2f}, ats={scores.breakdown['weights']['ats']:.2f} | "
               f"Estimated experience: {scores.breakdown['years_experience_estimate']} years | CGPA: {summary['cgpa']}")

    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Matched Skills (from JD)")
        if gaps["matched"]:
            st.success(", ".join(gaps["matched"]))
        else:
            st.info("No skills matched (based on current taxonomy). Add more skills to taxonomy or improve extraction.")

    with c2:
        st.subheader("Missing Skills (Skill Gap)")
        if gaps["missing"]:
            st.warning(", ".join(gaps["missing"]))
        else:
            st.success("No major missing skills detected!")

    st.subheader("Recommendations")
    st.write(recommendation_text(gaps["missing"]))

    st.subheader("Section Preview (Resume)")
    cols = st.columns(4)
    sec_names = ["education", "projects", "experience", "skills"]
    for i, sec in enumerate(sec_names):
        with cols[i]:
            st.markdown(f"**{sec.title()}**")
            st.write(parsed.sections.get(sec, "Not detected"))

    if show_raw:
        with st.expander("Show raw extracted resume text"):
            st.text(parsed.raw_text[:20000])
