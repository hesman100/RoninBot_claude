import os
import random
import sqlite3
import logging
from typing import Dict, List, Optional, Tuple
from telegram import Update
from telegram.ext import ContextTypes

# Set up logging
logger = logging.getLogger(__name__)

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

    def load_countries(self) -> List[Dict]:
        """Load countries from database or fall back to sample data"""
        try:
            # Try to open the SQLite database
            db_path = os.path.join("database", "countries.db")
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                cur = conn.cursor()
                # Check if countries table exists
                cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='countries'")
                if cur.fetchone():
                    # Get countries with their data
                    cur.execute("SELECT name, capital FROM countries")
                    rows = cur.fetchall()
                    conn.close()

                    # Return a list of dictionaries with country info
                    countries = []
                    for row in rows:
                        if row[0]:  # Ensure country name exists
                            countries.append({
                                "name": row[0],
                                "capital": row[1] if row[1] else "Unknown"
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
        """Return sample country data as fallback"""
        # This is a small sample. In production, you might want more countries.
        return [
            {"name": "United_States", "capital": "Washington, D.C."},
            {"name": "France", "capital": "Paris"},
            {"name": "Germany", "capital": "Berlin"},
            {"name": "Brazil", "capital": "Brasilia"},
            {"name": "Japan", "capital": "Tokyo"},
            {"name": "Australia", "capital": "Canberra"},
            {"name": "China", "capital": "Beijing"},
            {"name": "Russia", "capital": "Moscow"},
            {"name": "Egypt", "capital": "Cairo"},
            {"name": "South_Africa", "capital": "Pretoria"}
        ]

    def get_random_country(self) -> Dict:
        """Return a random country from the loaded countries"""
        return random.choice(self.countries)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Display help information for the game"""
        help_text = (
            "🌍 *Country Guessing Game Options* 🌍\n\n"
            "*/g help* - Show this help message\n"
            "*/g* or */g map* - Launch game in map mode (guess from a map)\n"
            "*/g flag* - Launch game in flag mode (guess from a flag)\n"
            "*/g capital* - Launch game in capital mode (guess from a capital city)\n\n"
            "To play: simply reply with the name of the country after seeing the image or hint."
        )
        await update.message.reply_text(help_text, parse_mode="Markdown")

    async def start_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE, game_mode: str) -> None:
        """Start a new game in the specified mode"""
        user_id = update.effective_user.id
        country = self.get_random_country()

        # Store game state
        self.active_games[user_id] = {
            "country": country,
            "mode": game_mode,
            "attempts": 0
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

    async def _send_map_challenge(self, update: Update, context: ContextTypes.DEFAULT_TYPE, country: Dict) -> None:
        """Send a map challenge to the user"""
        country_name = country["name"]
        image_path = os.path.join("wiki_all_map_400pi", f"{country_name}_locator_map.png")

        try:
            with open(image_path, "rb") as photo_file:
                caption = "🗺️ *Guess the country from this map!*"
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=photo_file,
                    caption=caption,
                    parse_mode="Markdown"
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
        """Send a flag challenge to the user"""
        country_name = country["name"]
        image_path = os.path.join("wiki_flag", f"{country_name}_flag.png")

        try:
            with open(image_path, "rb") as photo_file:
                caption = "🏳️ *Guess the country from this flag!*"
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=photo_file,
                    caption=caption,
                    parse_mode="Markdown"
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
        """Send a capital challenge to the user"""
        capital = country.get("capital", "Unknown")
        message = f"🏙️ *Guess the country whose capital is:* {capital}"
        await update.message.reply_text(message, parse_mode="Markdown")

    async def handle_answer(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle a user's answer to a game challenge"""
        user_id = update.effective_user.id

        # Check if user has an active game
        if user_id not in self.active_games:
            return

        # Get the active game
        game = self.active_games[user_id]
        correct_country = game["country"]["name"].replace("_", " ")
        user_answer = update.message.text.strip()

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

            # Update stats (to be implemented)
            self._update_user_stats(user_id, True)

            # Clean up
            del self.active_games[user_id]
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