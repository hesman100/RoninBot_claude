import requests
import logging
import time
import random
from typing import Dict, List, Optional
from .config import REQUEST_TIMEOUT, MAX_RETRIES, RETRY_DELAY, DEFAULT_VN_STOCKS, VN_STOCK_COMPANY_NAMES

logger = logging.getLogger(__name__)

class VietnamStockAPI:
    def __init__(self):
        self.session = requests.Session()
        self._cache = {}
        self._cache_expiry = {}
        self._cache_duration = 900  # Cache for 15 minutes to reduce API requests
        
        # Financial Modeling Prep API for Vietnam stocks
        self.fmp_base_url = "https://financialmodelingprep.com/api/v3"
        # Get API key from environment (provided by user)
        import os
        self.fmp_api_key = os.getenv('FMP_API_KEY', 'demo')
        
        # Alternative endpoints
        self.backup_sources = [
            "https://api.exchangerate-api.com/v4/latest/USD",  # For currency conversion
        ]

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

    def _make_fmp_request(self, endpoint: str) -> Dict:
        """Make a request to Financial Modeling Prep API with retry logic"""
        url = f"{self.fmp_base_url}/{endpoint}"
        logger.info(f"Making request to FMP: {url}")

        for attempt in range(MAX_RETRIES):
            try:
                if attempt > 0:
                    delay = RETRY_DELAY * (2 ** attempt) + random.uniform(0, 1)
                    logger.info(f"Waiting {delay:.2f} seconds before retry...")
                    time.sleep(delay)

                params = {"apikey": self.fmp_api_key}
                response = self.session.get(url, params=params, timeout=REQUEST_TIMEOUT)
                response.raise_for_status()
                data = response.json()
                
                logger.info(f"FMP response received with {len(data) if isinstance(data, list) else 'dict'} items")
                return {"success": True, "data": data}

            except requests.exceptions.RequestException as e:
                logger.error(f"FMP request failed on attempt {attempt + 1}: {str(e)}")
                if attempt < MAX_RETRIES - 1:
                    continue
                else:
                    return {"success": False, "error": f"Request failed after {MAX_RETRIES} attempts: {str(e)}"}

        return {"success": False, "error": "Max retries exceeded"}

    def get_stock_price(self, symbol: str) -> Dict:
        """Get current price for a single Vietnam stock using free APIs with extended caching"""
        logger.info(f"Fetching price for Vietnam stock: {symbol}")

        # Check cache first (15-minute cache to reduce API calls)
        cached_data = self._get_cached_data(symbol)
        if cached_data:
            logger.info(f"Returning cached data for {symbol}")
            return cached_data

        try:
            # Try Financial Modeling Prep first (supports international markets)
            vn_symbol = f"{symbol.upper().strip()}.VN"
            logger.info(f"Trying FMP API for symbol: {vn_symbol}")

            # Try quote endpoint
            result = self._make_fmp_request(f"quote/{vn_symbol}")
            
            if result["success"] and result["data"]:
                data = result["data"]
                if isinstance(data, list) and len(data) > 0:
                    stock_data = data[0]
                    
                    price = stock_data.get('price', 0)
                    change_percent = stock_data.get('changesPercentage', 0)
                    
                    if price > 0:
                        # Format the response
                        formatted_data = {
                            symbol.upper(): {
                                "usd": price,  # Actually in VND
                                "usd_24h_change": change_percent,
                                "name": VN_STOCK_COMPANY_NAMES.get(symbol.upper(), symbol.upper())
                            }
                        }
                        logger.info(f"Successfully got Vietnam stock data from FMP: {formatted_data}")

                        # Cache for 15 minutes to reduce API calls
                        self._cache_data(symbol, formatted_data)
                        return formatted_data

            # If FMP doesn't work, return informative error message
            logger.warning(f"No data available for {symbol} from free APIs")
            return {
                "error": f"Vietnam stock data for {symbol} is currently unavailable. "
                        f"Free APIs have limited coverage for Vietnamese market. "
                        f"Please try again later or check if {symbol} is a valid Vietnam stock symbol."
            }

        except Exception as e:
            logger.error(f"Error fetching stock price for {symbol}: {str(e)}")
            return {"error": f"Unable to fetch data for {symbol}: {str(e)}"}

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