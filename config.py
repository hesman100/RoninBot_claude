import os

# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'your_bot_token_here')
TELEGRAM_CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID', 'your_channel_id_here')

# CoinMarketCap API Configuration
COINMARKETCAP_BASE_URL = "https://pro-api.coinmarketcap.com/v1"

# Default cryptocurrencies to track (using symbols for CoinMarketCap)
DEFAULT_CRYPTOCURRENCIES = [
    "BTC",          # Bitcoin
    "ETH",         # Ethereum
    "SOL",          # Solana
    "RON",           # Ronin
    "AXS",   # Axie Infinity
    "PI",      # Pi Network
    "BNB",             # BNB
]

# Mapping of CoinMarketCap symbols to display names (for formatting)
SYMBOL_TO_DISPLAY = {
    'BTC': 'BTC  ',
    'ETH': 'ETH  ',
    'SOL': 'SOL  ',
    'RON': 'RON  ',
    'AXS': 'AXS  ',
    'PI': 'PI   ',
    'BNB': 'BNB  ',
}

# API request parameters
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds