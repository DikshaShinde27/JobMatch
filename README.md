# JobMatch 🤖

A Telegram-based job matching bot that helps users discover relevant job opportunities based on their skills, preferred job type, location and experience level.

## Features

- User preference collection and storage
- Skill-based job matching and ranking
- Job-type filtering
- Experience-level eligibility filtering
- Senior-role detection and penalties
- SQLite database integration
- Real job data ingestion through an external API
- Duplicate job prevention
- Telegram bot interface

## Tech Stack

- Python
- Telegram Bot API
- SQLite
- REST API
- Requests

## Project Structure

```text
job-match-bot/
├── bot.py
├── db.py
├── matcher.py
├── job_fetcher.py
├── llm.py
├── data/
│   └── jobs.csv
├── tests/
├── requirements.txt
├── .env.example
└── README.md