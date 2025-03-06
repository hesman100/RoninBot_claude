# Country Game Configuration
import os

# Version information
BOT_VERSION = "1.0.2"

# Game modes
MAP_MODE = "map"
FLAG_MODE = "flag"
CAPITAL_MODE = "capital"

# File paths
DATABASE_PATH = os.path.join("country_game", "database", "countries.db")
MAP_IMAGES_PATH = os.path.join("country_game", "images", "wiki_all_map_400pi")
FLAG_IMAGES_PATH = os.path.join("country_game", "images", "wiki_flag")

# Game settings
MAX_ATTEMPTS = 3
LEADERBOARD_SIZE = 10
GAME_TIMEOUT = 30  # 30 seconds to answer
NUM_OPTIONS = 10  # Number of answer options to provide

# Message templates
CORRECT_ANSWER_MESSAGE = """✅ *Correct!* Well done!

*Country:* {}
*Capital:* {}
*Region:* {}
*Population:* {}
*Area:* {}"""

WRONG_ANSWER_MESSAGE = """❌ That's not correct. The correct answer was *{}*.

*Country:* {}
*Capital:* {}
*Region:* {}
*Population:* {}
*Area:* {}"""

TOO_MANY_ATTEMPTS_MESSAGE = "❌ Sorry, that's not correct. The country was *{}*."
NO_IMAGE_MESSAGE = "Sorry, I couldn't find a {} image for this country. Please try another game!"
INVALID_MODE_MESSAGE = "Invalid game mode. Use /g help for options."
TIMEOUT_MESSAGE = """⏱️ Time's up! The correct answer was *{}*.

*Country:* {}
*Capital:* {}
*Region:* {}
*Population:* {}
*Area:* {}"""

# Help text
HELP_TEXT = """
🌍 *Country Guessing Game Options* 🌍

*/g help* - Show this help message
*/g* or */g map* - Launch game in map mode (guess from a map)
*/g flag* - Launch game in flag mode (guess from a flag)
*/g capital* - Launch game in capital mode (guess from a capital city)
*/g cap* - Launch game in capital guessing mode (see a map, guess the capital)
*/g lb* - Show the leaderboard for all game modes

To play: simply tap on the correct option from the choices provided.
You have 30 seconds to answer each question.

Bot version: {}
""".format(BOT_VERSION)