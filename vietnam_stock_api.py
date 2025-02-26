import requests
import logging
import time
from typing import Dict, List, Optional
from config import REQUEST_TIMEOUT, MAX_RETRIES, RETRY_DELAY, DEFAULT_VN_STOCKS

logger = logging.getLogger(__name__)

class VietnamStockAPI:
    def __init__(self):
        self.base_url = "https://wgateway-iboard.ssi.com.vn/v5/stocks"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0',
            'Referer': 'https://iboard.ssi.com.vn/',
            'Origin': 'https://iboard.ssi.com.vn'
        })
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

    def _make_request(self, symbol: str) -> Dict:
        """Make a request to SSI API with retry logic"""
        url = f"{self.base_url}/quote/{symbol}"
        logger.info(f"Making request to SSI API: {url}")

        for attempt in range(MAX_RETRIES):
            try:
                response = self.session.get(
                    url,
                    timeout=REQUEST_TIMEOUT
                )
                response.raise_for_status()
                data = response.json()
                logger.info(f"SSI API response: {data}")
                return data
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed (attempt {attempt + 1}/{MAX_RETRIES}): {str(e)}")
                if attempt == MAX_RETRIES - 1:
                    return {"error": str(e)}
                time.sleep(RETRY_DELAY * (attempt + 1))

        return {"error": "Maximum retries exceeded"}

    def get_stock_price(self, symbol: str) -> Dict:
        """Get current price for a single Vietnam stock"""
        logger.info(f"Fetching price for Vietnam stock: {symbol}")

        # Check cache first
        cached_data = self._get_cached_data(symbol)
        if cached_data:
            logger.info(f"Returning cached data for {symbol}")
            return cached_data

        try:
            # Get current quote
            data = self._make_request(symbol.upper())
            logger.info(f"Raw quote data for {symbol}: {data}")

            if "error" in data:
                return data

            if isinstance(data, dict):
                price = float(data.get('lastPrice', 0))
                prev_close = float(data.get('priorPrice', price))
                change_percent = ((price - prev_close) / prev_close * 100) if prev_close else 0

                formatted_data = {
                    symbol.upper(): {
                        "usd": price,  # Actually in VND but keeping same structure
                        "usd_24h_change": change_percent,
                        "name": data.get('stockSymbol', symbol.upper())
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

    def get_stock_prices(self, symbols: List[str] = None) -> Dict:
        """Get current prices for multiple Vietnam stocks"""
        if symbols is None:
            symbols = DEFAULT_VN_STOCKS

        logger.info(f"Fetching prices for Vietnam stocks: {symbols}")

        all_data = {}
        for symbol in symbols:
            try:
                data = self.get_stock_price(symbol)
                if not isinstance(data.get('error'), str):
                    all_data.update(data)
                time.sleep(0.2)  # Small delay between requests
            except Exception as e:
                logger.error(f"Error fetching price for {symbol}: {str(e)}")
                continue

        return all_data if all_data else {"error": "No stock data available"}