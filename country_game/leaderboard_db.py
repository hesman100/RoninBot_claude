import sqlite3
import logging
import os
import json
from typing import Dict, List, Any, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database constants
DB_PATH = "country_game/database/leaderboard.db"
DB_DIR = os.path.dirname(DB_PATH)

def ensure_db_directory():
    """Ensure the database directory exists."""
    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR)
        logger.info(f"Created database directory: {DB_DIR}")

def init_db():
    """Initialize the leaderboard database and create tables if they don't exist."""
    ensure_db_directory()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create leaderboard table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS leaderboard (
        user_id INTEGER,
        game_mode TEXT,
        total_games INTEGER DEFAULT 0,
        correct_games INTEGER DEFAULT 0,
        PRIMARY KEY (user_id, game_mode)
    )
    ''')

    # Create user info table to store user names
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_info (
        user_id INTEGER PRIMARY KEY,
        user_name TEXT,
        last_seen TEXT
    )
    ''')

    conn.commit()
    conn.close()

    logger.info("Leaderboard database initialized successfully")

def update_user_stat(user_id: int, user_name: str, game_mode: str, is_correct: bool):
    """
    Update a user's stats for a specific game mode.

    Args:
        user_id: The Telegram user ID
        user_name: The user's display name
        game_mode: The game mode (map, flag, capital, cap)
        is_correct: Whether the answer was correct
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Update user info
        cursor.execute('''
        INSERT OR REPLACE INTO user_info (user_id, user_name, last_seen)
        VALUES (?, ?, datetime('now'))
        ''', (user_id, user_name))

        # Check if user has stats for this mode
        cursor.execute('''
        SELECT total_games, correct_games FROM leaderboard
        WHERE user_id = ? AND game_mode = ?
        ''', (user_id, game_mode))

        existing = cursor.fetchone()

        if existing:
            # Update existing record
            total_games = existing[0] + 1
            correct_games = existing[1] + (1 if is_correct else 0)

            cursor.execute('''
            UPDATE leaderboard
            SET total_games = ?, correct_games = ?
            WHERE user_id = ? AND game_mode = ?
            ''', (total_games, correct_games, user_id, game_mode))
        else:
            # Insert new record
            cursor.execute('''
            INSERT INTO leaderboard (user_id, game_mode, total_games, correct_games)
            VALUES (?, ?, ?, ?)
            ''', (user_id, game_mode, 1, 1 if is_correct else 0))

        conn.commit()
        logger.info(f"Updated stats for user {user_id} in mode {game_mode}: correct={is_correct}")

    except Exception as e:
        logger.error(f"Error updating user stats: {e}")
        conn.rollback()
    finally:
        conn.close()

def get_user_stats(user_id: int) -> Dict[str, Dict[str, int]]:
    """
    Get all stats for a specific user.

    Returns:
        Dictionary mapping game modes to stats dictionaries
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute('''
        SELECT game_mode, total_games, correct_games
        FROM leaderboard
        WHERE user_id = ?
        ''', (user_id,))

        results = cursor.fetchall()

        stats = {}
        for row in results:
            game_mode, total, correct = row
            stats[game_mode] = {"total": total, "correct": correct}

        return stats

    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        return {}
    finally:
        conn.close()

def get_all_user_stats() -> Dict[int, Dict[str, Any]]:
    """
    Get stats for all users.

    Returns:
        Dictionary mapping user IDs to their stats dictionaries
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute('''
        SELECT l.user_id, l.game_mode, l.total_games, l.correct_games, u.user_name
        FROM leaderboard l
        JOIN user_info u ON l.user_id = u.user_id
        ''')

        results = cursor.fetchall()

        all_stats = {}
        for row in results:
            user_id, game_mode, total, correct, user_name = row

            if user_id not in all_stats:
                all_stats[user_id] = {"modes": {}, "name": user_name}

            all_stats[user_id]["modes"][game_mode] = {"total": total, "correct": correct}

        return all_stats

    except Exception as e:
        logger.error(f"Error getting all user stats: {e}")
        return {}
    finally:
        conn.close()

def get_leaderboard(limit: int = 10) -> List[Tuple[int, str, float, int, int, Dict[str, Dict[str, Any]]]]:
    """
    Get the top users for the leaderboard.

    Args:
        limit: Maximum number of users to return

    Returns:
        List of tuples with (user_id, user_name, accuracy, total_correct, total_games, modes_dict)
    """
    all_stats = get_all_user_stats()

    # Calculate overall stats for each user
    user_totals = []
    for user_id, user_data in all_stats.items():
        modes = user_data.get("modes", {})
        user_name = user_data.get("name", f"User {user_id}")

        total_games = 0
        total_correct = 0
        modes_with_accuracy = {}

        for mode, stats in modes.items():
            # Ensure stats is a dictionary with total and correct keys
            if isinstance(stats, dict) and "total" in stats and "correct" in stats:
                mode_total = stats["total"]
                mode_correct = stats["correct"]

                total_games += mode_total
                total_correct += mode_correct

                # Calculate accuracy for this mode
                accuracy = (mode_correct / mode_total * 100) if mode_total > 0 else 0

                modes_with_accuracy[mode] = {
                    "total": mode_total,
                    "correct": mode_correct,
                    "accuracy": accuracy
                }
            else:
                logger.warning(f"Unexpected stats format for user {user_id}, mode {mode}: {stats}")

        # Calculate overall accuracy
        overall_accuracy = (total_correct / total_games * 100) if total_games > 0 else 0

        user_totals.append((
            user_id,
            user_name,
            overall_accuracy,
            total_correct,
            total_games,
            modes_with_accuracy
        ))

    # Sort by overall accuracy (highest first)
    sorted_users = sorted(user_totals, key=lambda x: x[2], reverse=True)

    # Return top users up to the limit
    return sorted_users[:limit]

def export_leaderboard_to_json(output_path: str = "leaderboard_backup.json"):
    """Export the entire leaderboard to a JSON file for backup purposes."""
    try:
        all_stats = get_all_user_stats()
        with open(output_path, 'w') as f:
            json.dump(all_stats, f, indent=2)
        logger.info(f"Leaderboard exported successfully to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Error exporting leaderboard: {e}")
        return False

def import_leaderboard_from_json(input_path: str = "leaderboard_backup.json"):
    """Import leaderboard data from a JSON file."""
    if not os.path.exists(input_path):
        logger.warning(f"Import file not found: {input_path}")
        return False

    try:
        with open(input_path, 'r') as f:
            all_stats = json.load(f)

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        for user_id, user_data in all_stats.items():
            user_id = int(user_id)  # JSON keys are strings
            user_name = user_data.get("name", f"User {user_id}")

            # Update user info
            cursor.execute('''
            INSERT OR REPLACE INTO user_info (user_id, user_name, last_seen)
            VALUES (?, ?, datetime('now'))
            ''', (user_id, user_name))

            # Update stats for each mode
            for mode, stats in user_data.get("modes", {}).items():
                total = stats.get("total", 0)
                correct = stats.get("correct", 0)

                cursor.execute('''
                INSERT OR REPLACE INTO leaderboard (user_id, game_mode, total_games, correct_games)
                VALUES (?, ?, ?, ?)
                ''', (user_id, mode, total, correct))

        conn.commit()
        conn.close()
        logger.info(f"Leaderboard imported successfully from {input_path}")
        return True
    except Exception as e:
        logger.error(f"Error importing leaderboard: {e}")
        return False

# Initialize the database when the module is imported
init_db()