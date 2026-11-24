import csv
import sqlite3

DB_NAME = "jobmatch.db"


def load_csv_jobs(filename="data/jobs.csv"):
    try:
        with open(filename, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            return list(reader)
    except FileNotFoundError:
        return []


def load_database_jobs():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT source_job_id, title, company, skills, job_type,
                   location, level, link, description, source
            FROM jobs
        """)

        rows = cursor.fetchall()

    except sqlite3.OperationalError:
        rows = []

    conn.close()

    jobs = []

    for row in rows:
        jobs.append({
            "id": row[0],
            "title": row[1],
            "company": row[2],
            "skills": row[3] or "",
            "job_type": row[4] or "",
            "location": row[5] or "",
            "level": row[6] or "",
            "link": row[7] or "",
            "description": row[8] or "",
            "source": row[9] or "Unknown"
        })

    return jobs


def load_jobs():
    database_jobs = load_database_jobs()

    # Use real API data whenever available.
    # CSV remains our fallback for development.
    if database_jobs:
        return database_jobs

    return load_csv_jobs()

def score_job(job, preferences):
    score = 0
    reasons = []

    title = job.get("title", "").lower()
    actual_level = job.get("level", "").strip().lower()

    # Detect seniority directly from job titles
    senior_keywords = [
        "senior", "sr.", "lead", "principal", "staff",
        "architect", "director", "manager", "head of"
    ]

    beginner_keywords = [
        "intern", "internship", "junior", "entry level",
        "entry-level", "graduate", "trainee"
    ]

    is_senior = any(word in title for word in senior_keywords)
    is_beginner = any(word in title for word in beginner_keywords)

    # Skills matching
    user_skills = {
        skill.strip().lower()
        for skill in preferences.get("skills", "").split(",")
        if skill.strip()
    }

    job_skills = {
        skill.strip().lower()
        for skill in job.get("skills", "").split(",")
        if skill.strip()
    }

    matching_skills = user_skills.intersection(job_skills)

    score += len(matching_skills) * 3

    if matching_skills:
        reasons.append(
            "Matching skills: " + ", ".join(sorted(matching_skills))
        )

    # Job type matching
    preferred_type = preferences.get("job_type", "").strip().lower()
    actual_type = job.get("job_type", "").strip().lower()

    if preferred_type and actual_type:
        if preferred_type == actual_type:
            score += 2
            reasons.append("Preferred job type")
        else:
            score -= 3

    # Location matching
    preferred_location = preferences.get("location", "").strip().lower()
    actual_location = job.get("location", "").strip().lower()

    if preferred_location and actual_location:
        if preferred_location == actual_location:
            score += 2
            reasons.append("Preferred location")

        elif preferred_location == "remote" and (
            "remote" in actual_location or
            "worldwide" in actual_location or
            "anywhere" in actual_location
        ):
            score += 2
            reasons.append("Remote location")

    # Experience-level matching
    preferred_level = preferences.get("level", "").strip().lower()

    if preferred_level == "beginner":
        if is_senior or actual_level == "advanced":
            score -= 8
            reasons.append("Penalty: senior/advanced role")

        elif is_beginner or actual_level == "beginner":
            score += 3
            reasons.append("Beginner-friendly role")

    elif preferred_level == "intermediate":
        if actual_level == "intermediate":
            score += 2
            reasons.append("Suitable experience level")

        elif is_senior:
            score -= 5

    elif preferred_level == "advanced":
        if is_senior or actual_level == "advanced":
            score += 2
            reasons.append("Advanced role")

    return score, reasons


def get_matches(preferences, limit=3):
    jobs = load_jobs()
    results = []

    preferred_type = preferences.get("job_type", "").strip().lower()
    preferred_level = preferences.get("level", "").strip().lower()

    senior_keywords = [
        "senior", "sr.", "lead", "principal", "staff",
        "architect", "director", "manager", "head of"
    ]

    beginner_keywords = [
        "intern", "internship", "junior", "entry level",
        "entry-level", "graduate", "trainee"
    ]

    for job in jobs:
        title = job.get("title", "").lower()
        actual_type = job.get("job_type", "").strip().lower()
        actual_level = job.get("level", "").strip().lower()

        # Strict job type filtering
        if preferred_type and actual_type:
            if preferred_type != actual_type:
                continue

        # Exclude clearly senior jobs for beginners
        if preferred_level == "beginner":
            if any(word in title for word in senior_keywords):
                continue

            if actual_level == "advanced":
                continue

        # Score eligible jobs
        score, reasons = score_job(job, preferences)

        # Require at least one meaningful match
        if score > 0:
            results.append({
                "job": job,
                "score": score,
                "reasons": reasons
            })

    results.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    return results[:limit]