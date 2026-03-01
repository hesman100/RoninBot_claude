import os
import requests
import time
import logging
from typing import Dict, List, Optional
from .config import DEFAULT_CRYPTOCURRENCIES, REQUEST_TIMEOUT, MAX_RETRIES, RETRY_DELAY

logger = logging.getLogger(__name__)

# CMC category IDs for real-world asset pages
TOKENIZED_GOLD_CATEGORY_ID   = '625d09d246203827ab52dd53'  # /real-world-assets/gold/
TOKENIZED_SILVER_CATEGORY_ID = '68639ad6358e0763b448bf96'  # /real-world-assets/silver/

# RWA symbols and their category config: (category_id, display_name, min_price, max_price)
RWA_SYMBOLS = {
    'GOLD': (TOKENIZED_GOLD_CATEGORY_ID, 'Gold',   1500, 9000),
    'SLVR': (TOKENIZED_SILVER_CATEGORY_ID, 'Silver',  10,  500),
}

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

    def _get_rwa_price(self, display_symbol: str) -> Dict:
        """Get price from a CMC real-world-assets category.
        Filters coins by price range and excludes extreme movers.
        Uses market-cap-weighted average when available, otherwise simple average.
        """
        category_id, display_name, min_price, max_price = RWA_SYMBOLS[display_symbol]

        logger.info(f"Fetching {display_name} price from CMC category {category_id}")
        data = self._make_request('cryptocurrency/category',
                                  {'id': category_id, 'limit': 20})
        if 'error' in data:
            return data

        coins = data.get('data', {}).get('coins', [])
        if not coins:
            return {'error': f'No tokenized {display_name} data available'}

        valid = [
            c for c in coins
            if min_price < c.get('quote', {}).get('USD', {}).get('price', 0) < max_price
            and abs(c.get('quote', {}).get('USD', {}).get('percent_change_24h', 0)) < 30
        ]

        if not valid:
            return {'error': f'No valid {display_name} price data found'}

        total_mcap = sum(c['quote']['USD'].get('market_cap', 0) for c in valid)

        if total_mcap > 0:
            avg_price = sum(c['quote']['USD']['price'] * c['quote']['USD']['market_cap']
                            for c in valid) / total_mcap
            avg_change = sum(c['quote']['USD']['percent_change_24h'] * c['quote']['USD']['market_cap']
                             for c in valid) / total_mcap
        else:
            avg_price = sum(c['quote']['USD']['price'] for c in valid) / len(valid)
            avg_change = sum(c['quote']['USD']['percent_change_24h'] for c in valid) / len(valid)

        logger.info(f"{display_name} avg price: {avg_price:.2f} from {len(valid)} tokens")
        return {
            display_symbol: {
                'usd': avg_price,
                'usd_24h_change': avg_change,
                'market_cap': total_mcap,
                'name': display_name
            }
        }

    def get_price(self, symbol: str) -> Dict:
        """Get current price for a single cryptocurrency"""
        logger.info(f"Fetching price for symbol: {symbol}")

        if symbol.upper() in RWA_SYMBOLS:
            return self._get_rwa_price(symbol.upper())

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

            formatted_data = {
                symbol.upper(): {
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

        rwa_symbols = [s for s in symbols if s in RWA_SYMBOLS]
        crypto_symbols = [s for s in symbols if s not in RWA_SYMBOLS]

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
                for cmc_symbol, coin_data in data["data"].items():
                    quote = coin_data["quote"]["USD"]
                    formatted_data[cmc_symbol.upper()] = {
                        "usd": quote["price"],
                        "usd_24h_change": quote["percent_change_24h"],
                        "market_cap": quote.get("market_cap", 0),
                        "name": coin_data["name"]
                    }

        for sym in rwa_symbols:
            rwa_data = self._get_rwa_price(sym)
            if 'error' not in rwa_data:
                formatted_data.update(rwa_data)

        logger.info(f"Formatted multi-price data: {formatted_data}")
        return formatted_data if formatted_data else {"error": "Failed to fetch cryptocurrency prices"}
