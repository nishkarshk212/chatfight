from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database import db
import logging


def leaderboard_menu():
    """Create the leaderboard menu with inline keyboard buttons."""
    keyboard = [
        [
            InlineKeyboardButton("📅 Today", callback_data="daily"),
            InlineKeyboardButton("📊 Weekly", callback_data="weekly"),
        ],
        [
            InlineKeyboardButton("🏆 All Time", callback_data="alltime"),
        ],
        [
            InlineKeyboardButton("🌍 Global", callback_data="global"),
            InlineKeyboardButton("ParallelGroups", callback_data="groups_global")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


async def send_leaderboard(update, context, period='total', scope='group'):
    """Send the appropriate leaderboard based on period and scope."""
    query = update.callback_query
    if query:
        await query.answer()
    
    user = update.effective_user
    chat = update.effective_chat
    
    # Determine the period for the leaderboard
    period_map = {
        'daily': 'daily',
        'weekly': 'weekly', 
        'alltime': 'total',
        'total': 'total'
    }
    
    period_key = period_map.get(period, 'total')
    
    message_parts = []
    
    if scope == 'global':
        # Global leaderboard showing top users across all groups
        top_users = await db.get_global_leaderboard(limit=10, period=period_key)
        period_name = period.capitalize() if period != 'alltime' else 'All Time'
        message_parts.append(f"🌍 <b>{period_name} Global Leaderboard</b>\n")
        
        if top_users:
            for i, record in enumerate(top_users, 1):
                user_name = record['first_name'] or record['username'] or f"User {record['user_id']}"
                count = record[period_key]  # Use the mapped period key
                message_parts.append(f"{i}. <b>{user_name}</b>: {count} messages")
        else:
            message_parts.append("No data available yet.")
    
    elif chat.type in ["group", "supergroup"]:
        # Group-specific leaderboard
        top_users = await db.get_top_group_users(chat.id, limit=10, period=period_key)
        group_totals = await db.get_group_total_messages(chat.id)
        period_name = period.capitalize() if period != 'alltime' else 'All Time'
        message_parts.append(f"👥 <b>{period_name} Leaderboard for {chat.title}</b>\n")
        
        # Add group total message count
        if group_totals:
            total_messages = group_totals['total_messages'] or 0
            member_count = group_totals['member_count'] or 0
            message_parts.append(f"📊 <b>Total Messages:</b> {total_messages} | <b>Members:</b> {member_count}\n")
        
        if top_users:
            for i, record in enumerate(top_users, 1):
                user_name = record['first_name'] or record['username'] or f"User {record['user_id']}"
                count = record[period_key]  # Use the mapped period key
                message_parts.append(f"{i}. <b>{user_name}</b>: {count} messages")
        else:
            message_parts.append("No data available yet.")
    
    else:
        # Personal stats for private chats
        user_stats = await db.get_user_stats(user.id)
        if user_stats:
            period_name = period.capitalize() if period != 'alltime' else 'All Time'
            count = user_stats[f'{period_key}_messages']
            message_parts.append(f"👤 Your {period_name} Stats:")
            message_parts.append(f"Total Messages: {user_stats['total_messages']}")
            message_parts.append(f"Weekly Messages: {user_stats['weekly_messages']}")
            message_parts.append(f"Daily Messages: {user_stats['daily_messages']}")
        else:
            message_parts.append("No stats available for you yet.")
    
    message = "\n".join(message_parts)
    
    if query:
        await query.edit_message_text(text=message, parse_mode='HTML', reply_markup=leaderboard_menu())
    else:
        await update.message.reply_text(text=message, parse_mode='HTML', reply_markup=leaderboard_menu())


async def my_stats_command(update, context):
    """Handle the /mystats command."""
    user = update.effective_user
    user_stats = await db.get_user_stats(user.id)
    
    if user_stats:
        message = f"👤 <b>Your Stats:</b>\n"
        message += f"Total Messages: {user_stats['total_messages']}\n"
        message += f"Weekly Messages: {user_stats['weekly_messages']}\n"
        message += f"Daily Messages: {user_stats['daily_messages']}"
    else:
        message = "No stats available for you yet."
    
    await update.message.reply_text(text=message, parse_mode='HTML')


async def my_rank_command(update, context):
    """Handle the /myrank command."""
    user = update.effective_user
    chat = update.effective_chat
    
    if chat.type in ["group", "supergroup"]:
        # Get user's rank in the current group
        all_users = await db.get_top_group_users(chat.id, limit=1000, period='total')  # Get all users
        
        # Find user's position
        user_rank = None
        for i, record in enumerate(all_users, 1):
            if record['user_id'] == user.id:
                user_rank = i
                break
        
        if user_rank:
            message = f"👤 Your rank in {chat.title}: #{user_rank} out of {len(all_users)} users"
        else:
            message = "You don't have any messages in this group yet."
    else:
        # Global rank
        all_users = await db.get_global_leaderboard(limit=10000, period='total')
        
        user_rank = None
        for i, record in enumerate(all_users, 1):
            if record['user_id'] == user.id:
                user_rank = i
                break
                
        if user_rank:
            message = f"🌍 Your global rank: #{user_rank} out of {len(all_users)} users"
        else:
            message = "You don't have any messages recorded yet."
    
    await update.message.reply_text(text=message)


async def handle_leaderboard_callback(update, context):
    """Handle leaderboard menu callbacks."""
    query = update.callback_query
    data = query.data
    
    # Check if this callback should be handled by settings instead
    # If data starts with known settings patterns, don't handle it here
    if (data.startswith("setting_") or 
        data.startswith("set_") or 
        data.startswith("settings_menu") or 
        data in ["settings_here", "settings_private"] or
        data.startswith("back_to_main") or
        data.startswith("setting_save_")):
        # Don't handle settings-related callbacks here
        return
    
    if data in ['daily', 'weekly', 'alltime']:
        await send_leaderboard(update, context, period=data, scope='group')
    elif data == 'global':
        await send_leaderboard(update, context, period='total', scope='global')
    elif data == 'groups_global':
        await send_group_leaderboard(update, context, period='total')
    else:
        await query.edit_message_text(text="Invalid option selected.")


async def leaderboard_command(update, context):
    """Handle the /leaderboard command."""
    await send_leaderboard(update, context, period='total', scope='group')


async def daily_rank_command(update, context):
    """Handle the /dailyrank command."""
    await send_leaderboard(update, context, period='daily', scope='group')


async def weekly_rank_command(update, context):
    """Handle the /weeklyrank command."""
    await send_leaderboard(update, context, period='weekly', scope='group')


async def all_time_rank_command(update, context):
    """Handle the /alltimerank command."""
    await send_leaderboard(update, context, period='alltime', scope='group')


async def send_group_leaderboard(update, context, period='total'):
    """Send the group leaderboard based on period."""
    query = update.callback_query
    if query:
        await query.answer()
    
    # Get top groups by total messages
    top_groups = await db.get_groups_with_titles_and_totals(limit=10)
    period_name = period.capitalize() if period != 'alltime' else 'All Time'
    message_parts = []
    message_parts.append(f"🌍 <b>{period_name} Top Groups Leaderboard</b>\n")
    
    if top_groups:
        for i, record in enumerate(top_groups, 1):
            group_id = record['group_id']
            total_messages = record['total_messages'] or 0
            member_count = record['member_count'] or 0
            title = record['title']
            message_parts.append(f"{i}. <b>{title}</b>: {total_messages} messages ({member_count} members)")
    else:
        message_parts.append("No data available yet.")
    
    message = "\n".join(message_parts)
    
    if query:
        await query.edit_message_text(text=message, parse_mode='HTML', reply_markup=leaderboard_menu())
    else:
        await update.message.reply_text(text=message, parse_mode='HTML', reply_markup=leaderboard_menu())


async def group_global_command(update, context):
    """Handle the /groupglobal command to show top groups."""
    await send_group_leaderboard(update, context, period='total')
