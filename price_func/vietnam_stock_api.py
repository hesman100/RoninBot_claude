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
        self._cache_duration = 1800  # Cache for 30 minutes to significantly reduce API requests

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

    def _fetch_with_vndirect(self, symbol: str) -> Dict:
        """Fetch data using VND Direct API (Vietnamese broker with free API access)"""
        try:
            logger.info(f"Fetching data for {symbol} using VND Direct API")
            
            # VND Direct real-time API endpoint
            import requests
            import time
            from datetime import datetime, timedelta
            
            # Get current timestamp and yesterday's timestamp
            now = int(time.time())
            yesterday = now - 86400
            
            # VND Direct chart API for historical data
            url = f"https://dchart-api.vndirect.com.vn/dchart/history"
            params = {
                'resolution': '1D',
                'symbol': symbol.upper(),
                'from': yesterday,
                'to': now
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('s') == 'ok' and 'c' in data and len(data['c']) > 0:
                # Get the latest close price
                latest_price = data['c'][-1]  # Latest close price
                prev_price = data['c'][-2] if len(data['c']) > 1 else latest_price
                
                # Calculate change percentage
                change_percent = ((latest_price - prev_price) / prev_price * 100) if prev_price else 0
                
                return {
                    "success": True,
                    "price": float(latest_price),
                    "change_percent": float(change_percent)
                }
            else:
                logger.warning(f"No data returned from VND Direct for {symbol}")
                
        except Exception as e:
            logger.error(f"VND Direct API error for {symbol}: {str(e)}")
            
        return {"success": False, "error": "Unable to fetch data from Vietnamese market"}

    def get_stock_price(self, symbol: str) -> Dict:
        """Get current price for a single Vietnam stock using Vietnamese API with extended caching"""
        logger.info(f"Fetching price for Vietnam stock: {symbol}")

        # Check cache first (30-minute cache to significantly reduce API calls)
        cached_data = self._get_cached_data(symbol)
        if cached_data:
            logger.info(f"Returning cached data for {symbol} (30-min cache)")
            return cached_data

        try:
            # Use Vietnamese stock symbol directly (no .VN suffix needed for VND Direct)
            vn_symbol = symbol.upper().strip()
            logger.info(f"Using VND Direct API for symbol: {vn_symbol}")

            # Fetch data using VND Direct Vietnamese API
            result = self._fetch_with_vndirect(vn_symbol)
            
            if result["success"]:
                price = result["price"]
                change_percent = result["change_percent"]
                
                # Format the response to match existing structure
                formatted_data = {
                    symbol.upper(): {
                        "usd": price,  # Actually in VND but keeping same structure
                        "usd_24h_change": change_percent,
                        "name": VN_STOCK_COMPANY_NAMES.get(symbol.upper(), symbol.upper())
                    }
                }
                logger.info(f"Successfully got Vietnam stock data from VND Direct: {formatted_data}")

                # Cache for 30 minutes to significantly reduce API calls
                self._cache_data(symbol, formatted_data)
                return formatted_data
            else:
                error_msg = result.get("error", "Unknown error")
                logger.error(f"Failed to fetch data for {symbol}: {error_msg}")
                return {"error": f"Unable to fetch data for {symbol}. Please try again later."}

        except Exception as e:
            logger.error(f"Error fetching stock price for {symbol}: {str(e)}")
            return {"error": f"Unable to fetch data for {symbol}: {str(e)}"}

    def get_stock_prices(self, symbols: Optional[List[str]] = None) -> Dict:
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