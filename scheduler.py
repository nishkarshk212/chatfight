import asyncio
from database import db
from datetime import datetime, time
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger


class Scheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        
    async def start(self):
        """Start the scheduler."""
        # Reset daily stats at midnight
        self.scheduler.add_job(
            self.reset_daily_stats,
            CronTrigger(hour=0, minute=0),
            id='reset_daily'
        )
        
        # Reset weekly stats every Monday at midnight
        self.scheduler.add_job(
            self.reset_weekly_stats,
            CronTrigger(day_of_week=0, hour=0, minute=0),  # 0 is Monday
            id='reset_weekly'
        )
        
        # Reset daily XP at midnight
        self.scheduler.add_job(
            self.reset_daily_xp,
            CronTrigger(hour=0, minute=0),
            id='reset_daily_xp'
        )
        
        self.scheduler.start()
        logging.info("Scheduler started")
    
    async def stop(self):
        """Stop the scheduler."""
        self.scheduler.shutdown()
        logging.info("Scheduler stopped")
    
    async def reset_daily_stats(self):
        """Reset daily message counts."""
        try:
            async with db.pool.acquire() as conn:
                await conn.execute("UPDATE users SET daily_messages = 0")
                await conn.execute("UPDATE groups SET daily = 0")
            logging.info("Daily stats reset successfully")
        except Exception as e:
            logging.error(f"Error resetting daily stats: {e}")
    
    async def reset_weekly_stats(self):
        """Reset weekly message counts."""
        try:
            async with db.pool.acquire() as conn:
                await conn.execute("UPDATE users SET weekly_messages = 0")
                await conn.execute("UPDATE groups SET weekly = 0")
            logging.info("Weekly stats reset successfully")
        except Exception as e:
            logging.error(f"Error resetting weekly stats: {e}")
    
    async def reset_daily_xp(self):
        """Reset daily XP for all users."""
        try:
            # Reset daily_xp field in MongoDB
            result = await db.xp_users.update_many(
                {},
                {"$set": {"daily_xp": 0}}
            )
            logging.info(f"Daily XP reset successfully. Updated {result.modified_count} users")
        except Exception as e:
            logging.error(f"Error resetting daily XP: {e}")


# Create a global scheduler instance
scheduler = Scheduler()


async def reset_daily():
    """Manually reset daily stats - for backward compatibility."""
    await scheduler.reset_daily_stats()


async def reset_weekly():
    """Manually reset weekly stats - for backward compatibility."""
    await scheduler.reset_weekly_stats()
