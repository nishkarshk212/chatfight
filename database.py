import asyncpg
import os
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient


class Database:
    def __init__(self):
        self.pool = None
        self.mongo_client = None
        self.db = None
    
    @property
    def xp_users(self):
        """Get XP users collection from MongoDB."""
        if self.db is None:
            raise RuntimeError("Database not initialized")
        return self.db.xp_users
        
    async def init_db(self):
        """Initialize the database connection pool."""
        # Initialize PostgreSQL
        self.pool = await asyncpg.create_pool(
            os.getenv('DATABASE_URL', 'postgresql://localhost/telegram_stats'),
            min_size=1,
            max_size=10
        )
        
        # Initialize MongoDB for XP system
        mongo_url = os.getenv('MONGODB_URL', 'mongodb://localhost:27017')
        self.mongo_client = AsyncIOMotorClient(mongo_url)
        self.db = self.mongo_client.chatrank
        
        # Create indexes for XP users collection
        await self.xp_users.create_index([("user_id", 1), ("group_id", 1)], unique=True)
        
        # Create tables if they don't exist
        async with self.pool.acquire() as conn:
            # Create users table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id BIGINT PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    total_messages BIGINT DEFAULT 0,
                    weekly_messages BIGINT DEFAULT 0,
                    daily_messages BIGINT DEFAULT 0
                );
            ''')
            
            # Create groups table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS groups (
                    group_id BIGINT,
                    user_id BIGINT,
                    total BIGINT DEFAULT 0,
                    weekly BIGINT DEFAULT 0,
                    daily BIGINT DEFAULT 0,
                    PRIMARY KEY(group_id, user_id),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );
            ''')
            
            # Create daily_stats table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS daily_stats (
                    user_id BIGINT,
                    group_id BIGINT,
                    date DATE,
                    message_count INT,
                    PRIMARY KEY(user_id, group_id, date),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );
            ''')
            
            # Create group_info table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS group_info (
                    group_id BIGINT PRIMARY KEY,
                    title TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            ''')
            
            # Create group_settings table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS group_settings (
                    group_id BIGINT PRIMARY KEY,
                    track_messages BOOLEAN DEFAULT TRUE,
                    show_in_global BOOLEAN DEFAULT TRUE,
                    privacy_level TEXT DEFAULT 'public', -- public, private, group_only
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            ''')

    async def close(self):
        """Close the database connection pool."""
        if self.pool:
            await self.pool.close()

    async def get_user_stats(self, user_id):
        """Get user statistics."""
        async with self.pool.acquire() as conn:
            return await conn.fetchrow('''
                SELECT * FROM users WHERE id = $1
            ''', user_id)

    async def get_group_user_stats(self, group_id, user_id):
        """Get statistics for a user in a specific group."""
        async with self.pool.acquire() as conn:
            return await conn.fetchrow('''
                SELECT * FROM groups WHERE group_id = $1 AND user_id = $2
            ''', group_id, user_id)

    async def get_top_users(self, limit=10, period='total'):
        """Get top users based on the specified period."""
        column_map = {
            'total': 'total_messages',
            'weekly': 'weekly_messages',
            'daily': 'daily_messages'
        }
        
        column = column_map.get(period, 'total_messages')
        
        async with self.pool.acquire() as conn:
            return await conn.fetch(f'''
                SELECT * FROM users 
                ORDER BY {column} DESC 
                LIMIT $1
            ''', limit)

    async def get_top_group_users(self, group_id, limit=10, period='total'):
        """Get top users in a specific group based on the specified period."""
        column_map = {
            'total': 'total',
            'weekly': 'weekly',
            'daily': 'daily'
        }
        
        column = column_map.get(period, 'total')
        
        async with self.pool.acquire() as conn:
            return await conn.fetch(f'''
                SELECT g.*, u.username, u.first_name 
                FROM groups g
                JOIN users u ON g.user_id = u.id
                WHERE g.group_id = $1
                ORDER BY g.{column} DESC 
                LIMIT $2
            ''', group_id, limit)

    async def get_global_leaderboard(self, limit=10, period='total'):
        """Get global leaderboard combining all groups."""
        column_map = {
            'total': 'total',
            'weekly': 'weekly',
            'daily': 'daily'
        }
        
        column = column_map.get(period, 'total')
        
        async with self.pool.acquire() as conn:
            return await conn.fetch(f'''
                SELECT g.*, u.username, u.first_name 
                FROM groups g
                JOIN users u ON g.user_id = u.id
                ORDER BY g.{column} DESC 
                LIMIT $1
            ''', limit)

    async def get_user_daily_stats(self, user_id, days=30):
        """Get daily statistics for a user over the last N days."""
        async with self.pool.acquire() as conn:
            return await conn.fetch('''
                SELECT date, SUM(message_count) as total 
                FROM daily_stats 
                WHERE user_id = $1 
                AND date >= CURRENT_DATE - INTERVAL '$2 days'
                GROUP BY date 
                ORDER BY date
            ''', user_id, days)

    async def get_group_daily_stats(self, group_id, days=30):
        """Get daily statistics for a group over the last N days."""
        async with self.pool.acquire() as conn:
            return await conn.fetch('''
                SELECT date, SUM(message_count) as total 
                FROM daily_stats 
                WHERE group_id = $1 
                AND date >= CURRENT_DATE - INTERVAL '$2 days'
                GROUP BY date 
                ORDER BY date
            ''', group_id, days)

    async def get_date_range_stats(self, start_date, end_date):
        """Get statistics for a specific date range."""
        async with self.pool.acquire() as conn:
            return await conn.fetch('''
                SELECT user_id, SUM(message_count) as total
                FROM daily_stats 
                WHERE date BETWEEN $1 AND $2
                GROUP BY user_id 
                ORDER BY total DESC
            ''', start_date, end_date)

    async def get_groups_total_messages(self, limit=10):
        """Get total messages per group."""
        async with self.pool.acquire() as conn:
            return await conn.fetch('''
                SELECT g.group_id, SUM(g.total) as total_messages, COUNT(DISTINCT g.user_id) as member_count
                FROM groups g
                GROUP BY g.group_id
                ORDER BY total_messages DESC
                LIMIT $1
            ''', limit)

    async def get_group_total_messages(self, group_id):
        """Get total messages for a specific group."""
        async with self.pool.acquire() as conn:
            return await conn.fetchrow('''
                SELECT SUM(total) as total_messages, COUNT(DISTINCT user_id) as member_count
                FROM groups 
                WHERE group_id = $1
            ''', group_id)

    async def update_group_info(self, group_id, title):
        """Update group information in the database."""
        try:
            async with db.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO group_info (group_id, title)
                    VALUES ($1, $2)
                    ON CONFLICT (group_id)
                    DO UPDATE SET 
                        title = EXCLUDED.title
                """, group_id, title)
        except Exception as e:
            logging.error(f"Error updating group info: {e}")

    async def get_group_title(self, group_id):
        """Get group title by group_id."""
        async with self.pool.acquire() as conn:
            result = await conn.fetchrow('''
                SELECT title
                FROM group_info 
                WHERE group_id = $1
            ''', group_id)
            return result['title'] if result else f"Group {group_id}"

    async def get_groups_with_titles_and_totals(self, limit=10):
        """Get groups with titles and total messages."""
        async with self.pool.acquire() as conn:
            return await conn.fetch('''
                SELECT g.group_id, SUM(g.total) as total_messages, 
                       COUNT(DISTINCT g.user_id) as member_count,
                       COALESCE(gi.title, 'Unknown Group') as title
                FROM groups g
                LEFT JOIN group_info gi ON g.group_id = gi.group_id
                GROUP BY g.group_id, gi.title
                ORDER BY total_messages DESC
                LIMIT $1
            ''', limit)

    async def get_or_create_group_settings(self, group_id):
        """Get group settings or create default ones if they don't exist."""
        async with self.pool.acquire() as conn:
            # Try to get existing settings
            result = await conn.fetchrow('''
                SELECT * FROM group_settings WHERE group_id = $1
            ''', group_id)
            
            if result:
                return result
            
            # If not found, create default settings
            await conn.execute('''
                INSERT INTO group_settings (group_id, track_messages, show_in_global, privacy_level)
                VALUES ($1, $2, $3, $4)
            ''', group_id, True, True, 'public')
            
            return await conn.fetchrow('''
                SELECT * FROM group_settings WHERE group_id = $1
            ''', group_id)

    async def update_group_setting(self, group_id, setting_name, value):
        """Update a specific group setting."""
        async with self.pool.acquire() as conn:
            await conn.execute(f'''
                UPDATE group_settings 
                SET {setting_name} = $1, updated_at = CURRENT_TIMESTAMP
                WHERE group_id = $2
            ''', value, group_id)
            
            # Return updated settings
            return await conn.fetchrow('''
                SELECT * FROM group_settings WHERE group_id = $1
            ''', group_id)

    async def get_group_tracking_status(self, group_id):
        """Get whether messages should be tracked for a group."""
        async with self.pool.acquire() as conn:
            result = await conn.fetchrow('''
                SELECT track_messages FROM group_settings WHERE group_id = $1
            ''', group_id)
            return result['track_messages'] if result else True  # Default to True


db = Database()
