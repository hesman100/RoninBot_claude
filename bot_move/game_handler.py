import logging
import json
import os
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext, ConversationHandler, Filters
from config import (
    ANSWER_TIMEOUT, GAME_START_MESSAGE, CORRECT_ANSWER_MESSAGE, 
    WRONG_ANSWER_MESSAGE, TIMEOUT_MESSAGE
)
from country_database import get_database

# Define states for the conversation handler
AWAITING_ANSWER = 0

logger = logging.getLogger(__name__)

# User stats storage
STATS_FILE = 'user_stats.json'

class GameHandler:
    def __init__(self):
        self.country_database = get_database()
        self.active_games = {}  # Store active games by user_id
        self.user_stats = self._load_stats()
        
    def _ensure_db_connection(self):
        """Ensure database connection is valid, attempt to reconnect if needed"""
        try:
            # Test the connection with a simple query
            if self.country_database.conn is None or self.country_database.cursor is None:
                logger.warning("Database connection or cursor is None, reconnecting...")
                self.country_database.connect()
                self.country_database.cursor = self.country_database.conn.cursor()
                return True
                
            # Test if the connection is still alive
            self.country_database.cursor.execute("SELECT 1")
            return True
        except Exception as e:
            logger.warning(f"Database connection test failed: {e}")
            try:
                # Try to reconnect
                logger.info("Attempting to reconnect to database...")
                if self.country_database.conn:
                    try:
                        self.country_database.conn.close()
                    except:
                        pass
                self.country_database.connect()
                self.country_database.cursor = self.country_database.conn.cursor()
                logger.info("Database reconnection successful")
                return True
            except Exception as reconnect_error:
                logger.error(f"Failed to reconnect to database: {reconnect_error}")
                return False
        
    def handle_text_message(self, update: Update, context: CallbackContext):
        """Handle text messages outside of commands"""
        user_id = update.effective_user.id
        
        # Check if this user has an active game
        if user_id in self.active_games:
            # Pass to the answer handler
            return self.handle_answer(update, context)
        else:
            # No active game, just provide a hint
            update.message.reply_text(
                "You don't have an active game right now. Use /game or /game map to start a new game."
            )
        
    def _load_stats(self):
        """Load user stats from file"""
        if os.path.exists(STATS_FILE):
            try:
                with open(STATS_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading stats: {e}")
        return {}
        
    def _save_stats(self):
        """Save user stats to file"""
        try:
            with open(STATS_FILE, 'w') as f:
                json.dump(self.user_stats, f)
        except Exception as e:
            logger.error(f"Error saving stats: {e}")
            
    def _update_stats(self, user_id, username, correct=False, timeout=False, gave_up=False):
        """Update user statistics"""
        user_id = str(user_id)  # Convert to string for JSON keys
        
        if user_id not in self.user_stats:
            self.user_stats[user_id] = {
                'username': username,
                'games_played': 0,
                'correct_answers': 0,
                'timeout_answers': 0,
                'gave_up': 0,
                'incorrect_answers': 0,
                'streak': 0,
                'max_streak': 0
            }
            
        stats = self.user_stats[user_id]
        stats['games_played'] += 1
        
        # Update streak
        if correct:
            stats['correct_answers'] += 1
            stats['streak'] += 1
            stats['max_streak'] = max(stats['max_streak'], stats['streak'])
        else:
            stats['streak'] = 0
            if timeout:
                stats['timeout_answers'] += 1
            elif gave_up:
                stats['gave_up'] += 1
            else:
                stats['incorrect_answers'] += 1
                
        # Periodically save stats
        if stats['games_played'] % 5 == 0:
            self._save_stats()

    def start_game(self, update: Update, context: CallbackContext, game_mode="map"):
        """
        Start a new game based on the specified game mode:
        - map: Show country map, guess the country name (default)
        - flag: Show country flag, guess the country name
        - capital: Show country map, guess the capital city
        """
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        
        # Parse command args if provided - allows "/game flag" to work properly
        if hasattr(context, 'args') and context.args:
            arg = context.args[0].lower()
            if arg in ["map", "flag", "cap", "capital"]:
                if arg == "cap":
                    game_mode = "capital"
                else:
                    game_mode = arg
                logger.info(f"Game mode set from args: {game_mode}")
        
        logger.info(f"Starting new game with mode: {game_mode}")
        
        # Ensure database connection is valid before proceeding
        self._ensure_db_connection()
        
        # Get a random country
        country = self.country_database.get_random_country()
        country_name = country['name']['common']
        logger.info(f"Selected random country: {country_name} (ID: {country.get('id')})")
        
        # Get the appropriate image URL based on game mode
        if game_mode == "flag":
            # For flag mode, get the country's flag URL
            logger.info(f"Flag mode selected for {country_name}")
            map_url = self._get_flag_url(country)
            logger.info(f"Using flag URL: {map_url}")
        else:
            # For map mode or capital mode, use the regular map
            logger.info(f"{game_mode.capitalize()} mode selected for {country_name}")
            map_url = self.country_database.get_map_url(country)
            logger.info(f"Using map URL: {map_url}")
        
        # Prepare buttons based on game mode
        import random
        
        # Default button options in case database queries fail
        default_countries = ["United States", "China", "Russia", "Brazil", "India", 
                            "Germany", "Japan", "United Kingdom", "France"]
        default_capitals = ["Tokyo", "Beijing", "London", "Paris", "Berlin", 
                          "Moscow", "Washington D.C.", "Rome", "Madrid"]
        
        # Initialize variables
        button_options = []
        correct_capital = "Unknown"
        
        # Ensure we have a valid cursor
        if not self._ensure_db_connection():
            logger.error("Could not establish database connection for button creation")
            # Use defaults based on game mode
            if game_mode == "capital":
                button_options = default_capitals.copy()
                if 'capital' in country and country['capital']:
                    correct_capital = country['capital'][0]
            else:
                button_options = default_countries.copy()
        else:
            # We have a valid database connection
            cursor = self.country_database.cursor
            
            if game_mode == "capital":
                # For capital city mode, show capital cities instead of countries
                # Get the correct capital
                if 'capital' in country and country['capital']:
                    correct_capital = country['capital'][0]
                
                try:
                    # Get random capitals for buttons - directly get 9 random capitals
                    cursor.execute('''
                        SELECT capital 
                        FROM countries 
                        WHERE not_a_country = FALSE AND capital IS NOT NULL AND capital != %s 
                        ORDER BY RANDOM() 
                        LIMIT 9
                    ''', (correct_capital,))
                    
                    # Create button options from results
                    button_options = [row[0] for row in cursor.fetchall() if row[0]]
                except Exception as e:
                    logger.error(f"Database error when getting capital options: {e}")
                    # Fallback capital cities
                    button_options = default_capitals.copy()
            else:
                # For map and flag modes, show countries
                try:
                    cursor.execute('SELECT neighbors FROM countries WHERE id = %s', (country.get('id'),))
                    result = cursor.fetchone()
                    neighbors = result[0] if result and cursor.rowcount > 0 else []
                    
                    # If there are not enough neighbors, add random countries
                    if not neighbors or len(neighbors) < 9:
                        cursor.execute('''
                            SELECT name 
                            FROM countries 
                            WHERE not_a_country = FALSE AND name != %s 
                            ORDER BY RANDOM() 
                            LIMIT %s
                        ''', (country_name, max(9 - len(neighbors), 0)))
                        
                        random_countries = [row[0] for row in cursor.fetchall()]
                        button_options = (neighbors or []) + random_countries
                    else:
                        # If we have enough neighbors, limit to 9
                        button_options = neighbors[:9]
                except Exception as e:
                    logger.error(f"Database error when getting country options: {e}")
                    # Fallback countries if database fails
                    button_options = default_countries.copy()
        
        # Ensure we have at least one button option
        if not button_options:
            logger.warning("No button options available, using defaults")
            if game_mode == "capital":
                button_options = default_capitals.copy()
            else:
                button_options = default_countries.copy()
        
        # Make sure correct answer is in the list
        if game_mode == "capital":
            # For capital mode
            if correct_capital in button_options:
                # If the correct capital is already in the list, shuffle it
                random.shuffle(button_options)
            else:
                # Replace a random capital with the correct capital
                if button_options:
                    button_options[random.randint(0, len(button_options)-1)] = correct_capital
                else:
                    # Fallback if we somehow have no capitals
                    button_options = [correct_capital]
                random.shuffle(button_options)
        else:
            # For map and flag modes
            if country_name in button_options:
                # If the correct answer is already in the list, shuffle it
                random.shuffle(button_options)
            else:
                # Replace a random country with the correct answer
                if button_options:
                    button_options[random.randint(0, len(button_options)-1)] = country_name
                else:
                    # Fallback if we somehow have no options
                    button_options = [country_name]
                random.shuffle(button_options)
        
        # Get username for statistics
        username = update.effective_user.username or update.effective_user.first_name or "Anonymous"
        
        # Store button options along with the correct answer for validation
        self.active_games[user_id] = {
            'country': country,
            'button_options': button_options,
            'start_time': update.message.date if hasattr(update, 'message') and update.message else None,
            'game_mode': game_mode,  # Store the game mode to handle different answer types
            'username': username  # Store username for timeout scenarios
        }
        
        # Create buttons (3 rows of 3 buttons + give up button at the bottom)
        keyboard = []
        for i in range(0, len(button_options), 3):
            row = []
            for option in button_options[i:i+3]:
                row.append(InlineKeyboardButton(
                    option, 
                    callback_data=f"answer_{option}"
                ))
            keyboard.append(row)
        
        # Add "Give up" button at the bottom
        keyboard.append([InlineKeyboardButton("Give up", callback_data="give_up")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            # Log that we're attempting to send the map
            logger.info(f"Attempting to send map for {country_name}")
            
            # Check if the map URL is a local file path
            if map_url and map_url.startswith('./'):
                try:
                    # Open the file and send it directly
                    with open(map_url, 'rb') as photo_file:
                        # Customize caption based on game mode
                        if game_mode == "flag":
                            caption = "🚩 Guess the country from this flag! You have 15 seconds ⏱️\n\nSelect the country from the buttons below:"
                        elif game_mode == "capital":
                            caption = "🏙️ Guess the capital city of this country! You have 15 seconds ⏱️\n\nSelect the capital city from the buttons below:"
                        else:
                            # Default map mode
                            caption = f"{GAME_START_MESSAGE}\n\nSelect the country from the buttons below:"
                            
                        context.bot.send_photo(
                            chat_id=chat_id,
                            photo=photo_file,
                            caption=caption,
                            reply_markup=reply_markup
                        )
                    logger.info(f"Successfully sent local map image from {map_url}")
                except Exception as file_error:
                    logger.error(f"Error sending local map image: {file_error}")
                    # Fall through to the next approach
                    raise file_error
            else:
                # Customize caption based on game mode
                if game_mode == "flag":
                    caption = "🚩 Guess the country from this flag! You have 15 seconds ⏱️\n\nSelect the country from the buttons below:"
                elif game_mode == "capital":
                    caption = "🏙️ Guess the capital city of this country! You have 15 seconds ⏱️\n\nSelect the capital city from the buttons below:"
                else:
                    # Default map mode
                    caption = f"{GAME_START_MESSAGE}\n\nSelect the country from the buttons below:"
                
                # Try sending as URL if it's not a local file
                context.bot.send_photo(
                    chat_id=chat_id,
                    photo=map_url,
                    caption=caption,
                    reply_markup=reply_markup
                )
                logger.info("Successfully sent map image from URL")
            
            # If we got here, we succeeded in sending the image
        except Exception as url_error:
            logger.error(f"Error sending map image: {url_error}")
            
            # Alternative: Try using a placeholder image from a reliable source
            logger.info("Trying with a placeholder image")
            # Customize caption based on game mode, even for fallback
            if game_mode == "flag":
                caption = f"🚩 Guess the country from this flag! You have 15 seconds ⏱️\n\nSelect the country from the buttons below (hint: it's {country_name}):"
            elif game_mode == "capital":
                caption = f"🏙️ Guess the capital city of this country! You have 15 seconds ⏱️\n\nSelect the capital city from the buttons below (hint: it's {country_name}):"
            else:
                # Default map mode
                caption = f"{GAME_START_MESSAGE}\n\nSelect the country from the buttons below (hint: it's {country_name}):"
                
            context.bot.send_photo(
                chat_id=chat_id,
                photo="https://www.publicdomainpictures.net/pictures/30000/velka/plain-white-background.jpg",
                caption=caption,
                reply_markup=reply_markup
            )
        except Exception as e:
            logger.error(f"All attempts to send image failed: {e}")
            # Send message with country name as fallback
            context.bot.send_message(
                chat_id=chat_id,
                text=f"Could not load map. For a proper game experience, please set the GEOAPIFY_API_KEY environment variable.\n\n"
                     f"For testing purposes, the country is: {country_name}\n\n"
                     f"Please select from the buttons below:",
                reply_markup=reply_markup
            )
        
        # Set a job to check for timeout
        context.job_queue.run_once(
            self.check_timeout, 
            ANSWER_TIMEOUT,
            context={'user_id': user_id, 'chat_id': chat_id},
            name=f"timeout_{user_id}"
        )
        
        return AWAITING_ANSWER
    
    def check_timeout(self, context: CallbackContext):
        """Check if the user has answered within the time limit"""
        job = context.job
        user_id = job.context['user_id']
        chat_id = job.context['chat_id']
        
        # Check if game still exists (hasn't been answered)
        if user_id in self.active_games:
            country = self.active_games[user_id]['country']
            country_name = country['name']['common']
            
            # Get username from active_games dictionary
            username = self.active_games[user_id].get('username', 'Anonymous')
            self._update_stats(user_id, username, correct=False, timeout=True)
            
            # Get the game mode
            game_mode = self.active_games[user_id].get('game_mode', 'map')
            
            # Generate additional country info for educational value
            country_info = self._get_country_info(country)
            
            # Format the timeout message based on game mode
            if game_mode == "capital":
                # Get the capital city of the country
                capital_name = "Unknown"
                if 'capital' in country and country['capital']:
                    capital_name = country['capital'][0]
                
                timeout_message = f"{TIMEOUT_MESSAGE}\nThe country was: *{country_name}*\nThe capital is: *{capital_name}*"
            elif game_mode == "flag":
                timeout_message = f"{TIMEOUT_MESSAGE}\nThis flag belongs to: *{country_name}*"
            else:
                # Default map mode
                timeout_message = f"{TIMEOUT_MESSAGE}\nThe correct answer was: *{country_name}*"
            
            # Send timeout message with continue buttons
            context.bot.send_message(
                chat_id=chat_id,
                text=f"{timeout_message}\n\n{country_info}",
                parse_mode="Markdown",
                reply_markup=self._get_continue_game_buttons()
            )
            
            # Clean up
            del self.active_games[user_id]
            
            return ConversationHandler.END
    
    def handle_answer(self, update: Update, context: CallbackContext):
        """Process user's text answer (legacy method, kept for backward compatibility)"""
        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name or "Anonymous"
        
        # Update stored username in active_games for timeout/future reference
        if user_id in self.active_games:
            self.active_games[user_id]['username'] = username
            
        user_answer = update.message.text
        
        # Check if user has an active game
        if user_id not in self.active_games:
            update.message.reply_text("You don't have an active game. Use /game to start.")
            return ConversationHandler.END
        
        # Get the correct country
        correct_country = self.active_games[user_id]['country']
        country_name = correct_country['name']['common']
        game_mode = self.active_games[user_id].get('game_mode', 'map')
        
        # Check if the answer is correct
        is_correct = False
        if game_mode == "capital":
            # For capital city mode, need to check if answer matches capital city
            if 'capital' in correct_country and correct_country['capital']:
                capital_name = correct_country['capital'][0]
                is_correct = user_answer.lower() == capital_name.lower()
        else:
            # For map and flag mode, check country name
            is_correct = user_answer.lower() == country_name.lower()
        
        # Update stats
        self._update_stats(user_id, username, correct=is_correct)
        
        # Generate country info for educational value
        country_info = self._get_country_info(correct_country)
        
        # Create stats summary
        stats = self.user_stats.get(str(user_id), {})
        stats_text = f"\n\nYour Stats:\n" \
                     f"🎮 Games Played: {stats.get('games_played', 0)}\n" \
                     f"✅ Correct: {stats.get('correct_answers', 0)}\n" \
                     f"🔥 Current Streak: {stats.get('streak', 0)}\n" \
                     f"🏆 Best Streak: {stats.get('max_streak', 0)}"
        
        # Format response based on game mode
        if game_mode == "capital":
            # Get the capital city for the response
            capital_name = "Unknown"
            if 'capital' in correct_country and correct_country['capital']:
                capital_name = correct_country['capital'][0]
                
            if is_correct:
                update.message.reply_text(
                    f"{CORRECT_ANSWER_MESSAGE} The capital of *{country_name}* is indeed *{capital_name}*!\n\n{country_info}{stats_text}",
                    parse_mode="Markdown",
                    reply_markup=self._get_continue_game_buttons()
                )
            else:
                update.message.reply_text(
                    f"{WRONG_ANSWER_MESSAGE}\n\nYou entered: *{user_answer}*\nCorrect capital: *{capital_name}*\nCountry: *{country_name}*\n\n{country_info}{stats_text}",
                    parse_mode="Markdown",
                    reply_markup=self._get_continue_game_buttons()
                )
        elif game_mode == "flag":
            # For flag mode
            if is_correct:
                update.message.reply_text(
                    f"{CORRECT_ANSWER_MESSAGE} This flag belongs to *{country_name}*!\n\n{country_info}{stats_text}",
                    parse_mode="Markdown",
                    reply_markup=self._get_continue_game_buttons()
                )
            else:
                update.message.reply_text(
                    f"{WRONG_ANSWER_MESSAGE}\n\nYou entered: *{user_answer}*\nCorrect answer: *{country_name}*\n\n{country_info}{stats_text}",
                    parse_mode="Markdown",
                    reply_markup=self._get_continue_game_buttons()
                )
        else:
            # Default map mode
            if is_correct:
                update.message.reply_text(
                    f"{CORRECT_ANSWER_MESSAGE} The answer is indeed *{country_name}*!\n\n{country_info}{stats_text}",
                    parse_mode="Markdown",
                    reply_markup=self._get_continue_game_buttons()
                )
            else:
                update.message.reply_text(
                    f"{WRONG_ANSWER_MESSAGE}\n\nYou entered: *{user_answer}*\nCorrect answer: *{country_name}*\n\n{country_info}{stats_text}",
                    parse_mode="Markdown",
                    reply_markup=self._get_continue_game_buttons()
                )
        
        
        # Remove any pending timeout jobs
        current_jobs = context.job_queue.get_jobs_by_name(f"timeout_{user_id}")
        for job in current_jobs:
            job.schedule_removal()
        
        # Clean up
        del self.active_games[user_id]
        
        return ConversationHandler.END
        
    def handle_button_answer(self, update: Update, context: CallbackContext):
        """Process user's button answer"""
        query = update.callback_query
        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name or "Anonymous"
        
        # Update stored username in active_games for timeout/future reference
        if user_id in self.active_games:
            self.active_games[user_id]['username'] = username
            
        # Answer the callback query to remove the loading state
        query.answer()
        
        # Check if user has an active game
        if user_id not in self.active_games:
            query.edit_message_caption(caption="No active game found.")
            return ConversationHandler.END
        
        # Get the correct country
        correct_country = self.active_games[user_id]['country']
        country_name = correct_country['name']['common']
        
        # Extract selected country from callback data (format: "answer_CountryName")
        selected_country = query.data.replace("answer_", "")
        
        # Get the game mode
        game_mode = self.active_games[user_id].get('game_mode', 'map') 
        
        # Check if the answer is correct based on game mode
        if game_mode == "capital":
            # For capital city mode, we compare the selected option with the correct capital
            correct_capital = "Unknown"
            if 'capital' in correct_country and correct_country['capital']:
                correct_capital = correct_country['capital'][0]
            is_correct = selected_country == correct_capital
        else:
            # For map mode and flag mode, regular country name matching
            is_correct = selected_country == country_name
        
        # Update stats
        self._update_stats(user_id, username, correct=is_correct)
        
        # Generate country info for educational value
        country_info = self._get_country_info(correct_country)
        
        # Create stats summary
        stats = self.user_stats.get(str(user_id), {})
        stats_text = f"\n\nYour Stats:\n" \
                     f"🎮 Games Played: {stats.get('games_played', 0)}\n" \
                     f"✅ Correct: {stats.get('correct_answers', 0)}\n" \
                     f"🔥 Current Streak: {stats.get('streak', 0)}\n" \
                     f"🏆 Best Streak: {stats.get('max_streak', 0)}"
        
        # Format response based on game mode
        if game_mode == "capital":
            # Get the capital city of the country
            capital_name = "Unknown"
            if 'capital' in correct_country and correct_country['capital']:
                capital_name = correct_country['capital'][0]
                
            if is_correct:
                query.edit_message_caption(
                    caption=f"{CORRECT_ANSWER_MESSAGE} The capital of *{country_name}* is indeed *{capital_name}*!\n\n{country_info}{stats_text}",
                    parse_mode="Markdown",
                    reply_markup=self._get_continue_game_buttons()
                )
            else:
                query.edit_message_caption(
                    caption=f"{WRONG_ANSWER_MESSAGE}\n\nYou selected: *{selected_country}*\nCorrect capital: *{capital_name}*\nCountry: *{country_name}*\n\n{country_info}{stats_text}",
                    parse_mode="Markdown",
                    reply_markup=self._get_continue_game_buttons()
                )
        elif game_mode == "flag":
            # For flag mode, emphasize the flag in the answer
            if is_correct:
                query.edit_message_caption(
                    caption=f"{CORRECT_ANSWER_MESSAGE} This flag belongs to *{country_name}*!\n\n{country_info}{stats_text}",
                    parse_mode="Markdown",
                    reply_markup=self._get_continue_game_buttons()
                )
            else:
                query.edit_message_caption(
                    caption=f"{WRONG_ANSWER_MESSAGE}\n\nYou selected: *{selected_country}*\nCorrect answer: *{country_name}*\n\n{country_info}{stats_text}",
                    parse_mode="Markdown",
                    reply_markup=self._get_continue_game_buttons()
                )
        else:
            # Default map mode
            if is_correct:
                query.edit_message_caption(
                    caption=f"{CORRECT_ANSWER_MESSAGE} The answer is indeed *{country_name}*!\n\n{country_info}{stats_text}",
                    parse_mode="Markdown",
                    reply_markup=self._get_continue_game_buttons()
                )
            else:
                query.edit_message_caption(
                    caption=f"{WRONG_ANSWER_MESSAGE}\n\nYou selected: *{selected_country}*\nCorrect answer: *{country_name}*\n\n{country_info}{stats_text}",
                    parse_mode="Markdown",
                    reply_markup=self._get_continue_game_buttons()
                )
        
        # Remove any pending timeout jobs
        current_jobs = context.job_queue.get_jobs_by_name(f"timeout_{user_id}")
        for job in current_jobs:
            job.schedule_removal()
        
        # Clean up
        del self.active_games[user_id]
        
        return ConversationHandler.END
    
    def give_up(self, update: Update, context: CallbackContext):
        """Handle user giving up"""
        query = update.callback_query
        query.answer()
        
        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name or "Anonymous"
        
        # Update stored username in active_games for consistency in stats
        if user_id in self.active_games:
            self.active_games[user_id]['username'] = username
            
        # Check if user has an active game
        if user_id not in self.active_games:
            query.edit_message_caption(caption="No active game found.")
            return ConversationHandler.END
        
        country = self.active_games[user_id]['country']
        country_name = country['name']['common']
        game_mode = self.active_games[user_id].get('game_mode', 'map')
        
        # Update stats (using gave_up=True)
        self._update_stats(user_id, username, correct=False, gave_up=True)
        
        # Generate country info for educational value
        country_info = self._get_country_info(country)
        
        # Edit message with answer and country info based on game mode
        if game_mode == "capital":
            # Get the capital city of the country
            capital_name = "Unknown"
            if 'capital' in country and country['capital']:
                capital_name = country['capital'][0]
                
            query.edit_message_caption(
                caption=f"Game over! You gave up.\nThe country was: *{country_name}*\nThe capital is: *{capital_name}*\n\n{country_info}",
                parse_mode="Markdown",
                reply_markup=self._get_continue_game_buttons()
            )
        elif game_mode == "flag":
            query.edit_message_caption(
                caption=f"Game over! You gave up.\nThis flag belongs to: *{country_name}*\n\n{country_info}",
                parse_mode="Markdown",
                reply_markup=self._get_continue_game_buttons()
            )
        else:
            # Default map mode
            query.edit_message_caption(
                caption=f"Game over! You gave up.\nThe correct answer was: *{country_name}*\n\n{country_info}",
                parse_mode="Markdown",
                reply_markup=self._get_continue_game_buttons()
            )
        
        # Remove any pending timeout jobs
        current_jobs = context.job_queue.get_jobs_by_name(f"timeout_{user_id}")
        for job in current_jobs:
            job.schedule_removal()
        
        # Clean up
        del self.active_games[user_id]
        
        return ConversationHandler.END
        
    def _get_continue_game_buttons(self):
        """Generate buttons for continuing the game in different modes"""
        keyboard = [
            [
                InlineKeyboardButton("🗺️ Map Game", callback_data="continue_map"),
                InlineKeyboardButton("🚩 Flag Game", callback_data="continue_flag"),
            ],
            [
                InlineKeyboardButton("🏙️ Capital City Game", callback_data="continue_capital")
            ],
            [
                InlineKeyboardButton("🏆 Show Leaderboard", callback_data="continue_lb")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
        
    def _get_country_info(self, country):
        """Generate interesting information about a country"""
        info_parts = []
        country_name = country['name']['common']
        
        # Add country name with flag emoji if available
        if 'flag' in country and isinstance(country['flag'], str):
            info_parts.append(f"{country['flag']} *{country_name}*")
        else:
            info_parts.append(f"🏳️ *{country_name}*")
        
        # Create a "Quick Facts" section
        quick_facts = []
        
        # Add capital if available
        if 'capital' in country and country['capital']:
            quick_facts.append(f"🏙️ *Capital*: {', '.join(country['capital'])}")
            
        # Add region if available
        if 'region' in country and country['region']:
            region_text = country['region']
            if 'subregion' in country and country['subregion']:
                region_text += f" ({country['subregion']})"
            quick_facts.append(f"🌍 *Region*: {region_text}")
            
        # Add continent (if not already covered by region)
        if 'continents' in country and country['continents']:
            quick_facts.append(f"🗺️ *Continent*: {', '.join(country['continents'])}")
        
        # Hardcoded data for commonly played countries
        hardcoded_data = {
            "United States": {"population": 331_900_000, "area": 9_833_520, "independence": 1776},
            "Canada": {"population": 38_250_000, "area": 9_984_670, "independence": 1867},
            "Mexico": {"population": 128_900_000, "area": 1_972_550, "independence": 1821},
            "Brazil": {"population": 212_600_000, "area": 8_515_770, "independence": 1822},
            "Argentina": {"population": 45_380_000, "area": 2_780_400, "independence": 1816},
            "United Kingdom": {"population": 67_220_000, "area": 242_495, "independence": 1066},
            "France": {"population": 67_390_000, "area": 551_695, "independence": 843},
            "Germany": {"population": 83_240_000, "area": 357_022, "independence": 1871},
            "Italy": {"population": 60_360_000, "area": 301_340, "independence": 1861},
            "Spain": {"population": 46_940_000, "area": 505_992, "independence": 1492},
            "Russia": {"population": 144_100_000, "area": 17_098_246, "independence": 1991},
            "China": {"population": 1_402_000_000, "area": 9_596_961, "independence": 221},
            "India": {"population": 1_380_000_000, "area": 3_287_263, "independence": 1947},
            "Japan": {"population": 126_300_000, "area": 377_975, "independence": 660},
            "Australia": {"population": 25_690_000, "area": 7_692_024, "independence": 1901},
            "South Africa": {"population": 59_310_000, "area": 1_221_037, "independence": 1961},
            "Egypt": {"population": 102_300_000, "area": 1_002_450, "independence": 1922},
            "Nigeria": {"population": 206_100_000, "area": 923_768, "independence": 1960},
            "Kenya": {"population": 53_770_000, "area": 580_367, "independence": 1963},
            "Indonesia": {"population": 273_500_000, "area": 1_904_569, "independence": 1945},
            "Thailand": {"population": 69_800_000, "area": 513_120, "independence": 1238},
            "Philippines": {"population": 109_600_000, "area": 342_353, "independence": 1946},
            "Turkey": {"population": 84_340_000, "area": 783_356, "independence": 1923},
            "Saudi Arabia": {"population": 34_810_000, "area": 2_149_690, "independence": 1932},
            "Israel": {"population": 9_217_000, "area": 22_072, "independence": 1948},
        }
        
        # Use hardcoded data if available
        if country_name in hardcoded_data:
            data = hardcoded_data[country_name]
            
            # Add population
            pop = data.get("population")
            if pop:
                if pop >= 1_000_000_000:
                    population = f"{pop/1_000_000_000:.2f} billion"
                elif pop >= 1_000_000:
                    population = f"{pop/1_000_000:.1f} million"
                elif pop >= 1_000:
                    population = f"{pop/1_000:.1f} thousand"
                else:
                    population = f"{pop:,}"
                quick_facts.append(f"👥 *Population*: {population}")
            
            # Add area
            area_val = data.get("area")
            if area_val:
                if area_val >= 1_000_000:
                    area = f"{area_val/1_000_000:.2f} million km²"
                else:
                    area = f"{int(area_val):,} km²"
                quick_facts.append(f"📏 *Area*: {area}")
            
            # Add independence year
            if "independence" in data:
                quick_facts.append(f"🏛️ *Established*: {data['independence']}")
            
            # Generic independent status
            quick_facts.append(f"🎗️ *Status*: Independent country")
        else:
            # Use DB data if available
            # Add population if available with better unit formatting
            if 'population' in country and country['population']:
                pop = country['population']
                if pop:  # Check if the value is not None
                    if pop >= 1_000_000_000:
                        population = f"{pop/1_000_000_000:.2f} billion"
                    elif pop >= 1_000_000:
                        population = f"{pop/1_000_000:.2f} million"
                    elif pop >= 1_000:
                        population = f"{pop/1_000:.1f} thousand"
                    else:
                        population = f"{pop:,}"
                    quick_facts.append(f"👥 *Population*: {population}")
                
            # Add area if available with better formatting
            if 'area' in country and country['area']:
                area_val = country['area']
                if area_val:  # Check if the value is not None
                    try:
                        area_val = float(area_val)
                        if area_val >= 1_000_000:
                            area = f"{area_val/1_000_000:.2f} million km²"
                        else:
                            area = f"{int(area_val):,} km²"
                        quick_facts.append(f"📏 *Area*: {area}")
                    except (ValueError, TypeError):
                        pass
                
            # Add information about independence/establishment
            if 'independent' in country and country['independent']:
                independence_info = "Independent country"
                year_found = False
                
                # Try different fields that might contain year information
                
                # Check 'independence' field first
                if 'independence' in country and country['independence']:
                    independence_year = country['independence']
                    try:
                        year = int(independence_year)
                        if 1700 <= year <= 2023:  # Sanity check
                            independence_info = f"Independent since {year}"
                            year_found = True
                    except (ValueError, TypeError):
                        # If the year isn't a proper integer
                        if isinstance(independence_year, str) and independence_year.strip():
                            independence_info = f"Independence: {independence_year}"
                            year_found = True
                
                # If independence year not found, check 'founded' field
                if not year_found and 'founded' in country and country['founded']:
                    try:
                        year = int(country['founded'])
                        if 1000 <= year <= 2023:  # Sanity check
                            quick_facts.append(f"🏛️ *Founded*: {year}")
                            year_found = True
                    except (ValueError, TypeError):
                        pass
                
                # If still not found, check 'established' field
                if not year_found and 'established' in country and country['established']:
                    try:
                        year = int(country['established'])
                        if 1000 <= year <= 2023:  # Sanity check
                            quick_facts.append(f"🏛️ *Established*: {year}")
                            year_found = True
                    except (ValueError, TypeError):
                        pass
                        
                # Add independence status info
                quick_facts.append(f"🎗️ *Status*: {independence_info}")
        
        # Add quick facts section to main info
        if quick_facts:
            info_parts.append("*📊 Quick Facts:*")
            info_parts.extend(quick_facts)
            
        # Add "Cultural & Practical Info" section
        cultural_info = []
        
        # Add languages if available
        if 'languages' in country and country['languages']:
            languages = ', '.join(country['languages'].values())
            cultural_info.append(f"🗣️ *Languages*: {languages}")
            
        # Add currencies if available
        if 'currencies' in country and country['currencies']:
            currencies = []
            for code, currency in country['currencies'].items():
                curr_text = code
                if 'name' in currency:
                    curr_text = currency['name']
                    if 'symbol' in currency:
                        curr_text += f" ({currency['symbol']})"
                currencies.append(curr_text)
            if currencies:
                cultural_info.append(f"💰 *Currency*: {', '.join(currencies)}")
                
        # Add driving side
        if 'car' in country and 'side' in country['car']:
            side = country['car']['side'].capitalize()
            cultural_info.append(f"🚗 *Driving side*: {side}")
                
        # Add timezone
        if 'timezones' in country and country['timezones']:
            timezones = country['timezones']
            if len(timezones) > 2:
                timezone_text = f"{timezones[0]}, {timezones[1]} (+ {len(timezones)-2} more)"
            else:
                timezone_text = ', '.join(timezones)
            cultural_info.append(f"🕒 *Timezones*: {timezone_text}")
        
        # Add cultural info section to main info
        if cultural_info:
            info_parts.append("\n*🌐 Cultural & Practical Info:*")
            info_parts.extend(cultural_info)
            
        # Add "Interesting Facts" section
        facts = []
                
        # Add official name if different from common name
        if 'name' in country and 'official' in country['name'] and country['name']['official'] != country['name']['common']:
            facts.append(f"📝 *Official name*: {country['name']['official']}")
                
        # Add neighbors if available
        if 'borders' in country and country['borders']:
            if len(country['borders']) > 3:
                borders_text = f"{', '.join(country['borders'][:3])} (+ {len(country['borders'])-3} more)"
            else:
                borders_text = ', '.join(country['borders'])
            facts.append(f"🗾 *Neighbors*: {borders_text}")
        
        # Add establishment/foundation year if available
        if 'established' in country:
            if isinstance(country['established'], int) or (isinstance(country['established'], str) and country['established'].isdigit()):
                established_year = int(str(country['established']))
                if established_year > 0 and established_year < 2030:  # Sanity check on year
                    facts.append(f"🏛️ *Established*: Founded in {established_year}")
        
        # Add fun fact or notable feature
        if 'independent' in country and not country['independent']:
            facts.append(f"ℹ️ *Fun fact*: This is not an independent country")
        elif 'landlocked' in country and country['landlocked']:
            facts.append(f"ℹ️ *Fun fact*: This is a landlocked country with no coastline")
        elif 'borders' in country and len(country['borders']) == 0 and 'landlocked' in country and not country['landlocked']:
            facts.append(f"ℹ️ *Fun fact*: This is an island nation with no land borders")
            
        # Add facts section to main info
        if facts:
            info_parts.append("\n*⭐ Interesting Facts:*")
            info_parts.extend(facts)
        
        # Join all information with newlines
        return "\n".join(info_parts)
        
    def get_user_stats(self, user_id):
        """Get statistics for a specific user"""
        user_id_str = str(user_id)
        if user_id_str in self.user_stats:
            return self.user_stats[user_id_str]
        return None
        
    def get_leaderboard(self, limit=10):
        """Get the top players sorted by correct answers and accuracy"""
        if not self.user_stats:
            return []
            
        # Convert dict to list of (id, stats) pairs
        players = list(self.user_stats.items())
        
        # Sort by correct answers (primary) and accuracy (secondary)
        players.sort(key=lambda x: (
            x[1].get('correct_answers', 0),
            x[1].get('correct_answers', 0) / max(x[1].get('games_played', 1), 1),
            x[1].get('max_streak', 0)
        ), reverse=True)
        
        # Return top N players
        return players[:limit]
        
    def _get_flag_url(self, country):
        """Get the flag URL for a country"""
        # First try to get flag from database
        country_id = country.get('id')
        country_name = country['name']['common']
        
        logger.info(f"Looking for flag URL for country_id={country_id}, name={country_name}")
        
        # Check for local flag image first
        formatted_name = country_name.replace(' ', '_')
        formatted_name = ''.join(c for c in formatted_name if c.isalnum() or c == '_')
        local_flag_path = f"./wiki_flag/{formatted_name}_flag.png"
        
        # Special case for São Tomé and Príncipe
        if country_name == "São Tomé and Príncipe":
            local_flag_path = "./wiki_flag/So_Tom_and_Prncipe_flag.png"
        
        # Ensure valid database connection
        if self._ensure_db_connection():
            # Query the database for flag type map
            try:
                self.country_database.cursor.execute(
                    "SELECT map_url FROM maps WHERE country_id = %s AND map_type = 'flag'",
                    (country_id,)
                )
                result = self.country_database.cursor.fetchone()
                
                if result and result[0]:
                    logger.info(f"Found flag URL in database for {country_name}: {result[0]}")
                    return result[0]
                    
                # If we didn't find anything, let's check what maps are available
                self.country_database.cursor.execute(
                    "SELECT map_type, map_url FROM maps WHERE country_id = %s",
                    (country_id,)
                )
                all_maps = self.country_database.cursor.fetchall()
                logger.info(f"Available maps for {country_name}: {all_maps}")
                
                logger.warning(f"No flag found in database for {country_name}, trying fallbacks")
            except Exception as e:
                logger.error(f"Database error when trying to get flag: {e}")
                logger.warning(f"No flag found in database for {country_name} due to error, trying fallbacks")
        else:
            logger.warning(f"Database connection invalid, skipping database lookup for flag")
            
        # Try to use the local flag image path directly if it exists
        import os
        if os.path.exists(local_flag_path):
            logger.info(f"Using local flag image for {country_name}: {local_flag_path}")
            return local_flag_path
            
        # Try to get flag URL from country data
        if 'flags' in country and 'png' in country['flags']:
            return country['flags']['png']
        
        # Special handling for common countries that might have issues
        special_iso_codes = {
            "Singapore": "sg",
            "United States": "us",
            "United Kingdom": "gb",
            "South Korea": "kr",
            "North Korea": "kp",
            "United Arab Emirates": "ae",
            "Saudi Arabia": "sa",
            "New Zealand": "nz",
            "Sri Lanka": "lk",
            "South Africa": "za",
            "Costa Rica": "cr",
            "Dominican Republic": "do",
            "El Salvador": "sv",
            "Hong Kong": "hk",
            "Vatican City": "va",
            "San Marino": "sm",
            "Taiwan": "tw",
            "Grenada": "gd",
            "Antigua and Barbuda": "ag",
            "Saint Kitts and Nevis": "kn",
            "Saint Lucia": "lc",
            "Saint Vincent and the Grenadines": "vc",
            "Trinidad and Tobago": "tt",
            "Bosnia and Herzegovina": "ba",
            "Ivory Coast": "ci",
            "Czechia": "cz",
            "Democratic Republic of the Congo": "cd",
            "Republic of the Congo": "cg",
            "Equatorial Guinea": "gq",
            "Eswatini": "sz",
            "Guinea-Bissau": "gw",
            "East Timor": "tl"
        }
        
        if country_name in special_iso_codes:
            iso_code = special_iso_codes[country_name]
            logger.info(f"Using special ISO code for {country_name}: {iso_code}")
            return f"https://flagcdn.com/w320/{iso_code}.png"
        
        # Fallback: Try to construct flag URL using ISO code
        if 'cca2' in country and country['cca2']:
            iso_code = country['cca2'].lower()
            return f"https://flagcdn.com/w320/{iso_code}.png"
            
        # Try alternate approach with country name
        normalized_name = country_name.lower().replace(' ', '-')
        return f"https://flagcdn.com/w320/{normalized_name}.png"
        
        # Ultimate fallback: Use a placeholder image (code won't reach here due to above return)
        # return "https://via.placeholder.com/320x240/0066CC/FFFFFF?text=Flag+Not+Available"
    
    def generate_hint(self, country, game_mode="map"):
        """Generate a hint for the current country"""
        # Get country name
        country_name = country['name']['common']
        
        # For capital city mode, provide different hints specific to the capital
        if game_mode == "capital":
            # Get the capital city
            if 'capital' in country and country['capital']:
                capital_name = country['capital'][0]
                hints = []
                
                # First letter hint
                if capital_name:
                    hints.append(f"The capital city starts with *{capital_name[0]}*")
                    
                    # Word count hint
                    words = capital_name.split()
                    if len(words) > 1:
                        hints.append(f"The capital has *{len(words)}* words")
                        
                    # Letter count hint
                    hints.append(f"The capital has *{len(capital_name)}* letters")
                
                # Continent hint but for capital
                if 'region' in country and country['region']:
                    hints.append(f"The capital city is in *{country['region']}*")
                
                # Population hint for the country
                if 'population' in country and country['population']:
                    pop = country['population']
                    if pop < 1_000_000:
                        hint = "a small country (less than 1 million people)"
                    elif pop < 10_000_000:
                        hint = "a medium-sized country (1-10 million people)"
                    elif pop < 50_000_000:
                        hint = "a large country (10-50 million people)"
                    elif pop < 100_000_000:
                        hint = "a very large country (50-100 million people)"
                    else:
                        hint = "one of the most populous countries (100+ million people)"
                    hints.append(f"The capital is in *{hint}*")
                
                # Select 2-3 random hints
                import random
                if hints:
                    count = min(len(hints), random.randint(2, 3))
                    return " • ".join(random.sample(hints, count))
                
                return "Sorry, no hints available for this capital city."
        
        # For map or flag mode, use standard country hints
        # Try to get hints from database
        db_hints = self.country_database.get_country_hints(country_name)
        
        if db_hints and len(db_hints) > 0:
            # We have hints from the database, use those
            import random
            # Select 2-3 random hints
            count = min(len(db_hints), random.randint(2, 3))
            selected_hints = random.sample(db_hints, count)
            return " • ".join([f"{hint['text']}" for hint in selected_hints])
        
        # Fallback to generating hints on the fly
        hints = []
        
        # First letter hint
        if 'name' in country and 'common' in country['name']:
            name = country['name']['common']
            if name:
                hints.append(f"The country name starts with *{name[0]}*")
                
                # Word count hint
                words = name.split()
                if len(words) > 1:
                    hints.append(f"The name has *{len(words)}* words")
                    
                # Letter count hint
                hints.append(f"The name has *{len(name)}* letters")
        
        # Continent hint
        if 'region' in country and country['region']:
            hints.append(f"The country is in *{country['region']}*")
            
        # Subregion hint
        if 'subregion' in country and country['subregion']:
            hints.append(f"The country is in *{country['subregion']}*")
            
        # Capital hint
        if 'capital' in country and country['capital']:
            capital = country['capital'][0]
            hints.append(f"The capital city is *{capital}*")
            
        # Population hint (as a range)
        if 'population' in country and country['population']:
            pop = country['population']
            if pop < 1_000_000:
                hint = "less than 1 million people"
            elif pop < 10_000_000:
                hint = "between 1 and 10 million people"
            elif pop < 50_000_000:
                hint = "between 10 and 50 million people"
            elif pop < 100_000_000:
                hint = "between 50 and 100 million people"
            else:
                hint = "more than 100 million people"
            hints.append(f"The country has *{hint}*")
            
        # Neighbors hint - using our newly added neighbors data
        if 'neighbors' in country and country['neighbors']:
            import random
            neighbors = country['neighbors']
            
            # If we have too many neighbors, select 2-3 random ones
            if len(neighbors) > 3:
                selected_neighbors = random.sample(neighbors, min(3, len(neighbors)))
            else:
                selected_neighbors = neighbors
                
            if len(selected_neighbors) == 1:
                hints.append(f"This country borders *{selected_neighbors[0]}*")
            elif len(selected_neighbors) > 1:
                # Format as "borders X, Y, and Z"
                if len(selected_neighbors) == 2:
                    neighbor_text = f"*{selected_neighbors[0]}* and *{selected_neighbors[1]}*"
                else:
                    neighbor_text = ", ".join([f"*{n}*" for n in selected_neighbors[:-1]]) + f", and *{selected_neighbors[-1]}*"
                hints.append(f"This country borders {neighbor_text}")
                
            # Add a hint about the number of bordering countries
            if len(neighbors) > 0:
                count_description = ""
                if len(neighbors) == 0:
                    count_description = "no countries (it's an island)"
                elif len(neighbors) == 1:
                    count_description = "only 1 country"
                elif len(neighbors) <= 3:
                    count_description = "very few countries"
                elif len(neighbors) <= 6:
                    count_description = "several countries"
                elif len(neighbors) <= 10:
                    count_description = "many countries"
                else:
                    count_description = "a large number of countries"
                    
                hints.append(f"This country borders *{count_description}*")
                
        # Neighbor capitals hint - using our newly added neighbor capital cities data
        if 'neighbors_capital_city' in country and country['neighbors_capital_city'] and len(country['neighbors_capital_city']) > 0:
            import random
            neighbor_capitals = country['neighbors_capital_city']
            
            # Create a list of "Country (Capital)" pairs
            neighbor_capital_pairs = []
            for neighbor, capital in neighbor_capitals.items():
                if capital:  # Only add if capital is not empty
                    neighbor_capital_pairs.append(f"*{neighbor}* (capital: *{capital}*)")
            
            # If we have neighbor capitals to show
            if neighbor_capital_pairs:
                # If we have too many, select 1-2 random ones
                if len(neighbor_capital_pairs) > 2:
                    selected_pairs = random.sample(neighbor_capital_pairs, min(2, len(neighbor_capital_pairs)))
                else:
                    selected_pairs = neighbor_capital_pairs
                
                # Format the hint
                if len(selected_pairs) == 1:
                    hints.append(f"A neighboring country and its capital: {selected_pairs[0]}")
                elif len(selected_pairs) > 1:
                    pair_text = " and ".join(selected_pairs)
                    hints.append(f"Neighboring countries and their capitals: {pair_text}")
            
        # Select 2-3 random hints
        import random
        if hints:
            count = min(len(hints), random.randint(2, 3))
            return " • ".join(random.sample(hints, count))
        
        return "Sorry, no hints available for this country."
    
    def handle_continue_game(self, update: Update, context: CallbackContext):
        """Handle continue game button clicks"""
        query = update.callback_query
        query.answer()
        
        # Extract the game mode from callback data
        mode = query.data.replace("continue_", "")
        
        # Check if it's a special mode like leaderboard
        if mode == "lb":
            # Show leaderboard
            top_players = self.get_leaderboard(limit=10)
            
            if not top_players:
                query.message.reply_text("No players in the leaderboard yet. Use /game map to start.")
                return ConversationHandler.END
                
            # Create leaderboard message
            leaderboard_message = "🏆 *COUNTRY GUESS LEADERBOARD* 🏆\n\n"
            
            for i, (player_id, stats) in enumerate(top_players):
                # Get medal emoji for top 3
                medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1}."
                username = stats.get('username', 'Anonymous')
                correct = stats.get('correct_answers', 0)
                games = stats.get('games_played', 0)
                accuracy = correct / games * 100 if games > 0 else 0
                best_streak = stats.get('max_streak', 0)
                
                leaderboard_message += f"{medal} {username}: {correct} correct ({accuracy:.1f}%), {best_streak} best streak\n"
            
            query.message.reply_text(leaderboard_message, parse_mode="Markdown")
            return ConversationHandler.END
        else:
            # Start a new game with the selected mode
            return self.start_game(update, context, game_mode=mode)
        
    def start_command(self, update: Update, context: CallbackContext):
        """Entry point for the game command that properly delegates to other functions"""
        # Check if the command has arguments
        if not context.args:
            # No arguments, start a default game in map mode
            return self.start_game(update, context, game_mode="map")
            
        # Dispatch based on the first argument (subcommand)
        subcommand = context.args[0].lower()
        
        # Handle game mode subcommands
        if subcommand in ["map", "flag", "capital", "cap"]:
            # Convert "cap" to full "capital" mode
            game_mode = "capital" if subcommand == "cap" else subcommand
            return self.start_game(update, context, game_mode=game_mode)
            
        # Handle leaderboard command
        elif subcommand in ["lb", "leaderboard"]:
            top_players = self.get_leaderboard(limit=10)
            
            if not top_players:
                update.message.reply_text("No players in the leaderboard yet. Use /game map to start.")
                return ConversationHandler.END
                
            # Create leaderboard message
            leaderboard_message = "🏆 *COUNTRY GUESS LEADERBOARD* 🏆\n\n"
            
            for i, (player_id, stats) in enumerate(top_players):
                # Get medal emoji for top 3
                medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1}."
                username = stats.get('username', 'Anonymous')
                correct = stats.get('correct_answers', 0)
                games = stats.get('games_played', 0)
                accuracy = correct / games * 100 if games > 0 else 0
                best_streak = stats.get('max_streak', 0)
                
                leaderboard_message += f"{medal} {username}: {correct} correct ({accuracy:.1f}%), {best_streak} best streak\n"
            
            update.message.reply_text(leaderboard_message, parse_mode="Markdown")
            return ConversationHandler.END
            
        # Handle help command
        elif subcommand == "help":
            from config import HELP_MESSAGE
            update.message.reply_text(HELP_MESSAGE, parse_mode="Markdown")
            return ConversationHandler.END
            
        # Handle player stats command
        elif subcommand in ["me", "stats"]:
            user_id = update.effective_user.id
            user_stats = self.get_user_stats(user_id)
            
            if not user_stats:
                update.message.reply_text("You haven't played any games yet. Use /game map to start.")
                return ConversationHandler.END
                
            # Create stats message
            correct = user_stats.get('correct_answers', 0)
            games = user_stats.get('games_played', 0)
            accuracy = correct / games * 100 if games > 0 else 0
            current_streak = user_stats.get('current_streak', 0)
            best_streak = user_stats.get('max_streak', 0)
            
            stats_message = f"📊 *Your Statistics* 📊\n\n"
            stats_message += f"Games Played: {games}\n"
            stats_message += f"Correct Answers: {correct}\n"
            stats_message += f"Accuracy: {accuracy:.1f}%\n"
            stats_message += f"Current Streak: {current_streak}\n"
            stats_message += f"Best Streak: {best_streak}\n"
            
            update.message.reply_text(stats_message, parse_mode="Markdown")
            return ConversationHandler.END
            
        # Hint command has been removed
            
        # Unknown subcommand, default to map mode
        return self.start_game(update, context, game_mode="map")
    
    def get_conversation_handler(self):
        """Returns a ConversationHandler for the game"""
        from telegram.ext import CommandHandler, MessageHandler, CallbackQueryHandler, Filters
        
        # Create a conversation handler with per_message=False to avoid warnings
        return ConversationHandler(
            entry_points=[
                # Handle all game commands through our new start_command function
                CommandHandler(['game', 'g'], self.start_command, pass_args=True),
                # Handle continue game buttons from previous games
                CallbackQueryHandler(self.handle_continue_game, pattern="^continue_"),
            ],
            states={
                AWAITING_ANSWER: [
                    # Legacy text answer handler (kept for backward compatibility)
                    MessageHandler(Filters.text & ~Filters.command, self.handle_answer),
                    # Handle country selection buttons
                    CallbackQueryHandler(self.handle_button_answer, pattern="^answer_"),
                    # Handle give up button
                    CallbackQueryHandler(self.give_up, pattern="^give_up$"),
                    # Handle continue game buttons (in case user clicks after answering)
                    CallbackQueryHandler(self.handle_continue_game, pattern="^continue_")
                ]
            },
            fallbacks=[
                # Handle any command to start a new game as a fallback
                CommandHandler(['game', 'g'], self.start_command, pass_args=True)
            ],
            per_message=False  # Set to False to avoid the warning about callback handlers
        )
