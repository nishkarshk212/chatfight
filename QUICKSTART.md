# 🚀 Quick Start Guide - Chat Fight XP System

## Prerequisites Setup

### 1. Install MongoDB
**macOS:**
```bash
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community
```

**Verify MongoDB is running:**
```bash
mongosh
# Should connect successfully
```

### 2. Verify PostgreSQL
Make sure PostgreSQL is running:
```bash
# Check if PostgreSQL is running
brew services list | grep postgresql
```

### 3. Install Python Dependencies
All packages are already installed! ✅
```bash
pip install pyrogram tgcrypto motor pillow matplotlib apscheduler
```

## 🎮 Bot Commands Overview

### User Commands
| Command | Description |
|---------|-------------|
| `/mystats` | View your XP, level & prestige with rank card |
| `/xprank` | Group XP leaderboard with image |
| `/dailyxp` | Today's top XP earners |
| `/weeklyxp` | This week's champions |
| `/monthlyxp` | Monthly rankings |
| `/globalxp` | Global XP across all groups |

### Admin Commands
| Command | Description |
|---------|-------------|
| `/xpsettings` | Configure XP system settings |

### Existing Commands (Still Work)
- `/mygraph`, `/groupgraph`, `/globalgraph` - Activity graphs
- `/leaderboard`, `/dailyrank`, `/weeklyrank`, `/alltimerank` - Message leaderboards
- `/mystats`, `/myrank` - Personal stats

## 🎯 How the XP System Works

### Earning XP
1. **Send Messages**: Each message earns 3-8 XP randomly
2. **Quality Bonus**: Messages >50 chars get +5 XP bonus
3. **Cooldown**: 10 seconds between XP gains (prevents farming)

### Level System
```python
Level = int((XP / 50) ** 0.5) + 1
```

**Example Progression:**
- Level 1: 0 XP
- Level 5: ~800 XP
- Level 10: ~4,050 XP
- Level 25: ~28,800 XP
- Level 50: ~120,050 XP → **PRESTIGE!**

### Prestige System
When you reach level 50:
- Reset to level 1
- XP resets to 0
- Gain 1 prestige badge (🎖)
- Keep competing with higher prestige

## 🏆 Leaderboard Features

### Medal Rankings
- 🥇 1st Place
- 🥈 2nd Place  
- 🥉 3rd Place
- 4., 5., 6... Numeric for rest

### Time Periods
- **Daily**: Resets at midnight
- **Weekly**: Resets every Monday
- **Monthly**: Tracks entire month
- **All-Time**: Never resets

## ⚙️ XP Settings Panel

Access with `/xpsettings` (Admin only):

1. **XP Multiplier** - Adjust XP gain rates
2. **Toggle Cooldown** - Enable/disable 10s cooldown
3. **Reset Leaderboard** - Clear all XP data
4. **Enable Prestige** - Toggle prestige system
5. **Enable Global Rank** - Cross-group competition

## 📊 Database Structure

### MongoDB (XP System)
Collection: `xp_users`
```json
{
  "user_id": 123456789,
  "group_id": -1001234567,
  "xp": 1200,
  "level": 5,
  "daily_xp": 50,
  "weekly_xp": 300,
  "monthly_xp": 800,
  "prestige": 0,
  "last_message": 1700000000
}
```

### PostgreSQL (Message Stats)
- Users table
- Groups table  
- Daily stats table
- Group info table
- Group settings table

## 🔧 Configuration

### Environment Variables (.env)
Already configured! ✅
```
TELEGRAM_BOT_TOKEN=8191441261:AAHieKlPRhegYA8p8FCy4o9F-PMiPhkIX2k
DATABASE_URL=postgresql://localhost/telegram_stats
MONGODB_URL=mongodb://localhost:27017
```

## 🎨 Rank Cards

Generated automatically when using `/mystats`:
- Dark theme design
- Shows username, level, XP, prestige
- Beautiful visual representation
- Saved as `rank_card.png`

## 📝 Testing the Bot

### Step 1: Start the Bot
```bash
cd "/Users/nishkarshkr/Desktop/chat fight"
python bot.py
```

### Step 2: Add Bot to Group
1. Click "Add to Group" button from /start
2. Add to your test group
3. Make it an admin (optional but recommended)

### Step 3: Test Commands
In the group:
```
/mystats    # See your rank card
/xprank     # View leaderboard
/dailyxp    # Daily leaders
```

### Step 4: Send Messages
Send several messages to earn XP:
- Wait 10 seconds between messages for XP
- Write longer messages (>50 chars) for bonus
- Watch your level increase!

## 🎯 Example User Journey

1. User joins group chat
2. Sends message → Earns 5 XP
3. Sends another after 10s → Earns 8 XP
4. Writes long message (60 chars) → Earns 13 XP (8+5 bonus)
5. Reaches 100 XP → Level 2
6. Continues to level 50 → Prestiges!
7. Competes for top of leaderboard

## 🔄 Automatic Features

### Scheduler Tasks
- **Midnight**: Reset daily XP & messages
- **Monday 00:00**: Reset weekly stats
- **Every message**: Check cooldown, award XP, update level

## 🐛 Troubleshooting

### MongoDB Connection Error
```bash
# Start MongoDB
brew services start mongodb-community

# Or check status
brew services list
```

### PostgreSQL Connection Error
```bash
# Start PostgreSQL
brew services start postgresql@14

# Verify connection
psql $DATABASE_URL
```

### Bot Not Responding
1. Check token in .env is correct
2. Verify bot is added to group
3. Check bot has permission to send messages
4. Review terminal logs for errors

### Rank Card Not Generating
1. Check Pillow is installed: `pip show pillow`
2. Verify write permissions in bot directory
3. Check logs for font loading errors

## 📈 Monitoring

Watch the terminal logs for:
- "Message counted for user..." - XP being awarded
- "Daily stats reset successfully" - Scheduler working
- "Database initialized" - Connections ready
- "Scheduler started" - Automation active

## 🎉 Success Indicators

✅ Bot starts without errors
✅ MongoDB and PostgreSQL connected
✅ Messages earn XP after 10s cooldown
✅ `/mystats` shows rank card with level
✅ `/xprank` displays leaderboard
✅ Scheduler resets stats at midnight

## 💡 Tips

1. **Encourage Activity**: Announce XP system to group members
2. **Fair Play**: Cooldown prevents spam/farming
3. **Competition**: Weekly resets keep it fresh
4. **Prestige Goals**: Long-term engagement for active users
5. **Admin Control**: Customize XP rates per group

---

**Ready to battle?** 🎮⚔️
Start messaging and climb the ranks! 🏆
