import os, dotenv
import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest
from database import db
from message_counter import count_message
from leaderboard import (
    leaderboard_menu, my_stats_command, my_rank_command, 
    handle_leaderboard_callback, leaderboard_command,
    daily_rank_command, weekly_rank_command, all_time_rank_command,
    group_global_command
)

from graphs import my_graph_command, group_graph_command, global_graph_command
from scheduler import scheduler
from xp_system import (
    get_xp_stats, xp_leaderboard, daily_xp_command, weekly_xp_command,
    monthly_xp_command, global_xp_leaderboard, xp_settings_menu,
    handle_xp_settings_callback
)


# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def is_group_admin(update, context):
    """Check if the user is a group admin or owner."""
    # For private chats, allow the command
    if update.effective_chat.type == 'private':
        logger.debug(f"Private chat detected - allowing access for user {update.effective_user.id}")
        return True
    
    try:
        # Get chat member
        chat_member = await context.bot.get_chat_member(
            chat_id=update.effective_chat.id,
            user_id=update.effective_user.id
        )
        
        # Check if user is admin or creator
        is_admin = chat_member.status in ['administrator', 'creator']
        logger.debug(f"User {update.effective_user.id} status: {chat_member.status}, is_admin: {is_admin}")
        return is_admin
    except Exception as e:
        logger.error(f"Error checking admin status: {e}")
        return False  # Default to denying access on error


def admin_only_wrapper(command_func):
    """Wrapper function to restrict commands to group admins/owners only."""
    async def wrapper(update, context):
        # Check admin status first
        if not await is_group_admin(update, context):
            # Send error message based on update type
            if update.message:
                await update.message.reply_text(
                    "⛔ This command can only be used by group owners and admins."
                )
            elif update.callback_query:
                await update.callback_query.answer(
                    "⛔ This command can only be used by group owners and admins.",
                    show_alert=True
                )
            return
        
        # If admin, proceed with the command
        try:
            return await command_func(update, context)
        except Exception as e:
            logger.error(f"Error in admin command {command_func.__name__}: {e}")
            if update.message:
                await update.message.reply_text("An error occurred while processing your request.")
            elif update.callback_query:
                await update.callback_query.answer("An error occurred.", show_alert=True)
    
    return wrapper


async def start(update, context):
    """Handle the /start command."""
    welcome_message = '''
🚀 WELCOME TO THE CHAT RANK ARENA! 🚀

This isn't just a group... it's a battlefield! 💬⚔️

🎯 Earn XP, Level Up, Climb The Leaderboard 🏆
📊 Compete Daily • Weekly • All-Time

🔥 Send Messages  
⚡ Earn XP  
🎖 Unlock Badges  
👑 Become The Chat King  

Use /mystats to check your progress 📊  
Use /leaderboard to see the top warriors 🏆

Let the chat battle begin! 🔥👑
'''
    
    # Create inline keyboard with "Add to Group" button
    keyboard = [
        [InlineKeyboardButton("➘ Add to Group", url=f"https://t.me/{context.bot.username}?startgroup=true")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Try to send bot's profile photo with the welcome message and button
    try:
        # Get bot's profile photos using get_user_profile_photos
        photos = await context.bot.get_user_profile_photos(
            user_id=context.bot.id,
            offset=0,
            limit=1
        )
        
        if photos.photos and len(photos.photos) > 0:
            # Get the first (most recent) profile photo
            photo_id = photos.photos[0][-1].file_id
            
            # Send photo with caption and inline keyboard
            await update.message.reply_photo(
                photo=photo_id,
                caption=welcome_message,
                reply_markup=reply_markup
            )
        else:
            # No profile photo, send text with inline keyboard
            await update.message.reply_text(
                text=welcome_message,
                reply_markup=reply_markup
            )
    except Exception as e:
        logger.error(f"Error sending profile photo: {e}")
        # Fallback to text message with inline keyboard if photo sending fails
        await update.message.reply_text(
            text=welcome_message,
            reply_markup=reply_markup
        )


async def help_command(update, context):
    """Handle the /help command."""
    help_text = '''
Telegram Stats Bot Help 📚

This bot tracks messaging activity in Telegram groups and provides statistics and leaderboards.

📊 **Statistics Commands:**
/mygraph - Shows your personal activity graph over time
/groupgraph - Shows the activity graph for the current group
/globalgraph - Shows global activity across all tracked groups
/mystats - Shows your personal statistics (XP & Level)
/myrank - Shows your ranking in the current group or globally

🏆 **Leaderboard Commands:**
/leaderboard - Opens the interactive leaderboard menu
/dailyrank - Shows the daily leaderboard for the current group
/weeklyrank - Shows the weekly leaderboard for the current group
/alltimerank - Shows the all-time leaderboard for the current group
/groupglobal - Shows the global leaderboard of groups by total messages

⭐ **XP System Commands:**
/xprank - Shows the XP leaderboard with rank cards
/dailyxp - Shows daily XP leaders
/weeklyxp - Shows weekly XP leaders
/monthlyxp - Shows monthly XP leaders
/globalxp - Shows global XP rankings across all groups
/xpsettings - Configure XP system settings (Admin only)

The bot automatically counts messages, awards XP, and tracks levels in groups where it is present.
'''
    await update.message.reply_text(help_text)


def main():
    # Load environment variables
    dotenv.load_dotenv()

    """Run the bot."""
    # Create the Application and pass it your bot's token
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'YOUR_TELEGRAM_BOT_TOKEN_HERE')
    application = Application.builder().token(TOKEN).build()

    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    
    # Stats and leaderboard commands (restricted to group admins/owners)
    application.add_handler(CommandHandler("mystats", admin_only_wrapper(my_stats_command)))
    application.add_handler(CommandHandler("myrank", admin_only_wrapper(my_rank_command)))
    application.add_handler(CommandHandler("mygraph", admin_only_wrapper(my_graph_command)))
    application.add_handler(CommandHandler("groupgraph", admin_only_wrapper(group_graph_command)))
    application.add_handler(CommandHandler("globalgraph", admin_only_wrapper(global_graph_command)))
    application.add_handler(CommandHandler("leaderboard", admin_only_wrapper(leaderboard_command)))
    application.add_handler(CommandHandler("dailyrank", admin_only_wrapper(daily_rank_command)))
    application.add_handler(CommandHandler("weeklyrank", admin_only_wrapper(weekly_rank_command)))
    application.add_handler(CommandHandler("alltimerank", admin_only_wrapper(all_time_rank_command)))
    application.add_handler(CommandHandler("groupglobal", admin_only_wrapper(group_global_command)))
    
    # Handle leaderboard menu callbacks
    application.add_handler(CallbackQueryHandler(handle_leaderboard_callback))
    
    # Handle XP settings panel callbacks
    application.add_handler(CallbackQueryHandler(handle_xp_settings_callback))
    
    # XP system commands (restricted to group admins/owners)
    application.add_handler(CommandHandler("mystats", admin_only_wrapper(get_xp_stats)))
    application.add_handler(CommandHandler("xprank", admin_only_wrapper(xp_leaderboard)))
    application.add_handler(CommandHandler("dailyxp", admin_only_wrapper(daily_xp_command)))
    application.add_handler(CommandHandler("weeklyxp", admin_only_wrapper(weekly_xp_command)))
    application.add_handler(CommandHandler("monthlyxp", admin_only_wrapper(monthly_xp_command)))
    application.add_handler(CommandHandler("globalxp", admin_only_wrapper(global_xp_leaderboard)))
    application.add_handler(CommandHandler("xpsettings", admin_only_wrapper(xp_settings_menu)))
    
    # Handle all non-command text messages to count them
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, count_message))

    # Initialize the database
    async def initialize_database():
        await db.init_db()
        logger.info("Database initialized")
    
    # Start the scheduler
    async def start_scheduler():
        await scheduler.start()
        logger.info("Scheduler started")
    
    # Set up the application event loop
    async def post_init(app):
        await initialize_database()
        await start_scheduler()
    
    application.post_init = post_init

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=['message', 'callback_query'])


if __name__ == '__main__':
    main()
