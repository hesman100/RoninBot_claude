# Leaderboard Cleanup Guide

This document explains how to clean up test users from the leaderboard database on your deployment server.

## Option 1: Run the cleanup script directly

The project includes a ready-to-use cleanup script (`clean_leaderboard.py`) that will:

1. Remove test users (Test User, Sample User, Anonymous User, etc.) from the database
2. Restart the bot to clear any cached data
3. Verify the cleanup was successful

To run it:

```bash
python clean_leaderboard.py
```

## Option 2: Use the SQL commands directly

If you prefer to run the SQL commands directly (e.g., using a database management tool), here are the commands to use:

```sql
-- Connect to the database (path: country_game/database/countries.db)

-- Delete common test users by name pattern
DELETE FROM user_stats 
WHERE user_name LIKE '%Test%' 
OR user_name LIKE '%Sample%'
OR user_name LIKE '%Anonymous%'
OR user_name LIKE '%Demo%'
OR user_name LIKE '%Example%'
OR user_name = 'user123'
OR user_name = 'John Doe'
OR user_name = 'Jane Smith';

-- Delete low-activity users (likely test accounts)
DELETE FROM user_stats 
WHERE total < 5 AND login_method != 'tele';

-- Commit changes
COMMIT;
```

## Option 3: Run the commands via Python

If you need to integrate the cleanup into another script or add custom logic, here's a Python code snippet:

```python
import sqlite3
import os

# Path to the database
db_path = 'country_game/database/countries.db'

# Ensure the database exists
if not os.path.exists(db_path):
    print(f"Error: Database not found at {db_path}")
    exit(1)

# Connect to the database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Delete common test users by name pattern
    cursor.execute('''
        DELETE FROM user_stats 
        WHERE user_name LIKE '%Test%' 
        OR user_name LIKE '%Sample%'
        OR user_name LIKE '%Anonymous%'
        OR user_name LIKE '%Demo%'
        OR user_name LIKE '%Example%'
        OR user_name = 'user123'
        OR user_name = 'John Doe'
        OR user_name = 'Jane Smith'
    ''')
    print(f"Deleted {cursor.rowcount} entries matching test user name patterns")
    
    # Delete low-activity users (likely test accounts)
    cursor.execute('''
        DELETE FROM user_stats 
        WHERE total < 5 AND login_method != 'tele'
    ''')
    print(f"Deleted {cursor.rowcount} entries for low-activity users")
    
    # Commit changes
    conn.commit()
    print("Database changes committed successfully")
    
except Exception as e:
    print(f"Error: {e}")
    conn.rollback()
    
finally:
    conn.close()
```

## After Cleanup

After cleaning up the database, restart the Telegram bot to ensure any cached user data is cleared:

```bash
# Find and stop the running bot process
ps aux | grep "python.*bot.py" | grep -v grep | awk '{print $2}' | xargs kill -9

# Start the bot again
python bot.py &
```

## Setting Up Automatic Cleanup

For a production server, you may want to set up automatic cleanup to prevent test users from accumulating:

1. Create a cron job to run the script periodically (e.g., weekly)
2. Add startup logic to your bot deployment script to run cleanup on restart
3. Implement user authentication to prevent fake users from being created in the first place

## Notes

- The original script uses a whitelist approach (only keeping specific user IDs) which is commented out. For more aggressive cleaning, you can uncomment this section.
- Always back up your database before running cleanup operations.
- Test users with login_method='tele' and at least 5 activities are preserved to avoid deleting legitimate Telegram users.