import os
import sqlite3
import math
import asyncio
from datetime import datetime, date

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    CommandHandler,
    CallbackQueryHandler,
    filters
)

from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Load environment variables from .env file
try:
    with open('.env', 'r') as f:
        for line in f:
            if '=' in line:
                key, value = line.strip().split('=', 1)
                os.environ[key] = value
except FileNotFoundError:
    pass  # .env file doesn't exist, that's ok

# Load bot token from environment
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')

# ================= DATABASE ================= #

conn = sqlite3.connect("chatrank.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER,
    group_id INTEGER,
    username TEXT,
    xp INTEGER DEFAULT 0,
    daily_xp INTEGER DEFAULT 0,
    weekly_xp INTEGER DEFAULT 0,
    total_messages INTEGER DEFAULT 0,
    daily_messages INTEGER DEFAULT 0,
    weekly_messages INTEGER DEFAULT 0,
    last_active TEXT,
    streak INTEGER DEFAULT 0,
    PRIMARY KEY (user_id, group_id)
)
""")

conn.commit()

# ================= UTILITIES ================= #

def calculate_level(xp: int):
    return int(math.sqrt(xp / 100)) if xp > 0 else 0


def get_rank_badge(level):
    if level >= 50:
        return "💎 Legend"
    elif level >= 30:
        return "👑 King"
    elif level >= 15:
        return "🥇 Elite"
    elif level >= 5:
        return "🥈 Pro"
    else:
        return "🥉 Rookie"


def add_xp(message):
    if message.text:
        return 5
    elif message.photo:
        return 10
    elif message.voice:
        return 12
    else:
        return 5


# ================= MESSAGE HANDLER ================= #

async def count_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type not in ["group", "supergroup"]:
        return

    if update.effective_user.is_bot:
        return

    message = update.message
    user = update.effective_user
    group_id = update.effective_chat.id
    today = str(date.today())

    # Anti spam (ignore short messages)
    if message.text and len(message.text) < 3:
        return

    xp_gain = add_xp(message)

    cursor.execute("""
    SELECT xp, daily_xp, weekly_xp, total_messages, daily_messages, weekly_messages, last_active, streak
    FROM users WHERE user_id=? AND group_id=?
    """, (user.id, group_id))

    row = cursor.fetchone()

    if row:
        xp, daily_xp, weekly_xp, total_msg, daily_msg, weekly_msg, last_active, streak = row

        # Streak logic
        if last_active != today:
            streak += 1
        else:
            streak = streak

        cursor.execute("""
        UPDATE users SET
        xp=?,
        daily_xp=?,
        weekly_xp=?,
        total_messages=?,
        daily_messages=?,
        weekly_messages=?,
        last_active=?,
        streak=?
        WHERE user_id=? AND group_id=?
        """, (
            xp + xp_gain,
            daily_xp + xp_gain,
            weekly_xp + xp_gain,
            total_msg + 1,
            daily_msg + 1,
            weekly_msg + 1,
            today,
            streak,
            user.id,
            group_id
        ))

    else:
        cursor.execute("""
        INSERT INTO users VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (
            user.id,
            group_id,
            user.username,
            xp_gain,
            xp_gain,
            xp_gain,
            1,
            1,
            1,
            today,
            1
        ))

    conn.commit()


# ================= LEADERBOARD ================= #

def leaderboard_menu():
    keyboard = [
        [
            InlineKeyboardButton("📅 Daily", callback_data="daily"),
            InlineKeyboardButton("📊 Weekly", callback_data="weekly")
        ],
        [
            InlineKeyboardButton("🏆 All Time", callback_data="alltime")
        ],
        [
            InlineKeyboardButton("🌍 Global", callback_data="global")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏆 Choose Leaderboard Type",
        reply_markup=leaderboard_menu()
    )


async def leaderboard_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    group_id = query.message.chat.id
    mode = query.data

    if mode == "daily":
        cursor.execute("""
        SELECT username, daily_xp FROM users
        WHERE group_id=?
        ORDER BY daily_xp DESC LIMIT 10
        """, (group_id,))
    elif mode == "weekly":
        cursor.execute("""
        SELECT username, weekly_xp FROM users
        WHERE group_id=?
        ORDER BY weekly_xp DESC LIMIT 10
        """, (group_id,))
    elif mode == "alltime":
        cursor.execute("""
        SELECT username, xp FROM users
        WHERE group_id=?
        ORDER BY xp DESC LIMIT 10
        """, (group_id,))
    elif mode == "global":
        cursor.execute("""
        SELECT username, SUM(xp) as total FROM users
        GROUP BY user_id
        ORDER BY total DESC LIMIT 10
        """)

    rows = cursor.fetchall()

    text = "🏆 Leaderboard\n\n"
    for i, row in enumerate(rows, start=1):
        text += f"{i}. @{row[0]} — {row[1]} XP\n"

    await query.edit_message_text(text)


# ================= MY STATS ================= #

async def mystats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    group_id = update.effective_chat.id

    cursor.execute("""
    SELECT xp, total_messages, streak FROM users
    WHERE user_id=? AND group_id=?
    """, (user.id, group_id))

    row = cursor.fetchone()

    if not row:
        await update.message.reply_text("No stats yet.")
        return

    xp, total_msg, streak = row
    level = calculate_level(xp)
    badge = get_rank_badge(level)

    text = f"""
📊 Your Stats

👤 {user.first_name}
🎖 Level: {level}
🏅 Rank: {badge}
⚡ XP: {xp}
💬 Messages: {total_msg}
🔥 Streak: {streak} days
"""

    await update.message.reply_text(text)


# ================= RESET SYSTEM ================= #

async def reset_daily():
    cursor.execute("UPDATE users SET daily_xp=0, daily_messages=0")
    conn.commit()


async def reset_weekly():
    cursor.execute("UPDATE users SET weekly_xp=0, weekly_messages=0")
    conn.commit()


# ================= MAIN ================= #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_message = """🚀 <b>WELCOME TO THE CHAT RANK ARENA!</b> 🚀

<b>This isn't just a group... it's a battlefield!</b> 💬⚔️

🎯 <b>Earn XP, Level Up, Climb The Leaderboard</b> 🏆
📊 Compete Daily • Weekly • All-Time

🔥 Send Messages  
⚡ Earn XP  
🎖 Unlock Badges  
👑 Become The Chat King  

Use /mystats to check your progress 📊  
Use /leaderboard to see the top warriors 🏆

Let the chat battle begin! 🔥👑"""

    await update.message.reply_text(welcome_message, parse_mode='HTML')


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL, count_message))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.add_handler(CommandHandler("mystats", mystats))
    app.add_handler(CallbackQueryHandler(leaderboard_callback))

    scheduler = AsyncIOScheduler()
    scheduler.add_job(reset_daily, "cron", hour=0)
    scheduler.add_job(reset_weekly, "cron", day_of_week="mon", hour=0)
    scheduler.start()

    print("Bot Running...")
    app.run_polling()


if __name__ == "__main__":
    main()