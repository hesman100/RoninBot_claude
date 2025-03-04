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
        # Load ALL countries from the database
        self.all_countries = self.load_all_country_names()
        logger.info(f"Loaded {len(self.all_countries)} country names for selection")

        # Store detailed country data (will be loaded on demand)
        self.countries_data = {}

        # Store active games by user_id
        self.active_games = {}
        # Game stats by user_id
        self.user_stats = {}
        # Timer tasks for active games
        self.timer_tasks = {}
        self.current_game_mode = None  # Added to track the current game mode

    def load_all_country_names(self) -> List[str]:
        """Load the names of all 194 countries from the database or fallback"""
        try:
            # Try to load country names from the database
            logger.info("Loading all country names from database")

            db_path = "country_game/database/countries.db"
            if not os.path.exists(db_path):
                logger.error(f"Database file not found at: {db_path}")
                logger.info("Using fallback country list instead")
                # Use all countries from the fallback list
                fallback_countries = self._get_fallback_countries()
                country_names = [country["name"] for country in fallback_countries]
                logger.info(f"Loaded {len(country_names)} country names from fallback list")
                return country_names

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Check if the table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='countries'")
            if not cursor.fetchone():
                logger.error("Countries table does not exist in database")
                conn.close()
                # Use all countries from the fallback list
                fallback_countries = self._get_fallback_countries()
                country_names = [country["name"] for country in fallback_countries]
                logger.info(f"Loaded {len(country_names)} country names from fallback list")
                return country_names

            # Get all country names
            cursor.execute("SELECT name FROM countries")
            country_names = [row[0] for row in cursor.fetchall()]
            conn.close()

            logger.info(f"Loaded {len(country_names)} country names from database")

            # If the database had no countries, use the fallback list
            if not country_names:
                logger.warning("No country names found in database, using fallback")
                fallback_countries = self._get_fallback_countries()
                country_names = [country["name"] for country in fallback_countries]
                logger.info(f"Loaded {len(country_names)} country names from fallback list")

            # Add the country names from our fallback list to ensure the game works
            if len(country_names) < 30:
                logger.warning(f"Only {len(country_names)} countries found in database, adding fallback countries")
                fallback_countries = self._get_fallback_countries()
                fallback_names = [country["name"] for country in fallback_countries]

                # Add any fallback countries not already in the list
                for name in fallback_names:
                    if name not in country_names:
                        country_names.append(name)

                logger.info(f"Added fallback countries, now have {len(country_names)} total countries")

            return country_names

        except Exception as e:
            logger.error(f"Error loading country names: {e}")
            # Fallback to the hardcoded list
            fallback_countries = self._get_fallback_countries()
            country_names = [country["name"] for country in fallback_countries]
            logger.info(f"Loaded {len(country_names)} country names from fallback list after error")
            return country_names

    def load_country_details(self, country_name: str) -> Dict:
        """Load detailed information for a specific country"""
        # Check if we've already loaded this country
        if country_name in self.countries_data:
            return self.countries_data[country_name]

        try:
            logger.info(f"Loading details for country: {country_name}")

            db_path = "country_game/database/countries.db"
            if not os.path.exists(db_path):
                logger.error(f"Database file not found at: {db_path}")
                # Try to find country in fallback data
                for country in self._get_fallback_countries():
                    if country["name"] == country_name:
                        self.countries_data[country_name] = country
                        return country
                return None

            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get country details
            cursor.execute("SELECT * FROM countries WHERE name = ?", (country_name,))
            row = cursor.fetchone()

            if not row:
                logger.warning(f"Country {country_name} not found in database")
                conn.close()
                # Try to find country in fallback data
                for country in self._get_fallback_countries():
                    if country["name"] == country_name:
                        self.countries_data[country_name] = country
                        return country
                return None

            # Create country object
            country = {
                "name": row["name"],
                "capital": row["capital"],
                "neighbors": [],
                "region": row.get("region", "Unknown"),
                "subregion": row.get("subregion", ""),
                "population": row.get("population", 0),
                "area": row.get("area", 0)
            }

            # Get neighbors if available
            try:
                cursor.execute("SELECT neighbor_name FROM neighbors WHERE country_name = ?", (country_name,))
                neighbor_rows = cursor.fetchall()
                for neighbor_row in neighbor_rows:
                    country["neighbors"].append(neighbor_row["neighbor_name"])
            except Exception as e:
                logger.error(f"Error fetching neighbors for {country_name}: {e}")
                # Continue with empty neighbors list

            conn.close()

            # Cache the country data
            self.countries_data[country_name] = country
            return country

        except Exception as e:
            logger.error(f"Error loading country details for {country_name}: {e}")
            # Try to find country in fallback data
            for country in self._get_fallback_countries():
                if country["name"] == country_name:
                    self.countries_data[country_name] = country
                    return country
            return None

    def _cancel_timer(self, user_id: int) -> None:
        """Cancel any active timer for a user"""
        if user_id in self.timer_tasks:
            task = self.timer_tasks.pop(user_id)
            if not task.done() and not task.cancelled():
                task.cancel()
                logger.info(f"Cancelled timer for user {user_id}")

    async def _game_timeout_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int) -> None:
        """Handle game timeout"""
        try:
            await asyncio.sleep(GAME_TIMEOUT)

            # Check if the game is still active
            if user_id not in self.active_games:
                return

            # Get the game data
            game = self.active_games[user_id]
            correct_country = game["country"]
            correct_country_name = correct_country["name"].replace("_", " ")

            # Build timeout message
            timeout_msg = f"⏱️ Time's up! The correct answer was *{correct_country_name}*.\n\n"

            # Add country details
            timeout_msg += f"🏳️ {correct_country_name}\n"
            timeout_msg += f"📊 Quick Facts:\n"
            timeout_msg += f"🏙️ Capital: {correct_country.get('capital', 'Unknown')}\n"

            # Get region information
            region = correct_country.get("region", "Unknown")
            subregion = correct_country.get("subregion", "")
            timeout_msg += f"🌍 Region: {region}"
            if subregion:
                timeout_msg += f" ({subregion})"
            timeout_msg += "\n"

            # Get population and area information
            population = correct_country.get("population", 0)
            area = correct_country.get("area", 0)
            timeout_msg += f"👥 Population: {self._format_population(population)}\n"
            timeout_msg += f"📏 Area: {self._format_area(area)}"

            # Send timeout message
            chat_id = update.effective_chat.id

            # Get message ID and mode
            message_id = game.get("message_id")
            current_mode = game.get("mode", "map")

            # Try to edit the existing message with the timeout information
            try:
                if current_mode in ["map", "flag", "cap"]:
                    await context.bot.edit_message_caption(
                        chat_id=chat_id,
                        message_id=message_id,
                        caption=timeout_msg,
                        parse_mode="Markdown"
                    )
                else:  # Capital mode
                    await context.bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=message_id,
                        text=timeout_msg,
                        parse_mode="Markdown"
                    )
            except Exception as e:
                logger.error(f"Error editing timeout message: {e}")
                # Fallback to sending a new message
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=timeout_msg,
                    parse_mode="Markdown"
                )

            # Update stats
            self._update_user_stats(user_id, False)

            # Remove the active game
            del self.active_games[user_id]

            # Send navigation buttons for next game
            await self._send_game_navigation(update, context)

        except asyncio.CancelledError:
            logger.info(f"Timer for user {user_id} was cancelled")
        except Exception as e:
            logger.error(f"Error in game timeout callback: {e}")

    def _get_random_country(self, game_mode: str = "map") -> Dict:
        """
        Get a random country with assets for the specified game mode

        Flow:
        1. Randomly select from the full list of countries
        2. Load detailed information for the selected country
        3. Check if the required assets exist for the game mode
        4. If assets exist, use this country; otherwise, try another random country
        """
        logger.info(f"Getting random country for game mode: {game_mode}")

        # Get all country names for selection
        all_country_names = list(self.all_countries)
        logger.info(f"Total number of countries available: {len(all_country_names)}")

        # Shuffle the full list of country names
        random.shuffle(all_country_names)

        # Create a list to track rejected countries for debugging
        rejected_countries = []

        # Try up to 30 random countries before giving up
        max_attempts = min(30, len(all_country_names))

        for i in range(max_attempts):
            # Skip if we've run out of countries
            if not all_country_names:
                logger.warning("Ran out of countries to try")
                break

            # Get a random country name
            country_name = all_country_names.pop(0)
            logger.info(f"Attempt {i+1}/{max_attempts}: Selected country: {country_name}")

            # Load detailed information for this country
            country_data = self.load_country_details(country_name)

            if not country_data:
                logger.warning(f"Could not load details for {country_name}, skipping")
                rejected_countries.append(f"{country_name} (no details)")
                continue

            # Check if required assets exist for this game mode
            is_suitable = True
            reject_reason = ""

            if game_mode in ["map", "cap"]:
                # Need map image
                map_path = os.path.join("country_game", "images", "wiki_all_map_400pi", f"{country_name}_locator_map.png")
                if not os.path.exists(map_path):
                    is_suitable = False
                    reject_reason = "no map image"
                    logger.info(f"Map not found for {country_name}")

            if game_mode == "flag":
                # Need flag image
                flag_path = os.path.join("country_game", "images", "wiki_flag", f"{country_name}_flag.png")
                if not os.path.exists(flag_path):
                    is_suitable = False
                    reject_reason = "no flag image"
                    logger.info(f"Flag not found for {country_name}")

            if game_mode in ["capital", "cap"]:
                # Need capital information
                if not country_data.get("capital") or country_data["capital"] == "Unknown":
                    is_suitable = False
                    reject_reason = "no capital info"
                    logger.info(f"Capital not known for {country_name}")

            # If this country has all required assets, use it
            if is_suitable:
                logger.info(f"Found suitable country: {country_name} for {game_mode} mode")
                return country_data
            else:
                # Track rejected countries for debugging
                rejected_countries.append(f"{country_name} ({reject_reason})")

        # Log the rejected countries to help debug issues
        if rejected_countries:
            logger.warning(f"Rejected {len(rejected_countries)} countries: {', '.join(rejected_countries)}")

        # If we couldn't find a suitable country, use a fallback with known assets
        logger.warning(f"Could not find suitable country for {game_mode} mode, using fallback")

        # Define a list of countries we know have the required assets
        if game_mode == "map":
            fallback_options = ["United_States", "France", "Germany", "Japan", "Brazil", "Canada", "Italy", "Spain"]
        elif game_mode == "flag":
            fallback_options = ["United_States", "United_Kingdom", "France", "Germany", "Japan", "Canada", "Italy", "Brazil"]
        else:  # capital or cap mode
            fallback_options = ["United_States", "United_Kingdom", "France", "Germany", "Japan", "Australia", "Brazil", "Canada"]

        # Shuffle the fallback options
        random.shuffle(fallback_options)

        # Try each fallback option
        for country_name in fallback_options:
            country_data = self.load_country_details(country_name)
            if country_data:
                logger.info(f"Using fallback country: {country_name}")
                return country_data

        # If all else fails, use the first fallback country from our predefined list
        fallback_countries = self._get_fallback_countries()
        logger.warning("Using first fallback country as last resort")
        return fallback_countries[0]

    async def start_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE, game_mode: str = "map") -> None:
        """Start a new country guessing game"""
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        logger.info(f"Starting new game for user {user_id} in chat {chat_id} with mode {game_mode}")

        # Cancel any existing timer for this user
        self._cancel_timer(user_id)

        # Get a random country based on game mode
        country = self._get_random_country(game_mode)

        if not country:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"Sorry, I couldn't find any countries for the {game_mode} game mode. Please try a different mode."
            )
            return

        # Set up a new game for this user with start_time
        self.active_games[user_id] = {
            "country": country,
            "attempts": 0,
            "mode": game_mode,
            "start_time": time.time()  # Add start_time to track elapsed time
        }
        logger.info(f"Created new game for user {user_id} with country {country['name']}")

        # Send the appropriate challenge based on game mode
        if game_mode == "map":
            await self._send_map_challenge(update, context, country)
        elif game_mode == "flag":
            await self._send_flag_challenge(update, context, country)
        elif game_mode == "capital":
            await self._send_capital_challenge(update, context, country)
        elif game_mode == "cap":
            await self._send_capital_guessing_challenge(update, context, country)
        else:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"Unknown game mode: {game_mode}. Try /g help for available options."
            )
            # Clean up the game if we couldn't start it
            if user_id in self.active_games:
                del self.active_games[user_id]

        # Set a timer for this game that actually waits GAME_TIMEOUT seconds
        self.timer_tasks[user_id] = asyncio.create_task(
            self._game_timeout_callback(update, context, user_id)
        )

    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handles callback queries from inline keyboards."""
        query = update.callback_query
        user_id = update.effective_user.id

        # Add detailed logging to help debug navigation buttons
        logger.info(f"Received callback query with data: {query.data} from user {user_id}")

        # Cancel any timer when user interacts
        self._cancel_timer(user_id)

        await query.answer()  # Acknowledge the button press to Telegram

        # Check if it's a game guess
        if query.data.startswith("guess_"):
            logger.info(f"Processing guess: {query.data}")
            # Check if this is a capital guessing game
            if user_id in self.active_games and self.active_games[user_id].get("mode") == "cap":
                # For cap mode, format is "guess_CountryName_CapitalName" 
                parts = query.data.split("_", 2)
                if len(parts) == 3:
                    country_name = parts[1]
                    guessed_capital = parts[2]
                    await self._handle_capital_guess(update, context, country_name, guessed_capital)
                else:
                    logger.error(f"Invalid guess data format: {query.data}")
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="Sorry, there was an error processing your answer. Please try again."
                    )
                    # Send game navigation buttons
                    await self._send_game_navigation(update, context)
            else:
                # For other modes, handle as normal country guess
                await self._handle_guess(update, context, query.data)
        # Check if it's a navigation button
        elif query.data.startswith("play_"):
            game_mode = query.data.split("_")[1]
            logger.info(f"Starting new game with mode: {game_mode}")
            if game_mode == "help":
                await self.help_command(update, context)
            else:
                # Always allow starting a new game regardless of active_games state
                await self.start_game(update, context, game_mode)
        else:
            logger.warning(f"Unrecognized callback data: {query.data}")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Sorry, I didn't understand that command. Try /g help for options."
            )

    async def _send_map_challenge(self, update: Update, context: ContextTypes.DEFAULT_TYPE, country: Dict) -> None:
        """Send a map challenge to the user with multiple-choice options"""
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id

        logger.info(f"Sending map challenge for country: {country['name']}")

        # Generate answer options (1 correct + 9 others)
        options = self.get_answer_options(country)

        # Create inline keyboard with answer options
        keyboard = []
        row = []
        for i, option in enumerate(options):
            display_name = option["name"].replace("_", " ")
            callback_data = f"guess_{option['name']}"
            logger.info(f"Creating button for {display_name} with callback_data: {callback_data}")
            row.append(InlineKeyboardButton(display_name, callback_data=callback_data))

            # Create a new row after every 2 buttons
            if (i + 1) % 2 == 0 or (i + 1) == len(options):
                keyboard.append(row)
                row = []

        reply_markup = InlineKeyboardMarkup(keyboard)
        logger.info(f"Created keyboard with {len(keyboard)} rows for map challenge")

        # Get the map path
        map_path = os.path.join("country_game", "images", "wiki_all_map_400pi", f"{country['name']}_locator_map.png")

        # Check if map exists
        if not os.path.exists(map_path):
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"Sorry, I couldn't find a map for {country['name'].replace('_', ' ')}. Try another game!"
            )
            # Clean up the game
            if user_id in self.active_games:
                del self.active_games[user_id]
            # Send game navigation
            await self._send_game_navigation(update, context)
            return

        # Send the map image with answer options
        try:
            with open(map_path, 'rb') as photo:
                message = await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=photo,
                    caption="🌍 Which country is shown on this map?",
                    reply_markup=reply_markup
                )

                # Store the message ID for later reference
                if user_id in self.active_games:
                    self.active_games[user_id]["message_id"] = message.message_id

                logger.info(f"Successfully sent map challenge with message_id: {message.message_id}")
        except Exception as e:
            logger.error(f"Error sending map challenge: {e}")
            await context.bot.send_message(
                chat_id=chat_id,
                text="Sorry, there was an error starting the game. Please try again."
            )
            # Clean up the game
            if user_id in self.active_games:
                del self.active_games[user_id]
            # Send game navigation
            await self._send_game_navigation(update, context)
            return

    async def _send_flag_challenge(self, update: Update, context: ContextTypes.DEFAULT_TYPE, country: Dict) -> None:
        """Send a flag challenge to the user with multiple-choice options"""
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id

        logger.info(f"Sending flag challenge for country: {country['name']}")

        # Generate answer options (1 correct + 9 others)
        options = self.get_answer_options(country)

        # Create inline keyboard with answer options
        keyboard = []
        row = []
        for i, option in enumerate(options):
            display_name = option["name"].replace("_", " ")
            callback_data = f"guess_{option['name']}"
            logger.info(f"Creating button for {display_name} with callback_data: {callback_data}")
            row.append(InlineKeyboardButton(display_name, callback_data=callback_data))

            # Create a new row after every 2 buttons
            if (i + 1) % 2 == 0 or (i + 1) == len(options):
                keyboard.append(row)
                row = []

        reply_markup = InlineKeyboardMarkup(keyboard)
        logger.info(f"Created keyboard with {len(keyboard)} rows for flag challenge")

        # Get the flag path
        flag_path = os.path.join("country_game", "images", "wiki_flag", f"{country['name']}_flag.png")

        # Check if flag exists
        if not os.path.exists(flag_path):
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"Sorry, I couldn't find a flag for {country['name'].replace('_', ' ')}. Try another game!"
            )
            # Clean up the game
            if user_id in self.active_games:
                del self.active_games[user_id]
            # Send game navigation
            await self._send_game_navigation(update, context)
            return

        # Send the flag image with answer options
        try:
            with open(flag_path, 'rb') as photo:
                message = await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=photo,
                    caption="🏳️ Which country does this flag belong to?",
                    reply_markup=reply_markup
                )

                # Store the message ID for later reference
                if user_id in self.active_games:
                    self.active_games[user_id]["message_id"] = message.message_id

                logger.info(f"Successfully sent flag challenge with message_id: {message.message_id}")
        except Exception as e:
            logger.error(f"Error sending flag challenge: {e}")
            await context.bot.send_message(
                chat_id=chat_id,
                text="Sorry, there was an error starting the game. Please try again."
            )
            # Clean up the game
            if user_id in self.active_games:
                del self.active_games[user_id]
            # Send game navigation
            await self._send_game_navigation(update, context)
            return

    async def _send_capital_challenge(self, update: Update, context: ContextTypes.DEFAULT_TYPE, country: Dict) -> None:
        """Send a capital challenge to the user with multiple-choice options"""
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id

        logger.info(f"Sending capital challenge for country: {country['name']}")

        # Make sure the country has a known capital
        if not country.get("capital") or country["capital"] == "Unknown":
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"Sorry, I don't know the capital of {country['name'].replace('_', ' ')}. Try another game!"
            )
            # Clean up the game
            if user_id in self.active_games:
                del self.active_games[user_id]
            # Send game navigation
            await self._send_game_navigation(update, context)
            return

        # Generate answer options (1 correct + 9 others)
        options = self.get_answer_options(country)

        # Create inline keyboard with answer options
        keyboard = []
        row = []
        for i, option in enumerate(options):
            display_name = option["name"].replace("_", " ")
            callback_data = f"guess_{option['name']}"
            logger.info(f"Creating button for {display_name} with callback_data: {callback_data}")
            row.append(InlineKeyboardButton(display_name, callback_data=callback_data))

            # Create a new row after every 2 buttons
            if (i + 1) % 2 == 0 or (i + 1) == len(options):
                keyboard.append(row)
                row = []

        reply_markup = InlineKeyboardMarkup(keyboard)
        logger.info(f"Created keyboard with {len(keyboard)} rows for capital challenge")

        # Send the capital question with answer options
        try:
            message = await context.bot.send_message(
                chat_id=chat_id,
                text=f"🏙️ Which country has *{country['capital']}* as its capital?",
                parse_mode="Markdown",
                reply_markup=reply_markup
            )

            # Store the message ID for later reference
            if user_id in self.active_games:
                self.active_games[user_id]["message_id"] = message.message_id

            logger.info(f"Successfully sent capital challenge with message_id: {message.message_id}")
        except Exception as e:
            logger.error(f"Error sending capital challenge: {e}")
            await context.bot.send_message(
                chat_id=chat_id,
                text="Sorry, there was an error starting the game. Please try again."
            )
            # Clean up the game
            if user_id in self.active_games:
                del self.active_games[user_id]
            # Send game navigation
            await self._send_game_navigation(update, context)
            return

    async def _send_capital_guessing_challenge(self, update: Update, context: ContextTypes.DEFAULT_TYPE, country: Dict) -> None:
        """Send a challenge where user sees a map and needs to identify the capital city"""
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id

        logger.info(f"Sending capital guessing challenge for country: {country['name']}")

        # Get the map path for this country
        map_path = os.path.join("country_game", "images", "wiki_all_map_400pi", f"{country['name']}_locator_map.png")

        # Check if the map exists
        if not os.path.exists(map_path):
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"Sorry, I couldn't find the map for this country. Try another game!"
            )
            # Clean up the game
            if user_id in self.active_games:
                del self.active_games[user_id]
            # Send game navigation
            await self._send_game_navigation(update, context)
            return

        # Get the correct capital (answer)
        correct_capital = country.get('capital', 'Unknown')
        if correct_capital == 'Unknown':
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"Sorry, I don't know the capital of this country. Try another game!"
            )
            # Clean up the game
            if user_id in self.active_games:
                del self.active_games[user_id]
            # Send game navigation
            await self._send_game_navigation(update, context)
            return

        # Collect capital options (1 correct + 9 from neighbors or random countries)
        capital_options = [correct_capital]

        # Get neighboring countries' capitals
        neighbor_capitals = []
        for neighbor_name in country.get('neighbors', []):
            # Find the neighbor in our countries list
            for c in self.countries_data.values(): #use loaded data
                if c['name'] == neighbor_name and c.get('capital') != 'Unknown':
                    neighbor_capitals.append(c['capital'])
                    break

        # Shuffle the neighbor capitals and add them to options
        random.shuffle(neighbor_capitals)
        capital_options.extend(neighbor_capitals[:9])  # Take up to 9 neighbor capitals

        # If we don't have 10 options yet, add random capitals from other countries
        if len(capital_options) < 10:
            # Get random countries with known capitals
            other_countries = [c for c in self.countries_data.values() #use loaded data
                            if c['name'] != country['name'] 
                            and c.get('capital') != 'Unknown'
                            and c['capital'] not in capital_options]

            # Shuffle them and take as many as needed
            random.shuffle(other_countries)
            needed = 10 - len(capital_options)
            for i in range(min(needed, len(other_countries))):
                capital_options.append(other_countries[i]['capital'])

        # Ensure we have no more than 10 options
        capital_options = capital_options[:10]

        # Shuffle the options
        random.shuffle(capital_options)

        # Add detailed logging
        logger.info(f"Generated {len(capital_options)} capital options")
        logger.info(f"Capital options: {capital_options}")
        loggerinfo(f"Correct capital: {correct_capital}")

        # Create keyboard with capital options
        keyboard = []
        row = []

        for i, capital in enumerate(capital_options):
            # Create callback data for this option
            callback_data = f"guess_{country['name']}_{capital}"
            logger.info(f"Creating button with callback_data: {callback_data}")

            # Add button to current row
            row.append(InlineKeyboardButton(capital, callback_data=callback_data))

            # Start a new row after 2 buttons
            if (i + 1) % 2 == 0 or (i + 1) == len(capital_options):
                keyboard.append(row)
                row = []

        reply_markup = InlineKeyboardMarkup(keyboard)
        logger.info(f"Created keyboard with {len(keyboard)} rows")

        # Send the map image with capital options
        try:
            logger.info(f"Attempting to send photo from path: {map_path}")
            # Check if the map file exists and is readable
            if os.path.exists(map_path) and os.access(map_path, os.R_OK):
                logger.info(f"Map file exists and is readable")
                with open(map_path, 'rb') as photo_file:
                    # Try to read some bytes to confirm file is valid
                    photo_bytes = photo_file.read(1024)
                    if not photo_bytes:
                        logger.error(f"Map file is empty or could not be read")
                        raise ValueError("Map fileis empty or could not be read")

                    # Seek back to beginning of file
                    photo_file.seek(0)

                    message = await context.bot.send_photo(
                        chat_id=chat_id,
                        photo=photo_file,
                        caption=f"🌍 *What is the capital city of this country?*\n\nChoose from the options below:",
                        parse_mode="Markdown",
                        reply_markup=reply_markup
                    )

                    # Store the message ID for later reference (e.g., for editing)
                    if user_id in self.active_games:
                        self.active_games[user_id]["message_id"] = message.message_id

                    logger.info(f"Successfully sent photo and received message_id: {message.message_id}")
            else:
                # File doesn't exist or isn't readable
                logger.error(f"Map file doesn't exist or isn't readable: {map_path}")
                raise FileNotFoundError(f"Map file doesn't exist or isn't readable: {map_path}")

        except Exception as e:
            logger.error(f"Error sending capital guessing challenge: {str(e)}")
            # Try an alternative approach
            try:
                logger.info(f"Trying alternative approach with InputFile")
                with open(map_path, 'rb') as photo_file:
                    message = await context.bot.send_photo(
                        chat_id=chat_id,
                        photo=photo_file.read(),
                        caption=f"🌍 *What is the capital city of this country?*\n\nChoose from the options below:",
                        parse_mode="Markdown",
                        reply_markup=reply_markup
                    )

                    # Store the message ID for later reference
                    if user_id in self.active_games:
                        self.active_games[user_id]["message_id"] = message.message_id

                    logger.info(f"Successfullysent photo using alternative approach")
            except Exception as e2:
                logger.error(f"Alternative approach also failed: {str(e2)}")
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="Sorry, there was an error starting the game. Please try again."
                )
                # Clean up the game
                if user_id in self.active_games:
                    del self.active_games[user_id]
                # Send game navigation
                await self._send_game_navigation(update, context)
                return

    async def _handle_guess(self, update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str) -> None:
        """Handle a guess from the inline keyboard"""
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id

        # Parse the callback data - format is "guess_CountryName"
        parts = callback_data.split("_", 1)
        if len(parts) != 2:
            logger.error(f"Invalid callback data format: {callback_data}")
            return

        guessed_country_name = parts[1]
        logger.info(f"User {user_id} guessed {guessed_country_name}")

        # Check if user has an active game
        if user_id not in self.active_games:
            logger.warning(f"No active game found for user {user_id}")
            await context.bot.send_message(
                chat_id=chat_id,
                text="No active game found. Start a new game with /g"
            )
            return

        # Get the game data
        game = self.active_games[user_id]
        correct_country = game["country"]

        # Check if the guess is correct
        is_correct = (guessed_country_name == correct_country["name"])

        # Format country names for display (replace underscores with spaces)
        display_guessed = guessed_country_name.replace("_", " ")
        display_correct = correct_country["name"].replace("_", " ")

        # Calculate elapsed time
        elapsed_time = round(time.time() - game["start_time"], 1)

        # Prepare result message
        if is_correct:
            result_message = f"✅ *Correct!* Well done! (in {elapsed_time}s)\n\n"
            result_message += f"🏳️ *{display_correct}*\n"
            result_message += f"🏙️ Capital: *{correct_country.get('capital', 'Unknown')}*\n"

            # Get region information
            region = correct_country.get("region", "Unknown")
            subregion = correct_country.get("subregion", "")
            result_message += f"🌍 Region: {region}"
            if subregion:
                result_message += f" ({subregion})"
            result_message += "\n"

            # Get population and area information
            population = correct_country.get("population", 0)
            area = correct_country.get("area", 0)
            result_message += f"👥 Population: {self._format_population(population)}\n"
            result_message += f"📏 Area: {self._format_area(area)}"
        else:
            # For wrong answer, just indicate it's wrong
            result_message = f"❌ That's not correct. You selected *{display_guessed}*."

            # If this was the last attempt, show the correct answer
            game["attempts"] = game.get("attempts", 0) + 1
            if game["attempts"] >= 3:
                result_message += f"\nThe correct answer was *{display_correct}*."

                # Add some details about the correct country
                result_message += f"\n\n🏳️ *{display_correct}*\n"
                result_message += f"🏙️ Capital: *{correct_country.get('capital', 'Unknown')}*\n"

                # Get region information
                region = correct_country.get("region", "Unknown")
                result_message += f"🌍 Region: {region}\n"

                # Clean up the game after max attempts
                del self.active_games[user_id]

                # Cancel the timer if it exists
                self._cancel_timer(user_id)

                # Try to update the original message, then send navigation buttons
                try:
                    message_id = game.get("message_id")
                    if message_id:
                        current_mode = game.get("mode", "map")
                        if current_mode in ["map", "flag"]:
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
                        # If we don't have the message ID, send a new message
                        await context.bot.send_message(
                            chat_id=chat_id,
                            text=result_message,
                            parse_mode="Markdown"
                        )
                except Exception as e:
                    logger.error(f"Error updating message with result: {e}")
                    # Fallback to sending a new message
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=result_message,
                        parse_mode="Markdown"
                    )

                # Send game navigation buttons after showing the correct answer
                await self._send_game_navigation(update, context)
                return

        # Update user stats
        self._update_user_stats(user_id, is_correct)

        # If the answer was correct, end the game and show details
        if is_correct:
            # Clean up the game
            del self.active_games[user_id]

            # Cancel the timer if it exists
            self._cancel_timer(user_id)

            # Try to update the original message, then send navigation buttons
            try:
                message_id = game.get("message_id")
                if message_id:
                    current_mode = game.get("mode", "map")
                    if current_mode in ["map", "flag"]:
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
                    # If we don't have the message ID, send a new message
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=result_message,
                        parse_mode="Markdown"
                    )
            except Exception as e:
                logger.error(f"Error updating message with result: {e}")
                # Fallback to sending a new message
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=result_message,
                    parse_mode="Markdown"
                )

            # Send game navigation buttons after correct answer
            await self._send_game_navigation(update, context)
        else:
            # If the answer was wrong but not the last attempt, update the message with the wrong answer
            try:
                message_id = game.get("message_id")
                if message_id:
                    current_mode = game.get("mode", "map")
                    if current_mode in ["map", "flag"]:
                        await context.bot.edit_message_caption(
                            chat_id=chat_id,
                            message_id=message_id,
                            caption=f"{result_message}\n\nYou have {3 - game['attempts']} attempts remaining.",
                            parse_mode="Markdown"
                        )
                    else:
                        await context.bot.edit_message_text(
                            chat_id=chat_id,
                            message_id=message_id,
                            text=f"{result_message}\n\nYou have {3 - game['attempts']} attempts remaining.",
                            parse_mode="Markdown"
                        )
                else:
                    # If we don't have the message ID, send a new message
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=f"{result_message}\n\nYou have {3 - game['attempts']} attempts remaining.",
                        parse_mode="Markdown"
                    )
            except Exception as e:
                logger.error(f"Error updating message with result: {e}")
                # Fallback to sending a new message
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"{result_message}\n\nYou have {3 - game['attempts']} attempts remaining.",
                    parse_mode="Markdown"
                )

            # Reset the game timer since the user made a wrong guess
            self._cancel_timer(user_id)
            self.timer_tasks[user_id] = asyncio.create_task(
                self._game_timeout_callback(update, context, user_id)
            )

    async def _handle_capital_guess(self, update: Update, context: ContextTypes.DEFAULT_TYPE, country_name: str, guessed_capital: str) -> None:
        """Handle a guess for the capital city challenge"""
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id

        logger.info(f"Handling capital guess: {guessed_capital} for country: {country_name} by user: {user_id}")

        # Check if user has an active game
        if user_id not in self.active_games:
            logger.warning(f"No active game found for user: {user_id}")
            await context.bot.send_message(
                chat_id=chat_id,
                text="No active game found. Start a new game with /g cap"
            )
            return

        game = self.active_games[user_id]
        correct_country = game["country"]

        # Verify this guess is for the current game's country
        if correct_country["name"] != country_name:
            logger.warning(f"Guess for wrong country: expected {correct_country['name']}, got {country_name}")
            await context.bot.send_message(
                chat_id=chat_id,
                text="Sorry, this answer is for a different game. Please start a new game."
            )
            return

        # Get the correct capital
        correct_capital = correct_country.get("capital", "Unknown")

        # Format country name for display (replace underscores with spaces)
        display_country_name = correct_country["name"].replace("_", " ")

        # Check if guess is correct
        is_correct = (guessed_capital == correct_capital)

        # Prepare result message
        if is_correct:
            result_message = f"✅ *Correct!* {display_country_name}'s capital is indeed *{correct_capital}*.\n\n"
            result_message += f"🏳️ *{display_country_name}*\n"
            result_message += f"🏙️ Capital: *{correct_capital}*\n"

            # Get region information
            region = correct_country.get("region", "Unknown")
            subregion = correct_country.get("subregion", "")
            result_message += f"🌍 Region: {region}"
            if subregion:
                result_message += f" ({subregion})"
            result_message += "\n"

            # Get population and area information
            population = correct_country.get("population", 0)
            area = correct_country.get("area", 0)
            result_message += f"👥 Population: {self._format_population(population)}\n"
            result_message += f"📏 Area: {self._format_area(area)}"
        else:
            result_message = f"❌ Incorrect. The capital of *{display_country_name}* is *{correct_capital}*.\n"
            result_message += f"You selected: *{guessed_capital}*"

        # Update user stats
        self._update_user_stats(user_id, is_correct)

        # Try to edit the original message to show the result
        try:
            message_id = game.get("message_id")
            if message_id:
                await context.bot.edit_message_caption(
                    chat_id=chat_id,
                    message_id=message_id,
                    caption=result_message,
                    parse_mode="Markdown"
                )
            else:
                # If we don't have the message ID, send a new message
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=result_message,
                    parse_mode="Markdown"
                )
        except Exception as e:
            logger.error(f"Error updating message with result: {e}")
            # Fallback to sending a new message
            await context.bot.send_message(
                chat_id=chat_id,
                text=result_message,
                parse_mode="Markdown"
            )

        # Clean up the game
        if user_id in self.active_games:
            del self.active_games[user_id]

        # Cancel any active timer
        self._cancel_timer(user_id)

        # Send game navigation buttons
        await self._send_game_navigation(update, context)

    def get_answer_options(self, correct_country: Dict, num_options: int = 10) -> List[Dict]:
        """
        Get a list of answer options including the correct one and some decoys

        Args:
            correct_country: The correct country answer
            num_options: Total number of options to return (default: 10)

        Returns:
            List of country dictionaries to use as options
        """
        logger.info(f"Generating answer options for country: {correct_country['name']}")

        # Start with the correct country
        options = [correct_country]
        logger.info(f"Added correct country: {correct_country['name']}")

        # Try to get some neighbors
        neighbors = correct_country.get('neighbors', [])
        logger.info(f"Found {len(neighbors)} neighbors: {neighbors}")

        # If we have neighbors, load their details and add them
        neighbor_countries = []
        for neighbor_name in neighbors:
            # Load neighbor details
            neighbor = self.load_country_details(neighbor_name)
            if neighbor:
                neighbor_countries.append(neighbor)

        # Shuffle the neighbors and add them to options (up to 5 neighbors)
        random.shuffle(neighbor_countries)
        for neighbor in neighbor_countries[:5]:  # Limit to 5 neighbors max
            if len(options) < num_options:
                options.append(neighbor)
                logger.info(f"Added neighbor country: {neighbor['name']}")

        # If we still need more countries to reach num_options (10)
        if len(options) < num_options:
            logger.info(f"Need {num_options - len(options)} more countries to reach {num_options}")

            # Get all country names except those already in options
            used_country_names = {country['name'] for country in options}
            available_countries = [name for name in self.all_countries if name not in used_country_names]

            # Make sure we have enough countries to choose from
            if not available_countries:
                logger.warning("No additional countries available, using fallback")
                fallback_countries = self._get_fallback_countries()
                for country in fallback_countries:
                    if country['name'] not in used_country_names:
                        available_countries.append(country['name'])

            # Shuffle the available countries
            random.shuffle(available_countries)
            logger.info(f"Found {len(available_countries)} additional countries to choose from")

            # Add countries until we reach the desired number
            for country_name in available_countries:
                if len(options) >= num_options:
                    break

                country = self.load_country_details(country_name)
                if country:
                    options.append(country)
                    logger.info(f"Added additional country: {country_name}")

        # If we still don't have enough options, use fallback countries
        if len(options) < num_options:
            logger.warning(f"Only have {len(options)} options, using fallback countries")
            fallback_countries = self._get_fallback_countries()
            for country in fallback_countries:
                if country['name'] not in {c['name'] for c in options}:
                    if len(options) < num_options:
                        options.append(country)
                        logger.info(f"Added fallback country: {country['name']}")
                    else:
                        break

        # Ensure we don't exceed the requested number of options
        options = options[:num_options]

        # Shuffle the options to randomize the order
        random.shuffle(options)

        # Log the final options
        logger.info(f"Final options count: {len(options)}")
        logger.info(f"Option countries: {[country['name'] for country in options]}")

        # Return exactly num_options options
        return options

    async def _send_game_navigation(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Sends navigation buttons for different game modes"""
        logger.info(f"Sending game navigation buttons")
        chat_id = update.effective_chat.id

        # Create keyboard with game mode options
        keyboard = [
            [
                InlineKeyboardButton("🗺️ Play Map Game", callback_data="play_map"),
                InlineKeyboardButton("🏳️ Play Flag Game", callback_data="play_flag")
            ],
            [
                InlineKeyboardButton("🏙️ Play Capital Game", callback_data="play_cap")
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        # Send the navigation message
        await context.bot.send_message(
            chat_id=chat_id,
            text="Choose a game mode:",
            reply_markup=reply_markup
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show help message for the game"""
        from country_game.config import HELP_TEXT

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=HELP_TEXT,
            parse_mode="Markdown"
        )

        # After showing help, send game navigation buttons
        await self._send_game_navigation(update, context)

    async def handle_answer(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle text answers (currently not used, all answers use callback buttons)"""
        # This method is kept for potential future use with text-based answers
        pass

    def _update_user_stats(self, user_id: int, is_correct: bool) -> None:
        """Update user statistics"""
        if user_id not in self.user_stats:
            self.user_stats[user_id] = {
                "total": 0,
                "correct": 0
            }

        self.user_stats[user_id]["total"] += 1
        if is_correct:
            self.user_stats[user_id]["correct"] += 1

    def _format_population(self, population) -> str:
        """Format population number for display"""
        if not population:
            return "Unknown"

        try:
            pop = int(population)
            if pop >= 1_000_000_000:  # Billions
                return f"{pop / 1_000_000_000:.1f} billion"
            elif pop >= 1_000_000:  # Millions
                return f"{pop / 1_000_000:.1f} million"
            elif pop >= 1_000:  # Thousands
                return f"{pop / 1_000:.1f} thousand"
            else:
                return str(pop)
        except:
            return str(population)

    def _format_area(self, area) -> str:
        """Format area for display"""
        if not area:
            return "Unknown"

        try:
            area_val = float(area)
            return f"{area_val:,.0f} km²"
        except:
            return str(area)

    def _get_fallback_countries(self) -> List[Dict]:
        """Return a comprehensive list of countries as fallback with capitals and neighbors"""
        # This is a comprehensive list with essential country data
        countries = [
            {
                "name": "United_States",
                "capital": "Washington D.C.",
                "neighbors": ["Canada", "Mexico"],
                "region": "Americas",
                "subregion": "North America",
                "population": 331002651,
                "area": 9833517
            },
            {
                "name": "United_Kingdom",
                "capital": "London",
                "neighbors": ["Ireland"],
                "region": "Europe",
                "subregion": "Northern Europe",
                "population": 67886011,
                "area": 242900
            },
            {
                "name": "France",
                "capital": "Paris",
                "neighbors": ["Spain", "Andorra", "Monaco", "Italy", "Switzerland", "Germany", "Luxembourg", "Belgium"],
                "region": "Europe",
                "subregion": "Western Europe",
                "population": 65273511,
                "area": 551695
            },
            {
                "name": "Germany",
                "capital": "Berlin",
                "neighbors": ["Denmark", "Poland", "Czech_Republic", "Austria", "Switzerland", "France", "Luxembourg", "Belgium", "Netherlands"],
                "region": "Europe",
                "subregion": "Western Europe",
                "population": 83783942,
                "area": 357114
            },
            {
                "name": "Japan",
                "capital": "Tokyo",
                "neighbors": [],
                "region": "Asia",
                "subregion": "Eastern Asia",
                "population": 126476461,
                "area": 377975
            },
            {
                "name": "Australia",
                "capital": "Canberra",
                "neighbors": [],
                "region": "Oceania",
                "subregion": "Australia and New Zealand",
                "population": 25499884,
                "area": 7692024
            },
            {
                "name": "Brazil",
                "capital": "Brasília",
                "neighbors": ["Uruguay", "Argentina", "Paraguay", "Bolivia", "Peru", "Colombia", "Venezuela", "Guyana", "Suriname", "French_Guiana"],
                "region": "Americas",
                "subregion": "South America",
                "population": 212559417,
                "area": 8515767
            },
            {
                "name": "Canada",
                "capital": "Ottawa",
                "neighbors": ["United_States"],
                "region": "Americas",
                "subregion": "North America",
                "population": 37742154,
                "area": 9984670
            },
            {
                "name": "Mexico",
                "capital": "Mexico City",
                "neighbors": ["United_States", "Guatemala", "Belize"],
                "region": "Americas",
                "subregion": "North America",
                "population": 128932753,
                "area": 1964375
            },
            {
                "name": "China",
                "capital": "Beijing",
                "neighbors": ["Russia", "Mongolia", "North_Korea", "Vietnam", "Laos", "Myanmar", "India", "Bhutan", "Nepal", "Pakistan", "Afghanistan", "Tajikistan", "Kyrgyzstan", "Kazakhstan"],
                "region": "Asia",
                "subregion": "Eastern Asia",
                "population": 1439323776,
                "area": 9640011
            },
            # Additional countries to ensure good variety
            {
                "name": "India",
                "capital": "New Delhi",
                "neighbors": ["Pakistan", "China", "Nepal", "Bhutan", "Myanmar", "Bangladesh"],
                "region": "Asia",
                "subregion": "Southern Asia",
                "population": 1380004385,
                "area": 3287590
            },
            {
                "name": "Russia",
                "capital": "Moscow",
                "neighbors": ["Norway", "Finland", "Estonia", "Latvia", "Belarus", "Ukraine", "Georgia", "Azerbaijan", "Kazakhstan", "China", "Mongolia", "North_Korea"],
                "region": "Europe/Asia",
                "subregion": "Eastern Europe",
                "population": 145934462,
                "area": 17098246
            },
            {
                "name": "South_Africa",
                "capital": "Pretoria",
                "neighbors": ["Namibia", "Botswana", "Zimbabwe", "Mozambique", "Eswatini", "Lesotho"],
                "region": "Africa",
                "subregion": "Southern Africa",
                "population": 59308690,
                "area": 1221037
            },
            {
                "name": "Italy",
                "capital": "Rome",
                "neighbors": ["France", "Switzerland", "Austria", "Slovenia"],
                "region": "Europe",
                "subregion": "Southern Europe",
                "population": 60461826,
                "area": 301336
            },
            {
                "name": "Spain",
                "capital": "Madrid",
                "neighbors": ["Portugal", "France", "Andorra"],
                "region": "Europe",
                "subregion": "Southern Europe",
                "population": 46754778,
                "area": 505992
            },
            {
                "name": "Egypt",
                "capital": "Cairo",
                "neighbors": ["Libya", "Sudan", "Israel"],
                "region": "Africa",
                "subregion": "Northern Africa",
                "population": 102334404,
                "area": 1002450
            },
            {
                "name": "South_Korea",
                "capital": "Seoul",
                "neighbors": ["North_Korea"],
                "region": "Asia",
                "subregion": "Eastern Asia",
                "population": 51269185,
                "area": 100210
            },
            {
                "name": "Argentina",
                "capital": "Buenos Aires",
                "neighbors": ["Chile", "Bolivia", "Paraguay", "Brazil", "Uruguay"],
                "region": "Americas",
                "subregion": "South America",
                "population": 45195774,
                "area": 2780400
            },
            {
                "name": "Thailand",
                "capital": "Bangkok",
                "neighbors": ["Myanmar", "Laos", "Cambodia", "Malaysia"],
                "region": "Asia",
                "subregion": "South-Eastern Asia",
                "population": 69799978,
                "area": 513120
            },
            {
                "name": "Turkey",
                "capital": "Ankara",
                "neighbors": ["Greece", "Bulgaria", "Georgia", "Armenia", "Azerbaijan", "Iran", "Iraq", "Syria"],
                "region": "Asia/Europe",
                "subregion": "Western Asia",
                "population": 84339067,
                "area": 783562
            },
            {
                "name": "Poland",
                "capital": "Warsaw",
                "neighbors": ["Germany", "Czech_Republic", "Slovakia", "Ukraine", "Belarus", "Lithuania", "Russia"],
                "region": "Europe",
                "subregion": "Eastern Europe",
                "population": 37846611,
                "area": 312696
            },
            {
                "name": "Sweden",
                "capital": "Stockholm",
                "neighbors": ["Norway", "Finland"],
                "region": "Europe",
                "subregion": "Northern Europe",
                "population": 10099265,
                "area": 450295
            },
            {
                "name": "Ukraine",
                "capital": "Kyiv",
                "neighbors": ["Belarus", "Poland", "Slovakia", "Hungary", "Romania", "Moldova", "Russia"],
                "region": "Europe",
                "subregion": "Eastern Europe",
                "population": 43733762,
                "area": 603500
            },
            {
                "name": "Greece",
                "capital": "Athens",
                "neighbors": ["Albania", "North_Macedonia", "Bulgaria", "Turkey"],
                "region": "Europe",
                "subregion": "Southern Europe",
                "population": 10423054,
                "area": 131957
            },
            {
                "name": "Netherlands",
                "capital": "Amsterdam",
                "neighbors": ["Belgium", "Germany"],
                "region": "Europe",
                "subregion": "Western Europe",
                "population": 17134872,
                "area": 41850
            },
            {
                "name": "Switzerland",
                "capital": "Bern",
                "neighbors": ["Germany", "France", "Italy", "Austria", "Liechtenstein"],
                "region": "Europe",
                "subregion": "Western Europe",
                "population": 8654622,
                "area": 41284
            },
            {
                "name": "Indonesia",
                "capital": "Jakarta",
                "neighbors": ["Malaysia", "Papua_New_Guinea", "East_Timor"],
                "region": "Asia",
                "subregion": "South-Eastern Asia",
                "population": 273523615,
                "area": 1904569
            },
            {
                "name": "Saudi_Arabia",
                "capital": "Riyadh",
                "neighbors": ["Jordan", "Iraq", "Kuwait", "Bahrain", "Qatar", "United_Arab_Emirates", "Oman", "Yemen"],
                "region": "Asia",
                "subregion": "Western Asia",
                "population": 34813871,
                "area": 2149690
            },
            {
                "name": "New_Zealand",
                "capital": "Wellington",
                "neighbors": [],
                "region": "Oceania",
                "subregion": "Australia and New Zealand",
                "population": 4822233,
                "area": 270467
            },
            {
                "name": "Singapore",
                "capital": "Singapore",
                "neighbors": [],
                "region": "Asia",
                "subregion": "South-Eastern Asia",
                "population": 5850342,
                "area": 710
            }
        ]

        return countries

    async def _handle_guess(self, update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str) -> None:
        """Handle a guess from the inline keyboard"""
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id

        # Parse the callback data - format is "guess_CountryName"
        parts = callback_data.split("_", 1)
        if len(parts) != 2:
            logger.error(f"Invalid callback data format: {callback_data}")
            return

        guessed_country_name = parts[1]
        logger.info(f"User {user_id} guessed {guessed_country_name}")

        # Check if user has an active game
        if user_id not in self.active_games:
            logger.warning(f"No active game found for user {user_id}")
            await context.bot.send_message(
                chat_id=chat_id,
                text="No active game found. Start a new game with /g"
            )
            return

        # Get the game data
        game = self.active_games[user_id]
        correct_country = game["country"]

        # Check if the guess is correct
        is_correct = (guessed_country_name == correct_country["name"])

        # Format country names for display (replace underscores with spaces)
        display_guessed = guessed_country_name.replace("_", " ")
        display_correct = correct_country["name"].replace("_", " ")

        # Calculate elapsed time
        elapsed_time = round(time.time() - game["start_time"], 1)

        # Prepare result message
        if is_correct:
            result_message = f"✅ *Correct!* Well done! (in {elapsed_time}s)\n\n"
            result_message += f"🏳️ *{display_correct}*\n"
            result_message += f"🏙️ Capital: *{correct_country.get('capital', 'Unknown')}*\n"

            # Get region information
            region = correct_country.get("region", "Unknown")
            subregion = correct_country.get("subregion", "")
            result_message += f"🌍 Region: {region}"
            if subregion:
                result_message += f" ({subregion})"
            result_message += "\n"

            # Get population and area information
            population = correct_country.get("population", 0)
            area = correct_country.get("area", 0)
            result_message += f"👥 Population: {self._format_population(population)}\n"
            result_message += f"📏 Area: {self._format_area(area)}"
        else:
            # For wrong answer, just indicate it's wrong
            result_message = f"❌ That's not correct. You selected *{display_guessed}*."

            # If this was the last attempt, show the correct answer
            game["attempts"] = game.get("attempts", 0) + 1
            if game["attempts"] >= 3:
                result_message += f"\nThe correct answer was *{display_correct}*."

                # Add some details about the correct country
                result_message += f"\n\n🏳️ *{display_correct}*\n"
                result_message += f"🏙️ Capital: *{correct_country.get('capital', 'Unknown')}*\n"

                # Get region information
                region = correct_country.get("region", "Unknown")
                result_message += f"🌍 Region: {region}\n"

                # Clean up the game after max attempts
                del self.active_games[user_id]

                # Cancel the timer if it exists
                self._cancel_timer(user_id)

                # Try to update the original message, then send navigation buttons
                try:
                    message_id = game.get("message_id")
                    if message_id:
                        current_mode = game.get("mode", "map")
                        if current_mode in ["map", "flag"]:
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
                        # If we don't have the message ID, send a new message
                        await context.bot.send_message(
                            chat_id=chat_id,
                            text=result_message,
                            parse_mode="Markdown"
                        )
                except Exception as e:
                    logger.error(f"Error updating message with result: {e}")
                    # Fallback to sending a new message
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=result_message,
                        parse_mode="Markdown"
                    )

                # Send game navigation buttons after showing the correct answer
                await self._send_game_navigation(update, context)
                return

        # Update user stats
        self._update_user_stats(user_id, is_correct)

        # If the answer was correct, end the game and show details
        if is_correct:
            # Clean up the game
            del self.active_games[user_id]

            # Cancel the timer if it exists
            self._cancel_timer(user_id)

            # Try to update the original message, then send navigation buttons
            try:
                message_id = game.get("message_id")
                if message_id:
                    current_mode = game.get("mode", "map")
                    if current_mode in ["map", "flag"]:
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
                    # If we don't have the message ID, send a new message
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=result_message,
                        parse_mode="Markdown"
                    )
            except Exception as e:
                logger.error(f"Error updating message with result: {e}")
                # Fallback to sending a new message
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=result_message,
                    parse_mode="Markdown"
                )

            # Send game navigation buttons after correct answer
            await self._send_game_navigation(update, context)
        else:
            # If the answer was wrong but not the last attempt, update the message with the wrong answer
            try:
                message_id = game.get("message_id")
                if message_id:
                    current_mode = game.get("mode", "map")
                    if current_mode in ["map", "flag"]:
                        await context.bot.edit_message_caption(
                            chat_id=chat_id,
                            message_id=message_id,
                            caption=f"{result_message}\n\nYou have {3 - game['attempts']} attempts remaining.",
                            parse_mode="Markdown"
                        )
                    else:
                        await context.bot.edit_message_text(
                            chat_id=chat_id,
                            message_id=message_id,
                            text=f"{result_message}\n\nYou have {3 - game['attempts']} attempts remaining.",
                            parse_mode="Markdown"
                        )
                else:
                    # If we don't have the message ID, send a new message
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=f"{result_message}\n\nYou have {3 - game['attempts']} attempts remaining.",
                        parse_mode="Markdown"
                    )
            except Exception as e:
                logger.error(f"Error updating message with result: {e}")
                # Fallback to sending a new message
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"{result_message}\n\nYou have {3 - game['attempts']} attempts remaining.",
                    parse_mode="Markdown"
                )

            # Reset the game timer since the user made a wrong guess
            self._cancel_timer(user_id)
            self.timer_tasks[user_id] = asyncio.create_task(
                self._game_timeout_callback(update, context, user_id)
            )

    async def _handle_capital_guess(self, update: Update, context: ContextTypes.DEFAULT_TYPE, country_name: str, guessed_capital: str) -> None:
        """Handle a guess for the capital city challenge"""
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id

        logger.info(f"Handling capital guess: {guessed_capital} for country: {country_name} by user: {user_id}")

        # Check if user has an active game
        if user_id not in self.active_games:
            logger.warning(f"No active game found for user: {user_id}")
            await context.bot.send_message(
                chat_id=chat_id,
                text="No active game found. Start a new game with /g cap"
            )
            return

        game = self.active_games[user_id]
        correct_country = game["country"]

        # Verify this guess is for the current game's country
        if correct_country["name"] != country_name:
            logger.warning(f"Guess for wrong country: expected {correct_country['name']}, got {country_name}")
            await context.bot.send_message(
                chat_id=chat_id,
                text="Sorry, this answer is for a different game. Please start a new game."
            )
            return

        # Get the correct capital
        correct_capital = correct_country.get("capital", "Unknown")

        # Format country name for display (replace underscores with spaces)
        display_country_name = correct_country["name"].replace("_", " ")

        # Check if guess is correct
        is_correct = (guessed_capital == correct_capital)

        # Prepare result message
        if is_correct:
            result_message = f"✅ *Correct!* {display_country_name}'s capital is indeed *{correct_capital}*.\n\n"
            result_message += f"🏳️ *{display_country_name}*\n"
            result_message += f"🏙️ Capital: *{correct_capital}*\n"

            # Get region information
            region = correct_country.get("region", "Unknown")
            subregion = correct_country.get("subregion", "")
            result_message += f"🌍 Region: {region}"
            if subregion:
                result_message += f" ({subregion})"
            result_message += "\n"

            # Get population and area information
            population = correct_country.get("population", 0)
            area = correct_country.get("area", 0)
            result_message += f"👥 Population: {self._format_population(population)}\n"
            result_message += f"📏 Area: {self._format_area(area)}"
        else:
            result_message = f"❌ Incorrect. The capital of *{display_country_name}* is *{correct_capital}*.\n"
            result_message += f"You selected: *{guessed_capital}*"

        # Update user stats
        self._update_user_stats(user_id, is_correct)

        # Try to edit the original message to show the result
        try:
            message_id = game.get("message_id")
            if message_id:
                await context.bot.edit_message_caption(
                    chat_id=chat_id,
                    message_id=message_id,
                    caption=result_message,
                    parse_mode="Markdown"
                )
            else:
                # If we don't have the message ID, send a new message
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=result_message,
                    parse_mode="Markdown"
                )
        except Exception as e:
            logger.error(f"Error updating message with result: {e}")
            # Fallback to sending a new message
            await context.bot.send_message(
                chat_id=chat_id,
                text=result_message,
                parse_mode="Markdown"
            )

        # Clean up the game
        if user_id in self.active_games:
            del self.active_games[user_id]

        # Cancel any active timer
        self._cancel_timer(user_id)

        # Send game navigation buttons
        await self._send_game_navigation(update, context)

    def get_answer_options(self, correct_country: Dict, num_options: int = 10) -> List[Dict]:
        """
        Get a list of answer options including the correct one and some decoys

        Args:
            correct_country: The correct country answer
            num_options: Total number of options to return (default: 10)

        Returns:
            List of country dictionaries to use as options
        """
        logger.info(f"Generating answer options for country: {correct_country['name']}")

        # Start with the correct country
        options = [correct_country]
        logger.info(f"Added correct country: {correct_country['name']}")

        # Try to get some neighbors
        neighbors = correct_country.get('neighbors', [])
        logger.info(f"Found {len(neighbors)} neighbors: {neighbors}")

        # If we have neighbors, load their details and add them
        neighbor_countries = []
        for neighbor_name in neighbors:
            # Load neighbor details
            neighbor = self.load_country_details(neighbor_name)
            if neighbor:
                neighbor_countries.append(neighbor)

        # Shuffle the neighbors and add them to options (up to 5 neighbors)
        random.shuffle(neighbor_countries)
        for neighbor in neighbor_countries[:5]:  # Limit to 5 neighbors max
            if len(options) < num_options:
                options.append(neighbor)
                logger.info(f"Added neighbor country: {neighbor['name']}")

        # If we still need more countries to reach num_options (10)
        if len(options) < num_options:
            logger.info(f"Need {num_options - len(options)} more countries to reach {num_options}")

            # Get all country names except those already in options
            used_country_names = {country['name'] for country in options}
            available_countries = [name for name in self.all_countries if name not in used_country_names]

            # Make sure we have enough countries to choose from
            if not available_countries:
                logger.warning("No additional countries available, using fallback")
                fallback_countries = self._get_fallback_countries()
                for country in fallback_countries:
                    if country['name'] not in used_country_names:
                        available_countries.append(country['name'])

            # Shuffle the available countries
            random.shuffle(available_countries)
            logger.info(f"Found {len(available_countries)} additional countries to choose from")

            # Add countries until we reach the desired number
            for country_name in available_countries:
                if len(options) >= num_options:
                    break

                country = self.load_country_details(country_name)
                if country:
                    options.append(country)
                    logger.info(f"Added additional country: {country_name}")

        # If we still don't have enough options, use fallback countries
        if len(options) < num_options:
            logger.warning(f"Only have {len(options)} options, using fallback countries")
            fallback_countries = self._get_fallback_countries()
            for country in fallback_countries:
                if country['name'] not in {c['name'] for c in options}:
                    if len(options) < num_options:
                        options.append(country)
                        logger.info(f"Added fallback country: {country['name']}")
                    else:
                        break

        # Ensure we don't exceed the requested number of options
        options = options[:num_options]

        # Shuffle the options to randomize the order
        random.shuffle(options)

        # Log the final options
        logger.info(f"Final options count: {len(options)}")
        logger.info(f"Option countries: {[country['name'] for country in options]}")

        # Return exactly num_options options
        return options

    async def _send_game_navigation(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Sends navigation buttons for different game modes"""
        logger.info(f"Sending game navigation buttons")
        chat_id = update.effective_chat.id

        # Create keyboard with game mode options
        keyboard = [
            [
                InlineKeyboardButton("🗺️ Play Map Game", callback_data="play_map"),
                InlineKeyboardButton("🏳️ Play Flag Game", callback_data="play_flag")
            ],
            [
                InlineKeyboardButton("🏙️ Play Capital Game", callback_data="play_cap")
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        # Send the navigation message
        await context.bot.send_message(
            chat_id=chat_id,
            text="Choose a game mode:",
            reply_markup=reply_markup
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show help message for the game"""
        from country_game.config import HELP_TEXT

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=HELP_TEXT,
            parse_mode="Markdown"
        )

        # After showing help, send game navigation buttons
        await self._send_game_navigation(update, context)

    async def handle_answer(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle text answers (currently not used, all answers use callback buttons)"""
        # This method is kept for potential future use with text-based answers
        pass

    def _update_user_stats(self, user_id: int, is_correct: bool) -> None:
        """Update user statistics"""
        if user_id not in self.user_stats:
            self.user_stats[user_id] = {
                "total": 0,
                "correct": 0
            }

        self.user_stats[user_id]["total"] += 1
        if is_correct:
            self.user_stats[user_id]["correct"] += 1

    def _format_population(self, population) -> str:
        """Format population number for display"""
        if not population:
            return "Unknown"

        try:
            pop = int(population)
            if pop >= 1_000_000_000:  # Billions
                return f"{pop / 1_000_000_000:.1f} billion"
            elif pop >= 1_000_000:  # Millions
                return f"{pop / 1_000_000:.1f} million"
            elif pop >= 1_000:  # Thousands
                return f"{pop / 1_000:.1f} thousand"
            else:
                return str(pop)
        except:
            return str(population)

    def _format_area(self, area) -> str:
        """Format area for display"""
        if not area:
            return "Unknown"

        try:
            area_val = float(area)
            return f"{area_val:,.0f} km²"
        except:
            return str(area)