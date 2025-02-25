import os

# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'your_bot_token_here')
TELEGRAM_CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID', 'your_channel_id_here')

# CoinGecko API Configuration
COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"

# Default cryptocurrencies to track
DEFAULT_CRYPTOCURRENCIES = [
    "bitcoin",          # BTC
    "ethereum",         # ETH
    "solana",          # SOL
    "ronin",           # RON
    "axie-infinity",   # AXS
    "pi-network",      # PI
]

# Mapping of ticker symbols to CoinGecko IDs
TICKER_TO_ID = {
    # Original mappings
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "RON": "ronin",
    "AXS": "axie-infinity",
    "PI": "pi-network",
}

# API request parameters
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds