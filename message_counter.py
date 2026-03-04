from database import db
from datetime import datetime, date
import logging
import random
import time

COOLDOWN = 10  # seconds

async def add_xp(user_id, group_id, message_length):
    """Add XP to user based on message activity."""
    now = int(time.time())
    user = await db.xp_users.find_one({"user_id": user_id, "group_id": group_id})

    if user and now - user.get("last_message", 0) < COOLDOWN:
        return False

    xp_gain = random.randint(3, 8)

    if message_length > 50:
        xp_gain += 5  # bonus xp for quality message

    new_xp = (user["xp"] if user else 0) + xp_gain
    level = int((new_xp / 50) ** 0.5) + 1

    update_data = {
        "xp": new_xp,
        "level": level,
        "last_message": now
    }

    # Check for prestige
    if level >= 50:
        update_data["prestige"] = (user["prestige"] if user else 0) + 1
        update_data["xp"] = 0
        update_data["level"] = 1

    await db.xp_users.update_one(
        {"user_id": user_id, "group_id": group_id},
        {"$set": update_data},
        upsert=True
    )
    
    return True

async def count_message(update, context):
    """
    Count a message for the user in the group.
    Updates user stats, group stats, and daily stats.
    """
    user = update.effective_user
    chat = update.effective_chat

    if chat.type not in ["group", "supergroup"]:
        return
    
    # Check if message tracking is enabled for this group
    track_enabled = await db.get_group_tracking_status(chat.id)
    if not track_enabled:
        return  # Skip counting if tracking is disabled

    # Get today's date
    today = date.today()
    
    try:
        async with db.pool.acquire() as conn:
            # Insert or update user stats
            await conn.execute("""
                INSERT INTO users (id, username, first_name, total_messages, weekly_messages, daily_messages)
                VALUES ($1, $2, $3, 1, 1, 1)
                ON CONFLICT (id)
                DO UPDATE SET 
                    username = EXCLUDED.username,
                    first_name = EXCLUDED.first_name,
                    total_messages = users.total_messages + 1,
                    weekly_messages = users.weekly_messages + 1,
                    daily_messages = users.daily_messages + 1
            """, user.id, user.username, user.first_name)

            # Insert or update group stats
            await conn.execute("""
                INSERT INTO groups (group_id, user_id, total, weekly, daily)
                VALUES ($1, $2, 1, 1, 1)
                ON CONFLICT (group_id, user_id)
                DO UPDATE SET 
                    total = groups.total + 1,
                    weekly = groups.weekly + 1,
                    daily = groups.daily + 1
            """, chat.id, user.id)

            # Insert or update daily stats
            await conn.execute("""
                INSERT INTO daily_stats (user_id, group_id, date, message_count)
                VALUES ($1, $2, $3, 1)
                ON CONFLICT (user_id, group_id, date)
                DO UPDATE SET 
                    message_count = daily_stats.message_count + 1
            """, user.id, chat.id, today)
            
            # Update group info
            await db.update_group_info(chat.id, chat.title)
            
        # Add XP system
        message_length = len(update.message.text) if update.message.text else 0
        await add_xp(user.id, chat.id, message_length)
        
        logging.info(f"Message counted for user {user.id} in group {chat.id}")
    except Exception as e:
        logging.error(f"Error counting message: {e}")


async def update_user_info(user_id, username, first_name):
    """
    Update user info in the database.
    """
    try:
        async with db.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO users (id, username, first_name, total_messages, weekly_messages, daily_messages)
                VALUES ($1, $2, $3, 0, 0, 0)
                ON CONFLICT (id)
                DO UPDATE SET 
                    username = EXCLUDED.username,
                    first_name = EXCLUDED.first_name
            """, user_id, username, first_name)
    except Exception as e:
        logging.error(f"Error updating user info: {e}")
