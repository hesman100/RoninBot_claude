import requests
import time
from typing import Dict, List, Optional
import logging
from .config import (
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
        self._cache = {}
        self._cache_expiry = {}
        self._cache_duration = 300  # Cache for 5 minutes

    def _is_rate_limited(self, data: Dict) -> bool:
        """Check if the response indicates rate limiting"""
        if isinstance(data, dict):
            info_msg = data.get('Information', '').lower()
            note_msg = data.get('Note', '').lower()
            return 'rate limit' in info_msg or 'rate limit' in note_msg
        return False

    def _get_cached_data(self, symbol: str) -> Optional[Dict]:
        """Get cached data if available and not expired"""
        now = time.time()
        if symbol in self._cache and self._cache_expiry.get(symbol, 0) > now:
            return self._cache[symbol]
        return None

    def _cache_data(self, symbol: str, data: Dict):
        """Cache the data with expiration"""
        self._cache[symbol] = data
        self._cache_expiry[symbol] = time.time() + self._cache_duration

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
                logger.info(f"Raw API response: {data}")

                if self._is_rate_limited(data):
                    return {"error": "Rate limit reached. Please try again in a few minutes."}

                return data
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed (attempt {attempt + 1}/{MAX_RETRIES}): {str(e)}")
                if attempt == MAX_RETRIES - 1:
                    return {"error": str(e)}
                time.sleep(RETRY_DELAY * (attempt + 1))

        return {"error": "Maximum retries exceeded"}

    def get_stock_price(self, symbol: str) -> Dict:
        """Get current price and daily change for a single stock"""
        logger.info(f"Fetching price for stock: {symbol}")

        # Check cache first
        cached_data = self._get_cached_data(symbol)
        if cached_data:
            logger.info(f"Returning cached data for {symbol}")
            return cached_data

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
            if quote and len(quote) > 0:
                try:
                    price = float(quote.get('05. price', 0))
                    change_percent = float(quote.get('10. change percent', '0').rstrip('%'))

                    formatted_data = {
                        symbol.upper(): {
                            "usd": price,
                            "usd_24h_change": change_percent,
                            "name": symbol.upper()
                        }
                    }
                    logger.info(f"Formatted stock data: {formatted_data}")

                    # Cache the successful response
                    self._cache_data(symbol, formatted_data)
                    return formatted_data

                except (ValueError, TypeError) as e:
                    logger.error(f"Error parsing quote data: {str(e)}")
                    return {"error": f"Invalid data format for {symbol}"}

        return {"error": f"No data found for {symbol}"}

    def get_stock_prices(self) -> Dict:
        """Get current prices for multiple stocks using default list"""
        logger.info(f"Fetching prices for default stocks: {DEFAULT_STOCKS}")

        all_data = {}
        rate_limited = False

        for symbol in DEFAULT_STOCKS:
            # Check cache first
            cached_data = self._get_cached_data(symbol)
            if cached_data:
                logger.info(f"Using cached data for {symbol}")
                # Fix: Only update all_data if cached_data doesn't have an error
                if "error" not in cached_data:
                    all_data.update(cached_data)
                continue

            try:
                data = self.get_stock_price(symbol)
                logger.info(f"Stock data for {symbol}: {data}")

                # Check for rate limit error
                if "error" in data and "rate limit" in data["error"].lower():
                    logger.warning(f"Rate limit hit for {symbol}, will try fallback API")
                    rate_limited = True
                    break
                # Fix: Only update all_data if data doesn't have an error
                elif "error" not in data:
                    all_data.update(data)

                # Add small delay between API calls to avoid hitting rate limits
                time.sleep(0.2)
            except Exception as e:
                logger.error(f"Error fetching price for {symbol}: {str(e)}")
                continue

        if not all_data:
            if rate_limited:
                return {"error": "Rate limit reached. Please try again in a few minutes."}
            return {"error": "No stock data available"}

        logger.info(f"Combined stock data: {all_data}")
        return all_data