import os
import random
import sqlite3
import logging
import time
from typing import Dict, List, Optional, Tuple, Set, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackContext
import asyncio

# Set up logging
logger = logging.getLogger(__name__)

# Game constants
GAME_TIMEOUT = 15  # 15 seconds to answer
NUM_OPTIONS = 10   # Number of answer options to provide

class GameHandler:
    """Handles the country guessing game functionality"""

    def __init__(self):
        """Initialize the game handler"""
        # Load countries from the database
        self.countries = self.load_countries()
        # Store active games by user_id
        self.active_games = {}
        # Game stats by user_id
        self.user_stats = {}
        # Timer tasks for active games
        self.timer_tasks = {}

    def load_countries(self) -> List[Dict]:
        """Load countries from database or fall back to sample data"""
        try:
            # Try to open the SQLite database
            db_path = os.path.join("country_game", "database", "countries.db")
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                cur = conn.cursor()
                # Check if countries table exists
                cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='countries'")
                if cur.fetchone():
                    # Get countries with their data, including neighbors
                    cur.execute("SELECT name, capital, neighbors FROM countries")
                    rows = cur.fetchall()
                    conn.close()

                    # Return a list of dictionaries with country info
                    countries = []
                    for row in rows:
                        if row[0]:  # Ensure country name exists
                            neighbors = row[2].split(",") if row[2] else []
                            countries.append({
                                "name": row[0],
                                "capital": row[1] if row[1] else "Unknown",
                                "neighbors": [n.strip() for n in neighbors]
                            })

                    logger.info(f"Loaded {len(countries)} countries from database")
                    return countries

            # If we get here, either the database doesn't exist or the table is missing
            logger.warning("Countries table not found in database. Using fallback data.")
            return self._get_fallback_countries()

        except Exception as e:
            logger.error(f"Database error: {e}. Falling back to sample data.")
            return self._get_fallback_countries()

    def _get_fallback_countries(self) -> List[Dict]:
        """Return sample country data as fallback with neighbors"""
        # This is a small sample for testing
        return [
            {"name": "United_States", "capital": "Washington, D.C.", 
             "neighbors": ["Canada", "Mexico"]},
            {"name": "France", "capital": "Paris", 
             "neighbors": ["Spain", "Italy", "Germany", "Belgium", "Switzerland", "Luxembourg"]},
            {"name": "Germany", "capital": "Berlin", 
             "neighbors": ["France", "Netherlands", "Belgium", "Poland", "Czech_Republic", "Austria"]},
            {"name": "Brazil", "capital": "Brasilia", 
             "neighbors": ["Argentina", "Peru", "Colombia", "Bolivia", "Paraguay", "Uruguay"]},
            {"name": "Japan", "capital": "Tokyo", 
             "neighbors": ["South_Korea", "China", "Russia"]},
            {"name": "Australia", "capital": "Canberra", 
             "neighbors": ["New_Zealand", "Indonesia", "Papua_New_Guinea"]},
            {"name": "China", "capital": "Beijing", 
             "neighbors": ["Russia", "India", "Japan", "Mongolia", "North_Korea", "Vietnam"]},
            {"name": "Russia", "capital": "Moscow", 
             "neighbors": ["Ukraine", "Belarus", "China", "Kazakhstan", "Finland", "Norway", "Poland"]},
            {"name": "Egypt", "capital": "Cairo", 
             "neighbors": ["Libya", "Sudan", "Israel", "Jordan", "Saudi_Arabia"]},
            {"name": "South_Africa", "capital": "Pretoria", 
             "neighbors": ["Namibia", "Botswana", "Zimbabwe", "Mozambique", "Lesotho", "Eswatini"]}
        ]

    def get_random_country(self) -> Dict:
        """Return a random country from the loaded countries"""
        return random.choice(self.countries)

    def get_answer_options(self, correct_country: Dict) -> List[Dict]:
        """Generate a list of answer options (1 correct + 9 others)"""
        options = []

        # Add the correct country
        options.append(correct_country)

        # Try to add neighbors first
        neighbors = correct_country.get("neighbors", [])
        neighbor_countries = []

        for neighbor_name in neighbors:
            # Clean up the name by replacing underscores
            clean_name = neighbor_name.replace("_", " ")
            # Find matching countries
            for country in self.countries:
                if country["name"].replace("_", " ").lower() == clean_name.lower():
                    neighbor_countries.append(country)
                    break

        # Add unique neighbors to options
        for country in neighbor_countries:
            if len(options) < NUM_OPTIONS and country["name"] != correct_country["name"]:
                options.append(country)

        # If we don't have enough options, add random countries
        other_countries = [c for c in self.countries if c["name"] != correct_country["name"] 
                          and c not in options]
        random.shuffle(other_countries)

        for country in other_countries:
            if len(options) < NUM_OPTIONS:
                options.append(country)
            else:
                break

        # Shuffle options to randomize button positions
        random.shuffle(options)
        return options

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Display help information for the game"""
        help_text = (
            "🌍 *Country Guessing Game Options* 🌍\n\n"
            "*/g help* - Show this help message\n"
            "*/g* or */g map* - Launch game in map mode (guess from a map)\n"
            "*/g flag* - Launch game in flag mode (guess from a flag)\n"
            "*/g capital* - Launch game in capital mode (guess from a capital city)\n\n"
            "To play: simply tap on the correct country from the options provided.\n"
            "You have 15 seconds to answer each question."
        )
        await update.message.reply_text(help_text, parse_mode="Markdown")

    async def start_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE, game_mode: str) -> None:
        """Start a new game in the specified mode"""
        user_id = update.effective_user.id
        country = self.get_random_country()

        # Cancel any existing timer for this user
        self._cancel_timer(user_id)

        # Store game state
        self.active_games[user_id] = {
            "country": country,
            "mode": game_mode,
            "attempts": 0,
            "start_time": time.time()
        }

        # Log the game start
        logger.info(f"Starting {game_mode} game for user {user_id} with country {country['name']}")

        if game_mode == "map":
            await self._send_map_challenge(update, context, country)
        elif game_mode == "flag":
            await self._send_flag_challenge(update, context, country)
        elif game_mode == "capital":
            await self._send_capital_challenge(update, context, country)
        else:
            await update.message.reply_text("Invalid game mode. Use /g help for options.")

    def _cancel_timer(self, user_id: int) -> None:
        """Cancel the timer for a specific user if it exists"""
        if user_id in self.timer_tasks:
            task = self.timer_tasks.pop(user_id)
            if not task.done():
                task.cancel()

    async def _game_timeout_callback(self, update: Update, context: CallbackContext, user_id: int) -> None:
        """Handle game timeout after waiting for the timeout period"""
        try:
            # Capture chat_id before sleep to avoid any issues with update object becoming stale
            chat_id = update.effective_chat.id
            logger.info(f"Starting timeout timer for user {user_id} in chat {chat_id} - waiting {GAME_TIMEOUT} seconds")

            # Wait for GAME_TIMEOUT seconds
            await asyncio.sleep(GAME_TIMEOUT)

            logger.info(f"Timeout period completed for user {user_id} - checking if game is still active")

            # Check if the game is still active (user hasn't answered yet)
            if user_id in self.active_games:
                game = self.active_games[user_id]
                correct_country = game["country"]["name"].replace("_", " ")
                logger.info(f"Game for user {user_id} is still active - sending timeout message")

                try:
                    # Get the original message ID
                    message_id = game.get("message_id")
                    if message_id and game["mode"] in ["map", "flag"]:
                        # For map and flag modes, edit the caption
                        try:
                            await context.bot.edit_message_caption(
                                chat_id=chat_id,
                                message_id=message_id,
                                caption=f"⏱️ Time's up! The correct answer was *{correct_country}*.",
                                parse_mode="Markdown"
                            )
                            logger.info(f"Successfully edited caption for timeout in {game['mode']} mode")
                        except Exception as e:
                            logger.error(f"Error editing caption: {e}")
                            # Fall back to sending a new message
                            await context.bot.send_message(
                                chat_id=chat_id,
                                text=f"⏱️ Time's up! The correct answer was *{correct_country}*.",
                                parse_mode="Markdown"
                            )
                    elif message_id and game["mode"] == "capital":
                        # For capital mode, edit the text
                        try:
                            await context.bot.edit_message_text(
                                chat_id=chat_id,
                                message_id=message_id,
                                text=f"⏱️ Time's up! The correct answer was *{correct_country}*.",
                                parse_mode="Markdown"
                            )
                            logger.info(f"Successfully edited text for timeout in capital mode")
                        except Exception as e:
                            logger.error(f"Error editing text: {e}")
                            # Fall back to sending a new message
                            await context.bot.send_message(
                                chat_id=chat_id,
                                text=f"⏱️ Time's up! The correct answer was *{correct_country}*.",
                                parse_mode="Markdown"
                            )
                    else:
                        # If we don't have a message_id, send a new message
                        await context.bot.send_message(
                            chat_id=chat_id,
                            text=f"⏱️ Time's up! The correct answer was *{correct_country}*.",
                            parse_mode="Markdown"
                        )
                        logger.info("Sent new timeout message (no message_id available for editing)")

                    # Update stats
                    self._update_user_stats(user_id, False)

                    # Offer to play again with navigation buttons
                    await self._send_game_navigation(update, context)

                    # Remove game state
                    del self.active_games[user_id]
                    logger.info(f"Timeout handled successfully for user {user_id}")
                except Exception as e:
                    logger.error(f"Error handling game timeout: {e}")
            else:
                logger.info(f"Game for user {user_id} is no longer active - user already answered")
        except asyncio.CancelledError:
            # Timer was cancelled, no need to do anything
            logger.info(f"Timer for user {user_id} was cancelled - user answered before timeout")
        except Exception as e:
            logger.error(f"Error in game timeout callback: {e}")

    async def _send_map_challenge(self, update: Update, context: ContextTypes.DEFAULT_TYPE, country: Dict) -> None:
        """Send a map challenge to the user with multiple-choice options"""
        country_name = country["name"]
        image_path = os.path.join("country_game", "images", "wiki_all_map_400pi", f"{country_name}_locator_map.png")

        try:
            # Generate answer options (1 correct + 9 others)
            options = self.get_answer_options(country)

            # Create inline keyboard with answer options
            keyboard = []
            row = []
            for i, option in enumerate(options):
                display_name = option["name"].replace("_", " ")
                # Ensure consistency by using the exact country name as stored in the database
                callback_data = f"guess_{option['name']}"
                logger.info(f"Creating button for {display_name} with callback_data: {callback_data}")
                row.append(InlineKeyboardButton(display_name, callback_data=callback_data))

                # Create a new row after every 2 buttons
                if (i + 1) % 2 == 0 or (i + 1) == len(options):
                    keyboard.append(row)
                    row = []

            reply_markup = InlineKeyboardMarkup(keyboard)

            with open(image_path, "rb") as photo_file:
                caption = "🗺️ *Guess the country from this map!*\nYou have 15 seconds to answer."
                message = await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=photo_file,
                    caption=caption,
                    parse_mode="Markdown",
                    reply_markup=reply_markup
                )

                # Store the message_id for potential cleanup later
                self.active_games[update.effective_user.id]["message_id"] = message.message_id

                # Set a timer for this game that actually waits GAME_TIMEOUT seconds
                self.timer_tasks[update.effective_user.id] = asyncio.create_task(
                    self._game_timeout_callback(update, context, update.effective_user.id)
                )

        except FileNotFoundError:
            logger.error(f"Map image not found for {country_name}: {image_path}")
            await update.message.reply_text(
                f"Sorry, I couldn't find the map for this country. Try another game!"
            )
            # Clean up the game state
            if update.effective_user.id in self.active_games:
                del self.active_games[update.effective_user.id]

    async def _send_flag_challenge(self, update: Update, context: ContextTypes.DEFAULT_TYPE, country: Dict) -> None:
        """Send a flag challenge to the user with multiple-choice options"""
        country_name = country["name"]
        image_path = os.path.join("country_game", "images", "wiki_flag", f"{country_name}_flag.png")

        try:
            # Generate answer options (1 correct + 9 others)
            options = self.get_answer_options(country)

            # Create inline keyboard with answer options
            keyboard = []
            row = []
            for i, option in enumerate(options):
                display_name = option["name"].replace("_", " ")
                # Ensure consistency by using the exact country name as stored in the database
                callback_data = f"guess_{option['name']}"
                logger.info(f"Creating button for {display_name} with callback_data: {callback_data}")
                row.append(InlineKeyboardButton(display_name, callback_data=callback_data))

                # Create a new row after every 2 buttons
                if (i + 1) % 2 == 0 or (i + 1) == len(options):
                    keyboard.append(row)
                    row = []

            reply_markup = InlineKeyboardMarkup(keyboard)

            with open(image_path, "rb") as photo_file:
                caption = "🏳️ *Guess the country from this flag!*\nYou have 15 seconds to answer."
                message = await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=photo_file,
                    caption=caption,
                    parse_mode="Markdown",
                    reply_markup=reply_markup
                )

                # Store the message_id for potential cleanup later
                self.active_games[update.effective_user.id]["message_id"] = message.message_id

                # Set a timer for this game that actually waits GAME_TIMEOUT seconds
                self.timer_tasks[update.effective_user.id] = asyncio.create_task(
                    self._game_timeout_callback(update, context, update.effective_user.id)
                )

        except FileNotFoundError:
            logger.error(f"Flag image not found for {country_name}: {image_path}")
            await update.message.reply_text(
                f"Sorry, I couldn't find the flag for this country. Try another game!"
            )
            # Clean up the game state
            if update.effective_user.id in self.active_games:
                del self.active_games[update.effective_user.id]

    async def _send_capital_challenge(self, update: Update, context: ContextTypes.DEFAULT_TYPE, country: Dict) -> None:
        """Send a capital challenge to the user with multiple-choice options"""
        capital = country.get("capital", "Unknown")

        # Generate answer options (1 correct + 9 others)
        options = self.get_answer_options(country)

        # Create inline keyboard with answer options
        keyboard = []
        row = []
        for i, option in enumerate(options):
            display_name = option["name"].replace("_", " ")
            # Ensure consistency by using the exact country name as stored in the database
            callback_data = f"guess_{option['name']}"
            logger.info(f"Creating button for {display_name} with callback_data: {callback_data}")
            row.append(InlineKeyboardButton(display_name, callback_data=callback_data))

            # Create a new row after every 2 buttons
            if (i + 1) % 2 == 0 or (i + 1) == len(options):
                keyboard.append(row)
                row = []

        reply_markup = InlineKeyboardMarkup(keyboard)

        message = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"🏙️ *Guess the country whose capital is:* {capital}\nYou have 15 seconds to answer.",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )

        # Store the message_id for potential cleanup later
        self.active_games[update.effective_user.id]["message_id"] = message.message_id

        # Set a timer for this game that actually waits GAME_TIMEOUT seconds
        self.timer_tasks[update.effective_user.id] = asyncio.create_task(
            self._game_timeout_callback(update, context, update.effective_user.id)
        )

    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle callback queries from inline keyboard buttons"""
        query = update.callback_query
        user_id = update.effective_user.id

        # Cancel the timer for this game
        self._cancel_timer(user_id)

        await query.answer()  # Acknowledge the button press to Telegram

        # Check if it's a game guess
        if query.data.startswith("guess_"):
            await self._handle_guess(update, context, query)
        # Check if it's a navigation button
        elif query.data.startswith("play_"):
            game_mode = query.data.split("_")[1]
            await self.start_game(update, context, game_mode)

    async def _handle_guess(self, update: Update, context: ContextTypes.DEFAULT_TYPE, query) -> None:
        """Handle a guess from the inline keyboard"""
        user_id = update.effective_user.id

        # Check if user has an active game
        if user_id not in self.active_games:
            await query.edit_message_text("No active game found. Please start a new game.")
            return

        # Get the active game
        game = self.active_games[user_id]
        correct_country = game["country"]["name"]
        guess = query.data.split("_")[1]  # Format is "guess_CountryName"

        # Calculate elapsed time
        elapsed_time = round(time.time() - game["start_time"], 1)

        # Debug logs to help diagnose comparison issues
        logger.info(f"Comparing guess '{guess}' with correct answer '{correct_country}'")
        logger.info(f"After normalization: '{guess.lower().replace('_', '')}' vs '{correct_country.lower().replace('_', '')}'")

        # Fix: Normalize both strings for comparison to avoid false negatives
        # This makes the comparison more robust against format differences
        is_correct = guess.lower().replace("_", "") == correct_country.lower().replace("_", "")
        logger.info(f"Is correct: {is_correct}")

        if is_correct:
            # User got it right
            await query.edit_message_caption(
                caption=f"✅ *Correct!* The country is indeed *{correct_country.replace('_', ' ')}*!\n"\
                       f"You answered in {elapsed_time} seconds.",
                parse_mode="Markdown"
            )

            # Update stats
            self._update_user_stats(user_id, True)

        else:
            # Wrong answer
            await query.edit_message_caption(
                caption=f"❌ Sorry, that's not correct. The country was *{correct_country.replace('_', ' ')}*.",
                parse_mode="Markdown"
            )

            # Update stats
            self._update_user_stats(user_id, False)

        # Clean up
        del self.active_games[user_id]

        # Offer to play again with navigation buttons
        await self._send_game_navigation(update, context)

    async def _send_game_navigation(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send navigation buttons to select the next game"""
        keyboard = [
            [
                InlineKeyboardButton("🗺️ Play Map Game", callback_data="play_map"),
                InlineKeyboardButton("🏳️ Play Flag Game", callback_data="play_flag")
            ],
            [
                InlineKeyboardButton("🏙️ Play Capital Game", callback_data="play_capital")
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Choose your next game:",
            reply_markup=reply_markup
        )

    async def handle_answer(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Legacy handler for text answers (we now use inline keyboards)"""
        user_id = update.effective_user.id

        # Check if user has an active game
        if user_id not in self.active_games:
            return

        # Get the active game
        game = self.active_games[user_id]
        correct_country = game["country"]["name"].replace("_", " ")
        user_answer = update.message.text.strip()

        # Cancel the timer for this game
        self._cancel_timer(user_id)

        # Increment attempts
        game["attempts"] += 1

        # Check if the answer is correct (case insensitive comparison)
        is_correct = user_answer.lower() == correct_country.lower()

        if is_correct:
            # User got it right
            await update.message.reply_text(
                f"✅ *Correct!* The country is indeed *{correct_country}*!",
                parse_mode="Markdown"
            )

            # Update stats
            self._update_user_stats(user_id, True)

            # Clean up
            del self.active_games[user_id]

            # Offer to play again with navigation buttons
            await self._send_game_navigation(update, context)

        else:
            # Wrong answer
            if game["attempts"] >= 3:
                # Too many attempts, reveal the answer
                await update.message.reply_text(
                    f"❌ Sorry, that's not correct. The country was *{correct_country}*.",
                    parse_mode="Markdown"
                )

                # Update stats
                self._update_user_stats(user_id, False)

                # Clean up
                del self.active_games[user_id]

                # Offer to play again with navigation buttons
                await self._send_game_navigation(update, context)

            else:
                # Still has attempts left
                await update.message.reply_text(
                    f"❌ That's not correct. Try again! ({game['attempts']}/3 attempts)",
                    parse_mode="Markdown"
                )

    def _update_user_stats(self, user_id: int, is_correct: bool) -> None:
        """Update game statistics for a user"""
        if str(user_id) not in self.user_stats:
            self.user_stats[str(user_id)] = {
                "games_played": 0,
                "correct": 0,
                "streak": 0,
                "max_streak": 0
            }

        stats = self.user_stats[str(user_id)]
        stats["games_played"] += 1

        if is_correct:
            stats["correct"] += 1
            stats["streak"] += 1
            stats["max_streak"] = max(stats["max_streak"], stats["streak"])
        else:
            stats["streak"] = 0