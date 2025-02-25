import requests
import time
from typing import Dict, List, Optional
from config import COINGECKO_BASE_URL, REQUEST_TIMEOUT, MAX_RETRIES, RETRY_DELAY

class CoinGeckoAPI:
    def __init__(self):
        self.base_url = COINGECKO_BASE_URL
        self.session = requests.Session()

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

    def get_price(self, crypto_id: str) -> Dict:
        """Get current price for a single cryptocurrency"""
        params = {
            'ids': crypto_id,
            'vs_currencies': 'usd',
            'include_24hr_change': 'true',
            'include_market_cap': 'true'
        }

        return self._make_request('simple/price', params)

    def get_prices(self, crypto_ids: List[str]) -> Dict:
        """Get current prices for multiple cryptocurrencies"""
        params = {
            'ids': ','.join(crypto_ids),
            'vs_currencies': 'usd',
            'include_24hr_change': 'true',
            'include_market_cap': 'true'
        }

        return self._make_request('simple/price', params)