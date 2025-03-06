import logging
import os
import random
import time
from typing import Dict, List, Optional, Tuple, Any, Union
import asyncio
import sqlite3
import traceback # Added for more detailed error logging

# Our custom modules
from country_game import leaderboard_db
from country_game.config import GAME_TIMEOUT, MAX_HINT_COUNTRIES
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)
logger = logging.getLogger(__name__)



class GameHandler:
    """Handle country guessing game logic"""

    def __init__(self, bot_version: str = "1.0") -> None:
        """Initialize the game handler."""
        # Store bot version for result messages
        self.bot_version = bot_version

        # Database path
        self.db_path = "country_game/database/countries.db"

        # Initialize dictionaries to store active games and timers
        self.active_games = {}
        self.timers = {}

        # Dict to store user stats (also loaded from DB for persistence)
        self.user_stats = {}

        # Load existing stats from database
        self._load_stats_from_db()

        # Cache of country data
        self.countries_data = {}

        # All country names for reference
        self.all_countries = []

        # Load all country names from the database
        self._load_countries()

        logger.info("GameHandler initialized successfully")

    def _load_countries(self):
        """Load all countries from the database"""
        try:
            # Ensure database connection
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get all country names
            cursor.execute("SELECT name FROM countries ORDER BY name")
            country_names = [row[0] for row in cursor.fetchall()]

            self.all_countries = country_names
            logger.info(
                f"Loaded {len(self.all_countries)} countries from database")

            # Close the database connection
            conn.close()
        except Exception as e:
            logger.error(f"Error loading countries from database: {e}")
            # Use an empty list if database loading fails
            self.all_countries = []

    def _get_random_country_id(self) -> int:
        """Get a random country ID from the database (between 1 and 194)"""
        try:
            # Connect to the database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get the maximum country ID
            cursor.execute("SELECT MAX(number) FROM countries")
            max_id = cursor.fetchone()[0]

            # Close the connection
            conn.close()

            # Generate a random ID between 1 and max_id (should be 194)
            random_id = random.randint(1, max_id)
            return random_id
        except Exception as e:
            logger.error(f"Error getting random country ID: {e}")
            # Fallback to random between 1 and 194
            return random.randint(1, 194)

    def load_country_details(self, country_name: str) -> Dict:
        """Load country details from the database"""
        # Return from cache if available
        if country_name in self.countries_data:
            return self.countries_data[country_name]

        try:
            # Connect to the database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Query country data
            cursor.execute(
                """
                SELECT name, capital, region, population, area, 
                       map_image_link, flag_image_link, neighbor_country, neighbor_capital 
                FROM countries 
                WHERE name = ?
            """, (country_name, ))

            result = cursor.fetchone()

            if result:
                # Parse neighbor countries and capitals from comma-separated strings
                neighbor_countries = result[7].split(',') if result[7] else []
                neighbor_capitals = result[8].split(',') if result[8] else []

                # Create country data dictionary
                country_data = {
                    'name': result[0],
                    'capital': result[1],
                    'region': result[2],
                    'population': result[3],
                    'area': result[4],
                    'map_image_link': result[5],
                    'flag_image_link': result[6],
                    'neighbors': neighbor_countries,
                    'neighbor_capitals': neighbor_capitals
                }

                # Cache for future use
                self.countries_data[country_name] = country_data

                # Close the connection
                conn.close()

                return country_data
            else:
                logger.warning(
                    f"Country not found in database: {country_name}")
                conn.close()
                return {}

        except Exception as e:
            logger.error(f"Error loading country details: {e}")
            return {}

    def get_country_by_id(self, country_id: int) -> Dict:
        """Get country details by ID from the database"""
        try:
            # Connect to the database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Query country data by ID
            cursor.execute(
                """
                SELECT name, capital, region, population, area, 
                       map_image_link, flag_image_link, neighbor_country, neighbor_capital 
                FROM countries 
                WHERE number = ?
            """, (country_id, ))

            result = cursor.fetchone()

            if result:
                # Parse neighbor countries and capitals from comma-separated strings
                neighbor_countries = result[7].split(',') if result[7] else []
                neighbor_capitals = result[8].split(',') if result[8] else []

                # Create country data dictionary
                country_data = {
                    'name': result[0],
                    'capital': result[1],
                    'region': result[2],
                    'population': result[3],
                    'area': result[4],
                    'map_image_link': result[5],
                    'flag_image_link': result[6],
                    'neighbors': neighbor_countries,
                    'neighbor_capitals': neighbor_capitals
                }

                # Cache for future use
                self.countries_data[result[0]] = country_data

                # Close the connection
                conn.close()

                return country_data
            else:
                logger.warning(
                    f"Country ID not found in database: {country_id}")
                conn.close()
                return {}

        except Exception as e:
            logger.error(f"Error getting country by ID: {e}")
            return {}

    def _select_random_country(self) -> Dict:
        """Select a random country from the database using random ID"""
        # Get a random country ID between 1 and 194
        random_id = self._get_random_country_id()
        logger.info(f"Selected random country ID: {random_id}")

        # Get the country details by ID
        country = self.get_country_by_id(random_id)

        # If we got a valid country, return it
        if country and country.get('name'):
            logger.info(f"Successfully loaded country: {country.get('name')}")
            return country

        # Fallback: Only use Vietnam as our fallback country
        logger.warning(
            "Failed to select a random country, using Vietnam as fallback")
        fallback = self.load_country_details("Vietnam")

        # If even Vietnam isn't available in the database, create a minimal entry
        if not fallback or not fallback.get('name'):
            logger.error(
                "Fallback country (Vietnam) not found in database, creating minimal entry"
            )
            return {
                'name':
                'Vietnam',
                'capital':
                'Hanoi',
                'region':
                'Asia',
                'population':
                97000000,
                'area':
                331212,
                'map_image_link':
                'country_game/images/wiki_all_map_400pi/Vietnam_locator_map.png',
                'flag_image_link':
                'country_game/images/wiki_flag/Vietnam_flag.png',
                'neighbors': [
                    'China', 'Laos', 'Cambodia', 'Thailand', 'Malaysia',
                    'Philippines', 'Indonesia', 'Myanmar', 'Brunei'
                ],
                'neighbor_capitals': [
                    'Beijing', 'Vientiane', 'Phnom Penh', 'Bangkok',
                    'Kuala Lumpur', 'Manila', 'Jakarta', 'Naypyidaw',
                    'Bandar Seri Begawan'
                ]
            }

        return fallback

    def _cancel_timer(self, user_id: int) -> None:
        """Cancel a timer for a user's game"""
        # If the user has an active game with a timer job
        if user_id in self.active_games and "timer_job" in self.active_games[
                user_id]:
            # Cancel the timer job
            self.active_games[user_id]["timer_job"].cancel()
            logger.info(f"Cancelled timer for user {user_id}")

    async def _handle_timeout(self, context: ContextTypes.DEFAULT_TYPE, user_id: int) -> None:
        """Handle a game timeout"""
        # Check if the user still has an active game
        if user_id not in self.active_games:
            return

        game = self.active_games[user_id]
        chat_id = game.get("chat_id")

        if not chat_id:
            logger.error(f"Missing chat_id for user {user_id}")
            return

        # Get the correct country and mode
        correct_country = game.get("country", {})
        current_mode = game.get("mode", "map")

        # Format country name for display
        country_name = correct_country.get("name", "Unknown")
        display_country_name = country_name.replace("_", " ")

        # For capital mode, get the capital
        capital = correct_country.get("capital", "Unknown")

        # Prepare the timeout message
        if current_mode == "cap":
            timeout_message = f"⏰ Time's up! The capital of *{display_country_name}* is *{capital}*.\n\n"
        else:
            timeout_message = f"⏰ Time's up! The correct answer was *{display_country_name}*.\n\n"

        # Add country details
        timeout_message += f"📊 Quick Facts:\n"
        timeout_message += f"🌍 Region: {correct_country.get('region', 'Unknown')}\n"

        if current_mode != "cap":  # Don't show capital in capital guessing mode result
            timeout_message += f"🏙️ Capital: {capital}\n"

        # Add population and area
        population = correct_country.get("population", 0)
        area = correct_country.get("area", 0)
        timeout_message += f"👥 Population: {self._format_population(population)}\n"
        timeout_message += f"📏 Area: {self._format_area(area)}"
        timeout_message += f"\nBot Version: {self.bot_version}"

        # Record the timeout as an incorrect answer - get user name if available
        try:
            user = await context.bot.get_chat(user_id)
            user_name = user.first_name
        except Exception:
            user_name = f"User {user_id}"

        # Update stats for timeout (counted as incorrect)
        self._update_user_stats(user_id, False, current_mode, user_name)

        # Clean up the active game
        if user_id in self.active_games:
            del self.active_games[user_id]

        # Try to update the original message
        try:
            message_id = game.get("message_id")
            if message_id:
                try:
                    # Try editing depending on the game mode
                    if current_mode in ["map", "flag"]:
                        # These are photo messages with captions
                        await context.bot.edit_message_caption(
                            chat_id=chat_id,
                            message_id=message_id,
                            caption=timeout_message,
                            parse_mode="Markdown")
                    else:
                        # For text-based games like capital guessing
                        await context.bot.edit_message_text(
                            chat_id=chat_id,
                            message_id=message_id,
                            text=timeout_message,
                            parse_mode="Markdown")
                except Exception as edit_error:
                    logger.error(f"Error editing message: {edit_error}")
                    # Fallback to sending a new message if editing fails
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=timeout_message,
                        parse_mode="Markdown")
            else:
                # If we don't have the message ID, send a new message
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=timeout_message,
                    parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Error updating message with timeout: {e}")
            # Fallback to sending a new message
            await context.bot.send_message(
                chat_id=chat_id,
                text=timeout_message,
                parse_mode="Markdown")

        # Send game navigation buttons after timeout
        try:
            # Create an update object with just the chat_id for sending navigation
            class MockUpdate:
                def __init__(self, chat_id):
                    self.effective_chat = type('obj', (object,), {'id': chat_id})

            mock_update = MockUpdate(chat_id)
            await self._send_game_navigation(mock_update, context)
        except Exception as e:
            logger.error(f"Error sending game navigation after timeout: {e}")


    async def start_game(self,
                         update: Update,
                         context: ContextTypes.DEFAULT_TYPE,
                         game_mode: str = "map") -> None:
        """Start a new country guessing game"""
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        user_name = update.effective_user.first_name

        # Normalize game mode
        if game_mode == "cap":
            game_mode = "capital"

        logger.info(f"Starting {game_mode} game for user {user_id}")

        # Cancel any existing timer for this user
        self._cancel_timer(user_id)

        # Select a random country
        country = self._select_random_country()

        # Check if we got a valid country
        if not country or not country.get("name"):
            await context.bot.send_message(
                chat_id=chat_id,
                text=
                "Sorry, I couldn't find any countries to play with. Please try again later."
            )
            return

        logger.info(f"Selected country: {country.get('name', 'Unknown')}")

        # Set up the game in active_games
        self.active_games[user_id] = {
            "country": country,
            "start_time": time.time(),
            "mode": game_mode,
            "chat_id": chat_id
        }

        # Start a timer to end the game after GAME_TIMEOUT seconds
        timer_job = context.job_queue.run_once(
            lambda ctx: asyncio.create_task(
                self._handle_timeout(ctx, user_id)), GAME_TIMEOUT)

        # Store the timer job for potential cancellation
        self.active_games[user_id]["timer_job"] = timer_job

        # Based on the game mode, start the appropriate game
        if game_mode == "map":
            await self._start_map_game(update, context, country, user_id,
                                       chat_id, user_name)
        elif game_mode == "flag":
            await self._start_flag_game(update, context, country, user_id,
                                        chat_id, user_name)
        elif game_mode == "capital":
            await self._start_capital_game(update, context, country, user_id,
                                           chat_id, user_name)
        else:
            # Default to map game if mode is unknown
            await self._start_map_game(update, context, country, user_id,
                                       chat_id, user_name)

    async def _start_map_game(self, update: Update,
                              context: ContextTypes.DEFAULT_TYPE,
                              country: Dict, user_id: int, chat_id: int,
                              user_name: str) -> None:
        """Start a map guessing game"""
        # Get the map image path
        map_path = country.get("map_image_link")

        # Check if map exists
        if not map_path or not os.path.exists(map_path):
            await context.bot.send_message(
                chat_id=chat_id,
                text=
                "Sorry, I couldn't find a map for this country. Please try again."
            )
            # Clean up the game
            if user_id in self.active_games:
                del self.active_games[user_id]
            # Send game navigation
            await self._send_game_navigation(update, context)
            return

        # Get the correct answer (country name)
        correct_country = country["name"]

        # Get neighbor countries for options from the database
        neighbor_countries = country.get("neighbors", [])[:MAX_HINT_COUNTRIES]

        # Ensure we have enough options
        options = [correct_country]

        # Add neighbor countries first (if any)
        for neighbor in neighbor_countries:
            if neighbor not in options:
                options.append(neighbor)

        # If we still need more options, add random countries
        while len(options) < MAX_HINT_COUNTRIES:
            random_country_name = random.choice(self.all_countries)
            if random_country_name not in options:
                options.append(random_country_name)

        # Shuffle options
        random.shuffle(options)

        # Create keyboard with country options
        keyboard = []
        row = []
        for i, option in enumerate(options):
            # Format displayed name (replace underscores with spaces)
            display_name = option.replace("_", " ")

            # Create callback data
            callback_data = f"guess_{option}"

            # Add button to current row
            row.append(
                InlineKeyboardButton(display_name,
                                    callback_data=callback_data))

            # Start a new row after every 2 buttons
            if (i + 1) % 2 == 0 or (i + 1) == len(options):
                keyboard.append(row)
                row = []

        # Create the inline keyboard markup
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Send the map image with options
        try:
            with open(map_path, 'rb') as photo:
                message = await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=photo,
                    caption=
                    f"🌍 {user_name}, which country is highlighted on this map? (⏱️ {GAME_TIMEOUT}s)",
                    reply_markup=reply_markup)

            # Store the message ID for later reference
            if user_id in self.active_games:
                self.active_games[user_id]["message_id"] = message.message_id

            logger.info(f"Successfully sent map guessing challenge")
        except Exception as e:
            logger.error(f"Error sending map guessing challenge: {e}")
            await context.bot.send_message(
                chat_id=chat_id,
                text=
                "Sorry, there was an error starting the game. Please try again."
            )
            # Clean up the game
            if user_id in self.active_games:
                del self.active_games[user_id]
            # Send game navigation
            await self._send_game_navigation(update, context)

    async def _start_flag_game(self, update: Update,
                               context: ContextTypes.DEFAULT_TYPE,
                               country: Dict, user_id: int, chat_id: int,
                               user_name: str) -> None:
        """Start a flag guessing game"""
        # Get the flag image path
        flag_path = country.get("flag_image_link")

        # Check if flag exists
        if not flag_path or not os.path.exists(flag_path):
            await context.bot.send_message(
                chat_id=chat_id,
                text=
                "Sorry, I couldn't find a flag for this country. Please try again."
            )
            # Clean up the game
            if user_id in self.active_games:
                del self.active_games[user_id]
            # Send game navigation
            await self._send_game_navigation(update, context)
            return

        # Get the correct answer (country name)
        correct_country = country["name"]

        # Get neighbor countries for options from the database
        neighbor_countries = country.get("neighbors", [])[:MAX_HINT_COUNTRIES]

        # Ensure we have enough options
        options = [correct_country]

        # Add neighbor countries first (if any)
        for neighbor in neighbor_countries:
            if neighbor not in options:
                options.append(neighbor)

        # If we still need more options, add random countries
        while len(options) < MAX_HINT_COUNTRIES:
            random_country_name = random.choice(self.all_countries)
            if random_country_name not in options:
                options.append(random_country_name)

        # Shuffle options
        random.shuffle(options)

        # Create keyboard with country options
        keyboard = []
        row = []
        for i, option in enumerate(options):
            # Format displayed name (replace underscores with spaces)
            display_name = option.replace("_", " ")

            # Create callback data
            callback_data = f"guess_{option}"

            # Add button to current row
            row.append(
                InlineKeyboardButton(display_name,
                                    callback_data=callback_data))

            # Start a new row after every 2 buttons
            if (i + 1) % 2 == 0 or (i + 1) == len(options):
                keyboard.append(row)
                row = []

        # Create the inline keyboard markup
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Send the flag image with options
        try:
            with open(flag_path, 'rb') as photo:
                message = await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=photo,
                    caption=
                    f"🏳️ {user_name}, which country does this flag belong to? (⏱️ {GAME_TIMEOUT}s)",
                    reply_markup=reply_markup)

            # Store the message ID for later reference
            if user_id in self.active_games:
                self.active_games[user_id]["message_id"] = message.message_id

            logger.info(f"Successfully sent flag guessing challenge")
        except Exception as e:
            logger.error(f"Error sending flag guessing challenge: {e}")
            await context.bot.send_message(
                chat_id=chat_id,
                text=
                "Sorry, there was an error starting the game. Please try again."
            )
            # Clean up the game
            if user_id in self.active_games:
                del self.active_games[user_id]
            # Send game navigation
            await self._send_game_navigation(update, context)

    async def _start_capital_game(self, update: Update,
                                  context: ContextTypes.DEFAULT_TYPE,
                                  country: Dict, user_id: int, chat_id: int,
                                  user_name: str) -> None:
        """Start a capital guessing game"""
        # Get map image for the country
        map_path = country.get("map_image_link")

        # Get the correct answer (capital city)
        correct_capital = country.get("capital", "Unknown")

        # Check if map exists and capital is known
        if not map_path or not os.path.exists(
                map_path) or correct_capital == "Unknown":
            await context.bot.send_message(
                chat_id=chat_id,
                text=
                "Sorry, I couldn't find the necessary information for this country. Please try again."
            )
            # Clean up the game
            if user_id in self.active_games:
                del self.active_games[user_id]
            # Send game navigation
            await self._send_game_navigation(update, context)
            return

        # Get neighbor capitals for options from the database
        neighbor_capitals = country.get("neighbor_capitals",
                                        [])[:MAX_HINT_COUNTRIES]

        # Collect capital options (1 correct + others from neighbors)
        capital_options = [correct_capital]

        # Add neighbor capitals to options
        for capital in neighbor_capitals:
            if capital and capital not in capital_options:
                capital_options.append(capital)

        # If we still need more options, add some random capitals
        while len(capital_options) < MAX_HINT_COUNTRIES:
            # Get a random country and its capital
            random_country = self._select_random_country()
            random_capital = random_country.get("capital", "")

            if random_capital and random_capital not in capital_options:
                capital_options.append(random_capital)

        # Shuffle the options
        random.shuffle(capital_options)

        # Create keyboard with capital options
        keyboard = []
        row = []
        for i, capital in enumerate(capital_options):
            # Create callback data for this option
            callback_data = f"guess_{country['name']}_{capital}"

            # Add button to current row
            row.append(
                InlineKeyboardButton(capital, callback_data=callback_data))

            # Start a new row after every 2 buttons
            if (i + 1) % 2 == 0 or (i + 1) == len(capital_options):
                keyboard.append(row)
                row = []

        reply_markup = InlineKeyboardMarkup(keyboard)

        # Send the map image with capital options
        try:
            with open(map_path, 'rb') as photo:
                message = await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=photo,
                    caption=
                    f"🌍 {user_name}, what is the capital city of this country? (⏱️ {GAME_TIMEOUT}s)\n\nChoose from the options below:",
                    parse_mode="Markdown",
                    reply_markup=reply_markup)

                # Store the message ID for later reference
                if user_id in self.active_games:
                    self.active_games[user_id][
                        "message_id"] = message.message_id

                logger.info(f"Successfully sent capital guessing challenge")
        except Exception as e:
            logger.error(f"Error sending capital guessing challenge: {e}")
            await context.bot.send_message(
                chat_id=chat_id,
                text=
                "Sorry, there was an error starting the game. Please try again."
            )
            # Clean up the game
            if user_id in self.active_games:
                del self.active_games[user_id]
            # Send game navigation
            await self._send_game_navigation(update, context)

    async def handle_callback_query(
            self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handles callback queries from inline keyboards."""
        query = update.callback_query
        user_id = update.effective_user.id

        # Acknowledge the callback query
        await query.answer()

        # Check the callback data
        callback_data = query.data
        logger.info(
            f"Received callback query: {callback_data} from user {user_id}")

        # Handle different callback types
        if callback_data.startswith("guess_"):
            # Extract country and capital from the callback data
            parts = callback_data.split("_", 2)  # Split into at most 3 parts

            if len(parts) == 2:  # Format: "guess_CountryName"
                # This is a map or flag game guess
                guessed_country = parts[1]
                await self._handle_guess(update, context, guessed_country)
            elif len(parts) == 3:  # Format: "guess_CountryName_CapitalName"
                # This is a capital guessing game
                country_name = parts[1]
                guessed_capital = parts[2]
                await self._handle_capital_guess(update, context, country_name,
                                                 guessed_capital)
            else:
                logger.error(f"Invalid callback data format: {callback_data}")

        elif callback_data.startswith("play_"):
            # Handle game navigation buttons
            game_mode = callback_data.split("_")[1]
            await self.start_game(update, context, game_mode)

        elif callback_data == "show_leaderboard":
            # Show the leaderboard
            await self.show_leaderboard(update, context)

    async def _handle_guess(self, update: Update,
                            context: ContextTypes.DEFAULT_TYPE,
                            country_name: str) -> None:
        """Handle a guess from the inline keyboard"""
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        user_name = update.effective_user.first_name

        logger.info(f"User {user_id} guessed {country_name}")

        # Check if user has an active game
        if user_id not in self.active_games:
            logger.warning(f"No active game found for user {user_id}")
            await context.bot.send_message(
                chat_id=chat_id,
                text="No active game found. Start a new game with /g")
            return

        # Get the game data
        game = self.active_games[user_id]
        correct_country = game["country"]
        current_mode = game.get("mode", "map")

        # Check if the guess is correct
        is_correct = (country_name == correct_country["name"])

        # Format country names for display (replace underscores with spaces)
        display_guessed = country_name.replace("_", " ")
        display_correct = correct_country["name"].replace("_", " ")

        # Calculate elapsed time
        elapsed_time = round(time.time() - game["start_time"], 1)

        # Prepare result message
        if is_correct:
            result_message = f"✅ Correct! {user_name}, You Are A Marveller! (in {elapsed_time}s)\n\n"
            result_message += f"🏳️ *{display_correct}*\n"
            result_message += f"🏙️ Capital: *{correct_country.get('capital', 'Unknown')}*\n"

            # Get region information
            region = correct_country.get("region", "Unknown")
            result_message += f"🌍 Region: {region}\n"

            # Get population and area information
            population = correct_country.get("population", 0)
            area = correct_country.get("area", 0)
            result_message += f"👥 Population: {self._format_population(population)}\n"
            result_message += f"📏 Area: {self._format_area(area)}"
        else:
            # For wrong answer, immediately show the correct answer with details
            result_message = f"❌ Wrong! {user_name}, You Are A VOZER : ))\n"
            result_message += f"You selected *{display_guessed}*.\n"
            result_message += f"The correct answer was *{display_correct}*.\n\n"

            # Add details about the correct country
            result_message += f"🏳️ *{display_correct}*\n"
            result_message += f"🏙️ Capital: *{correct_country.get('capital', 'Unknown')}*\n"

            # Get region information
            region = correct_country.get("region", "Unknown")
            result_message += f"🌍 Region: {region}\n"

            # Get population and area information
            population = correct_country.get("population", 0)
            area = correct_country.get("area", 0)
            result_message += f"👥 Population: {self._format_population(population)}\n"
            result_message += f"📏 Area: {self._format_area(area)}"
        result_message += f"\nBot Version: {self.bot_version}"

        # Update user stats
        self._update_user_stats(user_id, is_correct, current_mode, user_name)

        # Always clean up the game after showing the result
        if user_id in self.active_games:
            # Cancel the timer job if it exists
            if "timer_job" in self.active_games[user_id]:
                try:
                    self.active_games[user_id]["timer_job"].cancel()
                except AttributeError:
                    # Handle case where Job object doesn't have cancel attribute
                    logger.warning("Timer job could not be cancelled due to missing cancel attribute")
            del self.active_games[user_id]

        message = update.callback_query.message

        try:
            # For map and flaggames, edit the caption if it's a photo message
            if current_mode in ["map", "flag"]:
                if hasattr(message, 'photo') and message.photo:
                    try:
                        await context.bot.edit_message_caption(
                            chat_id=chat_id,
                            message_id=message.message_id,
                            caption=result_message,
                            parse_mode="Markdown")
                    except Exception as edit_error:
                        logger.error(f"Error editing message caption: {edit_error}")
                        # Fallback to sending a new message
                        await context.bot.send_message(
                            chat_id=chat_id,
                            text=result_message,
                            parse_mode="Markdown")
                else:
                    # Not a photo message, send a new message instead
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=result_message,
                        parse_mode="Markdown")
            else:
                # For other game types, edit the text if it's a text message
                if hasattr(message, 'text') and message.text:
                    try:
                        await context.bot.edit_message_text(
                            chat_id=chat_id,
                            message_id=message.message_id,
                            text=result_message,
                            parse_mode="Markdown")
                    except Exception as edit_error:
                        logger.error(f"Error editing message text: {edit_error}")
                        # Fallback to sending a new message
                        await context.bot.send_message(
                            chat_id=chat_id,
                            text=result_message,
                            parse_mode="Markdown")
                else:
                    # Not a text message, send a new message instead
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=result_message,
                        parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Error updating message with result: {e}")
            # Fallback to sending a new message if editing fails
            await context.bot.send_message(
                chat_id=chat_id,
                text=result_message,
                parse_mode="Markdown")

        # Send game navigation buttons after showing result
        await self._send_game_navigation(update, context)

    async def _handle_capital_guess(self, update: Update,
                                    context: ContextTypes.DEFAULT_TYPE,
                                    country_name: str,
                                    guessed_capital: str) -> None:
        """Handle a capital guess from the inline keyboard"""
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        user_name = update.effective_user.first_name

        logger.info(f"User {user_id} guessed capital {guessed_capital} for {country_name}")

        # Check if user has an active game
        if user_id not in self.active_games:
            logger.warning(f"No active game found for user {user_id}")
            await context.bot.send_message(
                chat_id=chat_id,
                text="No active game found. Start a new game with /g")
            return

        # Get the game data
        game = self.active_games[user_id]
        correct_country = game["country"]

        # Safety check - make sure this is the right country
        if correct_country["name"] != country_name:
            logger.warning(f"Country mismatch in capital guess: {country_name} vs {correct_country['name']}")
            await context.bot.send_message(
                chat_id=chat_id,
                text="Something went wrong with your guess. Please start a new game.")
            return

        # Get the correct capital
        correct_capital = correct_country.get("capital", "Unknown")

        # Check if the guess is correct (case insensitive)
        is_correct = (guessed_capital.lower() == correct_capital.lower())

        # Format country and capital names for display
        display_country = country_name.replace("_", " ")

        # Calculate elapsed time
        elapsed_time = round(time.time() - game["start_time"], 1)

        # Prepare result message
        if is_correct:
            result_message = f"✅ Correct! {user_name}, You Are A Marveller! (in {elapsed_time}s)\n\n"
            result_message += f"🏳️ *{display_country}*\n"
            result_message += f"🏙️ Capital: *{correct_capital}*\n"
        else:
            result_message = f"❌ Wrong! {user_name}, You Are A VOZER : ))\n"
            result_message += f"You guessed *{guessed_capital}*.\n"
            result_message += f"The capital of *{display_country}* is *{correct_capital}*.\n\n"

        # Add additional country information
        region = correct_country.get("region", "Unknown")
        population = correct_country.get("population", 0)
        area = correct_country.get("area", 0)

        result_message += f"📊 Country Facts:\n"
        result_message += f"🌍 Region: {region}\n"
        result_message += f"👥 Population: {self._format_population(population)}\n"
        result_message += f"📏 Area: {self._format_area(area)}"
        result_message += f"\nBot Version: {self.bot_version}"

        # Update user stats
        self._update_user_stats(user_id, is_correct, "capital", user_name)

        # Always clean up the game after showing the result
        if user_id in self.active_games:
            # Cancel the timer job if it exists
            if "timer_job" in self.active_games[user_id]:
                try:
                    self.active_games[user_id]["timer_job"].cancel()
                except AttributeError:
                    # Handle case where Job object doesn't have cancel attribute
                    logger.warning("Timer job could not be cancelled due to missing cancel attribute")
            del self.active_games[user_id]

        # Try to update the original message
        message = update.callback_query.message
        try:
            # Capital game might be shown as a photo or text, so check message type
            if hasattr(message, 'photo') and message.photo:
                # This is a photo message, edit the caption
                try:
                    await context.bot.edit_message_caption(
                        chat_id=chat_id,
                        message_id=message.message_id,
                        caption=result_message,
                        parse_mode="Markdown")
                except Exception as edit_error:
                    logger.error(f"Error editing photo caption: {edit_error}")
                    # Fallback to sending a new message
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=result_message,
                        parse_mode="Markdown")
            elif hasattr(message, 'text') and message.text:
                # This is a text message, edit the text
                try:
                    await context.bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=message.message_id,
                        text=result_message,
                        parse_mode="Markdown")
                except Exception as edit_error:
                    logger.error(f"Error editing message text: {edit_error}")
                    # Fallback to sending a new message
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=result_message,
                        parse_mode="Markdown")
            else:
                # Neither photo nor text message, send a new message
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=result_message,
                    parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Error updating message with capital guess result: {e}")
            # Fallback to sending a new message
            await context.bot.send_message(
                chat_id=chat_id,
                text=result_message,
                parse_mode="Markdown")

        # Send game navigation buttons after showing result
        await self._send_game_navigation(update, context)

    def _format_population(self, population: int) -> str:
        """Format population number for display"""
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
        """Format area number for display"""
        if not area:
            return "Unknown"

        # Format with commas for thousands separator
        return f"{area:,.0f} km²"

    def _update_user_stats(self, user_id: int, is_correct: bool,
                           game_mode: str, user_name: str = None) -> None:
        """Update user statistics for the game both in memory and database."""
        # Skip updating stats for "update_only" mode (used for name updates)
        if game_mode == "update_only":
            # Only update the user's name in the database if provided
            if user_name:
                try:
                    leaderboard_db.update_user_stat(
                        user_id=user_id,
                        user_name=user_name,
                        game_mode="map",  # Use any mode, won't be counted
                        is_correct=False  # Won't be counted for this mode
                    )
                except Exception as e:
                    logger.error(f"Error updating user name in database: {e}")
            return

        # Initialize user stats if this is their first game
        if user_id not in self.user_stats:
            self.user_stats[user_id] = {}

        # Initialize mode stats if this is their first time playing this mode
        if game_mode not in self.user_stats[user_id]:
            self.user_stats[user_id][game_mode] = {"total": 0, "correct": 0}

        # Update in-memory stats
        self.user_stats[user_id][game_mode]["total"] += 1
        if is_correct:
            self.user_stats[user_id][game_mode]["correct"] += 1

        # Use provided user name or default
        display_name = user_name if user_name else f"User {user_id}"

        # Update database stats
        try:
            leaderboard_db.update_user_stat(
                user_id=user_id,
                user_name=display_name,
                game_mode=game_mode,
                is_correct=is_correct
            )
        except Exception as e:
            logger.error(f"Error updating stats in database: {e}")

        logger.info(
            f"Updated user stats for {user_id} in {game_mode} mode: {self.user_stats[user_id][game_mode]}"
        )

    def _load_stats_from_db(self) -> None:
        """Load user stats from the database into memory."""
        try:
            # Get all user stats from the database
            all_stats = leaderboard_db.get_all_user_stats()

            # Format for in-memory usage
            for user_id, user_data in all_stats.items():
                self.user_stats[user_id] = user_data.get("modes", {})

            logger.info(f"Loaded stats for {len(self.user_stats)} users from database")
        except Exception as e:
            logger.error(f"Error loading stats from database: {e}")

    async def _send_game_navigation(
            self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send buttons for navigating between game modes"""
        # Create buttons for different game modes
        keyboard = [[
            InlineKeyboardButton("🗺️ Map Mode", callback_data="play_map"),
            InlineKeyboardButton("🏳️ Flag Mode", callback_data="play_flag")
        ],
                    [
                        InlineKeyboardButton("🏙️ Capital Mode",
                                             callback_data="play_capital"),
                        InlineKeyboardButton("📊 Leaderboard",
                                             callback_data="show_leaderboard")
                    ]]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=f"Choose a game mode:\nBot Version: {self.bot_version}",
                                       reply_markup=reply_markup)

    async def help_command(self, update: Update,
                           context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show help message for the game"""
        help_text = f"""
        🌍 *Country Guessing Game Options* 🌍

        */g help* - Show this help message
        */g* or */g map* - Launch game in map mode (guess from a map)
        */g flag* - Launch game in flag mode (guess from a flag)
        */g capital* - Launch game in capital mode (guess from a capital city)
        */g cap* - Launch game in capital guessing mode (see a map, guess the capital)
        */g lb* - Show the leaderboard for all game modes

        To play: simply tap on the correct option from the choices provided.
        You have 30 seconds to answer each question.

        Bot Version: {self.bot_version}
        """

        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=help_text,
                                       parse_mode="Markdown")

    async def show_leaderboard(self, update: Update,
                               context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show the leaderboard for all players using persistent storage."""
        try:
            # Get the leaderboard data from the database
            leaderboard_data = leaderboard_db.get_leaderboard(limit=10)

            # Log the retrieved data for debugging
            logger.info(f"Retrieved leaderboard data: {leaderboard_data}")

            # If we have no data, show an appropriate message
            if not leaderboard_data:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"No games have been played yet. Be the first to play!\n\nBot Version: {self.bot_version}")
                return

            # Build leaderboard message
            message = f"🏆 *Country Game Leaderboard* 🏆\n\n"

            # Add top 10 users - using dictionary access instead of tuple unpacking for flexibility
            for i, entry in enumerate(leaderboard_data, 1):
                # Extract data from the entry dictionary
                user_id = entry.get('user_id')
                user_name = entry.get('name', f"User {user_id}")
                accuracy = entry.get('accuracy', 0)
                correct = entry.get('correct', 0)
                total = entry.get('total', 0)
                modes = entry.get('modes', {})

                # Try to get the user's name from Telegram if available and not already provided
                display_name = user_name
                if display_name == f"User {user_id}":
                    try:
                        user = await context.bot.get_chat(user_id)
                        display_name = user.first_name

                        # Update the name in the database for future use
                        self._update_user_stats(
                            user_id=user_id,
                            user_name=display_name,
                            game_mode="update_only",
                            is_correct=False
                        )
                    except Exception:
                        # Use default if we can't get the name
                        pass

                message += f"{i}. *{display_name}*: {accuracy:.1f}% ({correct}/{total})\n"

                # Add breakdown by mode
                for mode, mode_stats in modes.items():
                    # Mode display mapping with backward compatibility
                    mode_display_map = {
                        "map": "🗺️ Map",
                        "flag": "🏳️ Flag",
                        "capital": "🏙️ Capital",
                        "cap": "🏙️ Capital"
                    }

                    # Get display name or use raw mode name with capitalization
                    mode_display = mode_display_map.get(mode, mode.capitalize())
                    mode_accuracy = mode_stats.get("accuracy", 0)
                    mode_correct = mode_stats.get("correct", 0)
                    mode_total = mode_stats.get("total", 0)

                    message += f"  {mode_display}: {mode_accuracy:.1f}% ({mode_correct}/{mode_total})\n"

                message += "\n"

            # Add bot version at the end of the leaderboard
            message += f"Bot Version: {self.bot_version}"

            # Send the leaderboard
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=message,
                parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Error showing leaderboard: {e}")
            logger.error(f"Error details: {traceback.format_exc()}")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Sorry, there was an error displaying the leaderboard.\n\nBot Version: {self.bot_version}"
            )