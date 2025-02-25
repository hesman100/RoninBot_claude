import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from config import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHANNEL_ID,
    DEFAULT_CRYPTOCURRENCIES
)
from coingecko_api import CoinGeckoAPI
from utils import format_price_message, format_error_message

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize CoinGecko API client
coingecko = CoinGeckoAPI()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    welcome_message = (
        "🤖 Welcome to the Crypto Price Bot!\n\n"
        "Available commands:\n"
        "/price <crypto> - Get price for a specific cryptocurrency\n"
        "/prices - Get prices for popular cryptocurrencies\n"
        "/help - Show this help message"
    )
    await update.message.reply_text(welcome_message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await start(update, context)

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Get price for a specific cryptocurrency."""
    try:
        if not context.args:
            await update.message.reply_text("Please specify a cryptocurrency. Example: /price bitcoin")
            return

        crypto_id = context.args[0].lower()
        price_data = coingecko.get_price(crypto_id)

        if not price_data:
            await update.message.reply_text(f"Could not find cryptocurrency: {crypto_id}")
            return

        message = format_price_message(price_data)
        await update.message.reply_text(message)

        # Post to channel if channel ID is configured
        if TELEGRAM_CHANNEL_ID:
            await context.bot.send_message(
                chat_id=TELEGRAM_CHANNEL_ID,
                text=message
            )

    except Exception as e:
        logger.error(f"Error in price command: {str(e)}")
        await update.message.reply_text(format_error_message(e))

async def prices(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Get prices for multiple cryptocurrencies."""
    try:
        price_data = coingecko.get_prices(DEFAULT_CRYPTOCURRENCIES)
        message = format_price_message(price_data)
        await update.message.reply_text(message)

        # Post to channel if channel ID is configured
        if TELEGRAM_CHANNEL_ID:
            await context.bot.send_message(
                chat_id=TELEGRAM_CHANNEL_ID,
                text=message
            )

    except Exception as e:
        logger.error(f"Error in prices command: {str(e)}")
        await update.message.reply_text(format_error_message(e))

def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("price", price))
    application.add_handler(CommandHandler("prices", prices))

    # Start the Bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()