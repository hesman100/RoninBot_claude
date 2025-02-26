import yfinance as yf
import logging
import time
from typing import Dict, List, Optional
from config import REQUEST_TIMEOUT, MAX_RETRIES, RETRY_DELAY, DEFAULT_VN_STOCKS, VN_STOCK_COMPANY_NAMES

logger = logging.getLogger(__name__)

class VietnamStockAPI:
    def __init__(self):
        self._cache = {}
        self._cache_expiry = {}
        self._cache_duration = 60  # Cache for 1 minute to ensure fresh data
        self._price_cache = {}
        self._batch_cache = {}
        self._last_batch_update = 0
        self._batch_update_interval = 60  # Update batch data every minute

    def _get_cached_data(self, symbol: str) -> Optional[Dict]:
        """Get cached data if available and not expired"""
        now = time.time()
        if symbol in self._cache and self._cache_expiry.get(symbol, 0) > now:
            logger.info(f"Cache hit for {symbol}")
            return self._cache[symbol]
        return None

    def _cache_data(self, symbol: str, data: Dict):
        """Cache the data with expiration"""
        self._cache[symbol] = data
        self._cache_expiry[symbol] = time.time() + self._cache_duration

    def _update_batch_cache(self, symbols: List[str]):
        """Update cache for multiple symbols at once"""
        now = time.time()
        if now - self._last_batch_update < self._batch_update_interval:
            return

        try:
            # Format symbols for Yahoo Finance
            yahoo_symbols = [f"{symbol.upper().strip()}.VN" for symbol in symbols]
            logger.info(f"Batch updating data for symbols: {yahoo_symbols}")

            # Download data for all symbols at once
            data = yf.download(
                yahoo_symbols,
                period="2d",
                interval="1d",
                progress=False,
                group_by='ticker'
            )

            for symbol in symbols:
                yahoo_symbol = f"{symbol.upper().strip()}.VN"
                if yahoo_symbol in data.columns.levels[0]:
                    symbol_data = data[yahoo_symbol]
                    if not symbol_data.empty:
                        latest_row = symbol_data.iloc[-1]
                        prev_row = symbol_data.iloc[-2] if len(symbol_data) > 1 else latest_row

                        price = float(latest_row['Close'])
                        prev_close = float(prev_row['Close'])
                        change_percent = ((price - prev_close) / prev_close * 100) if prev_close else 0

                        formatted_data = {
                            symbol.upper(): {
                                "usd": price,
                                "usd_24h_change": change_percent,
                                "name": VN_STOCK_COMPANY_NAMES.get(symbol.upper(), symbol.upper())
                            }
                        }
                        self._cache_data(symbol, formatted_data)

            self._last_batch_update = now
            logger.info("Batch update completed successfully")

        except Exception as e:
            logger.error(f"Error in batch update: {str(e)}")

    def get_stock_price(self, symbol: str) -> Dict:
        """Get current price for a single Vietnam stock"""
        logger.info(f"Fetching price for Vietnam stock: {symbol}")

        # Check cache first
        cached_data = self._get_cached_data(symbol)
        if cached_data:
            logger.info(f"Returning cached data for {symbol}")
            return cached_data

        try:
            # Update cache for this symbol and related ones
            self._update_batch_cache([symbol] + DEFAULT_VN_STOCKS[:5])  # Update requested symbol and some default ones

            # Check cache again after batch update
            cached_data = self._get_cached_data(symbol)
            if cached_data:
                return cached_data

            # If still no data available after batch update, return error
            logger.error(f"No data available for {symbol} after batch update")
            return {"error": f"No data found for {symbol}. Make sure it's a valid Vietnam stock symbol."}

        except Exception as e:
            logger.error(f"Error fetching stock price for {symbol}: {str(e)}")
            return {"error": str(e)}

    def get_stock_prices(self, symbols: List[str] = None) -> Dict:
        """Get current prices for multiple Vietnam stocks"""
        if symbols is None:
            symbols = DEFAULT_VN_STOCKS

        logger.info(f"Fetching prices for Vietnam stocks: {symbols}")

        # Update cache for all symbols at once
        self._update_batch_cache(symbols)

        all_data = {}
        for symbol in symbols:
            try:
                cached_data = self._get_cached_data(symbol)
                if cached_data and not isinstance(cached_data.get('error'), str):
                    all_data.update(cached_data)
            except Exception as e:
                logger.error(f"Error fetching price for {symbol}: {str(e)}")
                continue

        if not all_data:
            logger.warning("No stock data available for any requested symbols")
            return {"error": "No stock data available"}

        return all_data