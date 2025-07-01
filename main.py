import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'project_root')))

# Import scripts
from Scripts.resume_parser import process_resumes
from Scripts.job_parser import parse_jobs
from Scripts.matcher import match_all_resumes

def main():
    print("\n--- Starting Resume Parsing ---")
    process_resumes()

    print("\n--- Starting Job Description Parsing ---")
    parse_jobs()

    print("\n--- Starting Resume-Job Matching ---")
    match_all_resumes()

    print("\n✅ All processes completed successfully.")

if __name__ == "__main__":
    main()
