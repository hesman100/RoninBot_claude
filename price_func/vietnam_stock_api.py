import yfinance as yf
import logging
import time
import random
from typing import Dict, List, Optional
from .config import REQUEST_TIMEOUT, MAX_RETRIES, RETRY_DELAY, DEFAULT_VN_STOCKS, VN_STOCK_COMPANY_NAMES

logger = logging.getLogger(__name__)

class VietnamStockAPI:
    def __init__(self):
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

    def _fetch_with_retry(self, yahoo_symbol: str, max_retries: int = 3) -> Dict:
        """Fetch data with retry logic for rate limiting"""
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempting to fetch {yahoo_symbol} (attempt {attempt + 1}/{max_retries})")
                
                # Add random delay to avoid rate limiting
                if attempt > 0:
                    delay = RETRY_DELAY * (2 ** attempt) + random.uniform(0, 1)
                    logger.info(f"Waiting {delay:.2f} seconds before retry...")
                    time.sleep(delay)
                
                # Use yfinance download function to get latest data
                data = yf.download(
                    yahoo_symbol,
                    period="2d",  # Get 2 days of data to calculate change
                    interval="1d",
                    progress=False
                )
                
                if data is not None and not data.empty:
                    return {"success": True, "data": data}
                else:
                    logger.warning(f"No data returned for {yahoo_symbol} on attempt {attempt + 1}")
                    
            except Exception as e:
                error_msg = str(e).lower()
                logger.error(f"Attempt {attempt + 1} failed for {yahoo_symbol}: {str(e)}")
                
                # Check if it's a rate limit error
                if "rate limit" in error_msg or "too many requests" in error_msg:
                    if attempt < max_retries - 1:
                        delay = RETRY_DELAY * (2 ** attempt) + random.uniform(1, 3)
                        logger.info(f"Rate limited. Waiting {delay:.2f} seconds before retry...")
                        time.sleep(delay)
                        continue
                    else:
                        return {"success": False, "error": "Rate limit exceeded. Please try again later."}
                else:
                    return {"success": False, "error": str(e)}
        
        return {"success": False, "error": "Max retries exceeded"}

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

            # Fetch data with retry logic
            result = self._fetch_with_retry(yahoo_symbol)
            
            if not result["success"]:
                error_msg = result["error"]
                logger.error(f"Failed to fetch data for {yahoo_symbol}: {error_msg}")
                return {"error": f"Unable to fetch data for {symbol}: {error_msg}"}
            
            data = result["data"]

            try:
                # Get the latest price from today's data
                latest_row = data.iloc[-1]
                prev_row = data.iloc[-2] if len(data) > 1 else latest_row

                # Handle both single and multi-column data
                if isinstance(latest_row['Close'], (int, float)):
                    price = float(latest_row['Close'])
                    prev_close = float(prev_row['Close'])
                else:
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