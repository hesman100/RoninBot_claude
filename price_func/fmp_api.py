"""
Commodity price API client for Gold, Silver, and Platinum
Primary: MetalpriceAPI, Backup: Metals-API
"""
import requests
import logging
import os
from typing import Dict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

METALPRICEAPI_KEY = os.environ.get('METALPRICEAPI_KEY', '')
METALPRICEAPI_BASE_URL = 'https://api.metalpriceapi.com/v1'

METALSAPI_KEY = os.environ.get('METALSAPI_KEY', '')
METALSAPI_BASE_URL = 'https://metals-api.com/api'

_commodity_cache = {
    'data': None,
    'timestamp': None,
    'cache_duration': timedelta(minutes=5)
}

GOLD_SUPPLY_OUNCES = 6_950_000_000
SILVER_SUPPLY_OUNCES = 54_700_000_000
PLATINUM_SUPPLY_OUNCES = 320_000_000


def _fetch_from_metalpriceapi() -> Dict:
    """Fetch prices from MetalpriceAPI (primary)"""
    if not METALPRICEAPI_KEY:
        logger.warning("METALPRICEAPI_KEY not set")
        return {}
    
    result = {}
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
            error_info = data.get('error', {})
            logger.error(f"MetalpriceAPI error: {error_info}")
            return {}
        
        rates = data.get('rates', {})
        logger.info(f"MetalpriceAPI raw rates: {rates}")
        
        gold_price = rates.get('USDXAU', 0)
        if gold_price and gold_price > 0:
            result['GOLD'] = {
                'usd': round(gold_price, 2),
                'usd_24h_change': 0,
                'market_cap': GOLD_SUPPLY_OUNCES * gold_price,
                'name': 'GOLD'
            }
            logger.info(f"Gold price: ${gold_price:.2f}")
        
        silver_price = rates.get('USDXAG', 0)
        if silver_price and silver_price > 0:
            result['SLVR'] = {
                'usd': round(silver_price, 2),
                'usd_24h_change': 0,
                'market_cap': SILVER_SUPPLY_OUNCES * silver_price,
                'name': 'SLVR'
            }
            logger.info(f"Silver price: ${silver_price:.2f}")
        
        platinum_price = rates.get('USDXPT', 0)
        if platinum_price and platinum_price > 0:
            result['PLAT'] = {
                'usd': round(platinum_price, 2),
                'usd_24h_change': 0,
                'market_cap': PLATINUM_SUPPLY_OUNCES * platinum_price,
                'name': 'PLAT'
            }
            logger.info(f"Platinum price: ${platinum_price:.2f}")
        
    except Exception as e:
        logger.error(f"MetalpriceAPI error: {str(e)}")
    
    return result


def _fetch_from_metalsapi() -> Dict:
    """Fetch prices from Metals-API (backup)"""
    if not METALSAPI_KEY:
        logger.warning("METALSAPI_KEY not set, skipping backup API")
        return {}
    
    result = {}
    try:
        logger.info("Fetching metal prices from Metals-API (backup)")
        url = f"{METALSAPI_BASE_URL}/latest"
        params = {
            'access_key': METALSAPI_KEY,
            'base': 'USD',
            'symbols': 'XAU,XAG,XPT'
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if not data.get('success', False):
            error_info = data.get('error', {})
            logger.error(f"Metals-API error: {error_info}")
            return {}
        
        rates = data.get('rates', {})
        logger.info(f"Metals-API raw rates: {rates}")
        
        gold_rate = rates.get('XAU', 0)
        if gold_rate and gold_rate > 0:
            gold_price = 1 / gold_rate
            result['GOLD'] = {
                'usd': round(gold_price, 2),
                'usd_24h_change': 0,
                'market_cap': GOLD_SUPPLY_OUNCES * gold_price,
                'name': 'GOLD'
            }
            logger.info(f"Gold price (backup): ${gold_price:.2f}")
        
        silver_rate = rates.get('XAG', 0)
        if silver_rate and silver_rate > 0:
            silver_price = 1 / silver_rate
            result['SLVR'] = {
                'usd': round(silver_price, 2),
                'usd_24h_change': 0,
                'market_cap': SILVER_SUPPLY_OUNCES * silver_price,
                'name': 'SLVR'
            }
            logger.info(f"Silver price (backup): ${silver_price:.2f}")
        
        platinum_rate = rates.get('XPT', 0)
        if platinum_rate and platinum_rate > 0:
            platinum_price = 1 / platinum_rate
            result['PLAT'] = {
                'usd': round(platinum_price, 2),
                'usd_24h_change': 0,
                'market_cap': PLATINUM_SUPPLY_OUNCES * platinum_price,
                'name': 'PLAT'
            }
            logger.info(f"Platinum price (backup): ${platinum_price:.2f}")
        
    except Exception as e:
        logger.error(f"Metals-API error: {str(e)}")
    
    return result


def get_commodity_prices() -> Dict:
    """
    Fetch gold, silver, and platinum prices
    Tries MetalpriceAPI first, falls back to Metals-API if primary fails
    """
    global _commodity_cache
    
    now = datetime.now()
    if (_commodity_cache['data'] is not None and 
        _commodity_cache['timestamp'] is not None and
        now - _commodity_cache['timestamp'] < _commodity_cache['cache_duration']):
        logger.info("Returning cached commodity prices")
        return _commodity_cache['data']
    
    result = _fetch_from_metalpriceapi()
    
    if not result or len(result) < 3:
        logger.info("Primary API failed or incomplete, trying backup API")
        backup_result = _fetch_from_metalsapi()
        if backup_result:
            for key in ['GOLD', 'SLVR', 'PLAT']:
                if key not in result and key in backup_result:
                    result[key] = backup_result[key]
    
    if result:
        _commodity_cache['data'] = result
        _commodity_cache['timestamp'] = now
    
    logger.info(f"Final commodity data: {result}")
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
