import requests
import time
from typing import Dict, List, Optional, Tuple
from config import COINGECKO_BASE_URL, REQUEST_TIMEOUT, MAX_RETRIES, RETRY_DELAY

class CoinGeckoAPI:
    def __init__(self):
        self.base_url = COINGECKO_BASE_URL
        self.session = requests.Session()
        self._coin_list_cache = {}
        self._cache_timestamp = 0
        self._cache_duration = 3600  # Cache for 1 hour

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make a request to CoinGecko API with retry logic"""
        url = f"{self.base_url}/{endpoint}"

        for attempt in range(MAX_RETRIES):
            try:
                response = self.session.get(
                    url,
                    params=params,
                    timeout=REQUEST_TIMEOUT
                )
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                if attempt == MAX_RETRIES - 1:
                    return {"error": str(e)}  # Return error dict instead of raising
                time.sleep(RETRY_DELAY)

        return {"error": "Maximum retries exceeded"}  # Fallback error response

    def get_coin_list(self) -> Dict[str, str]:
        """Get a mapping of coin symbols to their IDs, with caching"""
        current_time = time.time()

        # Return cached data if it's still valid
        if self._coin_list_cache and (current_time - self._cache_timestamp) < self._cache_duration:
            return self._coin_list_cache

        try:
            data = self._make_request('coins/list')
            if "error" in data:
                # If error and we have cached data, return cached data
                if self._coin_list_cache:
                    return self._coin_list_cache
                return {}

            # Create symbol to ID mapping (prioritize exact matches)
            symbol_to_id = {}
            for coin in data:
                symbol = coin.get('symbol', '').upper()
                coin_id = coin.get('id', '')

                # Skip invalid entries
                if not symbol or not coin_id:
                    continue

                # Only override if the new coin_id is exactly the same as the symbol
                # (lowercase) or if there's no existing mapping
                if symbol not in symbol_to_id or coin_id == symbol.lower():
                    symbol_to_id[symbol] = coin_id

            # Update cache
            self._coin_list_cache = symbol_to_id
            self._cache_timestamp = current_time
            return symbol_to_id

        except Exception as e:
            # Return cached data if available, empty dict otherwise
            return self._coin_list_cache if self._coin_list_cache else {}

    def get_coin_id(self, symbol_or_id: str) -> str:
        """Convert a symbol to coin ID, or return the ID if it's already an ID"""
        # If it's in our predefined mapping, use that
        from config import TICKER_TO_ID
        if symbol_or_id.upper() in TICKER_TO_ID:
            return TICKER_TO_ID[symbol_or_id.upper()]

        # Get the full coin list
        coin_list = self.get_coin_list()

        # Check if it's a symbol
        symbol = symbol_or_id.upper()
        if symbol in coin_list:
            return coin_list[symbol]

        # If not found as symbol, return the original input (assuming it's an ID)
        return symbol_or_id.lower()

    def get_price(self, crypto_id: str) -> Dict:
        """Get current price for a single cryptocurrency"""
        # Convert symbol to ID if needed
        coin_id = self.get_coin_id(crypto_id)

        params = {
            'ids': coin_id,
            'vs_currencies': 'usd',
            'include_24hr_change': 'true',
            'include_market_cap': 'true'
        }

        return self._make_request('simple/price', params)

    def get_prices(self, crypto_ids: List[str]) -> Dict:
        """Get current prices for multiple cryptocurrencies"""
        # Only fetch prices for cryptocurrencies in our DEFAULT_CRYPTOCURRENCIES list
        from config import DEFAULT_CRYPTOCURRENCIES
        import logging

        logger = logging.getLogger(__name__)
        logger.info(f"Fetching prices for cryptocurrencies: {DEFAULT_CRYPTOCURRENCIES}")

        params = {
            'ids': ','.join(DEFAULT_CRYPTOCURRENCIES),
            'vs_currencies': 'usd',
            'include_24hr_change': 'true',
            'include_market_cap': 'true'
        }

        data = self._make_request('simple/price', params)
        logger.info(f"Received price data for coins: {list(data.keys())}")
        return data