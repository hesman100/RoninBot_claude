import os

# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'your_bot_token_here')
TELEGRAM_CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID', 'your_channel_id_here')

# Alpha Vantage API Configuration
ALPHAVANTAGE_API_KEY = os.getenv('ALPHAVANTAGE_API_KEY')
ALPHAVANTAGE_BASE_URL = "https://www.alphavantage.co/query"

# CoinMarketCap API Configuration
COINMARKETCAP_BASE_URL = "https://pro-api.coinmarketcap.com/v1"

# Default cryptocurrencies to track (using symbols for CoinMarketCap)
DEFAULT_CRYPTOCURRENCIES = [
    "BTC",  # Bitcoin
    "ETH",  # Ethereum
    "SOL",  # Solana
    "RON",  # Ronin
    "AXS",  # Axie Infinity
    "PIXEL",  # Pixel
    "PI",  # Pi Network
    "BNB",  # BNB
]

# Default stocks to track
DEFAULT_STOCKS = [
    "TSLA",  # Tesla
    "NVDA",  # NVIDIA
    "AAPL",  # Apple
    "MRVL",  # Marvell
    "AMZN",  # Amazon
    "CDNS",  # Cadence
    "MSFT",  # Microsoft
    "GOOGL",  # Google
    "META",  # Meta
    "INTC",  # Intel
    "QCOM",  # Qualcomm
    "AVGO",  # Broadcom
]

# Mapping of CoinMarketCap symbols to display names (for formatting)
SYMBOL_TO_DISPLAY = {
    'BTC': 'BTC    ',  # Exactly 7 chars
    'ETH': 'ETH    ',  # Exactly 7 chars
    'SOL': 'SOL    ',  # Exactly 7 chars
    'RON': 'RON    ',  # Exactly 7 chars
    'AXS': 'AXS    ',  # Exactly 7 chars
    'PIXEL': 'PIXEL  ',  # Exactly 7 chars
    'PI': 'PI     ',  # Exactly 7 chars
    'BNB': 'BNB    ',  # Exactly 7 chars
}

# Mapping of stock symbols to display names (for formatting)
STOCK_TO_DISPLAY = {
    'TSLA': 'TSLA   ',  # Exactly 7 chars
    'NVDA': 'NVDA   ',  # Exactly 7 chars
    'AAPL': 'AAPL   ',  # Exactly 7 chars
    'MRVL': 'MRVL   ',  # Exactly 7 chars
    'AMZN': 'AMZN   ',  # Exactly 7 chars
    'CDNS': 'CDNS   ',  # Exactly 7 chars
    'MSFT': 'MSFT   ',  # Exactly 7 chars
    'GOOGL': 'GOOGL  ',  # Exactly 7 chars
    'META': 'META   ',  # Exactly 7 chars
    'INTC': 'INTC   ',  # Exactly 7 chars
    'QCOM': 'QCOM   ',  # Exactly 7 chars
    'AVGO': 'AVGO   ',  # Exactly 7 chars
}

# Mapping of stock symbols to full company names
STOCK_COMPANY_NAMES = {
    'TSLA': 'Tesla Inc.',
    'NVDA': 'NVIDIA Corporation',
    'AAPL': 'Apple Inc.',
    'MRVL': 'Marvell Technology',
    'AMZN': 'Amazon.com Inc.',
    'CDNS': 'Cadence Design Systems',
    'MSFT': 'Microsoft Corporation',
    'GOOGL': 'Alphabet Inc.',
    'META': 'Meta Platforms Inc.',
    'INTC': 'Intel Corporation',
    'QCOM': 'Qualcomm Inc.',
    'AVGO': 'Broadcom Inc.',
}

# Default Vietnam stocks to track
DEFAULT_VN_STOCKS = [
    "VCB",  # Vietcombank
    "MWG",  # Mobile World JSC
    "VIC",  # Vingroup
    "HPG",  # Hoa Phat Group
    "FPT",  # FPT Corporation
    "MSN",  # Masan Group
    "VNM",  # Vietnam Dairy Products
    "VHM",  # Vinhomes
    "PLX",  # Petrolimex
    "GAS",  # PetroVietnam Gas
    "PNJ"  # Phu Nhuan Jewelry
]

# Mapping of Vietnam stock symbols to display names (for formatting)
VN_STOCK_TO_DISPLAY = {
    'VCB': 'VCB    ',  # Exactly 7 chars
    'MWG': 'MWG    ',  # Exactly 7 chars'
    'VIC': 'VIC    ',  # Exactly 7 chars
    'HPG': 'HPG    ',  # Exactly 7 chars
    'FPT': 'FPT    ',  # Exactly 7 chars
    'MSN': 'MSN    ',  # Exactly 7 chars
    'VNM': 'VNM    ',  # Exactly 7 chars
    'VHM': 'VHM    ',  # Exactly 7 chars
    'PLX': 'PLX    ',  # Exactly 7 chars
    'GAS': 'GAS    ',  # Exactly 7 chars
    'PNJ': 'PNJ    ',  # Exactly 7 chars
}

# Mapping of Vietnam stock symbols to full company names
VN_STOCK_COMPANY_NAMES = {
    'VCB': 'Vietcombank',
    'MWG': 'Mobile World JSC',
    'VIC': 'Vingroup JSC',
    'HPG': 'Hoa Phat Group JSC',
    'FPT': 'FPT Corporation',
    'MSN': 'Masan Group Corporation',
    'VNM': 'Vietnam Dairy Products JSC',
    'VHM': 'Vinhomes JSC',
    'PLX': 'Petrolimex',
    'GAS': 'PetroVietnam Gas JSC',
    'PNJ': 'Phu Nhuan Jewelry JSC',
    'NVL': 'NovaLand',  # NVL
    'HSG': 'Hoa Sen Group',  # HSG
}

# API request parameters
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds
