import streamlit as st
from pypdf import PdfReader
from groq import Groq
from dotenv import load_dotenv
import os
import json

load_dotenv()

st.set_page_config(page_title="AI Resume Analyzer", page_icon="📄", layout="wide")

st.title("📄 AI Resume Analyzer")
st.markdown("Paste a job description and upload a PDF resume to get AI-powered feedback on missing skills.")

# --- Sidebar / inputs ---
st.sidebar.header("🔧 Settings")
model_name = st.sidebar.selectbox("Groq Model", ["openai/gpt-oss-120b", "qwen/qwen3.8-27b"], index=0)

col1, col2 = st.columns([2, 1])

with col1:
    job_description = st.text_area("Job Description", placeholder="Paste the full job description here...", height=300)

with col2:
    st.write("")
    uploaded_file = st.file_uploader("Resume PDF", type=["pdf"], help="Upload a PDF resume to analyze")

analyze_btn = st.button("🔍 Analyze Resume", type="primary", use_container_width=True)

# --- Logic ---
if analyze_btn:
    if not job_description.strip():
        st.warning("⚠️ Please paste a job description.")
    elif not uploaded_file:
        st.warning("⚠️ Please upload a resume PDF.")
    else:
        with st.spinner("📄 Extracting text from resume..."):
            try:
                reader = PdfReader(uploaded_file)
                resume_text = "\n".join((page.extract_text() or "") for page in reader.pages)
            except Exception as e:
                st.error(f"❌ Failed to read PDF: {e}")
                resume_text = ""

        if resume_text.strip():
            with st.spinner("🧠 Analyzing with Groq..."):
                try:
                    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

                    prompt = f"""
You are an expert career coach and recruiter. Given a job description and a resume, analyze the resume against the job description.

Return a JSON object with exactly these keys:
- "missing_skills": array of strings (key skills from the JD that are absent from the resume)
- "present_skills": array of strings (key skills from the JD that appear in the resume)
- "suggestions": string (brief suggestions on what the candidate should add or emphasize)

Only output valid JSON, no surrounding text, no markdown.

Job Description:
\"\"\"{job_description}\"\"\"

Resume Text:
\"\"\"{resume_text}\"\"\"
"""

                    response = client.chat.completions.create(
                        model=model_name,
                        messages=[{"role": "user", "content": prompt.strip()}],
                        temperature=0.2,
                    )

                    raw = response.choices[0].message.content.strip()

                    # Try to parse JSON
                    result = json.loads(raw)

                    missing = result.get("missing_skills", [])
                    present = result.get("present_skills", [])
                    suggestions = result.get("suggestions", "No suggestions provided.")

                    # --- Display results ---
                    st.success("✅ Analysis complete!")

                    # Three columns for summary
                    r1, r2, r3 = st.columns(3)
                    with r1:
                        st.metric("Missing Skills", len(missing))
                    with r2:
                        st.metric("Present Skills", len(present))
                    with r3:
                        # You could add a "match %" here if desired
                        pass

                    # Missing skills
                    if missing:
                        st.subheader("❌ Missing Skills")
                        for skill in missing:
                            st.markdown(f"- **{skill}**")
                    else:
                        st.subheader("❌ Missing Skills")
                        st.markdown("*No missing skills — great match!*")

                    # Present skills
                    if present:
                        st.subheader("✅ Present Skills")
                        for skill in present:
                            st.markdown(f"- {skill}")
                    else:
                        st.subheader("✅ Present Skills")
                        st.markdown("*No overlapping skills found.*")

                    # Suggestions
                    st.subheader("💡 Suggestions")
                    st.info(suggestions)

                except json.JSONDecodeError:
                    st.error("❌ Groq returned invalid JSON. Displaying raw output:")
                    st.code(raw[:1000])
                except Exception as e:
                    st.error(f"❌ Error calling Groq API: {e}")
        else:
            st.error("❌ Could not extract text from the PDF. The file may be image-based or corrupted.")