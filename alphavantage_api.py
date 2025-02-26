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
        self._company_names_cache = {}

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
                    if hasattr(e, 'response') and hasattr(e.response, 'status_code') and e.response.status_code == 429:
                        return {"error": "Rate limit exceeded. Please try again later."}
                    return {"error": str(e)}
                time.sleep(RETRY_DELAY * (attempt + 1))

        return {"error": "Maximum retries exceeded"}

    def get_company_name(self, symbol: str) -> str:
        """Get the full company name for a stock symbol"""
        if symbol in self._company_names_cache:
            return self._company_names_cache[symbol]

        params = {
            'function': 'OVERVIEW',
            'symbol': symbol.upper(),
            'apikey': self.api_key
        }

        data = self._make_request(params)
        if isinstance(data, dict) and "Name" in data:
            self._company_names_cache[symbol] = data["Name"]
            return data["Name"]
        return symbol.upper()  # Return symbol if name not found

    def get_stock_price(self, symbol: str) -> Dict:
        """Get current price and daily change for a single stock"""
        logger.info(f"Fetching price for stock: {symbol}")

        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol.upper(),
            'apikey': self.api_key
        }

        data = self._make_request(params)
        logger.info(f"Raw API response: {data}")  # Log raw response for debugging

        if "error" in data:
            return data

        if "Global Quote" in data and data["Global Quote"]:
            quote = data["Global Quote"]
            if quote:  # Check if quote has data
                try:
                    price = float(quote.get('05. price', 0))
                    change_percent = float(quote.get('10. change percent', '0').rstrip('%'))

                    # Get company name
                    company_name = self.get_company_name(symbol)

                    formatted_data = {
                        symbol.upper(): {
                            "usd": price,
                            "usd_24h_change": change_percent,
                            "name": company_name
                        }
                    }
                    logger.info(f"Formatted stock data: {formatted_data}")
                    return formatted_data
                except (ValueError, TypeError) as e:
                    logger.error(f"Error parsing quote data: {str(e)}")
                    return {"error": f"Invalid data format for {symbol}"}

        return {"error": f"No data found for {symbol}"}

    def get_stock_prices(self, symbols: Optional[List[str]] = None) -> Dict:
        """Get current prices for multiple stocks"""
        if symbols is None:
            symbols = DEFAULT_STOCKS

        logger.info(f"Fetching prices for stocks: {symbols}")

        all_data = {}
        for symbol in symbols:
            data = self.get_stock_price(symbol)
            if not isinstance(data, dict) or "error" not in data:
                all_data.update(data)
            time.sleep(0.2)  # Avoid hitting rate limits

        # Only return error if no data was fetched at all
        return all_data if all_data else {"error": "Failed to fetch stock prices"}