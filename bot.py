import logging
import sys
import os
import fcntl
import time
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
from price_func.config import (TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID,
                               DEFAULT_CRYPTOCURRENCIES, DEFAULT_STOCKS,
                               DEFAULT_VN_STOCKS, SYMBOL_TO_DISPLAY)
from price_func.coinmarketcap_api import CoinMarketCapAPI
from price_func.utils import format_price_message, format_error_message
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from price_func.alphavantage_api import AlphaVantageAPI
from price_func.finnhub_api import FinnhubAPI
from price_func.vietnam_stock_api import VietnamStockAPI
import time

# Add this import for the game handler
from country_game.game_handler import GameHandler

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log')
    ])
logger = logging.getLogger(__name__)

# Initialize API clients with proper error handling
try:
    crypto_api = CoinMarketCapAPI()
    stock_api = AlphaVantageAPI()
    finnhub_api = FinnhubAPI()
    vietnam_stock_api = VietnamStockAPI()
except Exception as e:
    logger.error(f"Failed to initialize API clients: {str(e)}")
    raise

# Fixed import issues for telegram and telegram.ext
try:
    from telegram import Update
    from telegram.ext import Application, CommandHandler, ContextTypes
except ImportError:
    # Add error handling for missing telegram package
    print("Error: python-telegram-bot package not found. Installing...")
    import subprocess
    subprocess.check_call(["pip", "install", "python-telegram-bot"])
    from telegram import Update
    from telegram.ext import Application, CommandHandler, ContextTypes


# Fix HTTPServer bot_running attribute
class HealthCheckHandler(BaseHTTPRequestHandler):

    def _send_response(self, status_code, message):
        self.send_response(status_code)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(message.encode())

    def do_GET(self):
        try:
            if self.path == '/':
                self._send_response(200, "Telegram Bot Service")
                logger.info("Root path accessed")
            elif self.path == '/health':
                # Check if server has bot_running attribute
                bot_running = getattr(self.server, 'bot_running', False)
                if bot_running:
                    self._send_response(200, "Bot is running")
                    logger.info("Health check succeeded")
                else:
                    self._send_response(503, "Bot is starting")
                    logger.warning("Health check failed - bot not ready")
            elif self.path == '/shutdown':
                logger.info("Shutdown request received")
                self._send_response(200, "Shutting down...")
                # Schedule the shutdown after responding
                threading.Thread(target=lambda: [
                    logger.info("Initiating shutdown sequence"),
                    setattr(self.server, 'bot_running', False),
                    self.server.shutdown(),
                    sys.exit(0)
                ]).start()
            else:
                self._send_response(404, "Not found")
        except Exception as e:
            logger.error(f"Health check error: {str(e)}")
            self._send_response(500, "Internal server error")

    def do_HEAD(self):
        self.do_GET()


def run_http_server():
    """Run HTTP server for health checks"""
    try:
        # Use PORT from environment for Autoscale compatibility
        port = int(os.environ.get('PORT', 5000))
        server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
        server.bot_running = True
        logger.info(f"Starting HTTP server on port {port}")
        server.serve_forever()
    except Exception as e:
        logger.error(f"Failed to start HTTP server: {str(e)}")
        raise


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    logger.info(
        f"Received /start command from chat {update.effective_chat.id}")

    is_group = update.effective_chat.type in ["group", "supergroup"]
    is_channel = update.effective_chat.type == "channel"

    if is_group:
        welcome_message = (
            "🤖 Welcome to the Ronin Bot (v1.3)!\n\n"
            "/help or /h - Show this help message\n\n"
            "\n ==== Price ==== \n"
            "/c <crypto> - Get price for any cryptocurrency\n"
            "              (Example: /c BTC or /c BNB)\n"
            "/c - Get prices for popular cryptocurrencies\n"
            "/s <stock> - Get price for any stock\n"
            "              (Example: /s AAPL or /s TSLA)\n"
            "/s - Get prices for popular stocks\n"
            "/vn <stock> - Get Vietnam stock price\n"
            "              (Example: /vn VNM or /vn HPG)\n"
            "/vn - Get prices for popular Vietnam stocks\n"
            "\n ==== Game ==== \n"
            "/g <option> - Play country guessing game\n"
            "               (Example: /g map, /g flag, /g capital)\n"
            "/g lb       - View country game leaderboard\n"
            "/g help     - More detail game options\n"
            "\n ====  ==== \n"
            "💡 Tip: Anyone in the group can use these commands!")
    else:
        welcome_message = (
            "🤖 Welcome to the Ronin Bot (v1.3)!\n\n"
            "\n ==== Price ==== \n"
            "/c <crypto> - Get price for any cryptocurrency\n"
            "              (Example: /c BTC, /c BNB)\n"
            "/c - Get prices for popular cryptocurrencies\n"
            "/s <stock> - Get price for any stock\n"
            "              (Example: /s AAPL, /s TSLA)\n"
            "/s - Get prices for popular stocks\n"
            "/vn <stock> - Get Vietnam stock price\n"
            "              (Example: /vn VNM or /vn HPG)\n"
            "/vn - Get prices for popular Vietnam stocks\n"
            "\n ==== Game ==== \n"
            "/g <option> - Play country guessing game\n"
            "              (Example: /g map, /g flag, /g capital)\n"
            "/g lb       - View country game leaderboard\n"
            "/g help     - More detail game options\n"
            "\n ====  ==== \n"
            "/help or /h - Show this help message\n\n"
            "💡 To use in groups:\n"
            "1. Add me to your group\n"
            "2. Use commands like /c BTC or /s AAPL\n\n"
            "💡 For channels:\n"
            "1. Add me as a channel admin\n"
            "2. Set up price updates using /setchannel")

    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text=welcome_message)


async def help_command(update: Update,
                       context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    logger.info(f"Received /help command from chat {update.effective_chat.id}")
    await start(update, context)


async def price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Get price for a specific cryptocurrency."""
    logger.info(f"Received /p command from chat {update.effective_chat.id}")
    try:
        if not context.args:
            # If no arguments, show all default cryptocurrencies
            logger.info("No cryptocurrency specified, showing default list")
            price_data = crypto_api.get_prices()
            logger.info(
                f"Received price data for coins: {list(price_data.keys()) if isinstance(price_data, dict) else 'error'}"
            )
        else:
            # Get price for the specified cryptocurrency
            crypto_input = context.args[0].upper()
            logger.info(f"Fetching price for {crypto_input}")
            price_data = crypto_api.get_price(crypto_input)
            logger.info(f"Price data received: {price_data}")

        if not price_data or "error" in price_data:
            error_msg = (
                f"Could not find cryptocurrency: {context.args[0] if context.args else 'unknown'}\n\n"
                f"Try using the cryptocurrency's symbol (e.g., BTC, BNB)")
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text=error_msg)
            return

        message = format_price_message(price_data)
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=message)

        # Only post to channel if explicitly configured and channel ID is valid
        if TELEGRAM_CHANNEL_ID and TELEGRAM_CHANNEL_ID.strip():
            try:
                logger.info(
                    f"Attempting to post price update to channel {TELEGRAM_CHANNEL_ID}"
                )
                await context.bot.send_message(chat_id=TELEGRAM_CHANNEL_ID,
                                               text=message)
                logger.info("Successfully posted to channel")
            except Exception as channel_error:
                logger.error(
                    f"Failed to post to channel: {str(channel_error)}")
                # Don't send channel errors to users in groups/private chats
                pass

    except Exception as e:
        logger.error(f"Error in price command: {str(e)}")
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=format_error_message(e))


async def stock(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Get price for a specific stock or default list of stocks."""
    logger.info(f"Received /s command from chat {update.effective_chat.id}")
    try:
        if not context.args:
            # If no arguments, show all default stocks
            logger.info("No stock specified, showing default list")
            price_data = stock_api.get_stock_prices()

            # Check if we need to use the fallback API by verifying:
            # 1. If there's a specific rate limit error message
            # 2. If we received fewer stocks than expected
            is_rate_limited = (isinstance(price_data, dict)
                               and "error" in price_data
                               and "rate limit" in price_data["error"].lower())

            # If the data isn't empty, check if we have fewer stocks than expected
            has_incomplete_data = (isinstance(price_data, dict) and len(
                price_data.keys()) < len(DEFAULT_STOCKS) / 2)

            if is_rate_limited or has_incomplete_data:
                logger.info(
                    f"AlphaVantage returned incomplete data ({len(price_data.keys()) if isinstance(price_data, dict) else 0} stocks) or is rate limited, falling back to Finnhub"
                )
                finnhub_data = finnhub_api.get_stock_prices()

                # If Finnhub data is valid, use it
                if isinstance(finnhub_data,
                              dict) and "error" not in finnhub_data:
                    logger.info(
                        f"Using Finnhub data with {len(finnhub_data.keys())} stocks"
                    )
                    price_data = finnhub_data
                else:
                    # If both APIs failed, combine any valid data we have
                    logger.warning(
                        "Both AlphaVantage and Finnhub had issues, using any available data"
                    )
                    if isinstance(price_data, dict) and isinstance(
                            finnhub_data, dict):
                        # Combine data from both sources
                        for symbol, data in finnhub_data.items():
                            if "error" not in data:
                                price_data[symbol] = data

            logger.info(f"Received price data: {price_data}")
        else:
            # Get price for the specified stock
            stock_input = context.args[0].upper()
            logger.info(f"Fetching price for {stock_input}")
            price_data = stock_api.get_stock_price(stock_input)

            # If AlphaVantage fails or hits rate limit, try Finnhub
            if isinstance(
                    price_data, dict
            ) and "error" in price_data and "rate limit" in price_data[
                    "error"].lower():
                logger.info(
                    "AlphaVantage rate limited, falling back to Finnhub")
                price_data = finnhub_api.get_stock_price(stock_input)

            logger.info(f"Price data received: {price_data}")

        if isinstance(price_data, dict) and "error" in price_data:
            error_msg = price_data["error"]
            if "rate limit" in error_msg.lower():
                error_msg = "⚠️ API rate limit reached\nPlease try again in a few minutes."
            else:
                error_msg = (
                    f"Could not find stock{': ' + context.args[0] if context.args else ''}\n\n"
                    f"Try using the stock symbol (e.g., AAPL, TSLA)")
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text=error_msg)
            return

        message = format_price_message(price_data)
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=message)

    except Exception as e:
        logger.error(f"Error in stock command: {str(e)}")
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=format_error_message(e))


async def vietnam_stock(update: Update,
                        context: ContextTypes.DEFAULT_TYPE) -> None:
    """Get price for a specific Vietnam stock or default list of Vietnam stocks."""
    logger.info(f"Received /vn command from chat {update.effective_chat.id}")
    try:
        if not context.args:
            # If no arguments, show all default Vietnam stocks
            logger.info(
                "No stock specified, showing default Vietnam stock list")
            price_data = vietnam_stock_api.get_stock_prices(DEFAULT_VN_STOCKS)
            logger.info(
                f"Received price data for Vietnam stocks: {list(price_data.keys()) if isinstance(price_data, dict) else 'error'}"
            )
        else:
            # Get price for the specified stock
            stock_input = context.args[0].upper()
            logger.info(f"Fetching price for Vietnam stock: {stock_input}")
            price_data = vietnam_stock_api.get_stock_price(stock_input)
            logger.info(f"Received price data: {price_data}")

        if isinstance(price_data, dict) and "error" in price_data:
            error_msg = (
                f"Could not find Vietnam stock{': ' + context.args[0] if context.args else ''}\n\n"
                f"Try using the stock symbol (e.g., VNM, HPG)")
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text=error_msg)
            return

        message = format_price_message(price_data)
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=message)

    except Exception as e:
        logger.error(f"Error in vietnam_stock command: {str(e)}")
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=format_error_message(e))


async def health_check(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Periodic health check to ensure bot is running."""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"Health check - Bot is running at {current_time}")


async def backup_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Backup the leaderboard data to a JSON file"""
    # Admin check - replace this with your actual Telegram user ID
    # To get your ID, talk to @userinfobot on Telegram
    admin_ids = []  # Replace with your Telegram user ID

    # If admin_ids is empty, allow anyone to use this command (for testing)
    if not admin_ids:
        logger.warning("No admin IDs configured for backup command - allowing all users")
    elif update.effective_user.id not in admin_ids:
        await update.message.reply_text("Sorry, only admins can use this command.")
        return

    from country_game import leaderboard_db

    # Default backup path
    backup_path = "country_game/database/leaderboard_backup.json"

    # If an argument was provided, use it as the backup path
    if context.args:
        backup_path = context.args[0]

    # Perform the backup
    success = leaderboard_db.export_leaderboard_to_json(backup_path)

    if success:
        await update.message.reply_text(f"✅ Leaderboard data successfully backed up to {backup_path}")
    else:
        await update.message.reply_text("❌ Failed to backup leaderboard data. Check logs for details.")


async def restore_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Restore the leaderboard data from a JSON file"""
    # Admin check - replace this with your actual Telegram user ID
    # To get your ID, talk to @userinfobot on Telegram
    admin_ids = []  # Replace with your Telegram user ID

    # If admin_ids is empty, allow anyone to use this command (for testing)
    if not admin_ids:
        logger.warning("No admin IDs configured for restore command - allowing all users")
    elif update.effective_user.id not in admin_ids:
        await update.message.reply_text("Sorry, only admins can use this command.")
        return

    from country_game import leaderboard_db

    # Default backup path
    backup_path = "country_game/database/leaderboard_backup.json"

    # If an argument was provided, use it as the backup path
    if context.args:
        backup_path = context.args[0]

    # Perform the restore
    success = leaderboard_db.import_leaderboard_from_json(backup_path)

    if success:
        await update.message.reply_text(f"✅ Leaderboard data successfully restored from {backup_path}")
    else:
        await update.message.reply_text("❌ Failed to restore leaderboard data. Check logs for details.")


async def game_command(update: Update,
                       context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all /g commands with subcommands"""
    # If we haven't initialized the game handler yet, do it now
    if 'game_handler' not in context.bot_data:
        context.bot_data['game_handler'] = GameHandler()

    game_handler = context.bot_data['game_handler']

    # If no arguments provided, default to map mode
    if not context.args:
        await game_handler.start_game(update, context, game_mode="map")
        return

    # Handle specific subcommands
    subcommand = context.args[0].lower()

    if subcommand == "help":
        await game_handler.help_command(update, context)
    elif subcommand in ["map", "flag", "capital",
                        "cap"]:  # Added "cap" to the list of valid subcommands
        await game_handler.start_game(update, context, game_mode=subcommand)
    elif subcommand in ["lb", "leaderboard"
                        ]:  # Added "lb" and "leaderboard" as valid subcommands
        await game_handler.show_leaderboard(update, context)
    else:
        # Unknown subcommand, show help
        await update.message.reply_text(
            f"Unknown game option: {subcommand}. Try /g help for available options."
        )


async def handle_message(update: Update,
                         context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text messages for both the existing bot functionality and the game answers"""
    # First, check if the user has an active game
    if 'game_handler' in context.bot_data:
        game_handler = context.bot_data['game_handler']
        user_id = update.effective_user.id

        # If user has an active game, process their answer
        if user_id in game_handler.active_games:
            await game_handler.handle_answer(update, context)
            return

    # If we get here, there's no active game, so this might be a command
    # that's missing the "/" prefix or some other message
    # Your existing message handler code can go here


async def handle_callback_query(update: Update,
                                context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles callback queries from inline keyboards."""
    query = update.callback_query
    await query.answer()  # Acknowledge the callback query

    if 'game_handler' in context.bot_data:
        game_handler = context.bot_data['game_handler']
        await game_handler.handle_callback_query(update, context)


# File lock to ensure only one instance runs
def acquire_lock():
    """Try to acquire a file lock to ensure only one instance runs"""
    lock_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             'bot.lock')
    lock_fd = open(lock_file, 'w')

    try:
        # Try to acquire an exclusive lock (non-blocking)
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        logger.info(
            "Successfully acquired lock. This is the only running instance.")
        return lock_fd
    except IOError:
        logger.error("Another instance is already running. Exiting.")
        sys.exit(1)


def main() -> None:
    """Start the bot with error handling and health checks."""
    # Ensure only one instance runs
    lock_fd = acquire_lock()

    # Start HTTP server in a separate thread for Autoscale health checks
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()
    logger.info("HTTP server thread started")

    while True:
        try:
            logger.info("Starting the bot...")

            # Create the Application and pass it your bot's token
            application = Application.builder().token(
                TELEGRAM_BOT_TOKEN).build()

            # Add command handlers
            application.add_handler(CommandHandler("start", start))
            application.add_handler(CommandHandler("help", help_command))
            application.add_handler(CommandHandler("h", help_command))
            application.add_handler(CommandHandler("c", price))
            application.add_handler(CommandHandler("s", stock))
            application.add_handler(CommandHandler("vn", vietnam_stock))

            # Add the game command handlers
            application.add_handler(CommandHandler("g", game_command))

            # Add backup and restore leaderboard commands
            application.add_handler(CommandHandler("backup_lb", backup_leaderboard))
            application.add_handler(CommandHandler("restore_lb", restore_leaderboard))

            # Add a callback query handler for the game buttons
            application.add_handler(
                CallbackQueryHandler(
                    lambda update, context: context.bot_data[
                        'game_handler'].handle_callback_query(update, context),
                    pattern=
                    "^(guess_|play_|show_leaderboard)"
                ))

            logger.info("Game callback handler registered")

            # Add a message handler to process game answers and other messages
            application.add_handler(
                MessageHandler(filters.TEXT & ~filters.COMMAND,
                               handle_message))

            # Add periodic health check (every 30 minutes)
            application.job_queue.run_repeating(health_check, interval=1800)

            # Start the Bot with error recovery
            logger.info("Bot is now running...")
            application.run_polling(allowed_updates=Update.ALL_TYPES,
                                    drop_pending_updates=True,
                                    close_loop=False)

        except Exception as e:
            logger.error(f"Bot crashed with error: {str(e)}")
            logger.info("Attempting to restart in 60 seconds...")
            time.sleep(60)  # Wait before restarting


if __name__ == '__main__':
    main()