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
    "RON",  # Ronin
    "BTC",  # Bitcoin
    "ETH",  # Ethereum
    "AXS",  # Axie Infinity
    "PI",  # Pi Network
    "BNB",  # BNB
    "SOL",  # Solana
    "GOLD",  # Gold (commodity, fetched from FMP API)
]

# Default stocks to track
DEFAULT_STOCKS = [
    "TSLA",  # Tesla
    "VFS",  # Vinfast
    "AAPL",  # Apple
    "AMZN",  # Amazon
    "MSFT",  # Microsoft
    "GOOGL",  # Google
    "META",  # Meta
    "NVDA",  # NVIDIA
    "INTC",  # Intel
    "QCOM",  # Qualcomm
    "AVGO",  # Broadcom
    "SNPS",  # Synopsys
    "MRVL",  # Marvell
    "CDNS",  # Cadence
]

# Mapping of CoinMarketCap symbols to display names (for formatting)
SYMBOL_TO_DISPLAY = {
    'BTC': 'BTC  ',  # Exactly 5 chars
    'ETH': 'ETH  ',  # Exactly 5 chars
    'SOL': 'SOL  ',  # Exactly 5 chars
    'RON': 'RON  ',  # Exactly 5 chars
    'AXS': 'AXS  ',  # Exactly 5 chars
    'PI': 'PI   ',  # Exactly 5 chars
    'BNB': 'BNB  ',  # Exactly 5 chars
    'GOLD': 'GOLD ',  # Exactly 5 chars
}

# Mapping of stock symbols to display names (for formatting)
STOCK_TO_DISPLAY = {
    'TSLA': 'TSLA ',  # Exactly 5 chars
    'NVDA': 'NVDA ',  # Exactly 5 chars
    'AAPL': 'AAPL ',  # Exactly 5 chars
    'MRVL': 'MRVL ',  # Exactly 5 chars
    'SNPS': 'SNPS ',  # Exactly 5 chars
    'AMZN': 'AMZN ',  # Exactly 5 chars
    'CDNS': 'CDNS ',  # Exactly 5 chars
    'MSFT': 'MSFT ',  # Exactly 5 chars
    'GOOGL': 'GOOGL',  # Exactly 5 chars
    'META': 'META ',  # Exactly 5 chars
    'INTC': 'INTC ',  # Exactly 5 chars
    'QCOM': 'QCOM ',  # Exactly 5 chars
    'AVGO': 'AVGO ',  # Exactly 5 chars
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
    'VFS': 'VinFast Auto Ltd',
    'SNPS': 'Synopsys Inc.'
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
    'VCB': 'VCB  ',  # Exactly 5 chars
    'MWG': 'MWG  ',  # Exactly 5 chars
    'VIC': 'VIC  ',  # Exactly 5 chars
    'HPG': 'HPG  ',  # Exactly 5 chars
    'FPT': 'FPT  ',  # Exactly 5 chars
    'MSN': 'MSN  ',  # Exactly 5 chars
    'VNM': 'VNM  ',  # Exactly 5 chars
    'VHM': 'VHM  ',  # Exactly 5 chars
    'PLX': 'PLX  ',  # Exactly 5 chars
    'GAS': 'GAS  ',  # Exactly 5 chars
    'PNJ': 'PNJ  ',  # Exactly 5 chars
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

# Financial Modeling Prep API Configuration
FMP_API_KEY = os.getenv('FMP_API_KEY')
FMP_BASE_URL = "https://financialmodelingprep.com/api/v3"

# API request parameters
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds
