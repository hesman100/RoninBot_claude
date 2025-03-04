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
        self.current_game_mode = None  # Added to track the current game mode

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
            region = self._get_mock_region(correct_country["name"])
            subregion = self._get_mock_subregion(correct_country["name"])
            timeout_msg += f"🌍 Region: {region}"
            if subregion:
                timeout_msg += f" ({subregion})"
            timeout_msg += "\n"

            # Get population and area information
            population = self._get_mock_population(correct_country["name"])
            area = self._get_mock_area(correct_country["name"])
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
            "start_time": time.time()  # Add start_time to fix the KeyError
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
            for c in self.countries:
                if c['name'] == neighbor_name and c.get('capital') != 'Unknown':
                    neighbor_capitals.append(c['capital'])
                    break

        # Shuffle the neighbor capitals and add them to options
        random.shuffle(neighbor_capitals)
        capital_options.extend(neighbor_capitals[:9])  # Take up to 9 neighbor capitals

        # If we don't have 10 options yet, add random capitals from other countries
        if len(capital_options) < 10:
            # Get random countries with known capitals
            other_countries = [c for c in self.countries 
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
        logger.info(f"Correct capital: {correct_capital}")

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
                        raise ValueError("Map file is empty or could not be read")

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

                    logger.info(f"Successfully sent photo using alternative approach")
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
            region = self._get_mock_region(correct_country["name"])
            subregion = self._get_mock_subregion(correct_country["name"])
            result_message += f"🌍 Region: {region}"
            if subregion:
                result_message += f" ({subregion})"
            result_message += "\n"

            # Get population and area information
            population = self._get_mock_population(correct_country["name"])
            area = self._get_mock_area(correct_country["name"])
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
                region = self._get_mock_region(correct_country["name"])
                result_message += f"🌍 Region: {region}\n"

                # Clean up the game after max attempts
                del self.active_games[user_id]

                # Cancel the timer if it exists
                self._cancel_timer(user_id)

                # Try to update the original message, then send navigation buttons
                try:
                    message_id = game.get("message_id")
                    if message_id:
                        game_mode = game.get("mode", "map")
                        if game_mode in ["map", "flag"]:
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
                        await context.bot.send_message(
                            chat_id=chat_id,
                            text=result_message,
                            parse_mode="Markdown"
                        )
                except Exception as e:
                    logger.error(f"Error updating message: {e}")
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
                    game_mode = game.get("mode", "map")
                    if game_mode in ["map", "flag"]:
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
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=result_message,
                        parse_mode="Markdown"
                    )
            except Exception as e:
                logger.error(f"Error updating message: {e}")
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=result_message,
                    parse_mode="Markdown"
                )

            # Send game navigation buttons after correct answer
            await self._send_game_navigation(update, context)
        else:
            # For wrong answers that aren't the last attempt, let the user try again
            # Just update the original message to show it was wrong
            try:
                message_id = game.get("message_id")
                if message_id:
                    # Get the original message with its keyboard
                    if game.get("mode") in ["map", "flag"]:
                        # For map and flag modes, update the caption
                        await context.bot.edit_message_caption(
                            chat_id=chat_id,
                            message_id=message_id,
                            caption=f"{result_message}\n\nYou have {3 - game['attempts']} attempts remaining.",
                            parse_mode="Markdown",
                            reply_markup=update.callback_query.message.reply_markup
                        )
                    else:
                        # For text-based modes, update the text
                        await context.bot.edit_message_text(
                            chat_id=chat_id,
                            message_id=message_id,
                            text=f"{result_message}\n\nYou have {3 - game['attempts']} attempts remaining.",
                            parse_mode="Markdown",
                            reply_markup=update.callback_query.message.reply_markup
                        )
                else:
                    # If we don't have message_id for some reason, send a new message
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=f"{result_message}\n\nYou have {3 - game['attempts']} attempts remaining.",
                        parse_mode="Markdown"
                    )
            except Exception as e:
                logger.error(f"Error updating message for wrong answer: {e}")
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
            region = self._get_mock_region(correct_country["name"])
            subregion = self._get_mock_subregion(correct_country["name"])
            result_message += f"🌍 Region: {region}"
            if subregion:
                result_message += f" ({subregion})"
            result_message += "\n"

            # Get population and area information
            population = self._get_mock_population(correct_country["name"])
            area = self._get_mock_area(correct_country["name"])
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

    def _get_random_country(self, game_mode: str = "map") -> Dict:
        """
        Get a random country that has appropriate assets for the specified game mode
        """
        logger.info(f"Getting random country for game mode: {game_mode}")

        # Filter countries based on game mode
        suitable_countries = []

        if game_mode == "map":
            # For map mode, check if country has a map image
            for country in self.countries:
                map_path = os.path.join("country_game", "images", "wiki_all_map_400pi", f"{country['name']}_locator_map.png")
                if os.path.exists(map_path):
                    suitable_countries.append(country)

        elif game_mode == "flag":
            # For flag mode, check if country has a flag image
            for country in self.countries:
                flag_path = os.path.join("country_game", "images", "wiki_flag", f"{country['name']}_flag.png")
                if os.path.exists(flag_path):
                    suitable_countries.append(country)

        elif game_mode == "capital" or game_mode == "cap":
            # For capital modes, only include countries with known capitals
            for country in self.countries:
                if country.get("capital") and country["capital"] != "Unknown":
                    # For cap mode, also need map
                    if game_mode == "cap":
                        map_path = os.path.join("country_game", "images", "wiki_all_map_400pi", f"{country['name']}_locator_map.png")
                        if os.path.exists(map_path):
                            suitable_countries.append(country)
                    else:
                        suitable_countries.append(country)

        # Log the number of suitable countries
        logger.info(f"Found {len(suitable_countries)} suitable countries for {game_mode} mode")

        # If no suitable countries were found, return a random country
        if not suitable_countries:
            logger.warning(f"No suitable countries found for {game_mode} mode, returning random country")
            return random.choice(self.countries)

        # Pick a random country from the suitable ones
        country = random.choice(suitable_countries)
        logger.info(f"Selected random country: {country['name']}")

        return country

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
                InlineKeyboardButton("🏙️ Play Capital Game", callback_data="play_capital"),
                InlineKeyboardButton("🏛️ Guess Capital Game", callback_data="play_cap")
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        # Send the navigation message
        await context.bot.send_message(
            chat_id=chat_id,
            text="Choose a game mode to play:",
            reply_markup=reply_markup
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show help information for the game"""
        from country_game.config import HELP_TEXT
        await update.message.reply_text(HELP_TEXT, parse_mode="Markdown")

    def _update_user_stats(self, user_id: int, correct: bool) -> None:
        """Update user stats for the game"""
        if user_id not in self.user_stats:
            self.user_stats[user_id] = {"correct": 0, "total": 0}

        self.user_stats[user_id]["total"] += 1
        if correct:
            self.user_stats[user_id]["correct"] += 1

    def get_answer_options(self, correct_country: Dict, num_options: int = 10) -> List[Dict]:
        """
        Get a list of answer options including the correct one and some decoys
        Parameters:
            correct_country: The correct country dict 
            num_options: Number of total options to provide (default: 10)
        Returns:
            A list of country dicts to use as options
        """
        # Ensure the correct country is in the options
        options = [correct_country]

        # Try to include neighboring countries first
        neighbor_countries = []
        neighbors = correct_country.get('neighbors', [])
        random.shuffle(neighbors)  # Randomize neighbor order

        for neighbor_name in neighbors:
            # Find the neighbor country in our list
            for country in self.countries:
                if country['name'] == neighbor_name:
                    # Add this neighbor to our options
                    neighbor_countries.append(country)
                    break

        # Add as many neighbors as possible (up to num_options - 1)
        options.extend(neighbor_countries[:num_options - 1])

        # If we need more options, add random countries
        if len(options) < num_options:
            # Get countries that aren't already in options
            remaining_countries = [c for c in self.countries 
                                if c['name'] != correct_country['name'] 
                                and c['name'] not in [o['name'] for o in options]]

            # Shuffle them and take as many as needed
            random.shuffle(remaining_countries)
            needed = num_options - len(options)
            options.extend(remaining_countries[:needed])

        # Shuffle the options
        random.shuffle(options)

        # Return the shuffled options
        return options[:num_options]  # Ensure we return exactly num_options

    def _get_mock_region(self, country_name: str) -> str:
        """Get the region for a country (placeholder until proper data is available)"""
        # This would be replaced with proper data from database
        regions = {
            "United_States": "North America",
            "Canada": "North America",
            "United_Kingdom": "Europe",
            "France": "Europe",
            "Germany": "Europe",
            "Japan": "Asia",
            "China": "Asia",
            "Australia": "Oceania",
            "Brazil": "South America",
            "South_Africa": "Africa"
        }
        return regions.get(country_name, "Unknown Region")

    def _get_mock_subregion(self, country_name: str) -> Optional[str]:
        """Get the subregion for a country (placeholder until proper data is available)"""
        # This would be replaced with proper data from database
        subregions = {
            "United_States": "Northern America",
            "Canada": "Northern America",
            "United_Kingdom": "Northern Europe",
            "France": "Western Europe",
            "Germany": "Western Europe",
            "Japan": "Eastern Asia",
            "China": "Eastern Asia",
            "Australia": "Australia and New Zealand",
            "Brazil": "Latin America",
            "South_Africa": "Southern Africa"
        }
        return subregions.get(country_name)

    def _get_mock_population(self, country_name: str) -> int:
        """Get the population for a country (placeholder until proper data is available)"""
        # This would be replaced with proper data from database
        populations = {
            "United_States": 331002651,
            "Canada": 37742154,
            "United_Kingdom": 67886011,
            "France": 65273511,
            "Germany": 83783942,
            "Japan": 126476461,
            "China": 1439323776,
            "Australia": 25499884,
            "Brazil": 212559417,
            "South_Africa": 59308690
        }
        return populations.get(country_name, 10000000)  # Default value

    def _get_mock_area(self, country_name: str) -> int:
        """Get the area (in km²) for a country (placeholder until proper data is available)"""
        # This would be replaced with proper data from database
        areas = {
            "United_States": 9372610,
            "Canada": 9984670,
            "United_Kingdom": 242900,
            "France": 551695,
            "Germany": 357022,
            "Japan": 377915,
            "China": 9596960,
            "Australia": 7692024,
            "Brazil": 8515767,
            "South_Africa": 1221037
        }
        return areas.get(country_name, 500000)  # Default value

    def _format_population(self, population: int) -> str:
        """Format population number for display"""
        if population >= 1000000000:
            return f"{population / 1000000000:.2f} billion"
        elif population >= 1000000:
            return f"{population / 1000000:.1f} million"
        elif population >= 1000:
            return f"{population / 1000:.1f} thousand"
        else:
            return str(population)

    def _format_area(self, area: int) -> str:
        """Format area for display"""
        if area >= 1000000:
            return f"{area / 1000000:.2f} million km²"
        elif area >= 1000:
            return f"{area / 1000:.1f} thousand km²"
        else:
            return f"{area} km²"

    def load_countries(self) -> List[Dict]:
        """Load countries from database or fall back to sample data"""
        try:
            # Try to load countries from the SQLite database
            # Connect to the database
            conn = sqlite3.connect("country_game/database/countries.db")
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Query for all countries
            cursor.execute("SELECT * FROM countries")
            rows = cursor.fetchall()

            # Create country objects with neighbors
            countries = []
            for row in rows:
                country = {
                    "name": row["name"],
                    "capital": row["capital"] if row["capital"] else "Unknown",
                    "region": row["region"] if row["region"] else "Unknown",
                    "neighbors": []
                }

                # Get neighbors
                cursor.execute("SELECT neighbor_name FROM neighbors WHERE country_name = ?", (country["name"],))
                neighbor_rows = cursor.fetchall()
                for neighbor_row in neighbor_rows:
                    country["neighbors"].append(neighbor_row["neighbor_name"])

                countries.append(country)

            conn.close()

            # If we got countries from the database, return them
            if countries:
                logger.info(f"Loaded {len(countries)} countries from database")
                return countries

            # Otherwise, fall back to sample data
            logger.warning("No countries found in database, falling back to sample data")
            return self._get_fallback_countries()

        except Exception as e:
            logger.error(f"Database error: {e}. Falling back to sample data.")
            return self._get_fallback_countries()

    def _get_fallback_countries(self) -> List[Dict]:
        """Return a comprehensive list of countries as fallback with capitals and neighbors"""
        # This is a simplified list just for demo purposes
        countries = [
            {
                "name": "United_States",
                "capital": "Washington D.C.",
                "neighbors": ["Canada", "Mexico"]
            },
            {
                "name": "Canada",
                "capital": "Ottawa",
                "neighbors": ["United_States"]
            },
            {
                "name": "Mexico",
                "capital": "Mexico City",
                "neighbors": ["United_States", "Guatemala", "Belize"]
            },
            {
                "name": "United_Kingdom",
                "capital": "London",
                "neighbors": ["Ireland"]
            },
            {
                "name": "France",
                "capital": "Paris",
                "neighbors": ["Spain", "Italy", "Switzerland", "Germany", "Belgium", "Luxembourg"]
            },
            {
                "name": "Germany",
                "capital": "Berlin",
                "neighbors": ["France", "Switzerland", "Austria", "Czech_Republic", "Poland", "Denmark", "Netherlands", "Belgium", "Luxembourg"]
            },
            {
                "name": "Japan",
                "capital": "Tokyo",
                "neighbors": []
            },
            {
                "name": "Australia",
                "capital": "Canberra",
                "neighbors": []
            },
            {
                "name": "Brazil",
                "capital": "Brasília",
                "neighbors": ["Argentina", "Uruguay", "Paraguay", "Bolivia", "Peru", "Colombia", "Venezuela", "Guyana", "Suriname", "French_Guiana"]
            },
            {
                "name": "China",
                "capital": "Beijing",
                "neighbors": ["Russia", "Mongolia", "North_Korea", "Vietnam", "Laos", "Myanmar", "India", "Bhutan", "Nepal", "Pakistan", "Afghanistan", "Tajikistan", "Kyrgyzstan", "Kazakhstan"]
            }
        ]

        logger.info(f"Using fallback data with {len(countries)} countries")
        return countries

    async def handle_answer(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle text-based answers (manual typing) - not used much with the button interface"""
        # Not implemented - we only support button-based answers
        pass