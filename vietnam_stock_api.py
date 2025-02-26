import requests
import logging
import time
from typing import Dict, List, Optional
from config import REQUEST_TIMEOUT, MAX_RETRIES, RETRY_DELAY, DEFAULT_VN_STOCKS

logger = logging.getLogger(__name__)

class VietnamStockAPI:
    def __init__(self):
        self.base_url = "https://wgateway-iboard.ssi.com.vn/graphql"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Origin': 'https://iboard.ssi.com.vn',
            'Referer': 'https://iboard.ssi.com.vn/'
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

    def _make_request(self, symbols: List[str]) -> Dict:
        """Make a GraphQL request to SSI iBoard API with retry logic"""
        query = """
        query stockRealtimes($exchange: String!, $symbols: [String!]) {
            stockRealtimes(exchange: $exchange, symbols: $symbols) {
                symbol
                refPrice
                matchPrice
                matchVolume
                priceChange
                priceChangePercent
                tradingDate
                exchange
                lastMatchTime
                lastMatchPrice
                totalMatchVolume
            }
        }
        """

        variables = {
            "exchange": "HOSE",  # Most VN stocks are on HOSE
            "symbols": symbols
        }

        payload = {
            "query": query,
            "variables": variables
        }

        logger.info(f"Making request to SSI iBoard API with symbols: {symbols}")

        for attempt in range(MAX_RETRIES):
            try:
                response = self.session.post(
                    self.base_url,
                    json=payload,
                    timeout=REQUEST_TIMEOUT
                )
                response.raise_for_status()
                data = response.json()
                logger.info(f"SSI iBoard API response status: {response.status_code}")
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
            data = self._make_request([symbol.upper()])
            logger.info(f"Raw quote data for {symbol}: {data}")

            if "errors" in data:
                return {"error": str(data["errors"][0]["message"])}

            if "data" in data and "stockRealtimes" in data["data"] and data["data"]["stockRealtimes"]:
                stock_data = data["data"]["stockRealtimes"][0]

                price = float(stock_data.get('matchPrice', 0))
                change_percent = float(stock_data.get('priceChangePercent', 0))

                formatted_data = {
                    symbol.upper(): {
                        "usd": price,  # Actually in VND but keeping same structure
                        "usd_24h_change": change_percent,
                        "name": symbol.upper()  # Use symbol as name since the API doesn't provide company names
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
            data = self._make_request([s.upper() for s in symbols])

            if "errors" in data:
                return {"error": str(data["errors"][0]["message"])}

            all_data = {}
            if "data" in data and "stockRealtimes" in data["data"]:
                for stock in data["data"]["stockRealtimes"]:
                    symbol = stock["symbol"]
                    price = float(stock.get('matchPrice', 0))
                    change_percent = float(stock.get('priceChangePercent', 0))

                    formatted_data = {
                        "usd": price,
                        "usd_24h_change": change_percent,
                        "name": symbol  # Use symbol as name
                    }
                    all_data[symbol] = formatted_data

            return all_data if all_data else {"error": "No stock data available"}

        except Exception as e:
            logger.error(f"Error fetching multiple stock prices: {str(e)}")
            return {"error": str(e)}