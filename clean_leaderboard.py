#!/usr/bin/env python3
"""
Script to clean up the leaderboard by removing test users.
This script will:
1. Remove all test users from the user_stats table
2. Force restart the Telegram bot to clear any cached data
3. Verify the cleanup was successful
"""

import sqlite3
import os
import time
import sys
import subprocess
import signal
from typing import List, Dict, Any

def find_bot_process():
    """Find the bot process ID (if it's running)"""
    try:
        # Look for processes with 'python' and 'bot.py' in their command line
        result = subprocess.run(
            ["ps", "aux"], 
            capture_output=True, 
            text=True, 
            check=True
        )
        
        for line in result.stdout.splitlines():
            if 'python' in line and 'bot.py' in line:
                # Extract PID (second column)
                return int(line.split()[1])
        
        return None
    except Exception as e:
        print(f"Error finding bot process: {e}")
        return None

def restart_bot():
    """Restart the Telegram bot to clear any cached user stats"""
    try:
        bot_pid = find_bot_process()
        if bot_pid:
            print(f"Found bot process (PID: {bot_pid}), stopping it...")
            os.kill(bot_pid, signal.SIGTERM)
            time.sleep(2)  # Wait for process to terminate
            
            # Check if it's still running
            if find_bot_process() == bot_pid:
                print("Bot didn't terminate gracefully, forcing termination...")
                os.kill(bot_pid, signal.SIGKILL)
                time.sleep(1)
        
        # Start the bot in the background
        print("Starting bot...")
        subprocess.Popen(["python", "bot.py"], 
                         stdout=subprocess.DEVNULL, 
                         stderr=subprocess.DEVNULL)
        
        # Wait for bot to initialize
        time.sleep(3)
        
        print("Bot restarted successfully")
        return True
    except Exception as e:
        print(f"Error restarting bot: {e}")
        return False

def get_all_tables(conn: sqlite3.Connection) -> List[str]:
    """Get all tables in the database"""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    return [row[0] for row in cursor.fetchall()]

def clean_leaderboard():
    """Remove all test users from the leaderboard database."""
    # Path to the database
    db_path = 'country_game/database/countries.db'
    
    # Ensure the database exists
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return False
    
    # Connect to the database with row factory for named columns
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # Check what tables we have in the database
        tables = get_all_tables(conn)
        print(f"Tables in database: {', '.join(tables)}")
        
        # First, let's check the structure of the user_stats table
        cursor.execute("PRAGMA table_info(user_stats)")
        columns = cursor.fetchall()
        print("\nUser Stats Table structure:")
        for col in columns:
            print(f"  {col['name']} ({col['type']})")
        
        # Get all records to see what's actually in there
        cursor.execute("SELECT * FROM user_stats")
        all_records = cursor.fetchall()
        print(f"\nFound {len(all_records)} total records in user_stats table")
        
        # Delete all test users - using a comprehensive approach
        print("\n=== Removing all test users ===")
        
        # First pass: remove by name pattern (all common test user patterns)
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
        
        # Check if we're in restrictive mode (only keep specific users)
        # You can uncomment this for more aggressive cleaning
        # cursor.execute('''
        #     DELETE FROM user_stats 
        #     WHERE user_id != 396254641  -- Keep only legitimate users
        # ''')
        # print(f"Deleted {cursor.rowcount} additional entries for non-legitimate users")
        
        # Alternative approach: Delete users with very low activity (likely test accounts)
        cursor.execute('''
            DELETE FROM user_stats 
            WHERE total < 5 AND login_method != 'tele'
        ''')
        print(f"Deleted {cursor.rowcount} entries for low-activity users (likely test accounts)")
        
        # Verify the cleaning
        cursor.execute("SELECT COUNT(*) FROM user_stats")
        remaining_count = cursor.fetchone()[0]
        
        # Get remaining user info
        cursor.execute('''
            SELECT DISTINCT user_id, user_name, login_method
            FROM user_stats
        ''')
        remaining_users = cursor.fetchall()
        print(f"\nRemaining users after cleaning ({len(remaining_users)}):")
        for user in remaining_users:
            print(f"ID: {user['user_id']}, Name: {user['user_name']}, Login Method: {user['login_method']}")
        
        # Final check of actual entries
        cursor.execute('''
            SELECT user_id, game_mode, total, correct, user_name
            FROM user_stats
            ORDER BY game_mode
        ''')
        print("\nRemaining entries:")
        for entry in cursor.fetchall():
            print(f"User ID: {entry['user_id']}, Mode: {entry['game_mode']}, " +
                  f"Score: {entry['correct']}/{entry['total']}, Name: {entry['user_name']}")

        # Commit the changes
        conn.commit()
        print("\nDatabase changes committed successfully")
        
        # Now restart the bot to clear any cached data
        print("\n=== Restarting bot to clear cache ===")
        restart_success = restart_bot()
        
        print("\nLeaderboard cleanup process complete.")
        return True
        
    except Exception as e:
        print(f"Error while cleaning leaderboard: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("=== Country Game Leaderboard Cleanup Tool ===")
    success = clean_leaderboard()
    sys.exit(0 if success else 1)