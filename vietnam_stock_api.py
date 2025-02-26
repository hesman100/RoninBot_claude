import requests
import logging
import time
from typing import Dict, List, Optional
from config import REQUEST_TIMEOUT, MAX_RETRIES, RETRY_DELAY, DEFAULT_VN_STOCKS

logger = logging.getLogger(__name__)

class VietnamStockAPI:
    def __init__(self):
        self.base_url = "https://fc-data.ssi.com.vn/api/v2/Market"
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
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

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make a request to SSI FastConnect API with retry logic"""
        url = f"{self.base_url}/{endpoint}"
        logger.info(f"Making request to SSI FastConnect API: {url} with params: {params}")

        for attempt in range(MAX_RETRIES):
            try:
                response = self.session.get(
                    url,
                    params=params,
                    timeout=REQUEST_TIMEOUT
                )
                response.raise_for_status()
                data = response.json()
                logger.info(f"SSI FastConnect API response: {data}")
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
            # Get current quote using SSI FastConnect API
            params = {
                'symbol': symbol.upper(),
                'offset': 0,
                'limit': 1
            }

            data = self._make_request('SecuritiesDetails', params)
            logger.info(f"Raw quote data for {symbol}: {data}")

            if "error" in data:
                return data

            if "data" in data and len(data["data"]) > 0:
                stock_data = data["data"][0]

                price = float(stock_data.get('matchPrice', 0))
                prev_close = float(stock_data.get('refPrice', price))
                change_percent = float(stock_data.get('changePercent', 0))

                formatted_data = {
                    symbol.upper(): {
                        "usd": price,  # Actually in VND but keeping same structure
                        "usd_24h_change": change_percent,
                        "name": stock_data.get('stockName', symbol.upper())
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

        try:
            # Get data for all symbols in one request
            params = {
                'symbol': ','.join(symbols),
                'offset': 0,
                'limit': len(symbols)
            }

            data = self._make_request('SecuritiesDetails', params)

            if "error" in data:
                return data

            all_data = {}
            if "data" in data:
                for stock in data["data"]:
                    symbol = stock.get('symbol')
                    if symbol:
                        price = float(stock.get('matchPrice', 0))
                        change_percent = float(stock.get('changePercent', 0))

                        formatted_data = {
                            "usd": price,
                            "usd_24h_change": change_percent,
                            "name": stock.get('stockName', symbol)
                        }
                        all_data[symbol] = formatted_data

            return all_data if all_data else {"error": "No stock data available"}

        except Exception as e:
            logger.error(f"Error fetching multiple stock prices: {str(e)}")
            return {"error": str(e)}