import requests
import time
from typing import Dict, List, Optional
import logging
from config import (
    ALPHAVANTAGE_API_KEY,
    ALPHAVANTAGE_BASE_URL,
    REQUEST_TIMEOUT,
    MAX_RETRIES,
    RETRY_DELAY,
    DEFAULT_STOCKS
)

logger = logging.getLogger(__name__)

class AlphaVantageAPI:
    def __init__(self):
        self.api_key = ALPHAVANTAGE_API_KEY
        self.base_url = ALPHAVANTAGE_BASE_URL
        self.session = requests.Session()

    def _make_request(self, params: Dict) -> Dict:
        """Make a request to Alpha Vantage API with retry logic"""
        logger.info(f"Making request to Alpha Vantage with params: {params}")

        for attempt in range(MAX_RETRIES):
            try:
                response = self.session.get(
                    self.base_url,
                    params=params,
                    timeout=REQUEST_TIMEOUT
                )
                response.raise_for_status()
                data = response.json()
                logger.info("Successful response received")
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

    def get_stock_price(self, symbol: str) -> Dict:
        """Get current price and daily change for a single stock"""
        logger.info(f"Fetching price for stock: {symbol}")

        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol.upper(),
            'apikey': self.api_key
        }

        data = self._make_request(params)

        if "error" in data:
            return data

        if "Global Quote" in data and data["Global Quote"]:
            quote = data["Global Quote"]
            price = float(quote.get('05. price', 0))
            change_percent = float(quote.get('10. change percent', '0').rstrip('%'))

            formatted_data = {
                symbol.upper(): {
                    "usd": price,
                    "usd_24h_change": change_percent,
                    "name": symbol.upper()  # Use symbol as name for stocks
                }
            }
            logger.info(f"Formatted stock data: {formatted_data}")
            return formatted_data

        return {"error": f"No data found for {symbol}"}

    def get_stock_prices(self) -> Dict:
        """Get current prices for multiple stocks using default list"""
        logger.info(f"Fetching prices for default stocks: {DEFAULT_STOCKS}")

        all_data = {}
        error_occurred = False

        for symbol in DEFAULT_STOCKS:
            try:
                data = self.get_stock_price(symbol)
                if "error" not in data:
                    all_data.update(data)
                time.sleep(0.2)  # Avoid hitting rate limits
            except Exception as e:
                logger.error(f"Error fetching price for {symbol}: {str(e)}")
                error_occurred = True
                continue

        if not all_data and error_occurred:
            return {"error": "Failed to fetch stock prices"}
        return all_data if all_data else {"error": "No stock data available"}