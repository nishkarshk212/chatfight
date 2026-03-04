from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database import db
from rank_cards import generate_rank_card, generate_leaderboard_image
import logging

logger = logging.getLogger(__name__)


async def get_xp_stats(update, context):
    """Get user's XP statistics."""
    user = update.effective_user
    chat = update.effective_chat
    
    if chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("This command can only be used in groups.")
        return
    
    # Get user's XP data from MongoDB
    xp_user = await db.xp_users.find_one({"user_id": user.id, "group_id": chat.id})
    
    if not xp_user:
        await update.message.reply_text(
            f"📊 No XP data yet!\n\n"
            f"Start sending messages to earn XP and level up! 💬"
        )
        return
    
    xp = xp_user.get("xp", 0)
    level = xp_user.get("level", 1)
    prestige = xp_user.get("prestige", 0)
    
    # Generate rank card
    rank_card_path = await generate_rank_card(xp_user, xp, level, prestige)
    
    # Send rank card with stats
    caption = (
        f"🎖 **Your Rank Stats**\n\n"
        f"⭐ Level: {level}\n"
        f"✨ XP: {xp}\n"
        f"🎖 Prestige: {prestige}\n"
        f"💬 Keep messaging to climb higher!"
    )
    
    try:
        with open(rank_card_path, 'rb') as photo:
            await update.message.reply_photo(photo=photo, caption=caption)
    except Exception as e:
        logger.error(f"Error sending rank card: {e}")
        await update.message.reply_text(caption)


async def xp_leaderboard(update, context):
    """Show the XP leaderboard."""
    chat = update.effective_chat
    
    if chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("This command can only be used in groups.")
        return
    
    # Get top users by XP from MongoDB
    top_users = await db.xp_users.find(
        {"group_id": chat.id}
    ).sort("xp", -1).limit(10).to_list(length=10)
    
    if not top_users:
        await update.message.reply_text("No XP data available yet. Start messaging!")
        return
    
    # Generate leaderboard image
    leaderboard_path = await generate_leaderboard_image(top_users)
    
    # Format leaderboard text
    medals = ["🥇", "🥈", "🥉"]
    leaderboard_text = f"🏆 **XP Leaderboard - {chat.title}** 🏆\n\n"
    
    for i, user in enumerate(top_users):
        if i < 3:
            medal = medals[i]
        else:
            medal = f"{i+1}."
        
        username = user.get("username") or user.get("first_name") or "Unknown"
        level = user.get("level", 1)
        xp = user.get("xp", 0)
        
        leaderboard_text += f"{medal} {username} - Lvl {level} ({xp} XP)\n"
    
    # Send both image and text
    try:
        with open(leaderboard_path, 'rb') as photo:
            await update.message.reply_photo(photo=photo, caption=leaderboard_text)
    except Exception as e:
        logger.error(f"Error sending leaderboard: {e}")
        await update.message.reply_text(leaderboard_text)


async def daily_xp_command(update, context):
    """Show daily XP leaderboard."""
    chat = update.effective_chat
    
    if chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("This command can only be used in groups.")
        return
    
    # Get users sorted by daily XP
    top_users = await db.xp_users.find(
        {"group_id": chat.id}
    ).sort("daily_xp", -1).limit(10).to_list(length=10)
    
    if not top_users:
        await update.message.reply_text("No daily XP data available yet.")
        return
    
    medals = ["🥇", "🥈", "🥉"]
    daily_text = f"🔥 **Daily XP Leaders - {chat.title}** 🔥\n\n"
    
    for i, user in enumerate(top_users):
        medal = medals[i] if i < 3 else f"{i+1}."
        username = user.get("username") or user.get("first_name") or "Unknown"
        daily_xp = user.get("daily_xp", 0)
        
        daily_text += f"{medal} {username} - {daily_xp} XP\n"
    
    await update.message.reply_text(daily_text)


async def weekly_xp_command(update, context):
    """Show weekly XP leaderboard."""
    chat = update.effective_chat
    
    if chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("This command can only be used in groups.")
        return
    
    # Get users sorted by weekly XP
    top_users = await db.xp_users.find(
        {"group_id": chat.id}
    ).sort("weekly_xp", -1).limit(10).to_list(length=10)
    
    if not top_users:
        await update.message.reply_text("No weekly XP data available yet.")
        return
    
    medals = ["🥇", "🥈", "🥉"]
    weekly_text = f"📅 **Weekly XP Leaders - {chat.title}** 📅\n\n"
    
    for i, user in enumerate(top_users):
        medal = medals[i] if i < 3 else f"{i+1}."
        username = user.get("username") or user.get("first_name") or "Unknown"
        weekly_xp = user.get("weekly_xp", 0)
        
        weekly_text += f"{medal} {username} - {weekly_xp} XP\n"
    
    await update.message.reply_text(weekly_text)


async def monthly_xp_command(update, context):
    """Show monthly XP leaderboard."""
    chat = update.effective_chat
    
    if chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("This command can only be used in groups.")
        return
    
    # Get users sorted by monthly XP
    top_users = await db.xp_users.find(
        {"group_id": chat.id}
    ).sort("monthly_xp", -1).limit(10).to_list(length=10)
    
    if not top_users:
        await update.message.reply_text("No monthly XP data available yet.")
        return
    
    medals = ["🥇", "🥈", "🥉"]
    monthly_text = f"🌙 **Monthly XP Leaders - {chat.title}** 🌙\n\n"
    
    for i, user in enumerate(top_users):
        medal = medals[i] if i < 3 else f"{i+1}."
        username = user.get("username") or user.get("first_name") or "Unknown"
        monthly_xp = user.get("monthly_xp", 0)
        
        monthly_text += f"{medal} {username} - {monthly_xp} XP\n"
    
    await update.message.reply_text(monthly_text)


async def global_xp_leaderboard(update, context):
    """Show global XP leaderboard across all groups."""
    # Get top users globally
    top_users = await db.xp_users.find({}).sort("xp", -1).limit(10).to_list(length=10)
    
    if not top_users:
        await update.message.reply_text("No global XP data available yet.")
        return
    
    medals = ["🥇", "🥈", "🥉"]
    global_text = "🌍 **Global XP Leaderboard** 🌍\n\n"
    
    for i, user in enumerate(top_users):
        medal = medals[i] if i < 3 else f"{i+1}."
        username = user.get("username") or user.get("first_name") or "Unknown"
        level = user.get("level", 1)
        xp = user.get("xp", 0)
        
        global_text += f"{medal} {username} - Lvl {level} ({xp} XP)\n"
    
    await update.message.reply_text(global_text)


async def xp_settings_menu(update, context):
    """Show XP settings menu for admins."""
    user = update.effective_user
    chat = update.effective_chat
    
    # Check if user is admin
    if chat.type in ["group", "supergroup"]:
        chat_member = await context.bot.get_chat_member(chat.id, user.id)
        if chat_member.status not in ['administrator', 'creator']:
            await update.message.reply_text("⛔ Only admins can access this menu.")
            return
    
    keyboard = [
        [InlineKeyboardButton("⚙ XP Multiplier", callback_data="xp_multiplier")],
        [InlineKeyboardButton("⏱ Toggle Cooldown", callback_data="toggle_cooldown")],
        [InlineKeyboardButton("🔄 Reset Leaderboard", callback_data="reset_leaderboard")],
        [InlineKeyboardButton("🎖 Enable Prestige", callback_data="enable_prestige")],
        [InlineKeyboardButton("🌍 Enable Global Rank", callback_data="enable_global")],
        [InlineKeyboardButton("❌ Close Panel", callback_data="close_panel")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    settings_text = (
        "⚙ **Ranking Settings**\n\n"
        f"Group: {chat.title if chat.type != 'private' else 'Private Chat'}\n\n"
        "Choose an option to configure:"
    )
    
    if update.message:
        await update.message.reply_text(settings_text, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.edit_message_text(settings_text, reply_markup=reply_markup)


async def handle_xp_settings_callback(update, context):
    """Handle XP settings panel callbacks."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "xp_multiplier":
        await query.edit_message_text(
            "⚙ **XP Multiplier Settings**\n\n"
            "Current: 1.0x\n\n"
            "Adjust the XP gain multiplier for this group."
        )
    elif data == "toggle_cooldown":
        await query.edit_message_text(
            "⏱ **Message Cooldown**\n\n"
            "Currently: ENABLED (10s)\n\n"
            "Prevents XP farming by limiting XP gains per message."
        )
    elif data == "reset_leaderboard":
        await query.edit_message_text(
            "🔄 **Reset Leaderboard**\n\n"
            "This will reset all XP data for this group.\n\n"
            "⚠ This action cannot be undone!"
        )
    elif data == "enable_prestige":
        await query.edit_message_text(
            "🎖 **Prestige System**\n\n"
            "Status: ENABLED\n\n"
            "Users can prestige at level 50, resetting to level 1 with a prestige badge."
        )
    elif data == "enable_global":
        await query.edit_message_text(
            "🌍 **Global Rankings**\n\n"
            "Status: ENABLED\n\n"
            "Users compete in global leaderboards across all groups."
        )
    elif data == "close_panel":
        await query.edit_message_text("Settings panel closed.")
