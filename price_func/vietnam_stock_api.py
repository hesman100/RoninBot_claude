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

    def _fetch_with_yfinance(self, yahoo_symbol: str) -> Dict:
        """Fetch data using Yahoo Finance with error handling"""
        try:
            logger.info(f"Fetching data for {yahoo_symbol} using Yahoo Finance")
            
            # Use yfinance with minimal requests
            ticker = yf.Ticker(yahoo_symbol)
            info = ticker.info
            
            if info and 'regularMarketPrice' in info:
                price = info.get('regularMarketPrice', 0)
                change_percent = info.get('regularMarketChangePercent', 0)
                
                return {
                    "success": True,
                    "price": price,
                    "change_percent": change_percent
                }
            else:
                # Fallback to historical data if info fails
                hist = ticker.history(period="2d")
                if not hist.empty:
                    latest_price = hist['Close'].iloc[-1]
                    prev_price = hist['Close'].iloc[-2] if len(hist) > 1 else latest_price
                    change_percent = ((latest_price - prev_price) / prev_price * 100) if prev_price else 0
                    
                    return {
                        "success": True,
                        "price": float(latest_price),
                        "change_percent": float(change_percent)
                    }
                    
        except Exception as e:
            logger.error(f"Yahoo Finance error for {yahoo_symbol}: {str(e)}")
            
        return {"success": False, "error": "Unable to fetch data"}

    def get_stock_price(self, symbol: str) -> Dict:
        """Get current price for a single Vietnam stock using Yahoo Finance with extended caching"""
        logger.info(f"Fetching price for Vietnam stock: {symbol}")

        # Check cache first (30-minute cache to significantly reduce API calls)
        cached_data = self._get_cached_data(symbol)
        if cached_data:
            logger.info(f"Returning cached data for {symbol} (30-min cache)")
            return cached_data

        try:
            # Format symbol for Yahoo Finance (Vietnam stocks end with .VN)
            vn_symbol = f"{symbol.upper().strip()}.VN"
            logger.info(f"Using Yahoo Finance symbol: {vn_symbol}")

            # Fetch data using Yahoo Finance
            result = self._fetch_with_yfinance(vn_symbol)
            
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
                logger.info(f"Successfully got Vietnam stock data: {formatted_data}")

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