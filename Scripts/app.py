import streamlit as st
import pandas as pd
from resume_parser import parse_resume
from job_parser import parse_job_description
from matcher import compute_matching_score
import os
import tempfile

# === Utility: Extract text from uploaded file ===
def extract_text_from_file(uploaded_file):
    ext = uploaded_file.name.split('.')[-1].lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix='.' + ext) as tmp_file:
        tmp_file.write(uploaded_file.read())
        tmp_path = tmp_file.name

    # Add your own parsing logic here for PDF/DOCX/TXT
    if ext == 'txt':
        with open(tmp_path, 'r', encoding='utf-8') as f:
            return f.read()
    elif ext == 'pdf':
        import fitz  # PyMuPDF
        text = ""
        with fitz.open(tmp_path) as doc:
            for page in doc:
                text += page.get_text()
        return text
    elif ext == 'docx':
        import docx
        doc = docx.Document(tmp_path)
        return "\n".join(p.text for p in doc.paragraphs)
    else:
        return ""

# === UI ===
st.title("Live Resume Matcher")
st.write("Upload a job description and multiple resumes to see best matches.")

uploaded_job = st.file_uploader("Upload Job Description", type=["txt", "pdf", "docx"])
uploaded_resumes = st.file_uploader("Upload Resumes", type=["pdf", "docx"], accept_multiple_files=True)

min_score = st.number_input("Minimum Matching Score", min_value=0.0, max_value=100.0, value=50.0, step=1.0)

if uploaded_job and uploaded_resumes and st.button("Match Resumes"):
    # Parse job description
    job_text = extract_text_from_file(uploaded_job)
    job_data = parse_job_description(job_text)
    job_title = job_data.get("job_title", "")
    job_skills = job_data.get("skills", [])

    # Parse resumes and compute match
    results = []
    for resume_file in uploaded_resumes:
        resume_text = extract_text_from_file(resume_file)
        resume_data = parse_resume(resume_text)

        score = compute_matching_score(resume_data["skills"], job_skills)

        if score >= min_score:
            results.append({
                "Name": resume_data.get("name", resume_file.name),
                "Email": resume_data.get("email", ""),
                "Phone": resume_data.get("phone", ""),
                "Matching Score": round(score, 2)
            })

    if results:
        st.success("Matched Resumes:")
        df = pd.DataFrame(results).sort_values(by="Matching Score", ascending=False)
        st.dataframe(df)
    else:
        st.warning("No resumes matched the criteria.")