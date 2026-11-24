# job_fetcher.py

import requests
import sqlite3
import re
from datetime import datetime, timezone

DB_NAME = "jobmatch.db"
API_URL = "https://remotive.com/api/remote-jobs"

SKILL_KEYWORDS = [
    "python", "java", "c++", "c", "sql", "javascript", "html", "css",
    "react", "node.js", "django", "flask", "machine learning", "ai",
    "numpy", "pandas", "git", "linux", "aws", "docker", "api",
    "mongodb", "postgresql", "excel", "data analysis"
]


def initialize_jobs_table():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            source_job_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            skills TEXT,
            job_type TEXT,
            location TEXT,
            level TEXT,
            link TEXT NOT NULL,
            description TEXT,
            source TEXT,
            fetched_at TEXT
        )
    """)
    conn.commit()
    conn.close()


def extract_skills(text):
    text = text.lower()
    found = []

    for skill in SKILL_KEYWORDS:
        if skill == "c":
            if re.search(r"\bc\b", text):
                found.append(skill)
        elif skill == "c++":
            if "c++" in text:
                found.append(skill)
        elif skill in text:
            found.append(skill)

    return ", ".join(sorted(set(found)))


def infer_level(text):
    text = text.lower()

    beginner_keywords = [
        "junior", "entry level", "entry-level", "intern",
        "graduate", "early career", "new grad"
    ]

    intermediate_keywords = [
        "mid-level", "mid level", "intermediate"
    ]

    senior_keywords = [
        "senior", "lead", "principal", "staff"
    ]

    if any(word in text for word in senior_keywords):
        return "Advanced"

    if any(word in text for word in intermediate_keywords):
        return "Intermediate"

    if any(word in text for word in beginner_keywords):
        return "Beginner"

    return "Unknown"


def normalize_job(job):
    title = job.get("title", "")
    description = job.get("description", "")
    combined_text = f"{title} {description}"

    raw_job_type = (job.get("job_type") or "").lower()

    type_mapping = {
        "full_time": "Full-time",
        "part_time": "Part-time",
        "contract": "Contract",
        "freelance": "Freelance",
        "internship": "Internship"
    }

    job_type = type_mapping.get(raw_job_type, raw_job_type.title() or "Unknown")

    location = job.get("candidate_required_location") or "Remote"

    return {
        "id": str(job.get("id")),
        "title": title,
        "company": job.get("company_name", "Unknown"),
        "skills": extract_skills(combined_text),
        "job_type": job_type,
        "location": location,
        "level": infer_level(combined_text),
        "link": job.get("url", ""),
        "description": description,
        "source": "Remotive"
    }


def fetch_jobs(search=None, limit=100):
    params = {"limit": limit}

    if search:
        params["search"] = search

    response = requests.get(
        API_URL,
        params=params,
        timeout=30,
        headers={"User-Agent": "JobMatchBot development project"}
    )

    response.raise_for_status()
    data = response.json()

    return data.get("jobs", [])


def save_jobs(jobs):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    now = datetime.now(timezone.utc).isoformat()
    saved = 0

    for raw_job in jobs:
        job = normalize_job(raw_job)

        if not job["id"] or not job["link"]:
            continue

        cursor.execute("""
            INSERT OR IGNORE INTO jobs (
                source_job_id, title, company, skills, job_type,
                location, level, link, description, source, fetched_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            job["id"],
            job["title"],
            job["company"],
            job["skills"],
            job["job_type"],
            job["location"],
            job["level"],
            job["link"],
            job["description"],
            job["source"],
            now
        ))

        if cursor.rowcount > 0:
            saved += 1

    conn.commit()
    conn.close()

    return saved


def refresh_jobs(search=None, limit=100):
    initialize_jobs_table()
    raw_jobs = fetch_jobs(search=search, limit=limit)
    saved = save_jobs(raw_jobs)

    return len(raw_jobs), saved


if __name__ == "__main__":
    try:
        fetched, saved = refresh_jobs(limit=100)

        print(f"Fetched {fetched} jobs from Remotive.")
        print(f"Added {saved} new jobs to the database.")

    except requests.RequestException as error:
        print("API request failed:", error)

    except Exception as error:
        print("Unexpected error:", error)