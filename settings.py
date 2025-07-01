# settings.py
# Input paths
RESUME_FOLDER = "input/resumes/"
JD_FOLDER = "input/job_descriptions/"
KEYWORDS_FILE = "input/other/Health_Canada_Jobs_With_Skills_1.csv"

# Output paths
PARSED_RESUMES_FILE = "output/parsed_resumes.csv"
PARSED_JD_FILE = "output/parsed_job_skills.csv"
MATCH_RESULTS_FILE = "output/resume_match_results.csv"

# Logging
LOG_FILE = "output/logs/errors.log"

# Aliases for backward compatibility
RESUME_FILE = PARSED_RESUMES_FILE
JOB_SKILL_FILE = PARSED_JD_FILE