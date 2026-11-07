"""
KJA IT Jobs AutoBot
Manual job submission -> scheduled Telegram channel posting.
Timezone: Asia/Kolkata. Maximum: 5 posts per day.
"""

import os
import re
import sqlite3
import logging
from datetime import time
from zoneinfo import ZoneInfo
from urllib.parse import urlparse

from telegram import Update
from telegram.ext import (
    Application, CommandHandler, ContextTypes, Defaults
)

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHANNEL_ID = os.environ["CHANNEL_ID"]  # e.g. @YourChannel or -1001234567890
ADMIN_IDS = {
    int(x.strip()) for x in os.environ.get("ADMIN_IDS", "").split(",")
    if x.strip()
}
TIMEZONE = ZoneInfo("Asia/Kolkata")
DB_PATH = os.environ.get("DB_PATH", "jobs.sqlite3")

# Five posting times in India time. Edit these if you prefer.
POST_TIMES = [
    time(9, 0, tzinfo=TIMEZONE),
    time(12, 0, tzinfo=TIMEZONE),
    time(15, 0, tzinfo=TIMEZONE),
    time(18, 0, tzinfo=TIMEZONE),
    time(20, 0, tzinfo=TIMEZONE),
]

IT_TERMS = {
    "software", "developer", "development", "programmer", "programming",
    "python", "java", "javascript", "react", "node", "php", "web",
    "android", "ios", "app", "mobile", "frontend", "front-end",
    "backend", "back-end", "full stack", "full-stack", "devops",
    "cloud", "data analyst", "data science", "machine learning",
    "artificial intelligence", "ai engineer", "qa", "testing",
    "automation tester", " cybersecurity", "cyber security", "sql",
    "database", "it support", "system administrator", "ui", "ux",
    "internship", "software engineer", "tech support"
}

INDIA_TERMS = {
    "india", "indian", "mumbai", "pune", "bengaluru", "bangalore",
    "hyderabad", "chennai", "delhi", "noida", "gurugram", "gurgaon",
    "kolkata", "ahmedabad", "jaipur", "indore", "bhopal", "jabalpur",
    "lucknow", "kochi", "remote india", "work from home india"
}

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                company TEXT NOT NULL,
                location TEXT NOT NULL,
                experience TEXT NOT NULL,
                description TEXT NOT NULL,
                apply_url TEXT NOT NULL UNIQUE,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                posted_at TEXT
            )
        """)


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def valid_url(url: str) -> bool:
    try:
        p = urlparse(url)
        return p.scheme in ("http", "https") and bool(p.netloc)
    except Exception:
        return False


def passes_filters(title: str, location: str, description: str) -> tuple[bool, str]:
    text = f"{title} {location} {description}".lower()
    if not any(term in text for term in IT_TERMS):
        return False, "यह पोस्ट Software/IT से संबंधित नहीं लगती।"
    if not any(term in text for term in INDIA_TERMS):
        return False, "India location स्पष्ट नहीं है। Location में India या भारतीय शहर लिखें।"
    return True, ""


def format_job(row) -> str:
    return (
        "🇮🇳 <b>INDIAN IT JOB ALERT</b>\n\n"
        f"💼 <b>{escape(row['title'])}</b>\n"
        f"🏢 Company: {escape(row['company'])}\n"
        f"📍 Location: {escape(row['location'])}\n"
        f"🎓 Experience: {escape(row['experience'])}\n\n"
        f"📝 {escape(row['description'])}\n\n"
        f"🔗 <a href=\"{escape(row['apply_url'])}\">Apply Now</a>\n\n"
        "#IndiaJobs #ITJobs #SoftwareJobs #FresherJobs\n"
        "<i>Posted by KJA IT Jobs AutoBot</i>"
    )


def escape(value: str) -> str:
    # Escape HTML for Telegram HTML parse mode.
    return (str(value).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Namaste! KJA IT Jobs AutoBot ready hai.\n\n"
        "Admin commands:\n"
        "/addjob - job add karne ka format dekhein\n"
        "/queue - pending jobs dekhein\n"
        "/postnow - queue se ek job abhi post karein\n"
        "/help - help"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Job add format (pipe | se alag karein):\n\n"
        "/addjob Job Title | Company | India Location | Experience | "
        "Description | https://apply-link\n\n"
        "Example:\n"
        "/addjob Python Developer | ABC Tech | Pune, India | 0-1 year | "
        "Python and Django role for freshers | https://company.example/jobs/123\n\n"
        "Sirf genuine Indian Software/IT jobs add karein. Apply link official "
        "company/careers page ka hona chahiye."
    )


async def addjob(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Sorry, sirf authorized admin jobs add kar sakta hai.")
        return

    raw = update.message.text.partition(" ")[2].strip()
    parts = [p.strip() for p in raw.split("|")]
    if len(parts) != 6 or not all(parts):
        await help_command(update, context)
        return

    title, company, location, experience, description, apply_url = parts
    if not valid_url(apply_url):
        await update.message.reply_text("Apply link valid http/https URL hona chahiye.")
        return

    ok, reason = passes_filters(title, location, description)
    if not ok:
        await update.message.reply_text("Job reject hui: " + reason)
        return

    try:
        with db() as conn:
            cur = conn.execute(
                """INSERT INTO jobs
                (title, company, location, experience, description, apply_url)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (title, company, location, experience, description, apply_url)
            )
            job_id = cur.lastrowid
        await update.message.reply_text(
            f"✅ Job #{job_id} queue mein add ho gayi. Daily schedule par post hogi."
        )
    except sqlite3.IntegrityError:
        await update.message.reply_text("⚠️ Ye apply link pehle se add hai (duplicate).")


async def queue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Admin only command.")
        return
    with db() as conn:
        rows = conn.execute(
            "SELECT id, title, company, location FROM jobs "
            "WHERE status='pending' ORDER BY id LIMIT 20"
        ).fetchall()
    if not rows:
        await update.message.reply_text("Queue khaali hai. /addjob se job add karein.")
        return
    lines = ["📋 <b>Pending Jobs</b>"]
    for r in rows:
        lines.append(
            f"#{r['id']} — {escape(r['title'])} | {escape(r['company'])} "
            f"| {escape(r['location'])}"
        )
    await update.message.reply_text("\n".join(lines), parse_mode="HTML")


async def post_one(application: Application) -> bool:
    with db() as conn:
        row = conn.execute(
            "SELECT * FROM jobs WHERE status='pending' ORDER BY id LIMIT 1"
        ).fetchone()
        if row is None:
            return False

        # Reserve the row before sending to avoid two scheduled tasks taking it.
        conn.execute(
            "UPDATE jobs SET status='sending' WHERE id=? AND status='pending'",
            (row["id"],)
        )

    try:
        await application.bot.send_message(
            chat_id=CHANNEL_ID,
            text=format_job(row),
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        with db() as conn:
            conn.execute(
                "UPDATE jobs SET status='posted', posted_at=CURRENT_TIMESTAMP WHERE id=?",
                (row["id"],)
            )
        logger.info("Posted job id=%s", row["id"])
        return True
    except Exception:
        logger.exception("Posting failed for job id=%s", row["id"])
        with db() as conn:
            conn.execute("UPDATE jobs SET status='pending' WHERE id=?", (row["id"],))
        return False


async def scheduled_post(context: ContextTypes.DEFAULT_TYPE):
    await post_one(context.application)


async def postnow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Admin only command.")
        return
    ok = await post_one(context.application)
    await update.message.reply_text(
        "✅ Channel par post ho gayi." if ok
        else "Abhi queue khaali hai ya posting fail hui. Logs check karein."
    )


async def post_init(application: Application):
    # Five scheduled attempts daily. Empty queue means nothing is posted.
    for idx, post_time in enumerate(POST_TIMES):
        application.job_queue.run_daily(
            scheduled_post,
            time=post_time,
            name=f"daily_post_{idx + 1}"
        )


def main():
    if not ADMIN_IDS:
        raise RuntimeError("ADMIN_IDS set karein. Apni Telegram numeric user ID add karein.")
    init_db()
    defaults = Defaults(tzinfo=TIMEZONE)
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .defaults(defaults)
        .post_init(post_init)
        .build()
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("addjob", addjob))
    app.add_handler(CommandHandler("queue", queue))
    app.add_handler(CommandHandler("postnow", postnow))
    logger.info("KJA IT Jobs AutoBot starting...")
    app.run_polling()


if __name__ == "__main__":
    main()
