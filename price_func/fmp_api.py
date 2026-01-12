"""
Commodity price API client for Gold, Silver, and Platinum using MetalpriceAPI
"""
import requests
import logging
import os
from typing import Dict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

METALPRICEAPI_KEY = os.environ.get('METALPRICEAPI_KEY', '')
METALPRICEAPI_BASE_URL = 'https://api.metalpriceapi.com/v1'

_commodity_cache = {
    'data': None,
    'timestamp': None,
    'cache_duration': timedelta(minutes=5)
}

GOLD_SUPPLY_OUNCES = 6_950_000_000
SILVER_SUPPLY_OUNCES = 54_700_000_000
PLATINUM_SUPPLY_OUNCES = 320_000_000


def get_commodity_prices() -> Dict:
    """
    Fetch gold, silver, and platinum prices from MetalpriceAPI
    Returns dict with commodity price data in format compatible with crypto data
    """
    global _commodity_cache
    
    now = datetime.now()
    if (_commodity_cache['data'] is not None and 
        _commodity_cache['timestamp'] is not None and
        now - _commodity_cache['timestamp'] < _commodity_cache['cache_duration']):
        logger.info("Returning cached commodity prices")
        return _commodity_cache['data']
    
    result = {}
    
    if not METALPRICEAPI_KEY:
        logger.error("METALPRICEAPI_KEY not set in environment variables")
        return result
    
    try:
        logger.info("Fetching metal prices from MetalpriceAPI")
        url = f"{METALPRICEAPI_BASE_URL}/latest"
        params = {
            'api_key': METALPRICEAPI_KEY,
            'base': 'USD',
            'currencies': 'XAU,XAG,XPT'
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if not data.get('success', False):
            logger.error(f"MetalpriceAPI error: {data.get('error', 'Unknown error')}")
            return result
        
        rates = data.get('rates', {})
        logger.info(f"MetalpriceAPI raw rates: {rates}")
        
        gold_price = rates.get('USDXAU', 0)
        if gold_price and gold_price > 0:
            gold_market_cap = GOLD_SUPPLY_OUNCES * gold_price
            result['GOLD'] = {
                'usd': round(gold_price, 2),
                'usd_24h_change': 0,
                'market_cap': gold_market_cap,
                'name': 'GOLD'
            }
            logger.info(f"Gold price: ${gold_price:.2f}")
        
        silver_price = rates.get('USDXAG', 0)
        if silver_price and silver_price > 0:
            silver_market_cap = SILVER_SUPPLY_OUNCES * silver_price
            result['SLVR'] = {
                'usd': round(silver_price, 2),
                'usd_24h_change': 0,
                'market_cap': silver_market_cap,
                'name': 'SLVR'
            }
            logger.info(f"Silver price: ${silver_price:.2f}")
        
        platinum_price = rates.get('USDXPT', 0)
        if platinum_price and platinum_price > 0:
            platinum_market_cap = PLATINUM_SUPPLY_OUNCES * platinum_price
            result['PLAT'] = {
                'usd': round(platinum_price, 2),
                'usd_24h_change': 0,
                'market_cap': platinum_market_cap,
                'name': 'PLAT'
            }
            logger.info(f"Platinum price: ${platinum_price:.2f}")
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching metal prices: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error fetching metal prices: {str(e)}")
    
    if result:
        _commodity_cache['data'] = result
        _commodity_cache['timestamp'] = now
    
    logger.info(f"Formatted commodity data: {result}")
    return result


def get_gold_price() -> Dict:
    """Get gold price only (for backward compatibility)"""
    commodities = get_commodity_prices()
    if 'GOLD' in commodities:
        return {'GOLD': commodities['GOLD']}
    return {}


def get_silver_price() -> Dict:
    """Get silver price only"""
    commodities = get_commodity_prices()
    if 'SLVR' in commodities:
        return {'SLVR': commodities['SLVR']}
    return {}
