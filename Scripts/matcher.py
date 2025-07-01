import pandas as pd
from rapidfuzz import fuzz
from sentence_transformers import SentenceTransformer, util
import re
import sys
import os
import logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from settings import RESUME_FILE, JOB_SKILL_FILE, MATCH_RESULTS_FILE, LOG_FILE
from utils import setup_logger, log_exceptions

setup_logger(LOG_FILE)
logger = logging.getLogger(__name__)

@log_exceptions
def load_job_skills():
    job_df = pd.read_csv(JOB_SKILL_FILE)
    job_skills_dict = {}

    for job_id, group in job_df.groupby("job_id"):
        job_title = group["job_title"].iloc[0]
        skill_weights = dict(zip(group["skill"].str.lower(), group["weight"]))
        job_skills_dict[job_id] = (job_title, skill_weights)

    return job_skills_dict

@log_exceptions
def load_resumes():
    df = pd.read_csv(RESUME_FILE)
    df["skills"] = df["Skills"].fillna("").apply(lambda x: [s.strip().lower() for s in x.split(";") if s.strip()])
    return df[["resume_id", "Name", "Email", "Phone", "Job Title", "skills"]]


@log_exceptions
def calculate_match(resume_skills, job_skills_with_weights, threshold=85):
    matched = {}
    missing = {}

    for job_skill, weight in job_skills_with_weights.items():
        is_matched = any(fuzz.partial_ratio(job_skill, res_skill) >= threshold for res_skill in resume_skills)
        if is_matched:
            matched[job_skill] = weight
        else:
            missing[job_skill] = weight

    total_weight = sum(job_skills_with_weights.values())
    matched_weight = sum(matched.values())
    match_score = round((matched_weight / total_weight) * 100, 1) if total_weight else 0.0

    return match_score, list(matched.keys()), list(missing.keys())

@log_exceptions
def match_all_resumes():
    all_jobs = load_job_skills()
    resumes = load_resumes()
    results = []

    for job_id, (job_title, job_skills) in all_jobs.items():
        for _, row in resumes.iterrows():
            resume_id = row["resume_id"]
            resume_skills = row["skills"]
            match_score, matched_skills, missing_skills = calculate_match(resume_skills, job_skills)

            results.append({
                "resume_id": resume_id,
                "name": row.get("Name", ""),
                "email": row.get("Email", ""),
                "phone": row.get("Phone", ""),
                "current_job_title": row.get("Job Title", ""),
                "job_id": job_id,
                "target_job_title": job_title,
                "match_percent": match_score,
                "matched_skills": ", ".join(matched_skills),
                "missing_skills": ", ".join(missing_skills)
            })


    df = pd.DataFrame(results)
    df.to_csv(MATCH_RESULTS_FILE, index=False)
    print(f"Matching results saved to: {MATCH_RESULTS_FILE}")

if __name__ == "__main__":
    match_all_resumes()