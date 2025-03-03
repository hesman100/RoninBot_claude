import logging
import os
from telegram import Update
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackContext,
    MessageHandler,
    Filters,
)
from config import TELEGRAM_TOKEN, START_MESSAGE, HELP_MESSAGE
from game_handler import GameHandler
from country_database import get_database

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def start(update: Update, context: CallbackContext):
    """Send a message when the command /start is issued."""
    update.message.reply_text(START_MESSAGE)

def game_command(update: Update, context: CallbackContext):
    """Handle all /game commands with subcommands"""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    game_handler = context.bot_data.get('game_handler')
    
    if not game_handler:
        update.message.reply_text("Game is not available right now.")
        return
    
    # Process subcommands
    if not context.args:
        # Default to "map" mode when no args are provided
        game_handler.start_game(update, context, game_mode="map")
        return
        
    subcommand = context.args[0].lower()
    
    # Handle different subcommands
    if subcommand in ["map", "flag", "capital", "cap"]:
        # Game modes
        # Convert "cap" to full "capital" mode
        game_mode = "capital" if subcommand == "cap" else subcommand
        game_handler.start_game(update, context, game_mode=game_mode)
        return
        
    elif subcommand == "clearcache":
        # Force refresh the country database (admin function)
        country_database = context.bot_data.get('country_database')
        if country_database:
            try:
                country_database.refresh_database(force=True)
                update.message.reply_text("Country database refreshed with new data.")
            except Exception as e:
                logger.error(f"Error refreshing database: {e}")
                update.message.reply_text(f"Error refreshing database: {str(e)}")
        else:
            update.message.reply_text("Country database not available.")
        return
    
    elif subcommand in ["lb", "leaderboard"]:
        # Show leaderboard
        top_players = game_handler.get_leaderboard(limit=10)
        
        if not top_players:
            update.message.reply_text("No players in the leaderboard yet. Use /game map to start.")
            return
            
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
        return
        
    # Hint command has been removed
        
    elif subcommand == "help":
        # Show help message
        update.message.reply_text(HELP_MESSAGE, parse_mode="Markdown")
        return
        
    elif subcommand in ["me", "stats"]:
        # Show user stats
        user_stats = game_handler.get_user_stats(user_id)
        
        if not user_stats or user_stats.get('games_played', 0) == 0:
            update.message.reply_text("You haven't played any games yet. Use /game map to start.")
            return
            
        # Create detailed stats message
        stats_message = (
            "📊 *Your Country Guess Stats* 📊\n\n"
            f"🎮 Games Played: {user_stats.get('games_played', 0)}\n"
            f"✅ Correct Answers: {user_stats.get('correct_answers', 0)}\n"
            f"❌ Incorrect Answers: {user_stats.get('incorrect_answers', 0)}\n"
            f"⏱️ Timeouts: {user_stats.get('timeout_answers', 0)}\n"
            f"🏳️ Gave Up: {user_stats.get('gave_up', 0)}\n"
            f"🔥 Current Streak: {user_stats.get('streak', 0)}\n"
            f"🏆 Best Streak: {user_stats.get('max_streak', 0)}\n\n"
            f"💯 Accuracy: {user_stats.get('correct_answers', 0) / user_stats.get('games_played', 1) * 100:.1f}%"
        )
        
        update.message.reply_text(stats_message, parse_mode="Markdown")
        return
        
    else:
        # Unknown subcommand
        update.message.reply_text(
            "Unknown command. Available options:\n"
            "/game map - Start a regular map game\n"
            "/game flag - Start a flag identification game\n"
            "/game cap - Start a capital city guessing game\n"
            "/game lb - View leaderboard\n"
            "/game me - View your stats\n"
            "/game help - Show help menu"
        )
        return

def reset_leaderboard(update: Update, context: CallbackContext):
    """Reset the leaderboard stats (admin only)"""
    # Get game handler from context
    game_handler = context.bot_data.get('game_handler')
    if not game_handler:
        update.message.reply_text("Game system is not available right now.")
        return
    
    # Only allow admin to reset
    if update.effective_user.id == 396254641:  # Replace with your actual admin user ID
        game_handler.user_stats = {}
        game_handler._save_stats()
        update.message.reply_text("🏆 The leaderboard has been reset! All player stats have been cleared.")
    else:
        update.message.reply_text("⛔ Sorry, only the administrator can reset the leaderboard.")

def main():
    """Start the bot."""
    # Check if we're using a dummy token
    if TELEGRAM_TOKEN == "1234567890:ABCdefGhIJKlmnOPQRstUVwxYZ":
        logger.warning("Using dummy Telegram token. To run a real bot, please:")
        logger.warning("1. Create a bot with @BotFather on Telegram")
        logger.warning("2. Get the token from BotFather")
        logger.warning("3. Set the TELEGRAM_TOKEN environment variable")
        logger.warning("Running in test mode with limited functionality...")
        
        # For development purposes, let's simulate a bot running without connecting to Telegram API
        simulate_development_mode()
        return
        
    try:
        # Create the Updater and pass it your bot's token
        updater = Updater(TELEGRAM_TOKEN)
        
        # Get the dispatcher to register handlers
        dispatcher = updater.dispatcher
        
        # Initialize the country database
        country_database = get_database()
        
        # Create the game handler with the country database
        game_handler = GameHandler()
        
        # Store game handler and country database in bot_data for access from command handlers
        dispatcher.bot_data['game_handler'] = game_handler
        dispatcher.bot_data['country_database'] = country_database

        # Add game conversation handler first (higher priority)
        dispatcher.add_handler(game_handler.get_conversation_handler())
        
        # Register other command handlers
        dispatcher.add_handler(CommandHandler("start", start))
        dispatcher.add_handler(CommandHandler("game", game_command, pass_args=True))
        # Add short command /g as an alias to /game
        dispatcher.add_handler(CommandHandler("g", game_command, pass_args=True))
        # Add admin command to reset leaderboard
        dispatcher.add_handler(CommandHandler("reset_leaderboard", reset_leaderboard))
        
        # Add handler for direct messages (not commands)
        dispatcher.add_handler(MessageHandler(
            Filters.text & ~Filters.command & ~Filters.update.edited_message, 
            game_handler.handle_text_message
        ))
        
        # Start the bot
        updater.start_polling()
        logger.info("Bot started successfully!")
        
        # Run the bot until you press Ctrl-C
        updater.idle()
    except Exception as e:
        logger.error(f"Error starting the bot: {e}")
        if "Invalid token" in str(e) or "Unauthorized" in str(e):
            logger.error("Please provide a valid Telegram token")
            logger.error("1. Create a bot with @BotFather on Telegram")
            logger.error("2. Get the token from BotFather")
            logger.error("3. Set the TELEGRAM_TOKEN environment variable")
        else:
            logger.error("Check your internet connection and configuration")
        
        # When in doubt, run in development mode
        simulate_development_mode()

def simulate_development_mode():
    """Run a simulated version of the bot for development purposes"""
    logger.info("Starting in DEVELOPMENT MODE (simulated interaction)")
    logger.info("In this mode, the bot does not connect to the Telegram API")
    logger.info("This is only for testing the code structure and logic")
    
    # Initialize the country database
    country_database = get_database()
    
    # Create the game handler to make sure it initializes properly
    game_handler = GameHandler()
    
    # Test if we can fetch countries
    random_country = country_database.get_random_country()
    logger.info(f"Successfully loaded example country: {random_country['name']['common']}")
    
    # Test map URL generation
    map_url = country_database.get_map_url(random_country)
    logger.info(f"Example map URL: {map_url}")
    
    # Show instructions for setting up the real bot
    logger.info("")
    logger.info("To run this bot with Telegram:")
    logger.info("1. Create a new bot with @BotFather on Telegram")
    logger.info("2. Get the API token from BotFather")
    logger.info("3. Set the TELEGRAM_TOKEN environment variable")
    logger.info("4. For map functionality, get an API key from https://www.geoapify.com/")
    logger.info("5. Set the GEOAPIFY_API_KEY environment variable")
    
    logger.info("")
    logger.info("Development mode simulation completed. Exiting.")

if __name__ == '__main__':
    main()
