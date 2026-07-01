import json
import os
import re

import PyPDF2
import streamlit as st
from dotenv import load_dotenv
from groq import Groq


load_dotenv()
st.set_page_config(page_title="Resume ATS Analyzer", page_icon="📄", layout="wide")

st.markdown(
    """
    <style>
        .stApp { background: linear-gradient(135deg, #07111f 0%, #13253f 100%); }
        .block-container { padding-top: 1rem; padding-bottom: 2rem; }
        .hero {
            background: linear-gradient(135deg, #2563eb, #7c3aed);
            padding: 1.4rem 1.5rem;
            border-radius: 20px;
            margin-bottom: 1rem;
            box-shadow: 0 10px 30px rgba(0,0,0,0.22);
        }
        .hero h1 { color: white; margin: 0; font-size: 2rem; }
        .hero p { color: #e0e7ff; margin: 0.35rem 0 0 0; }
        .panel {
            background: rgba(255,255,255,0.08);
            border: 1px solid rgba(255,255,255,0.12);
            border-radius: 18px;
            padding: 1rem 1.1rem;
            margin-bottom: 1rem;
            box-shadow: 0 8px 20px rgba(0,0,0,0.16);
        }
        .panel h3 { color: #ffffff; margin-bottom: 0.3rem; }
        .panel p, .panel li { color: #dce8ff; }
        .score-card {
            text-align: center;
            padding: 1.2rem;
            background: rgba(255,255,255,0.08);
            border-radius: 18px;
            border: 2px solid;
            margin-bottom: 1rem;
        }
        .score-number { font-size: 3.2rem; font-weight: 800; margin: 0.2rem 0; }
        .score-label { color: #c9d7f2; font-size: 0.9rem; }
        .small-card {
            background: rgba(255,255,255,0.07);
            border: 1px solid rgba(255,255,255,0.12);
            border-radius: 16px;
            padding: 0.9rem 1rem;
            margin-bottom: 0.8rem;
        }
        .small-card h4 { color: #ffffff; margin-top: 0; margin-bottom: 0.35rem; }
        .small-card ul { margin: 0; padding-left: 1.1rem; color: #e8f0ff; }
        .stButton > button {
            border-radius: 999px;
            border: none;
            padding: 0.6rem 1rem;
            background: linear-gradient(90deg, #4f8cff 0%, #7b61ff 100%);
            color: white;
            font-weight: 600;
        }
        .stButton > button:hover { filter: brightness(1.05); }
        div[data-testid="stFileUploader"] {
            background: rgba(255,255,255,0.06);
            border: 1px dashed rgba(255,255,255,0.2);
            border-radius: 16px;
            padding: 0.6rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
        <h1>Resume ATS Analyzer</h1>
        <p>Upload a resume PDF, target a job role, and receive a clear ATS score with smart suggestions to improve your chances.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Load API key from .env or Streamlit secrets
try:
    api_key = st.secrets.get("GROQ_API_KEY", "")
except Exception:
    api_key = ""

if not api_key:
    api_key = os.getenv("GROQ_API_KEY", "").strip()

if not api_key:
    st.warning("Set your GROQ_API_KEY in .env or Streamlit secrets to enable AI analysis.")
    client = None
else:
    client = Groq(api_key=api_key)


def ask_ai(prompt):
    if client is None:
        return "AI analysis is unavailable because no API key was provided."

    try:
        r = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=1200,
        )
        return r.choices[0].message.content
    except Exception as e:
        return f"AI request failed: {e}"


def extract_pdf(file):
    reader = PyPDF2.PdfReader(file)
    return "".join(page.extract_text() or "" for page in reader.pages)


def clean_json_response(raw):
    if not raw:
        return "{}"

    text = raw.strip()

    if "```" in text:
        parts = text.split("```")
        if len(parts) > 1:
            text = parts[1]
            if text.lower().startswith("json"):
                text = text[4:].strip()

    text = re.sub(r"^```json\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    return text


left, right = st.columns([1.1, 0.9], gap="large")

with left:
    st.markdown(
        """
        <div class="panel">
            <h3>📄 Resume Upload</h3>
            <p>Drop in your resume and tell us the role you want to target.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    resume_file = st.file_uploader("Upload PDF resume", type=["pdf"])
    job_role = st.text_input("Target job role", placeholder="e.g. Data Scientist")
    job_desc = st.text_area(
        "Paste job description (optional)",
        height=130,
        placeholder="Paste the target role description here...",
    )
    scan_btn = st.button("Scan Resume", use_container_width=True)

with right:
    st.markdown(
        """
        <div class="panel">
            <h3>✨ What this analyzer checks</h3>
            <ul>
                <li>ATS compatibility for your chosen role</li>
                <li>Strengths and weak spots in your resume</li>
                <li>Missing keywords and improvement tips</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if api_key:
        st.success("AI analysis is ready")
    else:
        st.warning("Add your GROQ_API_KEY to enable resume scoring")

    st.markdown(
        """
        <div class="panel">
            <h3>💡 Pro tip</h3>
            <p>Include relevant tools, metrics, and keywords from the job description to improve your ATS match.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

if scan_btn:
    if not api_key:
        st.error("Please add your GROQ_API_KEY before scanning your resume.")
    elif not resume_file:
        st.error("Please upload a PDF resume first.")
    elif not job_role:
        st.error("Please enter the target job role.")
    else:
        with st.spinner("Scanning resume and preparing insights..."):
            resume_text = extract_pdf(resume_file)
            prompt = (
                "You are an ATS and HR expert. Analyze the resume for the role: "
                + job_role
                + ". Resume text: "
                + resume_text[:4000]
                + ". Job description: "
                + (job_desc[:2000] if job_desc else "No job description provided")
                + ". Return ONLY valid JSON with keys: ats_score (0-100), overall_rating, strengths (list of 3), weaknesses (list of 3), missing_keywords (list of 5), improvement_tips (list of 3), summary (2 sentences)."
            )

            raw = ask_ai(prompt)
            if not isinstance(raw, str):
                st.error("AI returned an invalid response format.")
                st.stop()

            cleaned = clean_json_response(raw)

            try:
                result = json.loads(cleaned)
            except Exception:
                st.error("The AI response was not valid JSON. Please try again.")
                st.code(cleaned)
                st.stop()

            if not isinstance(result, dict):
                st.error("The AI response was not a JSON object.")
                st.stop()

            score = int(result.get("ats_score", 0))
            if score >= 75:
                color = "#22c55e"
                label = "Strong match"
            elif score >= 50:
                color = "#f59e0b"
                label = "Moderate match"
            else:
                color = "#ef4444"
                label = "Needs improvement"

            st.markdown(
                f"""
                <div class="score-card" style="border-color: {color};">
                    <div class="score-label">ATS Compatibility</div>
                    <div class="score-number" style="color: {color};">{score}</div>
                    <div class="score-label">Out of 100</div>
                    <div style="margin-top: 0.4rem; color: #ffffff; font-weight: 600;">{label}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.progress(min(score / 100, 1.0))
            st.caption(f"Target role: {job_role}")
            st.info(result.get("summary", "No summary available."))

            c1, c2 = st.columns(2, gap="medium")
            with c1:
                st.markdown(
                    """
                    <div class="small-card">
                        <h4>✅ Strengths</h4>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                for item in result.get("strengths", []) or []:
                    st.write(f"- {item}")

                st.markdown(
                    """
                    <div class="small-card">
                        <h4>⚠️ Weaknesses</h4>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                for item in result.get("weaknesses", []) or []:
                    st.write(f"- {item}")

            with c2:
                st.markdown(
                    """
                    <div class="small-card">
                        <h4>🔑 Missing Keywords</h4>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                for item in result.get("missing_keywords", []) or []:
                    st.write(f"- {item}")

                st.markdown(
                    """
                    <div class="small-card">
                        <h4>💬 Improvement Tips</h4>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                for item in result.get("improvement_tips", []) or []:
                    st.write(f"- {item}")