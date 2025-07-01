import os
import re
import csv
import fitz
import docx
import logging
from fuzzywuzzy import fuzz
import nltk
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from settings import KEYWORDS_FILE, RESUME_FOLDER, PARSED_RESUMES_FILE, LOG_FILE
from utils import setup_logger, log_exceptions

setup_logger(LOG_FILE)
logger = logging.getLogger(__name__)

nltk.download("stopwords", quiet=True)
nltk.download("punkt", quiet=True)

# ------------ Skill Parsing Section ------------ #
@log_exceptions
def load_job_title_skill_map():
    job_skill_map = {}
    with open(KEYWORDS_FILE, mode='r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        for row in reader:
            job = row.get('Job Title', '').strip()
            skills_str = row.get('Skills', '').strip()
            if job and skills_str:
                job_skill_map[job] = skills_str
    return job_skill_map

@log_exceptions
def extract_skills_from_resume(resume_text, job_title, job_skill_map):
    resume_text = resume_text.lower()
    matched_skills = []
    fallback_skills = []

    def split_skills(skill_str):
        parts = re.split(r",| or | and |/|\\|;", skill_str, flags=re.IGNORECASE)
        cleaned = []
        for part in parts:
            part = part.strip().lower()
            part = re.sub(
                r"^(proficient in|experienced with|experience in|strong|good knowledge of|familiarity with|bachelor's in|master's in|related field|skills in|including)\s*",
                "", part)
            if part and len(part) > 1 and not part.startswith("("):
                cleaned.append(part)
        return cleaned

    for job, skills_str in job_skill_map.items():
        similarity = fuzz.token_sort_ratio(job.lower(), job_title.lower())
        skills = split_skills(skills_str)
        found = [sk for sk in skills if sk in resume_text]
        if similarity >= 70:
            matched_skills.extend(found)
        elif not matched_skills:
            fallback_skills.extend(found)

    return list(set(matched_skills)) if matched_skills else list(set(fallback_skills))

# ------------ Resume Parsing Section ------------ #

@log_exceptions
def extract_text_from_docx(path):
    doc = docx.Document(path)
    return "\n".join([p.text for p in doc.paragraphs])

@log_exceptions
def extract_text_from_pdf(path):
    text = ""
    with fitz.open(path) as doc:
        for page in doc:
            text += page.get_text()
    return text

@log_exceptions
def extract_name(text):
    for line in text.splitlines()[:10]:
        line = line.strip()
        if not line or any(char in line for char in "@/|•") or re.search(r'\d', line):
            continue
        if re.search(r"(analyst|engineer|manager|consultant|developer|nurse|student)", line.lower()):
            continue
        words = line.split()
        if len(words) >= 2 and all(word[0].isupper() for word in words if word.isalpha()):
            return line
    return ""

@log_exceptions
def extract_email(text):
    match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
    return match.group(0) if match else ""

@log_exceptions
def extract_phone(text):
    match = re.search(r"(\+?\d{1,2}[\s\-\.])?\(?\d{3}\)?[\s\-\.]?\d{3}[\s\-\.]?\d{4}", text)
    return match.group(0) if match else ""

@log_exceptions
def extract_education(text):
    lines = text.splitlines()
    capture = False
    edu_lines = []
    edu_block = ""
    for line in lines:
        if "education" in line.lower():
            capture = True
            continue
        if capture:
            line = line.strip()
            if not line or re.match(r"^[A-Z\s]{5,}$", line): break
            edu_lines.append(line)
            edu_block += " " + line
            if len(edu_lines) >= 3: break

    match = re.search(r"(Bachelor|Master|PhD|Doctor|Diploma|Certificate)[^0-9\n]*(?:in)?[^0-9\n]*?\b(?:19|20)\d{2}\b", edu_block, re.IGNORECASE)
    if match:
        entry = match.group().strip()
        year = re.search(r"\b(19|20)\d{2}\b", entry)
        year = int(year.group()) if year else None
        parts = entry.split(str(year)) if year else [entry]
        course = parts[0].strip()
        institution = parts[1].strip() if len(parts) > 1 else ""
    else:
        if len(edu_lines) < 2: return []
        course, institution = edu_lines[0], edu_lines[1]
        year_line = edu_lines[2] if len(edu_lines) > 2 else ""
        year = re.search(r"\b(19|20)\d{2}\b", year_line or institution)
        year = int(year.group()) if year else None

    level_map = {
        "bachelor": "Bachelor's", "master": "Master's",
        "phd": "PhD", "doctor": "PhD",
        "diploma": "Diploma", "certificate": "Certificate"
    }
    degree_level = next((v for k, v in level_map.items() if k in course.lower()), "N/A")

    return [{
        "level": degree_level,
        "course": course.strip(),
        "institution": institution.strip(),
        "year": year
    }]

@log_exceptions
def extract_job_title(text, job_titles):
    lines = [line.strip() for line in text.splitlines()[:10] if line.strip()]
    best_title = ""
    best_score = 0
    for ref_title in job_titles:
        for line in lines:
            score = fuzz.token_sort_ratio(ref_title.lower(), line.lower())
            if score > best_score:
                best_score, best_title = score, ref_title
    return best_title

@log_exceptions
def process_resumes():
    job_skill_map = load_job_title_skill_map()
    job_titles = list(job_skill_map.keys())

    os.makedirs(os.path.dirname(PARSED_RESUMES_FILE), exist_ok=True)

    with open(PARSED_RESUMES_FILE, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['resume_id', 'Name', 'Email', 'Phone', 'Education', 'Job Title', 'Skills'])

        idx = 1
        for file_name in os.listdir(RESUME_FOLDER):
            if not file_name.lower().endswith(('.pdf', '.docx')):
                continue

            path = os.path.join(RESUME_FOLDER, file_name)
            print(f" Processing: {file_name}")

            text = extract_text_from_pdf(path) if path.endswith('.pdf') else extract_text_from_docx(path)
            if not text.strip():
                print(f" Skipped empty or unreadable file: {file_name}")
                continue

            resume_id = f"RES{idx:04d}"
            idx += 1

            name = extract_name(text)
            email = extract_email(text)
            phone = extract_phone(text)
            education = extract_education(text)
            job_title = extract_job_title(text, job_titles)
            skills = extract_skills_from_resume(text, job_title, job_skill_map)

            edu_str = ""
            if education:
                edu = education[0]
                edu_str = ", ".join(filter(None, [edu['course'], edu['institution'], str(edu['year'])]))

            writer.writerow([
                resume_id,
                name,
                email,
                f"\t{phone}",  # force Excel to treat phone as text
                edu_str,
                job_title,
                "; ".join(skills)
            ])

    print(f"\n Parsed resumes saved to: {PARSED_RESUMES_FILE}")

if __name__ == "__main__":
    process_resumes()