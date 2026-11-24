import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from db import get_connection, initialize_database
from matcher import get_matches

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hey! 👋 I'm JobMatch Bot.\n"
        "I'll help you find jobs matching your preferences!\n\n"
        "Use /prefs to set your job preferences."
    )


async def prefs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Send your preferences in this format:\n\n"
        "Skills: Python, Java\n"
        "Job type: Internship\n"
        "Location: Remote\n"
        "Level: Beginner"
    )

async def save_preferences(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text
    if message.strip().startswith("/"):
        return
    user = update.effective_user

    lines = message.split("\n")
    data = {}

    for line in lines:
        if ":" in line:
            key, value = line.split(":", 1)
            data[key.strip().lower()] = value.strip()

    skills = data.get("skills", "")
    job_type = data.get("job type", "")
    location = data.get("location", "")
    level = data.get("level", "")

    if not any([skills, job_type, location, level]):
        await update.message.reply_text(
            "I couldn't understand your preferences 😅\n\n"
            "Please send them in this format:\n"
            "Skills: Python, Java\n"
            "Job type: Internship\n"
            "Location: Remote\n"
            "Level: Beginner"
        )
        return

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)",
        (user.id, user.username)
    )

    cursor.execute(
        """
        INSERT OR REPLACE INTO preferences
        (user_id, skills, job_type, location, level)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user.id, skills, job_type, location, level)
    )

    conn.commit()
    conn.close()

    await update.message.reply_text(
        "Your preferences have been saved! 🎉\n\n"
        f"Skills: {skills}\n"
        f"Job type: {job_type}\n"
        f"Location: {location}\n"
        f"Level: {level}"
    )

async def myprefs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT skills, job_type, location, level FROM preferences WHERE user_id = ?",
        (user_id,)
    )

    result = cursor.fetchone()
    conn.close()

    if result:
        skills, job_type, location, level = result

        await update.message.reply_text(
            "Here's what I remember about you! 🧠\n\n"
            f"Skills: {skills}\n"
            f"Job type: {job_type}\n"
            f"Location: {location}\n"
            f"Level: {level}"
        )
    else:
        await update.message.reply_text(
            "I couldn't find your preferences. Use /prefs first!"
        )

async def matches(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT skills, job_type, location, level FROM preferences WHERE user_id = ?",
        (user_id,)
    )

    result = cursor.fetchone()
    conn.close()

    if not result:
        await update.message.reply_text(
            "You haven't saved your preferences yet! 😅\n"
            "Use /prefs to set them first."
        )
        return

    skills, job_type, location, level = result

    preferences = {
        "skills": skills or "",
        "job_type": job_type or "",
        "location": location or "",
        "level": level or "",
    }

    if not any(preferences.values()):
        await update.message.reply_text(
            "Your preferences appear to be empty 😅\n"
            "Please use /prefs and send your preferences again."
        )
        return

    results = get_matches(preferences, limit=3)

    if not results:
        await update.message.reply_text(
            "I couldn't find matching jobs right now. 😔"
        )
        return

    response = "🔎 Your Top Job Matches!\n\n"

    for index, item in enumerate(results, start=1):
        job = item["job"]
        score = item["score"]
        reasons = item["reasons"]

        response += (
            f"{index}. {job['title']}\n"
            f"🏢 Company: {job['company']}\n"
            f"📍 Location: {job['location']}\n"
            f"💼 Type: {job['job_type']}\n"
            f"🎯 Level: {job['level']}\n"
            f"⭐ Match Score: {score}\n"
            f"✅ {', '.join(reasons)}\n"
            f"🔗 {job['link']}\n"
        )

        if job.get("source") == "Remotive":
            response += "📌 Source: Remotive\n"

        response += "\n"

    await update.message.reply_text(response)

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM preferences WHERE user_id = ?",
        (user_id,)
    )

    conn.commit()
    conn.close()

    await update.message.reply_text(
        "Your preferences have been reset! 🧹\n\n"
        "Use /prefs whenever you'd like to set them again."
    )


def main():
    initialize_database()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("prefs", prefs))
    app.add_handler(CommandHandler("myprefs", myprefs))
    app.add_handler(CommandHandler("matches", matches))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, save_preferences))


    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()