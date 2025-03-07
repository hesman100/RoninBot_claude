#!/usr/bin/env python3
"""
Script to clean up the leaderboard by removing test users.
"""

import sqlite3
import os

def clean_leaderboard():
    """Remove all test users from the leaderboard database."""
    # Path to the database
    db_path = 'country_game/database/countries.db'
    
    # Ensure the database exists
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # First, let's check the structure of the user_stats table
        cursor.execute("PRAGMA table_info(user_stats)")
        columns = cursor.fetchall()
        print("Table structure:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
        
        # Get all records to see what's actually in there
        cursor.execute("SELECT * FROM user_stats")
        all_records = cursor.fetchall()
        print(f"\nFound {len(all_records)} total records in user_stats table")
        
        # Get all distinct user info to see who's in the leaderboard
        cursor.execute('''
            SELECT DISTINCT user_id, user_name, login_method
            FROM user_stats
        ''')
        users = cursor.fetchall()
        print(f"\nUsers in database ({len(users)}):")
        for user in users:
            print(f"ID: {user[0]}, Name: {user[1]}, Login Method: {user[2]}")

        # Keep only the legitimate user with ID 396254641
        cursor.execute('''
            DELETE FROM user_stats 
            WHERE user_id != 396254641
        ''')
        deleted_count = cursor.rowcount
        print(f"\nDeleted {deleted_count} entries for users other than the legitimate user")
        
        # Verify the cleaning
        cursor.execute("SELECT COUNT(*) FROM user_stats")
        remaining_count = cursor.fetchone()[0]
        print(f"Remaining entries: {remaining_count}")
        
        # Get remaining user info
        cursor.execute('''
            SELECT DISTINCT user_id, user_name, login_method
            FROM user_stats
        ''')
        remaining_users = cursor.fetchall()
        print(f"\nRemaining users after cleaning ({len(remaining_users)}):")
        for user in remaining_users:
            print(f"ID: {user[0]}, Name: {user[1]}, Login Method: {user[2]}")

        # Commit the changes
        conn.commit()
        
        print(f"\nLeaderboard cleanup complete.")
        
    except Exception as e:
        print(f"Error while cleaning leaderboard: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    clean_leaderboard()