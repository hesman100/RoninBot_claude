import os
import requests
import logging
import time
from typing import Dict, List, Optional
from config import DEFAULT_STOCKS, REQUEST_TIMEOUT, MAX_RETRIES, RETRY_DELAY

logger = logging.getLogger(__name__)

class FinnhubAPI:
    def __init__(self):
        self.api_key = os.getenv('FINNHUB_API_KEY', 'YOUR_API_KEY_HERE')  # Get from environment variable
        self.base_url = "https://finnhub.io/api/v1"
        self.session = requests.Session()
        self._cache = {}
        self._cache_expiry = {}
        self._cache_duration = 300  # Cache for 5 minutes

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

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make a request to Finnhub API with retry logic"""
        url = f"{self.base_url}/{endpoint}"
        params = params or {}
        params['token'] = self.api_key  # Add API key to parameters

        logger.info(f"Making request to Finnhub API: {url} with params: {params}")

        for attempt in range(MAX_RETRIES):
            try:
                response = self.session.get(
                    url,
                    params=params,
                    timeout=REQUEST_TIMEOUT
                )
                response.raise_for_status()
                data = response.json()
                logger.info(f"Finnhub API response: {data}")
                return data
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed (attempt {attempt + 1}/{MAX_RETRIES}): {str(e)}")
                if attempt == MAX_RETRIES - 1:
                    if hasattr(e, 'response') and e.response.status_code == 401:
                        return {"error": "Invalid API key or unauthorized access. Please check your Finnhub API key."}
                    return {"error": str(e)}
                time.sleep(RETRY_DELAY * (attempt + 1))

        return {"error": "Maximum retries exceeded"}

    def get_stock_price(self, symbol: str) -> Dict:
        """Get current price for a single stock"""
        logger.info(f"Fetching price for stock: {symbol}")

        # Check cache first
        cached_data = self._get_cached_data(symbol)
        if cached_data:
            logger.info(f"Returning cached data for {symbol}")
            return cached_data

        try:
            # Get current quote
            data = self._make_request('quote', {'symbol': symbol.upper()})
            logger.info(f"Raw quote data for {symbol}: {data}")

            if "error" in data:
                return data

            if data and 'c' in data:  # Current price exists
                price = data['c']
                prev_close = data['pc']  # Previous close

                # Calculate 24h change
                change_percent = ((price - prev_close) / prev_close) * 100 if prev_close else 0

                formatted_data = {
                    symbol.upper(): {
                        "usd": price,
                        "usd_24h_change": change_percent,
                        "name": symbol.upper()  # Use symbol as name for stocks
                    }
                }
                logger.info(f"Formatted stock data: {formatted_data}")

                # Cache the successful response
                self._cache_data(symbol, formatted_data)
                return formatted_data

            return {"error": f"No data found for {symbol}"}

        except Exception as e:
            logger.error(f"Error fetching stock price: {str(e)}")
            return {"error": str(e)}

    def get_stock_prices(self) -> Dict:
        """Get current prices for multiple stocks"""
        logger.info(f"Fetching prices for default stocks: {DEFAULT_STOCKS}")

        all_data = {}
        rate_limited = False

        for symbol in DEFAULT_STOCKS:
            # Check cache first
            cached_data = self._get_cached_data(symbol)
            if cached_data:
                logger.info(f"Using cached data for {symbol}")
                if not isinstance(cached_data.get('error'), str):
                    all_data.update(cached_data)
                continue

            try:
                data = self.get_stock_price(symbol)
                if "error" in data and "rate limit" in data["error"].lower():
                    rate_limited = True
                    break
                elif not isinstance(data.get('error'), str):
                    all_data.update(data)
                time.sleep(0.2)  # Small delay between requests
            except Exception as e:
                logger.error(f"Error fetching price for {symbol}: {str(e)}")
                continue

        if not all_data:
            if rate_limited:
                return {"error": "Rate limit reached. Please try again in a few minutes."}
            return {"error": "No stock data available"}
        return all_data