import logging
import sys
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from config import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHANNEL_ID,
    DEFAULT_CRYPTOCURRENCIES,
    SYMBOL_TO_DISPLAY
)
from coinmarketcap_api import CoinMarketCapAPI
from utils import format_price_message, format_error_message

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log')
    ]
)
logger = logging.getLogger(__name__)

# Initialize CoinMarketCap API client
crypto_api = CoinMarketCapAPI()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    logger.info(f"Received /start command from chat {update.effective_chat.id}")

    is_group = update.effective_chat.type in ["group", "supergroup"]
    is_channel = update.effective_chat.type == "channel"

    if is_group:
        welcome_message = (
            "🤖 Welcome to the Crypto Price Bot!\n\n"
            "Group Chat Commands:\n"
            "/p <crypto> - Get price for any cryptocurrency\n"
            "              (Example: /p BTC or /p BNB)\n"
            "/p - Get prices for popular cryptocurrencies\n"
            "/help - Show this help message\n\n"
            "💡 Tip: Anyone in the group can use these commands!"
        )
    else:
        welcome_message = (
            "🤖 Welcome to the Crypto Price Bot!\n\n"
            "Available commands:\n"
            "/p <crypto> - Get price for any cryptocurrency\n"
            "              (Example: /p BTC, /p BNB)\n"
            "/p - Get prices for popular cryptocurrencies\n"
            "/help - Show this help message\n\n"
            "💡 To use in groups:\n"
            "1. Add me to your group\n"
            "2. Use commands like /p BTC\n\n"
            "💡 For channels:\n"
            "1. Add me as a channel admin\n"
            "2. Set up price updates using /setchannel"
        )

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=welcome_message
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
            logger.info(f"Received price data for coins: {list(price_data.keys()) if isinstance(price_data, dict) else 'error'}")
        else:
            # Get price for the specified cryptocurrency
            crypto_input = context.args[0].upper()
            logger.info(f"Fetching price for {crypto_input}")
            price_data = crypto_api.get_price(crypto_input)
            logger.info(f"Price data received: {price_data}")

        if not price_data or "error" in price_data:
            error_msg = (
                f"Could not find cryptocurrency: {context.args[0] if context.args else 'unknown'}\n\n"
                f"Try using the cryptocurrency's symbol (e.g., BTC, BNB)"
            )
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=error_msg
            )
            return

        message = format_price_message(price_data)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=message
        )

        # Only post to channel if explicitly configured and channel ID is valid
        if TELEGRAM_CHANNEL_ID and TELEGRAM_CHANNEL_ID.strip():
            try:
                logger.info(f"Attempting to post price update to channel {TELEGRAM_CHANNEL_ID}")
                await context.bot.send_message(
                    chat_id=TELEGRAM_CHANNEL_ID,
                    text=message
                )
                logger.info("Successfully posted to channel")
            except Exception as channel_error:
                logger.error(f"Failed to post to channel: {str(channel_error)}")
                # Don't send channel errors to users in groups/private chats
                pass

    except Exception as e:
        logger.error(f"Error in price command: {str(e)}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=format_error_message(e)
        )

async def health_check(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Periodic health check to ensure bot is running."""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"Health check - Bot is running at {current_time}")

def main() -> None:
    """Start the bot with error handling and health checks."""
    while True:
        try:
            logger.info("Starting the bot...")

            # Create the Application and pass it your bot's token
            application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

            # Add command handlers
            application.add_handler(CommandHandler("start", start))
            application.add_handler(CommandHandler("help", help_command))
            application.add_handler(CommandHandler("p", price))

            # Add periodic health check (every 30 minutes)
            application.job_queue.run_repeating(health_check, interval=1800)

            # Start the Bot
            logger.info("Bot is now running...")
            application.run_polling(allowed_updates=Update.ALL_TYPES)

        except Exception as e:
            logger.error(f"Bot crashed with error: {str(e)}")
            logger.info("Attempting to restart in 60 seconds...")
            import time
            time.sleep(60)  # Wait 60 seconds before restarting

if __name__ == '__main__':
    main()