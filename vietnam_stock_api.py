import yfinance as yf
import logging
import time
from typing import Dict, List, Optional
from config import REQUEST_TIMEOUT, MAX_RETRIES, RETRY_DELAY, DEFAULT_VN_STOCKS

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

    def _find_vietnam_symbol(self, symbol: str) -> str:
        """Try different symbol formats for Vietnam stocks"""
        symbol = symbol.upper().strip()

        # Try different exchange suffixes
        suffixes = ['.HO', '.VN']  # .HO for HOSE stocks, .VN as fallback

        for suffix in suffixes:
            test_symbol = f"{symbol}{suffix}"
            logger.info(f"Trying symbol format: {test_symbol}")

            try:
                ticker = yf.Ticker(test_symbol)
                info = ticker.info

                # Verify we got valid data
                if info and info.get('regularMarketPrice'):
                    logger.info(f"Found working symbol: {test_symbol}")
                    return test_symbol
            except Exception as e:
                logger.debug(f"Symbol {test_symbol} not found: {str(e)}")
                continue

        # If no suffix worked, return the first format as default
        return f"{symbol}.HO"

    def get_stock_price(self, symbol: str) -> Dict:
        """Get current price for a single Vietnam stock"""
        logger.info(f"Fetching price for Vietnam stock: {symbol}")

        # Check cache first
        cached_data = self._get_cached_data(symbol)
        if cached_data:
            logger.info(f"Returning cached data for {symbol}")
            return cached_data

        try:
            # Find correct symbol format
            yahoo_symbol = self._find_vietnam_symbol(symbol)
            logger.info(f"Using Yahoo Finance symbol: {yahoo_symbol}")

            ticker = yf.Ticker(yahoo_symbol)
            info = ticker.info

            if not info or 'regularMarketPrice' not in info:
                logger.error(f"No market data available for {symbol}")
                return {"error": f"No data found for {symbol}. Please verify the stock symbol."}

            try:
                # Extract price information
                price = float(info.get('regularMarketPrice', 0))
                prev_close = float(info.get('regularMarketPreviousClose', info.get('previousClose', price)))
                change_percent = ((price - prev_close) / prev_close * 100) if prev_close else 0

                # Get company name from multiple possible fields
                company_name = (
                    info.get('longName') or 
                    info.get('shortName') or 
                    info.get('displayName') or 
                    symbol.upper()
                )

                formatted_data = {
                    symbol.upper(): {
                        "usd": price,  # Actually in VND but keeping same structure
                        "usd_24h_change": change_percent,
                        "name": company_name
                    }
                }
                logger.info(f"Formatted stock data: {formatted_data}")

                # Cache the successful response
                self._cache_data(symbol, formatted_data)
                return formatted_data

            except (ValueError, TypeError, KeyError) as e:
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