import logging
import sys
import os
import time
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from price_func.config import (TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID,
                               DEFAULT_CRYPTOCURRENCIES, DEFAULT_STOCKS)
from price_func.coinmarketcap_api import CoinMarketCapAPI
from price_func.alphavantage_api import AlphaVantageAPI
from price_func.finnhub_api import FinnhubAPI
from price_func.utils import format_price_message, format_error_message

BOT_VER = "1.7"

_log_handlers = [logging.StreamHandler(sys.stdout)]
try:
    _log_handlers.append(logging.FileHandler('bot.log'))
except PermissionError:
    pass

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=_log_handlers)
logger = logging.getLogger(__name__)

try:
    crypto_api = CoinMarketCapAPI()
    stock_api = AlphaVantageAPI()
    finnhub_api = FinnhubAPI()
except Exception as e:
    logger.error(f"Failed to initialize API clients: {str(e)}")
    raise


async def price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Get price for a specific cryptocurrency."""
    logger.info(f"Received /c command from chat {update.effective_chat.id}")
    try:
        if not context.args:
            logger.info("No cryptocurrency specified, showing default list")
            price_data = crypto_api.get_prices()
        else:
            crypto_input = context.args[0].upper()
            logger.info(f"Fetching price for {crypto_input}")
            price_data = crypto_api.get_price(crypto_input)

        if not price_data or "error" in price_data:
            error_msg = (
                f"Could not find cryptocurrency: {context.args[0] if context.args else 'unknown'}\n\n"
                f"Try using the cryptocurrency's symbol (e.g., BTC, BNB)")
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text=error_msg)
            return

        message = format_price_message(price_data)
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=message,
                                       parse_mode="Markdown")

        if TELEGRAM_CHANNEL_ID and TELEGRAM_CHANNEL_ID.strip():
            try:
                await context.bot.send_message(chat_id=TELEGRAM_CHANNEL_ID,
                                               text=message,
                                               parse_mode="Markdown")
            except Exception as channel_error:
                logger.error(f"Failed to post to channel: {str(channel_error)}")

    except Exception as e:
        logger.error(f"Error in price command: {str(e)}")
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=format_error_message(e))


async def stock(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Get price for a specific stock or default list of stocks."""
    logger.info(f"Received /s command from chat {update.effective_chat.id}")
    try:
        if not context.args:
            logger.info("No stock specified, showing default list")
            start_time = time.time()
            price_data = finnhub_api.get_stock_prices()
            logger.info(f"Finnhub API response time: {time.time() - start_time:.2f} seconds")

            if isinstance(price_data, dict) and "error" in price_data:
                logger.info("Finnhub API failed, falling back to AlphaVantage")
                start_time = time.time()
                alpha_data = stock_api.get_stock_prices()
                logger.info(f"AlphaVantage API response time: {time.time() - start_time:.2f} seconds")

                if isinstance(alpha_data, dict) and "error" not in alpha_data:
                    price_data = alpha_data
                else:
                    logger.warning("Both Finnhub and AlphaVantage had issues, using any available data")
                    if isinstance(alpha_data, dict) and isinstance(price_data, dict):
                        for symbol, data in alpha_data.items():
                            if "error" not in data and symbol not in price_data:
                                price_data[symbol] = data
        else:
            stock_input = context.args[0].upper()
            logger.info(f"Fetching price for {stock_input}")
            start_time = time.time()
            price_data = finnhub_api.get_stock_price(stock_input)
            logger.info(f"Finnhub API response time: {time.time() - start_time:.2f} seconds")

            if isinstance(price_data, dict) and "error" in price_data:
                logger.info(f"Finnhub failed for {stock_input}, trying AlphaVantage")
                start_time = time.time()
                price_data = stock_api.get_stock_price(stock_input)
                logger.info(f"AlphaVantage API response time: {time.time() - start_time:.2f} seconds")

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
                                       text=message,
                                       parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error in stock command: {str(e)}")
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=format_error_message(e))


def main() -> None:
    """Start the bot."""
    while True:
        try:
            logger.info("Starting the bot...")
            application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

            application.add_handler(CommandHandler("c", price))
            application.add_handler(CommandHandler("s", stock))

            logger.info("Bot is now running...")
            application.run_polling(allowed_updates=Update.ALL_TYPES,
                                    drop_pending_updates=True,
                                    close_loop=False)

        except Exception as e:
            logger.error(f"Bot crashed with error: {str(e)}")
            logger.info("Attempting to restart in 60 seconds...")
            time.sleep(60)


if __name__ == '__main__':
    main()
