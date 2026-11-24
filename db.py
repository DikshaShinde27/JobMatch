import sqlite3

DB_NAME = "jobmatch.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


def initialize_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS preferences (
            user_id INTEGER PRIMARY KEY,
            skills TEXT,
            job_type TEXT,
            location TEXT,
            level TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    cursor.execute("""
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


if __name__ == "__main__":
    initialize_database()
    print("Database initialized successfully!")