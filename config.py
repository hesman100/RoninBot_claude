import os

# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'your_bot_token_here')
TELEGRAM_CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID', 'your_channel_id_here')

# CoinGecko API Configuration
COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"

# Default cryptocurrencies to track
# Add or remove cryptocurrencies by their CoinGecko IDs
# You can find coin IDs at https://www.coingecko.com/en/all-cryptocurrencies
DEFAULT_CRYPTOCURRENCIES = [
    "bitcoin",          # BTC
    "ethereum",         # ETH
    "solana",          # SOL
    "Ronin",           # RON
    "axie",     # AXS
    "Freysa",     # FAI
    "Pi-network"    # PI
]

# API request parameters
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds