import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from database import db
import io
import base64


async def generate_xp_graph(user_id, group_id, days=7):
    """Generate a graph showing XP progression over time."""
    # Get user XP data from MongoDB
    user = await db.xp_users.find_one({"user_id": user_id, "group_id": group_id})
    
    if not user:
        return None
    
    # For now, create a simple XP progression graph
    # In production, you'd want to store historical XP data
    xp_data = [user.get("xp", 0)]
    labels = ["Current"]
    
    plt.figure(figsize=(10, 6))
    plt.bar(labels, xp_data, color=['#ffd700', '#00ffff', '#ff6b6b'])
    plt.title(f"XP Progression - Last {days} Days", fontsize=14, fontweight='bold')
    plt.xlabel("Time Period", fontsize=12)
    plt.ylabel("XP", fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # Save to bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150)
    buf.seek(0)
    
    # Clear the figure
    plt.clf()
    plt.close()
    
    return buf


def generate_user_graph(data, username):
    """Generate a line graph for user activity."""
    if not data:
        return None
    
    # Sort data by date
    sorted_data = sorted(data, key=lambda x: x['date'])
    dates = [record['date'].strftime('%m/%d') for record in sorted_data]
    counts = [record['total'] for record in sorted_data]

    plt.figure(figsize=(12, 6))
    plt.plot(dates, counts, marker='o', linewidth=2, markersize=6)
    plt.title(f"{username}'s Message Activity", fontsize=16, fontweight='bold')
    plt.xlabel("Date", fontsize=12)
    plt.ylabel("Number of Messages", fontsize=12)
    plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # Save to bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150)
    buf.seek(0)
    
    # Clear the figure to free memory
    plt.clf()
    plt.close()
    
    return buf


def generate_group_graph(data, group_name):
    """Generate a line graph for group activity."""
    if not data:
        return None
    
    # Sort data by date
    sorted_data = sorted(data, key=lambda x: x['date'])
    dates = [record['date'].strftime('%m/%d') for record in sorted_data]
    counts = [record['total'] for record in sorted_data]

    plt.figure(figsize=(12, 6))
    plt.plot(dates, counts, color='orange', marker='o', linewidth=2, markersize=6)
    plt.title(f"{group_name}'s Message Activity", fontsize=16, fontweight='bold')
    plt.xlabel("Date", fontsize=12)
    plt.ylabel("Number of Messages", fontsize=12)
    plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # Save to bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150)
    buf.seek(0)
    
    # Clear the figure to free memory
    plt.clf()
    plt.close()
    
    return buf


async def send_user_graph(update, context, user_id=None):
    """Send a graph of user activity."""
    if user_id is None:
        user_id = update.effective_user.id
    
    # Get user's daily stats for the last 30 days
    user_data = await db.get_user_daily_stats(user_id, days=30)
    
    if not user_data:
        await update.message.reply_text("No activity data available to generate a graph.")
        return
    
    # Format the data for the graph function
    formatted_data = [{'date': record['date'], 'total': record['total']} for record in user_data]
    
    # Get username for the title
    user_info = await db.get_user_stats(user_id)
    username = user_info['first_name'] if user_info and user_info['first_name'] else f"User {user_id}"
    
    # Generate the graph
    graph_buffer = generate_user_graph(formatted_data, username)
    
    if graph_buffer:
        await update.message.reply_photo(photo=graph_buffer, caption=f"Activity graph for {username}")
        graph_buffer.close()
    else:
        await update.message.reply_text("Could not generate the graph.")


async def send_group_graph(update, context, group_id=None):
    """Send a graph of group activity."""
    if group_id is None:
        chat = update.effective_chat
        if chat.type not in ["group", "supergroup"]:
            await update.message.reply_text("This command can only be used in groups.")
            return
        group_id = chat.id
    
    # Get group's daily stats for the last 30 days
    group_data = await db.get_group_daily_stats(group_id, days=30)
    
    if not group_data:
        await update.message.reply_text("No activity data available to generate a graph.")
        return
    
    # Format the data for the graph function
    formatted_data = [{'date': record['date'], 'total': record['total']} for record in group_data]
    
    # Get group name for the title
    group_name = update.effective_chat.title if update.effective_chat.title else f"Group {group_id}"
    
    # Generate the graph
    graph_buffer = generate_group_graph(formatted_data, group_name)
    
    if graph_buffer:
        await update.message.reply_photo(photo=graph_buffer, caption=f"Activity graph for {group_name}")
        graph_buffer.close()
    else:
        await update.message.reply_text("Could not generate the graph.")


async def my_graph_command(update, context):
    """Handle the /mygraph command."""
    await send_user_graph(update, context)


async def group_graph_command(update, context):
    """Handle the /groupgraph command."""
    await send_group_graph(update, context)


async def global_graph_command(update, context):
    """Handle the /globalgraph command."""
    # Get overall stats for all users in the last 30 days
    start_date = datetime.now() - timedelta(days=30)
    end_date = datetime.now()
    
    global_data = await db.get_date_range_stats(start_date.date(), end_date.date())
    
    if not global_data:
        await update.message.reply_text("No global activity data available to generate a graph.")
        return
    
    # Since global data doesn't have dates, we'll need to aggregate by date differently
    # For now, we'll just use the group graph function as a placeholder
    # This would need to be adjusted based on how you want to visualize global data
    
    await update.message.reply_text("Global graph functionality is under development.")
