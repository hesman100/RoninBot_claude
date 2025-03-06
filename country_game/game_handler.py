import logging
import os
import random
import re
import time
import sqlite3
import asyncio
from typing import Dict, List, Optional, Tuple, Union, Any

from PIL import Image
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from country_game.config import (CAPITAL_MODE, DATABASE_PATH, FLAG_MODE,
                                MAP_MODE, MAP_IMAGES_PATH, FLAG_IMAGES_PATH,
                                MAX_ATTEMPTS, GAME_TIMEOUT, NUM_OPTIONS,
                                CORRECT_ANSWER_MESSAGE, WRONG_ANSWER_MESSAGE,
                                TOO_MANY_ATTEMPTS_MESSAGE, NO_IMAGE_MESSAGE,
                                TIMEOUT_MESSAGE)

logger = logging.getLogger(__name__)

# Game configuration constants
GAME_TIMEOUT = 15  # seconds - changed from 60 to 15 seconds
MAX_HINT_COUNTRIES = 9  # Maximum number of hint countries to display

class GameHandler:
    """Handler for the country guessing game"""

    def __init__(self):
        """Initialize the game handler"""
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
                    PRIMARY KEY (user_id, game_mode)
                )
            ''')

            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")

    def _load_user_stats_from_database(self):
        """Load user statistics from the database"""
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()

            cursor.execute("SELECT user_id, game_mode, total, correct FROM user_stats")
            rows = cursor.fetchall()

            for row in rows:
                user_id, game_mode, total, correct = row

                if user_id not in self.user_stats:
                    self.user_stats[user_id] = {}

                self.user_stats[user_id][game_mode] = {
                    "total": total,
                    "correct": correct
                }

            conn.close()
            logger.info(f"Loaded stats for {len(self.user_stats)} users from database")
        except Exception as e:
            logger.error(f"Error loading user stats from database: {e}")

    def _save_user_stats_to_database(self, user_id: int, game_mode: str, stats: Dict[str, int]):
        """Save user statistics to the database"""
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO user_stats (user_id, game_mode, total, correct)
                VALUES (?, ?, ?, ?)
            ''', (user_id, game_mode, stats["total"], stats["correct"]))

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
                          game_mode: str) -> None:
        """Update user statistics for the game"""
        # Initialize user stats if this is their first game
        if user_id not in self.user_stats:
            self.user_stats[user_id] = {}

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
            self.user_stats[user_id][game_mode]
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

            # Calculate totals across all modes
            for mode, stats in modes.items():
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
            # Try to get the user's name
            try:
                user = await context.bot.get_chat(user_id)
                user_name = user.first_name
            except Exception:
                user_name = f"User {user_id}"

            message += f"{i}. *{user_name}*: {stats['accuracy']:.1f}% ({stats['correct']}/{stats['total']})\n"

            # Add breakdown by mode
            for mode, mode_stats in stats["modes"].items():
                mode_display = {
                    "map": "🗺️ Map",
                    "flag": "🏳️ Flag",
                    "capital": "🏙️ Capital",
                    "cap": "🏙️ Capital Guess"
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
        except ValueError as e:
            await context.bot.send_message(chat_id=chat_id, text=str(e))
            return

        # Set up the game in active_games
        self.active_games[user_id] = {
            "country": country,
            "start_time": time.time(),
            "mode": game_mode,
            "attempts": 0
        }

        # Start a timer to end the game after GAME_TIMEOUT seconds
        timer_job = context.job_queue.run_once(
            lambda ctx: asyncio.create_task(
                self._game_timeout(ctx, user_id, chat_id)), GAME_TIMEOUT)

        # Store the timer job for potential cancellation
        self.active_games[user_id]["timer_job"] = timer_job

        # Based on the game mode, start the appropriate game
        if game_mode == MAP_MODE:
            await self._start_map_game(update, context, country, user_id, chat_id, user_name)
        elif game_mode == FLAG_MODE:
            await self._start_flag_game(update, context, country, user_id, chat_id, user_name)
        elif game_mode == CAPITAL_MODE:
            await self._start_capital_game(update, context, country, user_id, chat_id, user_name)
        else:
            await context.bot.send_message(chat_id=chat_id, text="Invalid game mode selected.")
            del self.active_games[user_id]

    async def _start_map_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE, country: Dict, user_id: int, chat_id: int, user_name: str) -> None:
        map_path = os.path.join(MAP_IMAGES_PATH, f"{country['name']}.png")
        if not os.path.exists(map_path):
            await context.bot.send_message(chat_id=chat_id, text=NO_IMAGE_MESSAGE.format("map"))
            del self.active_games[user_id]
            await self._send_game_navigation(update, context)
            return

        options = self._generate_options(country, MAP_MODE)
        keyboard = self._create_keyboard(options)

        try:
            with open(map_path, 'rb') as photo:
                message = await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=photo,
                    caption=f"🌍 {user_name}, which country is highlighted on this map? (⏱️ {GAME_TIMEOUT}s)",
                    reply_markup=keyboard)
                self.active_games[user_id]["message_id"] = message.message_id
        except Exception as e:
            logger.error(f"Error sending map guessing challenge: {e}")
            await context.bot.send_message(chat_id=chat_id, text="Sorry, there was an error starting the game. Please try again.")
            del self.active_games[user_id]
            await self._send_game_navigation(update, context)

    async def _start_flag_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE, country: Dict, user_id: int, chat_id: int, user_name: str) -> None:
        flag_path = os.path.join(FLAG_IMAGES_PATH, f"{country['name']}.png")
        if not os.path.exists(flag_path):
            await context.bot.send_message(chat_id=chat_id, text=NO_IMAGE_MESSAGE.format("flag"))
            del self.active_games[user_id]
            await self._send_game_navigation(update, context)
            return

        options = self._generate_options(country, FLAG_MODE)
        keyboard = self._create_keyboard(options)

        try:
            with open(flag_path, 'rb') as photo:
                message = await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=photo,
                    caption=f"🏳️ {user_name}, which country does this flag belong to? (⏱️ {GAME_TIMEOUT}s)",
                    reply_markup=keyboard)
                self.active_games[user_id]["message_id"] = message.message_id
        except Exception as e:
            logger.error(f"Error sending flag guessing challenge: {e}")
            await context.bot.send_message(chat_id=chat_id, text="Sorry, there was an error starting the game. Please try again.")
            del self.active_games[user_id]
            await self._send_game_navigation(update, context)

    async def _start_capital_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE, country: Dict, user_id: int, chat_id: int, user_name: str) -> None:
        map_path = os.path.join(MAP_IMAGES_PATH, f"{country['name']}.png")
        if not os.path.exists(map_path) or not country.get("capital"):
            await context.bot.send_message(chat_id=chat_id, text=NO_IMAGE_MESSAGE.format("capital"))
            del self.active_games[user_id]
            await self._send_game_navigation(update, context)
            return

        options = self._generate_options(country, CAPITAL_MODE)
        keyboard = self._create_keyboard(options)

        try:
            with open(map_path, 'rb') as photo:
                message = await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=photo,
                    caption=f"🌍 {user_name}, what is the capital city of this country? (⏱️ {GAME_TIMEOUT}s)\n\nChoose from the options below:",
                    parse_mode="Markdown",
                    reply_markup=keyboard)
                self.active_games[user_id]["message_id"] = message.message_id
        except Exception as e:
            logger.error(f"Error sending capital guessing challenge: {e}")
            await context.bot.send_message(chat_id=chat_id, text="Sorry, there was an error starting the game. Please try again.")
            del self.active_games[user_id]
            await self._send_game_navigation(update, context)

    def _generate_options(self, country: Dict, game_mode: str) -> List[str]:
        correct_answer = country["name"] if game_mode != CAPITAL_MODE else country["capital"]
        options = [correct_answer]

        neighbors = country.get("neighbors", [])
        neighbor_capitals = country.get("neighbor_capitals", [])

        if game_mode == MAP_MODE or game_mode == FLAG_MODE:
            for neighbor in neighbors[:MAX_HINT_COUNTRIES]:
                if neighbor not in options:
                    options.append(neighbor)
        elif game_mode == CAPITAL_MODE:
            for capital in neighbor_capitals[:MAX_HINT_COUNTRIES]:
                if capital and capital not in options:
                    options.append(capital)


        while len(options) < NUM_OPTIONS:
            random_country = random.choice(self.countries)
            random_option = random_country["name"] if game_mode != CAPITAL_MODE else random_country["capital"]
            if random_option not in options:
                options.append(random_option)

        random.shuffle(options)
        return options

    def _create_keyboard(self, options: List[str]) -> InlineKeyboardMarkup:
        keyboard = []
        row = []
        for i, option in enumerate(options):
            # Fixed: Use simple callback data that doesn't reference undefined variable
            callback_data = f"guess_{option}"
            row.append(InlineKeyboardButton(option, callback_data=callback_data))
            if (i + 1) % 2 == 0 or (i + 1) == len(options):
                keyboard.append(row)
                row = []
        return InlineKeyboardMarkup(keyboard)


    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        user_id = update.effective_user.id
        await query.answer()
        callback_data = query.data
        logger.info(f"Received callback query: {callback_data} from user {user_id}")

        if callback_data.startswith("guess_"):
            parts = callback_data.split("_", 2)
            if len(parts) == 2:
                guessed_answer = parts[1]
                await self._handle_guess(update, context, guessed_answer)
            elif len(parts) == 3:
                country_name, guessed_answer = parts[1], parts[2]
                await self._handle_capital_guess(update, context, country_name, guessed_answer)
            else:
                logger.error(f"Invalid callback data format: {callback_data}")

        elif callback_data.startswith("play_"):
            game_mode = callback_data.split("_")[1]
            await self.start_game(update, context, game_mode)

        elif callback_data == "show_leaderboard":
            await self.show_leaderboard(update, context)


    async def _handle_guess(self, update: Update, context: ContextTypes.DEFAULT_TYPE, guessed_answer: str) -> None:
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        user_name = update.effective_user.first_name

        if user_id not in self.active_games:
            logger.warning(f"No active game found for user {user_id}")
            await context.bot.send_message(chat_id=chat_id, text="No active game found. Start a new game with /g")
            return

        game = self.active_games[user_id]
        country = game["country"]
        game_mode = game["mode"]
        correct_answer = country["name"] if game_mode != CAPITAL_MODE else country["capital"]
        is_correct = (guessed_answer == correct_answer)
        elapsed_time = round(time.time() - game["start_time"], 1)

        result_message = CORRECT_ANSWER_MESSAGE if is_correct else WRONG_ANSWER_MESSAGE.format(correct_answer)

        self._update_user_stats(user_id, is_correct, game_mode)
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


    async def _handle_capital_guess(self, update: Update, context: ContextTypes.DEFAULT_TYPE, country_name: str, guessed_capital: str) -> None:
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

        result_message = CORRECT_ANSWER_MESSAGE if is_correct else WRONG_ANSWER_MESSAGE.format(correct_capital)

        self._update_user_stats(user_id, is_correct, game_mode)
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



    def _format_population(self, population: int) -> str:
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
        if not area:
            return "Unknown"
        return f"{area:,.0f} km²"

    def _cancel_timer(self, user_id: int) -> None:
        if user_id in self.timers and self.timers[user_id]:
            self.timers[user_id].cancel()
            logger.info(f"Cancelled timer for user {user_id}")

    async def _game_timeout(self, context: ContextTypes.DEFAULT_TYPE, user_id: int, chat_id: int) -> None:
        logger.info(f"Game timed out for user {user_id}")
        if user_id not in self.active_games:
            return

        game = self.active_games[user_id]
        country = game.get("country", {})
        game_mode = game.get("mode", "map")

        timeout_message = TIMEOUT_MESSAGE.format(country.get("name", "Unknown"))

        if user_id in self.active_games:
            self._update_user_stats(user_id, False, game_mode)
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


    async def _send_game_navigation(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show help for the country game"""
        from country_game.config import HELP_TEXT, BOT_VERSION

        # Format the help text with the version number
        formatted_help_text = HELP_TEXT.format(VERSION=BOT_VERSION)

        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text=formatted_help_text, 
            parse_mode="Markdown"
        )