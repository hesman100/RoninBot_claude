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

-- Delete only specific test users to avoid affecting legitimate users
DELETE FROM user_stats 
WHERE user_name = 'Test User'
OR user_name = 'TestUser'
OR user_name = 'Sample User'
OR user_name = 'Anonymous'
OR user_name = 'Anonymous User' 
OR user_name = 'user123'
OR user_name = 'John Doe'
OR user_name = 'Jane Smith';

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
    # Delete only specific test users to avoid affecting legitimate users
    cursor.execute('''
        DELETE FROM user_stats 
        WHERE user_name = 'Test User'
        OR user_name = 'TestUser'
        OR user_name = 'Sample User'
        OR user_name = 'Anonymous'
        OR user_name = 'Anonymous User' 
        OR user_name = 'user123'
        OR user_name = 'John Doe'
        OR user_name = 'Jane Smith'
    ''')
    print(f"Deleted {cursor.rowcount} entries matching specific test user names")
    
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

## Manual Cleanup (Recommended Approach)

To avoid accidentally affecting legitimate users, automatic cleanup at startup has been disabled.

Instead, use the manual cleanup tool when needed:

1. Stop the running bot and API server
2. Run `python clean_leaderboard.py` to clean up test users
3. Start the services again using `run_all.py` or `integrated_server.py`

Example log output during manual cleanup:
```
=== Country Game Leaderboard Cleanup Tool ===
=== Removing all test users ===
Deleted 8 entries matching specific test user names

Remaining users after cleaning (2):
ID: 396254641, Name: hes man, Login Method: tele
ID: 987654321, Name: Your Name, Login Method: web

Database changes committed successfully

=== Restarting bot to clear cache ===
Leaderboard cleanup process complete.
```

## Additional Automatic Cleanup Options

If you want additional automatic cleanup beyond what happens at startup:

1. Create a cron job to run the script periodically (e.g., weekly)
2. Implement user authentication to prevent fake users from being created in the first place
3. Add a database trigger to automatically reject entries with known test user patterns

## Notes

- The original script had a more aggressive approach with wildcard patterns and activity filters, but this was removed to protect legitimate users like "hes man".
- The current implementation only removes specific test usernames to ensure legitimate users are preserved.
- Always back up your database before running cleanup operations.
- If you need to implement more aggressive cleaning, modify the SQL query to include additional specific test usernames.