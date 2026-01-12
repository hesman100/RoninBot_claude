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

    def get_price(self, symbol: str) -> Dict:
        """Get current price for a single cryptocurrency"""
        logger.info(f"Fetching price for symbol: {symbol}")
        
        # Check if requesting GOLD or SLVR (fetched from Yahoo Finance)
        if symbol.upper() in ['GOLD', 'SLVR']:
            from .fmp_api import get_commodity_prices
            commodities = get_commodity_prices()
            if symbol.upper() in commodities:
                return {symbol.upper(): commodities[symbol.upper()]}
            return {}

        params = {
            'symbol': symbol.upper(),
            'convert': 'USD'
        }

        data = self._make_request('cryptocurrency/quotes/latest', params)

        if "error" in data:
            return data

        if "data" in data and data["data"]:
            coin_data = next(iter(data["data"].values()))
            quote = coin_data["quote"]["USD"]

            # Format response to match our existing structure
            formatted_data = {
                symbol.upper(): {
                    "usd": quote["price"],
                    "usd_24h_change": quote["percent_change_24h"],
                    "market_cap": quote.get("market_cap", 0),
                    "name": coin_data["name"]  # Include the full name
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
        
        # Separate commodities (GOLD, SLVR) from crypto symbols
        commodity_symbols = ['GOLD', 'SLVR']
        crypto_symbols = [s for s in symbols if s.upper() not in commodity_symbols]
        has_commodities = any(s.upper() in commodity_symbols for s in symbols)

        # Fetch crypto prices from CoinMarketCap
        formatted_data = {}
        if crypto_symbols:
            params = {
                'symbol': ','.join(crypto_symbols),
                'convert': 'USD'
            }

            data = self._make_request('cryptocurrency/quotes/latest', params)

            if "error" in data:
                return data

            if "data" in data:
                for symbol, coin_data in data["data"].items():
                    quote = coin_data["quote"]["USD"]
                    formatted_data[symbol.upper()] = {
                        "usd": quote["price"],
                        "usd_24h_change": quote["percent_change_24h"],
                        "market_cap": quote.get("market_cap", 0),
                        "name": coin_data["name"]  # Include the full name
                    }
        
        # Add commodity prices (GOLD, SLVR) from Yahoo Finance if requested
        if has_commodities:
            from .fmp_api import get_commodity_prices
            commodity_data = get_commodity_prices()
            if commodity_data:
                # Only add commodities that were requested
                for sym in symbols:
                    if sym.upper() in commodity_data:
                        formatted_data[sym.upper()] = commodity_data[sym.upper()]
        
        logger.info(f"Formatted multi-price data: {formatted_data}")
        return formatted_data if formatted_data else {"error": "Failed to fetch cryptocurrency prices"}