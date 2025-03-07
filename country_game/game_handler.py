import logging
import os
import random
import re
import time
import sqlite3
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union, Any

from PIL import Image
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from country_game.config import (CAPITAL_MODE, CAP_MODE, DATABASE_PATH, FLAG_MODE,
                                MAP_MODE, MAP_IMAGES_PATH, FLAG_IMAGES_PATH,
                                MAX_ATTEMPTS, GAME_TIMEOUT, NUM_OPTIONS,
                                CORRECT_ANSWER_MESSAGE, WRONG_ANSWER_MESSAGE,
                                TOO_MANY_ATTEMPTS_MESSAGE, NO_IMAGE_MESSAGE,
                                TIMEOUT_MESSAGE)

logger = logging.getLogger(__name__)

# Game configuration constants (from config.py, used here for easier imports)
MAX_HINT_COUNTRIES = 9  # Maximum number of hint countries to display

class GameHandler:
    """Handler for the country guessing game"""

    def __init__(self):
        """Initialize the game handler"""
        logger.info("Initializing GameHandler")
        self.active_games = {}  # User ID -> Game data
        self.user_stats = {}  # User ID -> Stats
        self.timers = {}  # User ID -> Timer job

        # Load countries from database
        self.countries = []
        self._load_countries_from_database()

        # Initialize database and create user_stats table if it doesn't exist
        self._init_database()

        # Load user stats from database
        self._load_user_stats_from_database()

        # Run sanity check for image availability
        self._verify_image_availability()
        logger.info("GameHandler initialization complete")

    def _verify_image_availability(self):
        """Verify that images are available and accessible with the correct file patterns"""
        try:
            # Check if image directories exist
            if not os.path.exists(MAP_IMAGES_PATH):
                logger.warning(f"Map images directory not found: {MAP_IMAGES_PATH}")
            if not os.path.exists(FLAG_IMAGES_PATH):
                logger.warning(f"Flag images directory not found: {FLAG_IMAGES_PATH}")

            # Get a sample country to test
            if self.countries:
                test_country = self.countries[0]
                country_name = test_country.get('name', 'Unknown')

                # Test map image path
                map_path = os.path.join(MAP_IMAGES_PATH, f"{country_name}_locator_map.png")
                if os.path.exists(map_path):
                    logger.info(f"Image path test: Found map image at {map_path}")
                else:
                    logger.warning(f"Image path test: Map image not found at {map_path}")

                # Test flag image path  
                flag_path = os.path.join(FLAG_IMAGES_PATH, f"{country_name}_flag.png")
                if os.path.exists(flag_path):
                    logger.info(f"Image path test: Found flag image at {flag_path}")
                else:
                    logger.warning(f"Image path test: Flag image not found at {flag_path}")
            else:
                logger.warning("Image path test: No countries loaded to test image paths")
        except Exception as e:
            logger.error(f"Error in image path verification: {e}")

    def _init_database(self):
        """Initialize database connection and create user_stats table if it doesn't exist"""
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()

            # Create user_stats table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_stats (
                    user_id INTEGER,
                    game_mode TEXT,
                    total INTEGER DEFAULT 0,
                    correct INTEGER DEFAULT 0,
                    login_method TEXT DEFAULT 'tele',
                    user_name TEXT,
                    wallet_address TEXT DEFAULT '0xtele',
                    first_play_timestamp INTEGER,
                    PRIMARY KEY (user_id, game_mode)
                )
            ''')

            # Check if we need to add the new columns (for existing installations)
            # Get current column names
            cursor.execute("PRAGMA table_info(user_stats)")
            columns = [column[1] for column in cursor.fetchall()]
            
            # Add new columns if they don't exist
            if "login_method" not in columns:
                cursor.execute("ALTER TABLE user_stats ADD COLUMN login_method TEXT DEFAULT 'tele'")
            if "user_name" not in columns:
                cursor.execute("ALTER TABLE user_stats ADD COLUMN user_name TEXT")
            if "wallet_address" not in columns:
                cursor.execute("ALTER TABLE user_stats ADD COLUMN wallet_address TEXT DEFAULT '0xtele'")
            if "first_play_timestamp" not in columns:
                cursor.execute("ALTER TABLE user_stats ADD COLUMN first_play_timestamp INTEGER")

            conn.commit()
            conn.close()
            logger.info("Database initialized successfully with new columns")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")

    def _load_user_stats_from_database(self):
        """Load user statistics from the database"""
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()

            # Get all columns from the table
            cursor.execute("PRAGMA table_info(user_stats)")
            columns = [column[1] for column in cursor.fetchall()]
            
            # Construct a query based on available columns
            select_columns = ["user_id", "game_mode", "total", "correct"]
            
            # Add new columns if they exist
            if "login_method" in columns:
                select_columns.append("login_method")
            if "user_name" in columns:
                select_columns.append("user_name")
            if "wallet_address" in columns:
                select_columns.append("wallet_address")
            if "first_play_timestamp" in columns:
                select_columns.append("first_play_timestamp")
                
            query = f"SELECT {', '.join(select_columns)} FROM user_stats"
            cursor.execute(query)
            rows = cursor.fetchall()

            for row in rows:
                # The first 4 columns are always user_id, game_mode, total, correct
                user_id, game_mode, total, correct = row[0:4]
                
                if user_id not in self.user_stats:
                    self.user_stats[user_id] = {}
                    # Store user metadata at the user level
                    self.user_stats[user_id]["metadata"] = {}
                elif "metadata" not in self.user_stats[user_id]:
                    self.user_stats[user_id]["metadata"] = {}

                # Add game mode stats
                self.user_stats[user_id][game_mode] = {
                    "total": total,
                    "correct": correct
                }
                
                # Add additional columns if they exist
                col_index = 4
                if "login_method" in columns and col_index < len(row):
                    self.user_stats[user_id]["metadata"]["login_method"] = row[col_index]
                    col_index += 1
                    
                if "user_name" in columns and col_index < len(row):
                    self.user_stats[user_id]["metadata"]["user_name"] = row[col_index]
                    col_index += 1
                    
                if "wallet_address" in columns and col_index < len(row):
                    self.user_stats[user_id]["metadata"]["wallet_address"] = row[col_index]
                    col_index += 1
                    
                if "first_play_timestamp" in columns and col_index < len(row):
                    self.user_stats[user_id]["metadata"]["first_play_timestamp"] = row[col_index]

            conn.close()
            logger.info(f"Loaded stats for {len(self.user_stats)} users from database")
        except Exception as e:
            logger.error(f"Error loading user stats from database: {e}")

    def _save_user_stats_to_database(self, user_id: int, game_mode: str, stats: Dict[str, int], metadata: Optional[Dict] = None):
        """Save user statistics to the database"""
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            # Get current columns from the table
            cursor.execute("PRAGMA table_info(user_stats)")
            columns = [column[1] for column in cursor.fetchall()]
            
            # Prepare column names and values for the SQL query
            column_names = ["user_id", "game_mode", "total", "correct"]
            values = [user_id, game_mode, stats["total"], stats["correct"]]
            
            # If metadata is provided, add relevant fields
            if metadata:
                # Use user metadata if provided
                metadata_dict = metadata
            elif user_id in self.user_stats and "metadata" in self.user_stats[user_id]:
                # Use existing metadata from in-memory storage
                metadata_dict = self.user_stats[user_id]["metadata"]
            else:
                # Initialize empty metadata
                metadata_dict = {}
            
            # Add login_method if the column exists
            if "login_method" in columns:
                column_names.append("login_method")
                values.append(metadata_dict.get("login_method", "tele"))
                
            # Add user_name if the column exists
            if "user_name" in columns:
                column_names.append("user_name")
                values.append(metadata_dict.get("user_name", None))
                
            # Add wallet_address if the column exists
            if "wallet_address" in columns:
                column_names.append("wallet_address")
                values.append(metadata_dict.get("wallet_address", "0xtele"))
                
            # Add first_play_timestamp if the column exists
            if "first_play_timestamp" in columns:
                column_names.append("first_play_timestamp")
                values.append(metadata_dict.get("first_play_timestamp", int(time.time())))
            
            # Construct placeholders for SQL query
            placeholders = ", ".join(["?"] * len(values))
            columns_str = ", ".join(column_names)
            
            # Execute query
            cursor.execute(f'''
                INSERT OR REPLACE INTO user_stats ({columns_str})
                VALUES ({placeholders})
            ''', values)

            conn.commit()
            conn.close()
            logger.info(f"Saved stats for user {user_id}, mode {game_mode} to database")
        except Exception as e:
            logger.error(f"Error saving user stats to database: {e}")

    def _load_countries_from_database(self):
        """Load countries from the database"""
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM countries")
            rows = cursor.fetchall()

            # Get column names
            column_names = [description[0] for description in cursor.description]

            # Convert rows to dictionaries
            for row in rows:
                country = {}
                for i, value in enumerate(row):
                    country[column_names[i]] = value
                self.countries.append(country)

            conn.close()
            logger.info(f"Loaded {len(self.countries)} countries from database")
        except Exception as e:
            logger.error(f"Error loading countries from database: {e}")
            # If database loading fails, fallback to a default country
            self.countries = [{
                "id": 1,
                "name": "Vietnam",
                "capital": "Hanoi",
                "region": "Asia",
                "population": 97338579,
                "area": 331212
            }]
            logger.info("Using default fallback country")

    def _get_random_country(self) -> dict:
        """Get a random country from the database"""
        # Select a random country ID between 1 and the total number of countries
        if not self.countries:
            raise ValueError("No countries loaded from database")

        random_index = random.randint(0, len(self.countries) - 1)
        country = self.countries[random_index]

        # Log the selected country
        logger.info(f"Selected random country ID: {country.get('id')}")
        logger.info(f"Successfully loaded country: {country.get('name')}")

        return country

    def _update_user_stats(self, user_id: int, is_correct: bool,
                          game_mode: str, user_name: Optional[str] = None) -> None:
        """Update user statistics for the game"""
        # Initialize user stats if this is their first game
        if user_id not in self.user_stats:
            self.user_stats[user_id] = {}
            self.user_stats[user_id]["metadata"] = {
                "login_method": "tele",
                "user_name": user_name,
                "wallet_address": "0xtele",
                "first_play_timestamp": int(time.time())
            }
        elif "metadata" not in self.user_stats[user_id]:
            # Add metadata if missing
            self.user_stats[user_id]["metadata"] = {
                "login_method": "tele",
                "user_name": user_name,
                "wallet_address": "0xtele",
                "first_play_timestamp": int(time.time())
            }
        elif user_name and "user_name" not in self.user_stats[user_id]["metadata"]:
            # Update user name if provided and not already set
            self.user_stats[user_id]["metadata"]["user_name"] = user_name

        # Initialize stats for this mode if first time
        if game_mode not in self.user_stats[user_id]:
            self.user_stats[user_id][game_mode] = {"total": 0, "correct": 0}

        # Update stats
        self.user_stats[user_id][game_mode]["total"] += 1
        if is_correct:
            self.user_stats[user_id][game_mode]["correct"] += 1

        # Save updated stats to database
        self._save_user_stats_to_database(
            user_id, 
            game_mode, 
            self.user_stats[user_id][game_mode],
            self.user_stats[user_id]["metadata"]
        )

        logger.info(
            f"Updated user stats for {user_id} in {game_mode} mode: {self.user_stats[user_id][game_mode]}"
        )

    async def show_leaderboard(self, update: Update,
                              context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show the leaderboard for all players"""
        # Ensure we have the latest stats from the database
        self._load_user_stats_from_database()

        # Check if we have any stats
        if not self.user_stats:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="No games have been played yet. Be the first to play!")
            return

        # Calculate total stats and accuracy for each user
        user_totals = {}
        for user_id, modes in self.user_stats.items():
            user_totals[user_id] = {"total": 0, "correct": 0, "modes": {}}
            
            # Store user metadata if available
            if "metadata" in modes:
                user_totals[user_id]["metadata"] = modes["metadata"]
            
            # Calculate totals across all game modes
            for mode, stats in modes.items():
                if mode == "metadata" or mode == "capital":
                    continue  # Skip the metadata dict and deprecated capital mode when summing game stats
                
                # Make sure this is a game stats dictionary
                if isinstance(stats, dict) and "total" in stats and "correct" in stats:
                    user_totals[user_id]["total"] += stats["total"]
                    user_totals[user_id]["correct"] += stats["correct"]

                    # Calculate accuracy for this mode
                    accuracy = (stats["correct"] / stats["total"] *
                                100) if stats["total"] > 0 else 0
                    user_totals[user_id]["modes"][mode] = {
                        "total": stats["total"],
                        "correct": stats["correct"],
                        "accuracy": accuracy
                    }

            # Calculate overall accuracy
            user_totals[user_id]["accuracy"] = (
                user_totals[user_id]["correct"] /
                user_totals[user_id]["total"] *
                100) if user_totals[user_id]["total"] > 0 else 0

        # Sort users by overall accuracy (highest first)
        sorted_users = sorted(user_totals.items(),
                              key=lambda x: x[1]["accuracy"],
                              reverse=True)

        # Build leaderboard message
        message = "🏆 *Country Game Leaderboard* 🏆\n\n"

        # Add top 10 users
        for i, (user_id, stats) in enumerate(sorted_users[:10], 1):
            # Try to get the user's name from metadata or fallback to Telegram API
            user_name = None
            login_method = None
            joined_date = None
            
            if "metadata" in stats and stats["metadata"].get("user_name"):
                user_name = stats["metadata"].get("user_name")
                login_method = stats["metadata"].get("login_method", "tele")
                
                # Format first play date if available
                if "first_play_timestamp" in stats["metadata"]:
                    timestamp = stats["metadata"]["first_play_timestamp"]
                    joined_date = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
            
            # Fallback to Telegram API if no metadata name
            if not user_name:
                try:
                    user = await context.bot.get_chat(user_id)
                    user_name = user.first_name
                except Exception:
                    user_name = f"User {user_id}"

            # Add login method icon
            login_icon = "🌐" if login_method == "web" else "📱" if login_method == "tele" else "👤"
            
            # Display user rank, name, and stats
            rank_display = f"{i}. {login_icon} *{user_name}*"
            message += f"{rank_display}: {stats['accuracy']:.1f}% ({stats['correct']}/{stats['total']})"
            
            # Add joined date if available
            if joined_date:
                message += f" - Joined: {joined_date}"
                
            message += "\n"

            # Add breakdown by mode
            for mode, mode_stats in stats["modes"].items():
                mode_display = {
                    "map": "🗺️ Map",
                    "flag": "🏳️ Flag",
                    "cap": "🏙️ Capital"
                }.get(mode, mode)

                message += f"  {mode_display}: {mode_stats['accuracy']:.1f}% ({mode_stats['correct']}/{mode_stats['total']})\n"

            message += "\n"

        # Send the leaderboard
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                      text=message,
                                      parse_mode="Markdown")

    async def start_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE, game_mode: str = MAP_MODE) -> None:
        """Start a new country guessing game"""
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        user_name = update.effective_user.first_name

        logger.info(f"Starting {game_mode} game for user {user_id}")

        # Cancel any existing timer for this user
        self._cancel_timer(user_id)

        # Select a random country
        try:
            country = self._get_random_country()
            logger.info(f"Selected country for game: {country}")
        except ValueError as e:
            logger.error(f"Error selecting country: {e}")
            await context.bot.send_message(chat_id=chat_id, text=str(e))
            return

        # Set up the game in active_games
        self.active_games[user_id] = {
            "country": country,
            "start_time": time.time(),
            "mode": game_mode,
            "attempts": 0,
            "user_name": user_name  # Store username for timeout handler
        }

        # Start a timer to end the game after GAME_TIMEOUT seconds
        try:
            # Using asyncio.create_task instead of job queue for better control
            timer_job = asyncio.create_task(
                self._game_timeout(context, user_id, chat_id))
            self.timers[user_id] = timer_job
            self.active_games[user_id]["timer_job"] = timer_job
        except Exception as e:
            logger.error(f"Error setting up timer: {e}")
            await context.bot.send_message(chat_id=chat_id, 
                                          text="Error setting up game timer. Please try again.")
            if user_id in self.active_games:
                del self.active_games[user_id]
            return

        # Based on the game mode, start the appropriate game
        try:
            if game_mode == MAP_MODE:
                await self._start_map_game(update, context, country, user_id, chat_id, user_name)
            elif game_mode == FLAG_MODE:
                await self._start_flag_game(update, context, country, user_id, chat_id, user_name)
            elif game_mode == CAPITAL_MODE:
                await self._start_capital_game(update, context, country, user_id, chat_id, user_name)
            elif game_mode == CAP_MODE:
                # Cap mode is like map mode but user guesses the capital
                # For now, we'll reuse the map game with a different message
                await self._start_cap_game(update, context, country, user_id, chat_id, user_name)
            else:
                logger.error(f"Invalid game mode: {game_mode}")
                await context.bot.send_message(chat_id=chat_id, text="Invalid game mode selected.")
                del self.active_games[user_id]
        except Exception as e:
            logger.error(f"Error in start_game: {e}")
            await context.bot.send_message(chat_id=chat_id, 
                                          text="Sorry, there was an error starting the game. Please try again.")
            if user_id in self.active_games:
                del self.active_games[user_id]

    async def _start_map_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE, country: Dict, user_id: int, chat_id: int, user_name: str) -> None:
        try:
            logger.info(f"Starting map game for country: {country['name']}")
            # Fixed: Use correct image filename pattern with _locator_map.png suffix
            map_path = os.path.join(MAP_IMAGES_PATH, f"{country['name']}_locator_map.png")
            logger.info(f"Looking for map at: {map_path}")

            if not os.path.exists(map_path):
                # Try alternative pattern without underscore replacement
                formatted_name = country['name'].replace(' ', '_')
                map_path = os.path.join(MAP_IMAGES_PATH, f"{formatted_name}_locator_map.png")
                logger.info(f"Alternative path: {map_path}")

                if not os.path.exists(map_path):
                    logger.warning(f"Could not find map image for {country['name']}")
                    await context.bot.send_message(chat_id=chat_id, text=NO_IMAGE_MESSAGE.format("map"))
                    del self.active_games[user_id]
                    await self._send_game_navigation(update, context)
                    return

            options = self._generate_options(country, MAP_MODE)
            keyboard = self._create_keyboard(options)
            logger.info(f"Generated options: {options}")

            with open(map_path, 'rb') as photo:
                message = await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=photo,
                    caption=f"🌍 {user_name}, which country is highlighted on this map? (⏱️ {GAME_TIMEOUT}s)",
                    reply_markup=keyboard)
                self.active_games[user_id]["message_id"] = message.message_id
                logger.info(f"Successfully sent map game to user {user_id}")
        except Exception as e:
            logger.error(f"Error in _start_map_game: {e}")
            await context.bot.send_message(chat_id=chat_id, text="Sorry, there was an error starting the game. Please try again.")
            if user_id in self.active_games:
                del self.active_games[user_id]
            await self._send_game_navigation(update, context)

    async def _start_flag_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE, country: Dict, user_id: int, chat_id: int, user_name: str) -> None:
        try:
            logger.info(f"Starting flag game for country: {country['name']}")
            # Fixed: Use correct image filename pattern with _flag.png suffix
            flag_path = os.path.join(FLAG_IMAGES_PATH, f"{country['name']}_flag.png")
            logger.info(f"Looking for flag at: {flag_path}")

            if not os.path.exists(flag_path):
                # Try alternative pattern without underscore replacement
                formatted_name = country['name'].replace(' ', '_')
                flag_path = os.path.join(FLAG_IMAGES_PATH, f"{formatted_name}_flag.png")
                logger.info(f"Alternative path: {flag_path}")

                if not os.path.exists(flag_path):
                    logger.warning(f"Could not find flag image for {country['name']}")
                    await context.bot.send_message(chat_id=chat_id, text=NO_IMAGE_MESSAGE.format("flag"))
                    del self.active_games[user_id]
                    await self._send_game_navigation(update, context)
                    return

            options = self._generate_options(country, FLAG_MODE)
            keyboard = self._create_keyboard(options)
            logger.info(f"Generated options: {options}")

            with open(flag_path, 'rb') as photo:
                message = await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=photo,
                    caption=f"🏳️ {user_name}, which country does this flag belong to? (⏱️ {GAME_TIMEOUT}s)",
                    reply_markup=keyboard)
                self.active_games[user_id]["message_id"] = message.message_id
                logger.info(f"Successfully sent flag game to user {user_id}")
        except Exception as e:
            logger.error(f"Error in _start_flag_game: {e}")
            await context.bot.send_message(chat_id=chat_id, text="Sorry, there was an error starting the game. Please try again.")
            if user_id in self.active_games:
                del self.active_games[user_id]
            await self._send_game_navigation(update, context)

    async def _start_capital_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE, country: Dict, user_id: int, chat_id: int, user_name: str) -> None:
        try:
            logger.info(f"Starting capital game for country: {country['name']}")
            # Fixed: Use correct image filename pattern with _locator_map.png suffix
            map_path = os.path.join(MAP_IMAGES_PATH, f"{country['name']}_locator_map.png")
            logger.info(f"Looking for map at: {map_path}")

            # Try alternative pattern if the first one doesn't work
            if not os.path.exists(map_path):
                formatted_name = country['name'].replace(' ', '_')
                map_path = os.path.join(MAP_IMAGES_PATH, f"{formatted_name}_locator_map.png")
                logger.info(f"Alternative path: {map_path}")

            if not os.path.exists(map_path) or not country.get("capital"):
                logger.warning(f"Could not find map image or capital for {country['name']}")
                await context.bot.send_message(chat_id=chat_id, text=NO_IMAGE_MESSAGE.format("capital"))
                del self.active_games[user_id]
                await self._send_game_navigation(update, context)
                return

            options = self._generate_options(country, CAPITAL_MODE)
            keyboard = self._create_keyboard(options)
            logger.info(f"Generated options: {options}")

            with open(map_path, 'rb') as photo:
                message = await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=photo,
                    caption=f"🌍 {user_name}, what is the capital city of this country? (⏱️ {GAME_TIMEOUT}s)\n\nChoose from the options below:",
                    parse_mode="Markdown",
                    reply_markup=keyboard)
                self.active_games[user_id]["message_id"] = message.message_id
                logger.info(f"Successfully sent capital game to user {user_id}")
        except Exception as e:
            logger.error(f"Error in _start_capital_game: {e}")
            await context.bot.send_message(chat_id=chat_id, text="Sorry, there was an error starting the game. Please try again.")
            if user_id in self.active_games:
                del self.active_games[user_id]
            await self._send_game_navigation(update, context)
            
    async def _start_cap_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE, country: Dict, user_id: int, chat_id: int, user_name: str) -> None:
        try:
            logger.info(f"Starting cap (capital guessing) game for country: {country['name']}")
            # Use correct image filename pattern with _locator_map.png suffix
            map_path = os.path.join(MAP_IMAGES_PATH, f"{country['name']}_locator_map.png")
            logger.info(f"Looking for map at: {map_path}")

            # Try alternative pattern if the first one doesn't work
            if not os.path.exists(map_path):
                formatted_name = country['name'].replace(' ', '_')
                map_path = os.path.join(MAP_IMAGES_PATH, f"{formatted_name}_locator_map.png")
                logger.info(f"Alternative path: {map_path}")

            if not os.path.exists(map_path) or not country.get("capital"):
                logger.warning(f"Could not find map image or capital for {country['name']}")
                await context.bot.send_message(chat_id=chat_id, text=NO_IMAGE_MESSAGE.format("map or capital"))
                del self.active_games[user_id]
                await self._send_game_navigation(update, context)
                return

            options = self._generate_options(country, CAPITAL_MODE)
            keyboard = self._create_keyboard(options)
            logger.info(f"Generated options: {options}")

            with open(map_path, 'rb') as photo:
                message = await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=photo,
                    caption=f"🏙️ {user_name}, what is the capital city of this country? (⏱️ {GAME_TIMEOUT}s)\n\nChoose from the options below:",
                    parse_mode="Markdown",
                    reply_markup=keyboard)
                self.active_games[user_id]["message_id"] = message.message_id
                logger.info(f"Successfully sent cap game to user {user_id}")
        except Exception as e:
            logger.error(f"Error in _start_cap_game: {e}")
            await context.bot.send_message(chat_id=chat_id, text="Sorry, there was an error starting the game. Please try again.")
            if user_id in self.active_games:
                del self.active_games[user_id]
            await self._send_game_navigation(update, context)

    def _generate_options(self, country: Dict, game_mode: str) -> List[str]:
        try:
            logger.info(f"Generating options for {game_mode} mode, country: {country['name']}")
            # For both CAPITAL_MODE and CAP_MODE, we're guessing the capital
            correct_answer = country["name"] if game_mode not in [CAPITAL_MODE, CAP_MODE] else country["capital"]
            logger.info(f"Correct answer: {correct_answer}")

            options = [correct_answer]
            logger.info(f"Initial options: {options}")

            neighbors = country.get("neighbors", [])
            neighbor_capitals = country.get("neighbor_capitals", [])
            logger.info(f"Neighbors: {neighbors}")
            logger.info(f"Neighbor capitals: {neighbor_capitals}")

            if game_mode == MAP_MODE or game_mode == FLAG_MODE:
                for neighbor in neighbors[:MAX_HINT_COUNTRIES]:
                    if neighbor not in options:
                        options.append(neighbor)
            elif game_mode in [CAPITAL_MODE, CAP_MODE]:
                for capital in neighbor_capitals[:MAX_HINT_COUNTRIES]:
                    if capital and capital not in options:
                        options.append(capital)

            # Fill with random options if needed
            while len(options) < NUM_OPTIONS:
                random_country = random.choice(self.countries)
                random_option = random_country["name"] if game_mode not in [CAPITAL_MODE, CAP_MODE] else random_country["capital"]
                if random_option not in options:
                    options.append(random_option)

            random.shuffle(options)
            logger.info(f"Final options (shuffled): {options}")
            return options
        except Exception as e:
            logger.error(f"Error generating options: {e}")
            # Return a minimal set of options to avoid breaking the game
            return [country["name"] if game_mode not in [CAPITAL_MODE, CAP_MODE] else country["capital"]]

    def _create_keyboard(self, options: List[str]) -> InlineKeyboardMarkup:
        try:
            logger.info(f"Creating keyboard with options: {options}")
            keyboard = []
            row = []
            for i, option in enumerate(options):
                # Fixed: Use simple callback data that doesn't reference undefined variable
                callback_data = f"guess_{option}"
                logger.info(f"Option {i}: '{option}' with callback_data: '{callback_data}'")
                row.append(InlineKeyboardButton(option, callback_data=callback_data))
                if (i + 1) % 2 == 0 or (i + 1) == len(options):
                    keyboard.append(row)
                    row = []
            return InlineKeyboardMarkup(keyboard)
        except Exception as e:
            logger.error(f"Error creating keyboard: {e}")
            # Return a minimal keyboard with just one option to avoid breaking the game
            return InlineKeyboardMarkup([[InlineKeyboardButton("Continue", callback_data="continue")]])

    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        try:
            query = update.callback_query
            user_id = update.effective_user.id
            await query.answer()
            callback_data = query.data
            logger.info(f"Received callback query: {callback_data} from user {user_id}")

            if callback_data.startswith("guess_"):
                parts = callback_data.split("_", 1)
                if len(parts) == 2:
                    guessed_answer = parts[1]
                    logger.info(f"User {user_id} guessed: {guessed_answer}")
                    await self._handle_guess(update, context, guessed_answer)
                else:
                    logger.error(f"Invalid callback data format: {callback_data}")

            elif callback_data.startswith("play_"):
                action = callback_data.split("_")[1]
                logger.info(f"User {user_id} wants to play: {action}")
                
                # For 'capital' we use CAP_MODE (capital guessing game) 
                # This maps the button UI to the actual game mode
                if action == "capital":
                    await self.start_game(update, context, CAP_MODE)
                else:
                    await self.start_game(update, context, action)

            elif callback_data == "show_leaderboard":
                logger.info(f"User {user_id} wants to see the leaderboard")
                await self.show_leaderboard(update, context)
        except Exception as e:
            logger.error(f"Error handling callback query: {e}")
            # Don't send error to user here, as we've already answered the callback query

    async def _handle_guess(self, update: Update, context: ContextTypes.DEFAULT_TYPE, guessed_answer: str) -> None:
        try:
            user_id = update.effective_user.id
            chat_id = update.effective_chat.id
            user_name = update.effective_user.first_name
            logger.info(f"Handling guess from user {user_id}: {guessed_answer}")

            if user_id not in self.active_games:
                logger.warning(f"No active game found for user {user_id}")
                await context.bot.send_message(chat_id=chat_id, text="No active game found. Start a new game with /g")
                return

            game = self.active_games[user_id]
            country = game["country"]
            game_mode = game["mode"]
            # For both CAPITAL_MODE and CAP_MODE, we're guessing the capital
            correct_answer = country["name"] if game_mode not in [CAPITAL_MODE, CAP_MODE] else country["capital"]
            is_correct = (guessed_answer == correct_answer)
            elapsed_time = round(time.time() - game["start_time"], 1)
            logger.info(f"Correct answer: {correct_answer}, User guessed: {guessed_answer}, Is correct: {is_correct}")

            # Format country information for display
            country_name = country.get("name", "Unknown")
            capital = country.get("capital", "Unknown")
            region = country.get("region", "Unknown")
            population = self._format_population(country.get("population", 0))
            area = self._format_area(country.get("area", 0))
            
            # Escape markdown special characters
            safe_country_name = self._escape_markdown(country_name)
            safe_capital = self._escape_markdown(capital)
            safe_region = self._escape_markdown(region)
            safe_population = self._escape_markdown(population)
            safe_area = self._escape_markdown(area)
            safe_correct_answer = self._escape_markdown(correct_answer)

            # Use the formatted values in the result message
            if is_correct:
                result_message = CORRECT_ANSWER_MESSAGE.format(
                    safe_country_name, safe_capital, safe_region, safe_population, safe_area
                )
            else:
                result_message = WRONG_ANSWER_MESSAGE.format(
                    safe_correct_answer, safe_country_name, safe_capital, safe_region, safe_population, safe_area
                )

            self._update_user_stats(user_id, is_correct, game_mode, user_name)
            del self.active_games[user_id]
            self._cancel_timer(user_id)

            try:
                message_id = game.get("message_id")
                if message_id:
                    if game_mode in [MAP_MODE, FLAG_MODE]:
                        await context.bot.edit_message_caption(
                            chat_id=chat_id, 
                            message_id=message_id, 
                            caption=result_message, 
                            parse_mode="Markdown"
                        )
                    else:
                        await context.bot.edit_message_text(
                            chat_id=chat_id, 
                            message_id=message_id, 
                            text=result_message, 
                            parse_mode="Markdown"
                        )
                else:
                    await context.bot.send_message(chat_id=chat_id, text=result_message, parse_mode="Markdown")
            except Exception as e:
                logger.error(f"Error updating message with result: {e}")
                await context.bot.send_message(chat_id=chat_id, text=result_message, parse_mode="Markdown")
            await self._send_game_navigation(update, context)
        except Exception as e:
            logger.error(f"Error in _handle_guess: {e}")
            await context.bot.send_message(
                chat_id=chat_id, 
                text="Sorry, there was an error processing your answer. Please try a new game."
            )

    async def _handle_capital_guess(self, update: Update, context: ContextTypes.DEFAULT_TYPE, country_name: str, guessed_capital: str) -> None:
        try:
            user_id = update.effective_user.id
            chat_id = update.effective_chat.id
            user_name = update.effective_user.first_name

            logger.info(f"Handling capital guess: {guessed_capital} for country: {country_name} by user: {user_id}")

            if user_id not in self.active_games:
                logger.warning(f"No active game found for user: {user_id}")
                await context.bot.send_message(chat_id=chat_id, text="No active game found. Start a new game with /g")
                return

            game = self.active_games[user_id]
            country = game["country"]
            game_mode = game["mode"]  # Fixed: Use game["mode"] instead of undefined game_mode
            correct_capital = country["capital"]
            elapsed_time = round(time.time() - game["start_time"], 1)
            is_correct = (guessed_capital == correct_capital)

            # Format country information for display
            country_name = country.get("name", "Unknown")
            capital = country.get("capital", "Unknown")
            region = country.get("region", "Unknown")
            population = self._format_population(country.get("population", 0))
            area = self._format_area(country.get("area", 0))
            
            # Escape markdown special characters
            safe_country_name = self._escape_markdown(country_name)
            safe_capital = self._escape_markdown(capital)
            safe_region = self._escape_markdown(region)
            safe_population = self._escape_markdown(population)
            safe_area = self._escape_markdown(area)
            safe_correct_capital = self._escape_markdown(correct_capital)

            # Use the formatted values in the result message
            if is_correct:
                result_message = CORRECT_ANSWER_MESSAGE.format(
                    safe_country_name, safe_capital, safe_region, safe_population, safe_area
                )
            else:
                result_message = WRONG_ANSWER_MESSAGE.format(
                    safe_correct_capital, safe_country_name, safe_capital, safe_region, safe_population, safe_area
                )

            self._update_user_stats(user_id, is_correct, game_mode, user_name)
            del self.active_games[user_id]
            self._cancel_timer(user_id)

            try:
                message_id = game.get("message_id")
                if message_id:
                    await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=result_message, parse_mode="Markdown")
                else:
                    await context.bot.send_message(chat_id=chat_id, text=result_message, parse_mode="Markdown")
            except Exception as e:
                logger.error(f"Error updating message with result: {e}")
                await context.bot.send_message(chat_id=chat_id, text=result_message, parse_mode="Markdown")

            await self._send_game_navigation(update, context)
        except Exception as e:
            logger.error(f"Error in _handle_capital_guess: {e}")
            await context.bot.send_message(
                chat_id=chat_id, 
                text="Sorry, there was an error processing your answer. Please try a new game."
            )

    def _format_population(self, population: int) -> str:
        """Format population numbers for display"""
        if not population:
            return "Unknown"
        if population >= 1000000000:
            return f"{population/1000000000:.2f} billion"
        elif population >= 1000000:
            return f"{population/1000000:.2f} million"
        elif population >= 1000:
            return f"{population/1000:.1f} thousand"
        else:
            return str(population)

    def _format_area(self, area: float) -> str:
        """Format area numbers for display"""
        if not area:
            return "Unknown"
        return f"{area:,.0f} km²"
        
    def _escape_markdown(self, text: str) -> str:
        """Escape Markdown special characters to prevent parsing errors
        
        Special handling for country names and population info:
        - Country names with underscores (_) are not escaped
        - Population values keep their number formatting
        """
        if not text or not isinstance(text, str):
            return str(text)
            
        # Clean up any text that looks like a country name (contains underscores)
        # or population value (contains "million", "billion", or number with commas)
        if '_' in text or 'million' in text or 'billion' in text or (',' in text and any(c.isdigit() for c in text)):
            # For these special cases, only escape minimal set of characters that would break Markdown
            for char in ['*', '[', ']', '`', '>', '#']:
                text = text.replace(char, f"\\{char}")
        else:
            # Normal Markdown escaping for other text
            for char in ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']:
                text = text.replace(char, f"\\{char}")
        return text

    def _cancel_timer(self, user_id: int) -> None:
        try:
            if user_id in self.timers and self.timers[user_id]:
                self.timers[user_id].cancel()
                logger.info(f"Cancelled timer for user {user_id}")
        except Exception as e:
            logger.error(f"Error cancelling timer: {e}")

    async def _game_timeout(self, context: ContextTypes.DEFAULT_TYPE, user_id: int, chat_id: int) -> None:
        try:
            logger.info(f"Game timeout started for user {user_id}")
            # Sleep for GAME_TIMEOUT seconds
            await asyncio.sleep(GAME_TIMEOUT)

            logger.info(f"Game timed out for user {user_id}")
            if user_id not in self.active_games:
                logger.info(f"No active game found for user {user_id} after timeout")
                return

            game = self.active_games[user_id]
            country = game.get("country", {})
            game_mode = game.get("mode", "map")

            # Format country information for display
            country_name = country.get("name", "Unknown")
            capital = country.get("capital", "Unknown")
            region = country.get("region", "Unknown")
            population = self._format_population(country.get("population", 0))
            area = self._format_area(country.get("area", 0))
            
            # Escape markdown special characters
            safe_country_name = self._escape_markdown(country_name)
            safe_capital = self._escape_markdown(capital)
            safe_region = self._escape_markdown(region)
            safe_population = self._escape_markdown(population)
            safe_area = self._escape_markdown(area)

            # Use the formatted values in the timeout message
            timeout_message = TIMEOUT_MESSAGE.format(
                safe_country_name, safe_country_name, safe_capital, safe_region, safe_population, safe_area
            )

            if user_id in self.active_games:
                # Try to get username from the current game data or use a generic one
                user_name = self.active_games[user_id].get("user_name", f"User {user_id}")
                self._update_user_stats(user_id, False, game_mode, user_name)
                message_id = game.get("message_id")
                if message_id:
                    try:
                        if game_mode in ["map", "flag"]:
                            await context.bot.edit_message_caption(
                                chat_id=chat_id, 
                                message_id=message_id, 
                                caption=timeout_message, 
                                parse_mode="Markdown"
                            )
                        else:
                            await context.bot.edit_message_text(
                                chat_id=chat_id, 
                                message_id=message_id, 
                                text=timeout_message, 
                                parse_mode="Markdown"
                            )
                    except Exception as e:
                        logger.error(f"Error updating timeout message: {e}")
                        await context.bot.send_message(chat_id=chat_id, text=timeout_message, parse_mode="Markdown")
                else:
                    await context.bot.send_message(chat_id=chat_id, text=timeout_message, parse_mode="Markdown")
                del self.active_games[user_id]

                # Fixed: Create keyboard and send directly instead of using _send_game_navigation which requires update
                keyboard = [[
                    InlineKeyboardButton("🗺️ Map Mode", callback_data="play_map"),
                    InlineKeyboardButton("🏳️ Flag Mode", callback_data="play_flag")
                ],
                [
                    InlineKeyboardButton("🏙️ Capital Mode", callback_data="play_capital"),
                    InlineKeyboardButton("📊 Leaderboard", callback_data="show_leaderboard")
                ]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await context.bot.send_message(chat_id=chat_id, text="Choose a game mode:", reply_markup=reply_markup)
        except Exception as e:
            logger.error(f"Error in game timeout: {e}")
            # Try to send a fallback message if possible
            try:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="The game has timed out. Please start a new game."
                )
            except:
                pass

    async def _send_game_navigation(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        try:
            keyboard = [[
                InlineKeyboardButton("🗺️ Map Mode", callback_data="play_map"),
                InlineKeyboardButton("🏳️ Flag Mode", callback_data="play_flag")
            ],
            [
                InlineKeyboardButton("🏙️ Capital Mode", callback_data="play_capital"),
                InlineKeyboardButton("📊 Leaderboard", callback_data="show_leaderboard")
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Choose a game mode:", reply_markup=reply_markup)
        except Exception as e:
            logger.error(f"Error sending game navigation: {e}")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show help for the country game"""
        from country_game.config import HELP_TEXT, BOT_VERSION

        # Format the help text with the version number
        formatted_help_text = HELP_TEXT.format(BOT_VERSION)

        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text=formatted_help_text, 
            parse_mode="Markdown"
        )