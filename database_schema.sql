-- Database schema for Telegram Stats Bot

-- Table to store user statistics
CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    total_messages BIGINT DEFAULT 0,
    weekly_messages BIGINT DEFAULT 0,
    daily_messages BIGINT DEFAULT 0
);

-- Table to store group statistics (per user per group)
CREATE TABLE IF NOT EXISTS groups (
    group_id BIGINT,
    user_id BIGINT,
    total BIGINT DEFAULT 0,
    weekly BIGINT DEFAULT 0,
    daily BIGINT DEFAULT 0,
    PRIMARY KEY(group_id, user_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Table to store daily statistics for graphing
CREATE TABLE IF NOT EXISTS daily_stats (
    user_id BIGINT,
    group_id BIGINT,
    date DATE,
    message_count INT,
    PRIMARY KEY(user_id, group_id, date),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Table to store group information
CREATE TABLE IF NOT EXISTS group_info (
    group_id BIGINT PRIMARY KEY,
    title TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table to store group settings
CREATE TABLE IF NOT EXISTS group_settings (
    group_id BIGINT PRIMARY KEY,
    track_messages BOOLEAN DEFAULT TRUE,
    show_in_global BOOLEAN DEFAULT TRUE,
    privacy_level TEXT DEFAULT 'public', -- public, private, group_only
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
