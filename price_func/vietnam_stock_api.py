import requests
import logging
import time
import random
from typing import Dict, List, Optional
from .config import (
    ALPHAVANTAGE_API_KEY,
    ALPHAVANTAGE_BASE_URL,
    REQUEST_TIMEOUT, 
    MAX_RETRIES, 
    RETRY_DELAY, 
    DEFAULT_VN_STOCKS, 
    VN_STOCK_COMPANY_NAMES
)

logger = logging.getLogger(__name__)

class VietnamStockAPI:
    def __init__(self):
        self.api_key = ALPHAVANTAGE_API_KEY
        self.base_url = ALPHAVANTAGE_BASE_URL
        self.session = requests.Session()
        self._cache = {}
        self._cache_expiry = {}
        self._cache_duration = 60  # Cache for 1 minute to match other APIs

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

    def _is_rate_limited(self, data: Dict) -> bool:
        """Check if the response indicates rate limiting"""
        if isinstance(data, dict):
            info_msg = data.get('Information', '').lower()
            note_msg = data.get('Note', '').lower()
            return 'rate limit' in info_msg or 'rate limit' in note_msg
        return False

    def _make_request(self, params: Dict) -> Dict:
        """Make a request to Alpha Vantage API with retry logic"""
        logger.info(f"Making request to Alpha Vantage for Vietnam stock with params: {params}")

        for attempt in range(MAX_RETRIES):
            try:
                if attempt > 0:
                    delay = RETRY_DELAY * (2 ** attempt) + random.uniform(0, 1)
                    logger.info(f"Waiting {delay:.2f} seconds before retry...")
                    time.sleep(delay)

                response = self.session.get(
                    self.base_url,
                    params=params,
                    timeout=REQUEST_TIMEOUT
                )
                response.raise_for_status()
                data = response.json()
                
                logger.info(f"Alpha Vantage response keys: {list(data.keys()) if isinstance(data, dict) else 'not a dict'}")

                # Check for rate limiting
                if self._is_rate_limited(data):
                    logger.warning(f"Rate limited on attempt {attempt + 1}")
                    if attempt < MAX_RETRIES - 1:
                        continue
                    else:
                        return {"error": "Rate limit exceeded. Please try again later."}

                return data

            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed on attempt {attempt + 1}: {str(e)}")
                if attempt < MAX_RETRIES - 1:
                    continue
                else:
                    return {"error": f"Request failed after {MAX_RETRIES} attempts: {str(e)}"}

        return {"error": "Max retries exceeded"}

    def get_stock_price(self, symbol: str) -> Dict:
        """Get current price for a single Vietnam stock using Alpha Vantage"""
        logger.info(f"Fetching price for Vietnam stock: {symbol}")

        # Check cache first
        cached_data = self._get_cached_data(symbol)
        if cached_data:
            logger.info(f"Returning cached data for {symbol}")
            return cached_data

        try:
            # Format symbol for Alpha Vantage (Vietnam stocks end with .VN)
            av_symbol = f"{symbol.upper().strip()}.VN"
            logger.info(f"Using Alpha Vantage symbol: {av_symbol}")

            # Prepare request parameters for Alpha Vantage
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': av_symbol,
                'apikey': self.api_key
            }

            # Make request to Alpha Vantage
            data = self._make_request(params)
            
            if "error" in data:
                logger.error(f"Failed to fetch data for {av_symbol}: {data['error']}")
                return {"error": f"Unable to fetch data for {symbol}: {data['error']}"}

            # Parse Alpha Vantage response
            try:
                global_quote = data.get('Global Quote', {})
                
                if not global_quote:
                    logger.error(f"No global quote data found for {symbol}")
                    return {"error": f"No data found for {symbol}. Make sure it's a valid Vietnam stock symbol."}

                # Extract data from Alpha Vantage response
                price = float(global_quote.get('05. price', 0))
                change_percent = float(global_quote.get('10. change percent', '0').replace('%', ''))

                if price == 0:
                    logger.error(f"Invalid price data for {symbol}")
                    return {"error": f"Invalid price data for {symbol}"}

                # Format the response to match existing structure
                formatted_data = {
                    symbol.upper(): {
                        "usd": price,  # Actually in VND but keeping same structure
                        "usd_24h_change": change_percent,
                        "name": VN_STOCK_COMPANY_NAMES.get(symbol.upper(), symbol.upper())
                    }
                }
                logger.info(f"Successfully formatted Vietnam stock data: {formatted_data}")

                # Cache the successful response
                self._cache_data(symbol, formatted_data)
                return formatted_data

            except (ValueError, TypeError, KeyError) as e:
                logger.error(f"Error parsing Alpha Vantage data for {symbol}: {str(e)}")
                return {"error": f"Invalid data format for {symbol}"}

        except Exception as e:
            logger.error(f"Error fetching stock price for {symbol}: {str(e)}")
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
                time.sleep(0.2)  # Small delay between requests to avoid rate limits
            except Exception as e:
                logger.error(f"Error fetching price for {symbol}: {str(e)}")
                continue

        if not all_data:
            logger.warning("No stock data available for any requested symbols")
            return {"error": "No stock data available"}

        return all_data