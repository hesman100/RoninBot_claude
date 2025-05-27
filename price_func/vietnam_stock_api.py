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

    def _fetch_with_yahoo_alternative(self, symbol: str) -> Dict:
        """Fetch data using alternative Yahoo Finance approach with proper headers"""
        try:
            logger.info(f"Fetching data for {symbol} using alternative Yahoo Finance method")
            
            import requests
            import json
            
            # Vietnamese stocks use .VN suffix on Yahoo Finance
            vn_symbol = f"{symbol.upper()}.VN"
            
            # Use Yahoo Finance's query API with proper headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/json',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            # Yahoo Finance query API
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{vn_symbol}"
            params = {
                'interval': '1d',
                'range': '2d',
                'includePrePost': 'false',
                'useYfid': 'true',
                'includeAdjustedClose': 'true'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            if data.get('chart') and data['chart'].get('result') and len(data['chart']['result']) > 0:
                result = data['chart']['result'][0]
                
                # Get current price from meta data
                meta = result.get('meta', {})
                current_price = meta.get('regularMarketPrice', 0)
                prev_close = meta.get('previousClose', 0)
                
                if current_price > 0 and prev_close > 0:
                    change_percent = ((current_price - prev_close) / prev_close) * 100
                    
                    return {
                        "success": True,
                        "price": float(current_price),
                        "change_percent": float(change_percent)
                    }
                else:
                    logger.warning(f"Invalid price data from Yahoo for {vn_symbol}")
                    
            else:
                logger.warning(f"No chart data returned from Yahoo for {vn_symbol}")
                
        except Exception as e:
            logger.error(f"Alternative Yahoo Finance error for {symbol}: {str(e)}")
            
        return {"success": False, "error": "Unable to fetch Vietnamese stock data"}

    def get_stock_price(self, symbol: str) -> Dict:
        """Get current price for a single Vietnam stock using Vietnamese API with extended caching"""
        logger.info(f"Fetching price for Vietnam stock: {symbol}")

        # Check cache first (30-minute cache to significantly reduce API calls)
        cached_data = self._get_cached_data(symbol)
        if cached_data:
            logger.info(f"Returning cached data for {symbol} (30-min cache)")
            return cached_data

        try:
            # Use Vietnamese stock symbol for Yahoo Finance
            vn_symbol = symbol.upper().strip()
            logger.info(f"Using alternative Yahoo Finance for Vietnamese symbol: {vn_symbol}")

            # Fetch data using alternative Yahoo Finance method
            result = self._fetch_with_yahoo_alternative(vn_symbol)
            
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