import os
import requests
import time
import logging
from typing import Dict, List, Optional
from .config import DEFAULT_CRYPTOCURRENCIES, REQUEST_TIMEOUT, MAX_RETRIES, RETRY_DELAY

logger = logging.getLogger(__name__)

class CoinMarketCapAPI:
    def __init__(self):
        self.api_key = os.getenv('COINMARKETCAP_API_KEY')
        self.base_url = "https://pro-api.coinmarketcap.com/v1"
        self.session = requests.Session()
        self.session.headers.update({
            'X-CMC_PRO_API_KEY': self.api_key,
            'Accept': 'application/json'
        })

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make a request to CoinMarketCap API with retry logic"""
        url = f"{self.base_url}/{endpoint}"
        logger.info(f"Making request to {url} with params: {params}")

        for attempt in range(MAX_RETRIES):
            try:
                response = self.session.get(
                    url,
                    params=params,
                    timeout=REQUEST_TIMEOUT
                )
                response.raise_for_status()
                data = response.json()
                logger.info(f"Successful response received")
                return data
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed (attempt {attempt + 1}/{MAX_RETRIES}): {str(e)}")
                if attempt == MAX_RETRIES - 1:
                    if hasattr(e, 'response') and hasattr(e.response, 'status_code'):
                        if e.response.status_code == 429:
                            return {"error": "Rate limit exceeded. Please try again later."}
                    return {"error": str(e)}
                time.sleep(RETRY_DELAY * (attempt + 1))

        return {"error": "Maximum retries exceeded"}

    # Map display symbols to their CoinMarketCap symbols
    SYMBOL_ALIASES = {
        'GOLD': 'XAUT',  # Tether Gold
    }

    def get_price(self, symbol: str) -> Dict:
        """Get current price for a single cryptocurrency"""
        logger.info(f"Fetching price for symbol: {symbol}")

        display_symbol = symbol.upper()
        cmc_symbol = self.SYMBOL_ALIASES.get(display_symbol, display_symbol)

        params = {
            'symbol': cmc_symbol,
            'convert': 'USD'
        }

        data = self._make_request('cryptocurrency/quotes/latest', params)

        if "error" in data:
            return data

        if "data" in data and data["data"]:
            coin_data = next(iter(data["data"].values()))
            quote = coin_data["quote"]["USD"]

            formatted_data = {
                display_symbol: {
                    "usd": quote["price"],
                    "usd_24h_change": quote["percent_change_24h"],
                    "market_cap": quote.get("market_cap", 0),
                    "name": coin_data["name"]
                }
            }
            logger.info(f"Formatted price data: {formatted_data}")
            return formatted_data

        return {"error": f"No data found for {symbol}"}

    def get_prices(self, symbols: List[str] = None) -> Dict:
        """Get current prices for multiple cryptocurrencies"""
        if symbols is None:
            symbols = [symbol.upper() for symbol in DEFAULT_CRYPTOCURRENCIES]

        logger.info(f"Fetching prices for symbols: {symbols}")

        # Build alias map for this request: display_symbol -> cmc_symbol
        display_to_cmc = {s: self.SYMBOL_ALIASES.get(s, s) for s in symbols}
        cmc_to_display = {v: k for k, v in display_to_cmc.items()}
        cmc_symbols = list(display_to_cmc.values())

        params = {
            'symbol': ','.join(cmc_symbols),
            'convert': 'USD'
        }

        data = self._make_request('cryptocurrency/quotes/latest', params)

        if "error" in data:
            return data

        formatted_data = {}
        if "data" in data:
            for cmc_symbol, coin_data in data["data"].items():
                quote = coin_data["quote"]["USD"]
                display_symbol = cmc_to_display.get(cmc_symbol.upper(), cmc_symbol.upper())
                formatted_data[display_symbol] = {
                    "usd": quote["price"],
                    "usd_24h_change": quote["percent_change_24h"],
                    "market_cap": quote.get("market_cap", 0),
                    "name": coin_data["name"]
                }

        logger.info(f"Formatted multi-price data: {formatted_data}")
        return formatted_data if formatted_data else {"error": "Failed to fetch cryptocurrency prices"}