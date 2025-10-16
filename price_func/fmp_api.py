"""
Financial Modeling Prep (FMP) API client for commodity prices (Gold)
"""
import requests
import logging
from typing import Dict
from .config import FMP_API_KEY, FMP_BASE_URL, REQUEST_TIMEOUT
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Cache for gold prices (5 minutes)
_gold_cache = {
    'data': None,
    'timestamp': None,
    'cache_duration': timedelta(minutes=5)
}


def get_gold_price() -> Dict:
    """
    Fetch gold price from FMP API
    Returns dict with gold price data in format compatible with crypto data
    """
    global _gold_cache
    
    # Check cache first
    now = datetime.now()
    if (_gold_cache['data'] is not None and 
        _gold_cache['timestamp'] is not None and
        now - _gold_cache['timestamp'] < _gold_cache['cache_duration']):
        logger.info("Returning cached gold price")
        return _gold_cache['data']
    
    if not FMP_API_KEY:
        logger.error("FMP_API_KEY not found in environment variables")
        return {}
    
    try:
        # Fetch gold price (GCUSD = Gold in USD)
        url = f"{FMP_BASE_URL}/quote/GCUSD"
        params = {'apikey': FMP_API_KEY}
        
        logger.info(f"Fetching gold price from FMP API: {url}")
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        
        data = response.json()
        logger.info(f"FMP API response for gold: {data}")
        
        if not data or len(data) == 0:
            logger.error("No gold price data received from FMP API")
            return {}
        
        gold_data = data[0]  # FMP returns array with single item
        
        # Extract relevant fields
        price = gold_data.get('price', 0)
        change_pct = gold_data.get('changesPercentage', 0)
        
        # Note: FMP doesn't provide market cap for commodities
        # Gold's "market cap" would be total gold supply * price, but that's not standard
        # We'll use 0 for market cap to display "-" in the output
        
        result = {
            'GOLD': {
                'usd': price,
                'usd_24h_change': change_pct,
                'market_cap': 0,  # No market cap for commodities
                'name': 'GOLD'
            }
        }
        
        # Update cache
        _gold_cache['data'] = result
        _gold_cache['timestamp'] = now
        
        logger.info(f"Formatted gold data: {result}")
        return result
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching gold price from FMP API: {str(e)}")
        return {}
    except Exception as e:
        logger.error(f"Unexpected error fetching gold price: {str(e)}")
        return {}
