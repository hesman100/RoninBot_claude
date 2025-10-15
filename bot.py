import logging
import sys
import os
import fcntl
import time
import random
import psycopg2
from datetime import datetime, timezone, timedelta
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

BOT_VER = "1.7"

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
        welcome_message = (f"🤖 Welcome to the Ronin Bot (v{BOT_VER})!\n\n"
                           "/help or /h - Show this help message\n\n"
                           "\n ==== Price ==== \n"
                           "/c <crypto> - Get price for any cryptocurrency\n"
                           "              (Example: /c BTC or /c BNB)\n"
                           "/c - Get prices for popular cryptocurrencies\n"
                           "/s <stock> - Get price for any stock\n"
                           "              (Example: /s AAPL or /s TSLA)\n"
                           "/s - Get prices for popular stocks\n\n"
                           "\n ==== Quotes ==== \n"
                           "/q - Get a random inspirational quote\n"
                           "/q <number> - Get a specific quote by ID\n"
                           "/q <name> - Search quotes by author\n"
                           "              (Example: /q Einstein)\n\n"
                           "\n ==== Lunar Calendar ==== \n"
                           "/l - Show current lunar calendar date\n")
    else:
        welcome_message = (f"🤖 Welcome to the Ronin Bot (v{BOT_VER})!\n\n"
                           "\n ==== Price ==== \n"
                           "/c <crypto> - Get price for any cryptocurrency\n"
                           "              (Example: /c BTC, /c BNB)\n"
                           "/c - Get prices for popular cryptocurrencies\n"
                           "/s <stock> - Get price for any stock\n"
                           "              (Example: /s AAPL, /s TSLA)\n"
                           "/s - Get prices for popular stocks\n\n"
                           "\n ==== Quotes ==== \n"
                           "/q - Get a random inspirational quote\n"
                           "/q <number> - Get a specific quote by ID\n"
                           "/q <name> - Search quotes by author\n"
                           "              (Example: /q Einstein)\n\n"
                           "\n ==== Lunar Calendar ==== \n"
                           "/l - Show current lunar calendar date\n")

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
                                       text=message,
                                       parse_mode="Markdown")

        # Only post to channel if explicitly configured and channel ID is valid
        if TELEGRAM_CHANNEL_ID and TELEGRAM_CHANNEL_ID.strip():
            try:
                logger.info(
                    f"Attempting to post price update to channel {TELEGRAM_CHANNEL_ID}"
                )
                await context.bot.send_message(chat_id=TELEGRAM_CHANNEL_ID,
                                               text=message,
                                               parse_mode="Markdown")
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
        # Use Finnhub as primary API source since it's faster
        if not context.args:
            # If no arguments, show all default stocks
            logger.info("No stock specified, showing default list")

            # Try Finnhub first as it's significantly faster
            start_time = time.time()
            price_data = finnhub_api.get_stock_prices()
            logger.info(
                f"Finnhub API response time: {time.time() - start_time:.2f} seconds"
            )

            # If Finnhub fails, fall back to AlphaVantage
            if isinstance(price_data, dict) and "error" in price_data:
                logger.info("Finnhub API failed, falling back to AlphaVantage")
                start_time = time.time()
                alpha_data = stock_api.get_stock_prices()
                logger.info(
                    f"AlphaVantage API response time: {time.time() - start_time:.2f} seconds"
                )

                if isinstance(alpha_data, dict) and "error" not in alpha_data:
                    price_data = alpha_data
                else:
                    # If both APIs failed but we have partial data from either, use what we have
                    logger.warning(
                        "Both Finnhub and AlphaVantage had issues, using any available data"
                    )
                    if isinstance(alpha_data, dict) and isinstance(
                            price_data, dict):
                        # Combine any valid data from both sources
                        for symbol, data in alpha_data.items():
                            if "error" not in data and symbol not in price_data:
                                price_data[symbol] = data

            logger.info(
                f"Received price data: {list(price_data.keys()) if isinstance(price_data, dict) else 'error'}"
            )
        else:
            # Get price for the specified stock
            stock_input = context.args[0].upper()
            logger.info(f"Fetching price for {stock_input}")

            # Try Finnhub first
            start_time = time.time()
            price_data = finnhub_api.get_stock_price(stock_input)
            logger.info(
                f"Finnhub API response time: {time.time() - start_time:.2f} seconds"
            )

            # If Finnhub fails, try AlphaVantage
            if isinstance(price_data, dict) and "error" in price_data:
                logger.info(
                    f"Finnhub failed for {stock_input}, trying AlphaVantage")
                start_time = time.time()
                price_data = stock_api.get_stock_price(stock_input)
                logger.info(
                    f"AlphaVantage API response time: {time.time() - start_time:.2f} seconds"
                )

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
                                       text=message,
                                       parse_mode="Markdown")

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
                                       text=message,
                                       parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error in vietnam_stock command: {str(e)}")
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=format_error_message(e))


async def health_check(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Periodic health check to ensure bot is running."""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"Health check - Bot is running at {current_time}")


async def get_gold_price_vnd() -> str:
    """Get current gold price in VND per tael (lượng)"""
    try:
        import requests
        import os

        # Get FMP API key
        api_key = os.getenv('FMP_API_KEY')
        if not api_key:
            return "❌ Không có API key để lấy giá vàng"

        # Get gold price in USD per ounce
        gold_url = f"https://financialmodelingprep.com/api/v3/quote/GCUSD?apikey={api_key}"
        gold_response = requests.get(gold_url, timeout=10)

        if gold_response.status_code != 200:
            return "❌ Lỗi khi lấy giá vàng"

        gold_data = gold_response.json()
        if not gold_data or len(gold_data) == 0:
            return "❌ Không có dữ liệu giá vàng"

        gold_price_usd_per_ounce = gold_data[0]['price']

        # Get USD/VND exchange rate
        usd_vnd_url = f"https://financialmodelingprep.com/api/v3/quote/USDVND?apikey={api_key}"
        usd_response = requests.get(usd_vnd_url, timeout=10)

        if usd_response.status_code != 200:
            return "❌ Lỗi khi lấy tỷ giá USD/VND"

        usd_data = usd_response.json()
        if not usd_data or len(usd_data) == 0:
            return "❌ Không có dữ liệu tỷ giá"

        usd_to_vnd = usd_data[0]['price']

        # Convert to VND per tael (1 tael = 1.20337 ounces)
        tael_to_ounce = 1.20337
        gold_price_vnd_per_tael = gold_price_usd_per_ounce * usd_to_vnd * tael_to_ounce

        gmt_plus_7 = timezone(timedelta(hours=7))
        current_time = datetime.now(gmt_plus_7).strftime("%d %b %Y, %H:%M")
        return f"💰 Vàng (TG): {gold_price_vnd_per_tael:,.0f} VND/lượng\n\n🕐 {current_time} (GMT+7)"

    except Exception as e:
        logger.error(f"Error getting gold price: {str(e)}")
        return "❌ Lỗi khi lấy giá vàng"


async def get_vietnam_gold_price() -> str:
    """Get current Vietnam gold price from giavang.org"""
    try:
        import requests
        from bs4 import BeautifulSoup
        import re

        # GiaVang.org URL for SJC gold prices
        url = "https://giavang.org/trong-nuoc/sjc/"

        headers = {
            'User-Agent':
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept':
            'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8'
        }

        response = requests.get(url, headers=headers, timeout=15)

        if response.status_code != 200:
            return "❌ Lỗi khi lấy giá vàng VN"

        soup = BeautifulSoup(response.content, 'html.parser')

        # Find the first table with gold prices
        table = soup.find('table')
        if not table:
            return "❌ Không tìm thấy bảng giá vàng"

        rows = table.find_all('tr')

        # Look for SJC gold data in the rows
        buy_price = None
        sell_price = None

        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 4:
                row_text = [cell.get_text().strip() for cell in cells]

                # Check if this row contains SJC gold info
                if any('SJC' in text.upper() for text in row_text):
                    try:
                        # Extract buy and sell prices (usually in positions 2 and 3)
                        buy_text = row_text[2] if len(row_text) > 2 else ""
                        sell_text = row_text[3] if len(row_text) > 3 else ""

                        # Extract numbers from price text
                        buy_match = re.search(r'(\d{2,3})[.,](\d{3})',
                                              buy_text)
                        sell_match = re.search(r'(\d{2,3})[.,](\d{3})',
                                               sell_text)

                        if buy_match and sell_match:
                            buy_price = float(
                                f"{buy_match.group(1)}{buy_match.group(2)}"
                            ) * 1000
                            sell_price = float(
                                f"{sell_match.group(1)}{sell_match.group(2)}"
                            ) * 1000
                            break

                    except (ValueError, IndexError):
                        continue

        if buy_price and sell_price:
            gmt_plus_7 = timezone(timedelta(hours=7))
            current_time = datetime.now(gmt_plus_7).strftime("%d %b %Y, %H:%M")
            return (f"🟢 VN (mua): {buy_price:,.0f} VND/lượng\n"
                    f"🔴 VN (bán): {sell_price:,.0f} VND/lượng\n\n"
                    f"🕐 {current_time} (GMT+7)")
        else:
            return "❌ Không tìm thấy giá vàng SJC"

    except Exception as e:
        logger.error(f"Error getting Vietnam gold price: {str(e)}")
        return "❌ Lỗi khi lấy giá vàng VN"


async def get_lunar_detail_info() -> str:
    """Get detailed lunar calendar information from xemlicham.com"""
    try:
        import requests
        from bs4 import BeautifulSoup
        import re

        # Use the home page which shows current day information
        url = "https://www.xemlicham.com/"

        headers = {
            'User-Agent':
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept':
            'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8'
        }

        response = requests.get(url, headers=headers, timeout=15)

        if response.status_code != 200:
            return "❌ Lỗi khi lấy thông tin lịch âm"

        soup = BeautifulSoup(response.content, 'html.parser')
        text = soup.get_text()

        # Extract lunar day information - flexible pattern for "Ngày X tháng Y năm Z"
        lunar_day = None
        day_name = month_name = year_name = ""
        day_pattern = r'Ngày\s+([A-Za-zÀ-ỹ]+\s+[A-Za-zÀ-ỹ]+)\s+tháng\s+([A-Za-zÀ-ỹ]+\s+[A-Za-zÀ-ỹ]+)\s+năm\s+([A-Za-zÀ-ỹ]+\s+[A-Za-zÀ-ỹ]+)'
        day_match = re.search(day_pattern, text, re.IGNORECASE)
        if day_match:
            day_name = day_match.group(1).strip()
            month_name = day_match.group(2).strip()
            year_name = day_match.group(3).strip()
            lunar_day = f"Ngày {day_name} tháng {month_name} năm {year_name}"

        # Extract fortune information - look for specific fortune types only
        fortune_info = None
        # Try to find specific fortune types like "Thiên Tài", "Thuần Dương", "Thiên Tặc", etc.
        fortune_patterns = [
            r'Ngày\s+(Thiên\s+Tài):\s*([^\n]*)',
            r'Ngày\s+(Thiên\s+Tặc):\s*([^\n]*)',
            r'Ngày\s+(Thuần\s+Dương):\s*([^\n]*)',
            r'Ngày\s+(Kim\s+Dương):\s*([^\n]*)',
            r'Ngày\s+(Đạo\s+Tặc):\s*([^\n]*)',
            r'Ngày\s+([A-Za-zÀ-ỹ]+\s+[A-Za-zÀ-ỹ]+):\s*([^\n]*(?:nên|thuận|lợi|tốt|thắng|xuất hành|cầu tài|xấu|không được|thông suốt|phù trợ|rất xấu|bị hại)[^\n]*)'
        ]

        for pattern in fortune_patterns:
            fortune_match = re.search(pattern, text, re.IGNORECASE)
            if fortune_match:
                fortune_name = fortune_match.group(1).strip()
                fortune_desc = fortune_match.group(2).strip()
                # Skip if it's the same as the lunar day info
                if lunar_day and fortune_name not in lunar_day:
                    fortune_info = f"🌟 Ngày {fortune_name}: {fortune_desc}"
                    break
                elif not lunar_day:
                    fortune_info = f"🌟 Ngày {fortune_name}: {fortune_desc}"
                    break

        # Extract Giờ Hoàng Đạo - flexible pattern
        hoang_dao_hours = None
        time_pattern = r'Giờ\s+Hoàng\s+Đạo[^:]*:\s*([^.\n]*(?:\([0-9-]+\))[^.\n]*)'
        time_match = re.search(time_pattern, text, re.IGNORECASE)
        if time_match:
            hoang_dao_hours = time_match.group(1).strip()

        # Format the result - separate lunar day from other info
        lunar_day_info = f"📜 {lunar_day}" if lunar_day else ""

        other_parts = []
        if fortune_info:
            other_parts.append(fortune_info)

        if hoang_dao_hours:
            other_parts.append(f"⏰ Giờ Hoàng Đạo: {hoang_dao_hours}")

        # Get a random quote to replace the fortune info
        random_quote = await get_random_quote()
        quote_text = ""
        if random_quote:
            # Check if this is a Vozer Collection quote for special formatting
            if random_quote.get("source") == "Vozer Collection":
                # Special format for Vozer Collection - only Vietnamese, no English translation
                formatted_text = random_quote["quote_text"].replace('\\n', '\n')
                quote_text = f'💭 "{formatted_text}"\n                    ( {random_quote["author"]} / #{random_quote["id"]} )'
            else:
                # Regular format for other quotes
                if random_quote.get("language") == "vi" or random_quote["author"] in ["Hồ Chí Minh", "Câu ngạn ngữ Việt Nam"]:
                    # Vietnamese original first, then English translation
                    formatted_text = random_quote["quote_text"].replace('\\n', '\n')
                    formatted_translation = random_quote["vietnamese_translation"].replace('\\n', '\n')
                    quote_text = f'===\n💭 "{formatted_text}"\n     ({random_quote["author"]} / #{random_quote["id"]})\n🔁 "{formatted_translation}"\n==='
                else:
                    # English original first, then Vietnamese translation
                    formatted_text = random_quote["quote_text"].replace('\\n', '\n')
                    formatted_translation = random_quote["vietnamese_translation"].replace('\\n', '\n')
                    quote_text = f'===\n💭 "{formatted_text}"\n     ({random_quote["author"]} / #{random_quote["id"]})\n🔁 "{formatted_translation}"\n==='

        # Combine with proper spacing, replacing fortune info with quote
        if lunar_day_info and quote_text:
            return f"{lunar_day_info}\n\n{quote_text}"
        elif lunar_day_info:
            return lunar_day_info
        elif quote_text:
            return quote_text
        else:
            return "❌ Không tìm thấy thông tin lịch âm chi tiết"

    except Exception as e:
        logger.error(f"Error getting lunar detail info: {str(e)}")
        return "❌ Lỗi khi lấy thông tin lịch âm"


async def lunar_calendar(update: Update,
                         context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display current lunar calendar date."""
    logger.info(f"Received /l command from chat {update.effective_chat.id}")

    try:
        from lunardate import LunarDate
        from datetime import datetime, timezone, timedelta

        # Get current date in GMT+7 (Vietnam time)
        vietnam_tz = timezone(timedelta(hours=7))
        today = datetime.now(vietnam_tz)

        # Convert to lunar date
        lunar_today = LunarDate.fromSolarDate(today.year, today.month,
                                              today.day)

        # Get gold prices and lunar detail info
        world_gold_price = await get_gold_price_vnd()
        vietnam_gold_price = await get_vietnam_gold_price()
        lunar_detail_info = await get_lunar_detail_info()

        # Get day of week in Vietnamese
        days_of_week = {
            0: "Thứ Hai",  # Monday
            1: "Thứ Ba",  # Tuesday
            2: "Thứ Tư",  # Wednesday
            3: "Thứ Năm",  # Thursday
            4: "Thứ Sáu",  # Friday
            5: "Thứ Bảy",  # Saturday
            6: "Chủ Nhật"  # Sunday
        }

        day_of_week = days_of_week[today.weekday()]

        # Format the message
        # Extract lunar day from detail info to place it next to lunar calendar date
        lunar_detail_parts = lunar_detail_info.split(
            '\n\n') if lunar_detail_info else []
        lunar_day_detail = ""
        other_detail_info = ""

        if lunar_detail_parts:
            # First part should be the lunar day detail
            if lunar_detail_parts[0].startswith("📜"):
                lunar_day_detail = lunar_detail_parts[0].replace("📜 ", "")
                # Update format: "Ngày X tháng Y năm Z" -> "Ngày X, tháng Y, năm Z"
                lunar_day_detail = lunar_day_detail.replace(
                    " tháng ", ", tháng ").replace(" năm ", ", năm ")
                if len(lunar_detail_parts) > 1:
                    other_detail_info = '\n\n'.join(lunar_detail_parts[1:])
            else:
                other_detail_info = lunar_detail_info

        message = (
            f"🗓️ **{day_of_week} - Dương Lịch ({today.day} / tháng {today.month} / {today.year})**\n\n"
            f"{world_gold_price}\n"
            f"{vietnam_gold_price}\n\n"
            f"🌕 Âm lịch: ngày {lunar_today.day}, tháng {lunar_today.month}, {lunar_today.year}\n"
            f"📜 {lunar_day_detail}\n\n"
            f"{other_detail_info}\n\n"
            f"📍 Thời gian: {today.strftime('%H:%M:%S')}")

        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=message,
                                       parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error in lunar_calendar command: {str(e)}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Lỗi khi lấy thông tin âm lịch. Vui lòng thử lại sau.")


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
    elif subcommand in ["map", "flag"]:
        await game_handler.start_game(update, context, game_mode=subcommand)
    elif subcommand == "capital":
        # Use CAP_MODE from country_game.config for capital guessing game
        from country_game.config import CAP_MODE
        await game_handler.start_game(update, context, game_mode=CAP_MODE)
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
def get_database_connection():
    """Get PostgreSQL database connection"""
    try:
        return psycopg2.connect(os.environ.get("DATABASE_URL"))
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        return None


async def get_random_quote():
    """Get a random quote from the database"""
    conn = get_database_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, quote_text, author, source, vietnamese_translation, language FROM quotes ORDER BY RANDOM() LIMIT 1")
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result:
            return {
                'id': result[0],
                'quote_text': result[1],
                'author': result[2],
                'source': result[3],
                'vietnamese_translation': result[4],
                'language': result[5]
            }
        return None
    except Exception as e:
        logger.error(f"Error getting random quote: {str(e)}")
        return None


async def get_quote_by_id(quote_id):
    """Get a specific quote by ID from the database"""
    conn = get_database_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, quote_text, author, source, vietnamese_translation, source_url, language FROM quotes WHERE id = %s", (quote_id,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result:
            return {
                'id': result[0],
                'quote_text': result[1],
                'author': result[2],
                'source': result[3],
                'vietnamese_translation': result[4],
                'source_url': result[5],
                'language': result[6]
            }
        return None
    except Exception as e:
        logger.error(f"Error getting quote by ID {quote_id}: {str(e)}")
        return None


async def get_quotes_by_author_search(author_search):
    """Get quotes by author name search (case-insensitive partial match)"""
    conn = get_database_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        # Special handling for "vozer" search - include all Vozer Collection quotes
        if author_search.lower() == "vozer":
            cursor.execute("SELECT id, quote_text, author, source, vietnamese_translation, language FROM quotes WHERE source = 'Vozer Collection' ORDER BY id", ())
        else:
            # Use ILIKE for case-insensitive search with wildcards
            search_pattern = f"%{author_search}%"
            cursor.execute("SELECT id, quote_text, author, source, vietnamese_translation, language FROM quotes WHERE author ILIKE %s ORDER BY author, id", (search_pattern,))
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if results:
            quotes = []
            for result in results:
                quotes.append({
                    'id': result[0],
                    'quote_text': result[1],
                    'author': result[2],
                    'source': result[3],
                    'vietnamese_translation': result[4],
                    'language': result[5]
                })
            return quotes
        return []
    except Exception as e:
        logger.error(f"Error searching quotes by author '{author_search}': {str(e)}")
        return None


async def quote_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /q command to show quotes"""
    logger.info(f"Received /q command from chat {update.effective_chat.id}")
    
    try:
        if context.args and len(context.args) > 0:
            arg = " ".join(context.args)  # Join all arguments to handle multi-word author names
            
            # Try to parse as quote ID first
            try:
                quote_id = int(arg)
                quote = await get_quote_by_id(quote_id)
                
                if quote:
                    # Check if this is a Vozer Collection quote for special formatting
                    if quote.get("source") == "Vozer Collection":
                        # Special format for Vozer Collection - only Vietnamese, no English translation
                        formatted_text = quote["quote_text"].replace('\\n', '\n')
                        message = f'💭 "{formatted_text}"\n'
                        message += f'                    ( {quote["author"]} / #{quote["id"]} )'
                    else:
                        # Regular format for other quotes
                        message = f"===\n"
                        
                        # Check if originally Vietnamese (for quotes like Ho Chi Minh's)
                        if quote.get("language") == "vi" or quote["author"] in ["Hồ Chí Minh", "Câu ngạn ngữ Việt Nam"]:
                            # Vietnamese original first, then English translation
                            formatted_text = quote["quote_text"].replace('\\n', '\n')
                            formatted_translation = quote["vietnamese_translation"].replace('\\n', '\n')
                            message += f'💭 "{formatted_text}"\n'
                            message += f'     ( {quote["source"]} / {quote["author"]} / #{quote["id"]} )\n'
                            if quote.get("source_url"):
                                message += f'     ({quote["source_url"]})\n'
                            message += f'🔁 "{formatted_translation}"\n'
                        else:
                            # English original first, then Vietnamese translation
                            formatted_text = quote["quote_text"].replace('\\n', '\n')
                            formatted_translation = quote["vietnamese_translation"].replace('\\n', '\n')
                            message += f'💭 "{formatted_text}"\n'
                            message += f'     ( {quote["source"]} / {quote["author"]} / #{quote["id"]} )\n'
                            if quote.get("source_url"):
                                message += f'     ({quote["source_url"]})\n'
                            message += f'🔁 "{formatted_translation}"\n'
                        
                        message += f"==="
                else:
                    message = f"❌ Không tìm thấy quote với ID #{quote_id}"
                    
            except ValueError:
                # Not a number, search by author name
                quotes = await get_quotes_by_author_search(arg)
                
                if quotes is None:
                    message = "❌ Lỗi khi tìm kiếm tác giả trong database"
                elif len(quotes) == 0:
                    message = f"❌ Không tìm thấy quote nào của tác giả có tên chứa '{arg}'"
                else:
                    # Format author search results
                    message = f"📚 Tìm thấy {len(quotes)} quote(s) cho '{arg}':\n\n"
                    
                    # Special handling for Vozer Collection quotes
                    if arg.lower() == "vozer":
                        for quote in quotes:
                            # Use special Vozer format for search results - only Vietnamese, no English translation
                            formatted_text = quote["quote_text"].replace('\\n', '\n')
                            message += f'💭 "{formatted_text}"\n'
                            message += f'                    ( {quote["author"]} / #{quote["id"]} )\n\n'
                    else:
                        for quote in quotes:
                            message += f"#{quote['id']} - {quote['author']}\n"
                            
                            # Show original language first in search results too
                            if quote.get("language") == "vi" or quote["author"] in ["Hồ Chí Minh", "Câu ngạn ngữ Việt Nam"]:
                                # Vietnamese original first, then English
                                message += f'"{quote["quote_text"][:80]}{"..." if len(quote["quote_text"]) > 80 else ""}"\n'
                                message += f'"{quote["vietnamese_translation"][:80]}{"..." if len(quote["vietnamese_translation"]) > 80 else ""}"\n\n'
                            else:
                                # English original first, then Vietnamese
                                message += f'"{quote["quote_text"][:80]}{"..." if len(quote["quote_text"]) > 80 else ""}"\n'
                                message += f'"{quote["vietnamese_translation"][:80]}{"..." if len(quote["vietnamese_translation"]) > 80 else ""}"\n\n'
                        
                        message += "💡 Dùng /q [ID] để xem chi tiết quote cụ thể"
        else:
            # Get random quote
            quote = await get_random_quote()
            
            if quote:
                # Check if this is a Vozer Collection quote for special formatting
                if quote.get("source") == "Vozer Collection":
                    # Special format for Vozer Collection - only Vietnamese, no English translation
                    formatted_text = quote["quote_text"].replace('\\n', '\n')
                    message = f'💭 "{formatted_text}"\n'
                    message += f'                    ( {quote["author"]} / #{quote["id"]} )'
                else:
                    # Regular format for other quotes
                    message = f"===\n"
                    
                    # Check if originally Vietnamese (for quotes like Ho Chi Minh's)
                    if quote.get("language") == "vi" or quote["author"] in ["Hồ Chí Minh", "Câu ngạn ngữ Việt Nam"]:
                        # Vietnamese original first, then English translation
                        formatted_text = quote["quote_text"].replace('\\n', '\n')
                        formatted_translation = quote["vietnamese_translation"].replace('\\n', '\n')
                        message += f'💭 "{formatted_text}"\n'
                        message += f'     ( {quote["source"]} / {quote["author"]} / #{quote["id"]} )\n'
                        message += f'🔁 "{formatted_translation}"\n'
                    else:
                        # English original first, then Vietnamese translation
                        formatted_text = quote["quote_text"].replace('\\n', '\n')
                        formatted_translation = quote["vietnamese_translation"].replace('\\n', '\n')
                        message += f'💭 "{formatted_text}"\n'
                        message += f'     ( {quote["source"]} / {quote["author"]} / #{quote["id"]} )\n'
                        message += f'🔁 "{formatted_translation}"\n'
                    
                    message += f"==="
            else:
                message = "❌ Không thể lấy quote từ database"
        
        await context.bot.send_message(chat_id=update.effective_chat.id, text=message)
        
    except Exception as e:
        logger.error(f"Error in quote command: {str(e)}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="❌ Lỗi khi lấy quote từ database"
        )


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

    # Start API server in a background thread
    try:
        import sys
        from xbot_api.server import run_in_thread

        # Update the API port to use 5000 for shared access
        os.environ["API_PORT"] = "5000"

        api_thread = run_in_thread()
        logger.info("API server thread started")
    except Exception as e:
        logger.error(f"Failed to start API server: {str(e)}")
        # Continue with bot initialization even if API server fails

    # Start HTTP server in a separate thread for Autoscale health checks
    # Note: The health check now needs to be modified to work with Flask
    # Will use Flask for health checks too
    # http_thread = threading.Thread(target=run_http_server, daemon=True)
    # http_thread.start()
    # logger.info("HTTP server thread started")

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
            application.add_handler(CommandHandler("l", lunar_calendar))
            application.add_handler(CommandHandler("q", quote_command))
            application.add_handler(CommandHandler("vn", vietnam_stock))

            # Add the game command handlers
            application.add_handler(CommandHandler("g", game_command))

            # Add a callback query handler for the game buttons
            # Make sure it captures all callback query patterns used by the game
            application.add_handler(
                CallbackQueryHandler(
                    lambda update, context: context.bot_data[
                        'game_handler'].handle_callback_query(update, context),
                    pattern=
                    "^(guess_|play_|show_leaderboard)"  # Added show_leaderboard to the pattern
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
#"\n ==== Game ==== \n"
#"/g <option> - Play country guessing game\n"
#"              (Example: /g map, /g flag, /g capital)\n"
#"/g lb       - View country game leaderboard\n"
#"/g help     - More detail game options\n"
#"\n ====  ==== \n"
#"/help or /h - Show this help message\n\n"
#"💡 To use in groups:\n"
#"1. Add me to your group\n"
#"2. Use commands like /c BTC or /s AAPL\n\n"
#"💡 For channels:\n"
#"1. Add me as a channel admin\n"
#"2. Set up price updates using /setchannel")
