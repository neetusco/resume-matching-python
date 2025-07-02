# Resume Matching System (Capstone Project)

This Python-based project automates the process of parsing resumes and matching them to job descriptions using rule-based scoring. Built as part of a capstone project in collaboration with a 4-member team.

---

## Quick Setup

**For detailed setup steps, see:** [environment_setup_instructions.txt]

This includes instructions for setting up your Python environment using Anaconda Navigator and running the project in Visual Studio Code.

---

## Features

- Parses resumes (PDF, DOCX) to extract name, email, phone, skills, and education
- Parses job descriptions to identify required and preferred skills
- Matches resumes to job descriptions using scoring logic
- Outputs a ranked list of candidates in CSV format

---

## Project Structure

resume-matching-python/
├── resumes/ # Sample resumes
├── job_descriptions/ # Sample job descriptions
├── output/ # Matching result CSVs
├── scripts/ # All Python logic modules
│ ├── resume_parser.py
│ ├── jd_parser.py
│ ├── matcher.py
│ └── utils.py
├── requirements.txt # Python dependencies
├── setup_instructions.txt # Environment setup guide
├── main.py # Main driver script
└── README.md # Project overview

Team Members:

Neetika Upadhyay (Team Lead)
Prajna Ganji
Maruta Zalane
Shiva