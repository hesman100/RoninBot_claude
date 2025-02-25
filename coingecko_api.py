import requests
import time
from typing import Dict, List, Optional, Tuple
from config import COINGECKO_BASE_URL, REQUEST_TIMEOUT, MAX_RETRIES, RETRY_DELAY, DEFAULT_CRYPTOCURRENCIES

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
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Making request to {url} with params: {params}")

        for attempt in range(MAX_RETRIES):
            try:
                response = self.session.get(
                    url,
                    params=params,
                    timeout=REQUEST_TIMEOUT
                )
                response.raise_for_status()
                data = response.json()
                logger.info(f"Successful response: {data}")
                return data
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed (attempt {attempt + 1}/{MAX_RETRIES}): {str(e)}")
                if attempt == MAX_RETRIES - 1:
                    if hasattr(e, 'response') and hasattr(e.response, 'status_code') and e.response.status_code == 429:
                        return {"error": "Rate limit exceeded. Please try again later."}
                    return {"error": str(e)}  # Return error dict instead of raising
                time.sleep(RETRY_DELAY * (attempt + 1))  # Exponential backoff

        return {"error": "Maximum retries exceeded"}

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
        import logging
        logger = logging.getLogger(__name__)

        # If it's in our predefined mapping, use that
        from config import TICKER_TO_ID
        symbol = symbol_or_id.upper()
        logger.info(f"Looking up coin ID for input: {symbol}")

        # Special debug for BNB
        if symbol == "BNB":
            logger.info("Processing BNB specifically")
            logger.info(f"Available mappings: {TICKER_TO_ID}")
            if symbol in TICKER_TO_ID:
                logger.info(f"BNB mapping found: {TICKER_TO_ID[symbol]}")

        if symbol in TICKER_TO_ID:
            coin_id = TICKER_TO_ID[symbol]
            logger.info(f"Found coin ID in TICKER_TO_ID mapping: {coin_id}")
            return coin_id

        # Try searching for the coin if not in our mappings
        try:
            search_data = self._make_request('search', {'query': symbol_or_id})
            if search_data and 'coins' in search_data and search_data['coins']:
                coin_id = search_data['coins'][0]['id']
                logger.info(f"Found coin ID via search: {coin_id}")
                return coin_id
        except Exception as e:
            logger.error(f"Search request failed: {str(e)}")

        # If not found as symbol, return the original input (assuming it's an ID)
        logger.info(f"Using input as coin ID: {symbol_or_id.lower()}")
        return symbol_or_id.lower()

    def get_price(self, crypto_id: str) -> Dict:
        """Get current price for a single cryptocurrency"""
        import logging
        logger = logging.getLogger(__name__)

        # Convert symbol to ID if needed
        coin_id = self.get_coin_id(crypto_id)
        logger.info(f"Fetching price for coin ID: {coin_id}")

        params = {
            'ids': coin_id,
            'vs_currencies': 'usd',
            'include_24hr_change': 'true',
            'include_market_cap': 'true'
        }

        logger.info(f"Making API request with params: {params}")  # Added logging
        data = self._make_request('simple/price', params)
        logger.info(f"Received raw price data: {data}")

        # If we got valid data back, create a properly structured response
        if isinstance(data, dict) and coin_id in data:
            logger.info(f"Found price data for {coin_id}: {data[coin_id]}")
            return {coin_id: data[coin_id]}

        # Log error case
        logger.error(f"No price data found for {coin_id}. Response: {data}")
        if isinstance(data, dict) and "error" in data:
            return data
        return {"error": f"No data found for {coin_id}"}

    def get_prices(self, crypto_ids: List[str] = None) -> Dict:
        """Get current prices for multiple cryptocurrencies"""
        import logging
        logger = logging.getLogger(__name__)

        # If no specific IDs provided, use default list
        if crypto_ids is None:
            crypto_ids = DEFAULT_CRYPTOCURRENCIES

        logger.info(f"Fetching prices for cryptocurrencies: {crypto_ids}")

        params = {
            'ids': ','.join(crypto_ids),
            'vs_currencies': 'usd',
            'include_24hr_change': 'true',
            'include_market_cap': 'true'  
        }

        data = self._make_request('simple/price', params)
        logger.info(f"Received price data for coins: {list(data.keys())}")
        return data