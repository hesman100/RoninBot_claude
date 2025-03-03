import yfinance as yf
import logging
import time
from typing import Dict, List, Optional
from .config import REQUEST_TIMEOUT, MAX_RETRIES, RETRY_DELAY, DEFAULT_VN_STOCKS, VN_STOCK_COMPANY_NAMES

logger = logging.getLogger(__name__)

class VietnamStockAPI:
    def __init__(self):
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

    def get_stock_price(self, symbol: str) -> Dict:
        """Get current price for a single Vietnam stock"""
        logger.info(f"Fetching price for Vietnam stock: {symbol}")

        # Check cache first
        cached_data = self._get_cached_data(symbol)
        if cached_data:
            logger.info(f"Returning cached data for {symbol}")
            return cached_data

        try:
            # Format symbol for Yahoo Finance
            yahoo_symbol = f"{symbol.upper().strip()}.VN"
            logger.info(f"Using Yahoo Finance symbol: {yahoo_symbol}")

            # Use yfinance download function to get latest data
            data = yf.download(
                yahoo_symbol,
                period="2d",  # Get 2 days of data to calculate change
                interval="1d",
                progress=False
            )

            if data.empty:
                logger.error(f"No market data available for {yahoo_symbol}")
                return {"error": f"No data found for {symbol}. Make sure it's a valid Vietnam stock symbol."}

            try:
                # Get the latest price from today's data
                latest_row = data.iloc[-1]
                prev_row = data.iloc[-2] if len(data) > 1 else latest_row

                price = float(latest_row['Close'].iloc[0])
                prev_close = float(prev_row['Close'].iloc[0])
                change_percent = ((price - prev_close) / prev_close * 100) if prev_close else 0

                # Format the response
                formatted_data = {
                    symbol.upper(): {
                        "usd": price,  # Actually in VND but keeping same structure
                        "usd_24h_change": change_percent,
                        "name": VN_STOCK_COMPANY_NAMES.get(symbol.upper(), symbol.upper())  # Get company name if available
                    }
                }
                logger.info(f"Formatted stock data: {formatted_data}")

                # Cache the successful response
                self._cache_data(symbol, formatted_data)
                return formatted_data

            except (ValueError, TypeError, KeyError, IndexError) as e:
                logger.error(f"Error parsing price data for {symbol}: {str(e)}")
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