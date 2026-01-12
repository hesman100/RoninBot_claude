"""
Commodity price API client for Gold, Silver, and Platinum
Primary: MetalpriceAPI, Backup: GoldAPI.io
"""
import requests
import logging
import os
from typing import Dict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

METALPRICEAPI_KEY = os.environ.get('METALPRICEAPI_KEY', '')
METALPRICEAPI_BASE_URL = 'https://api.metalpriceapi.com/v1'

GOLDAPIIO_KEY = os.environ.get('GOLDAPIIO_KEY', '')
GOLDAPIIO_BASE_URL = 'https://www.goldapi.io/api'

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


def _fetch_from_goldapiio() -> Dict:
    """Fetch prices from GoldAPI.io (backup)"""
    if not GOLDAPIIO_KEY:
        logger.warning("GOLDAPIIO_KEY not set, skipping backup API")
        return {}
    
    result = {}
    headers = {'x-access-token': GOLDAPIIO_KEY}
    
    metals = [
        ('XAU', 'GOLD', GOLD_SUPPLY_OUNCES),
        ('XAG', 'SLVR', SILVER_SUPPLY_OUNCES),
        ('XPT', 'PLAT', PLATINUM_SUPPLY_OUNCES)
    ]
    
    for symbol, key, supply in metals:
        try:
            logger.info(f"Fetching {symbol} price from GoldAPI.io (backup)")
            url = f"{GOLDAPIIO_BASE_URL}/{symbol}/USD"
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'error' in data:
                logger.error(f"GoldAPI.io error for {symbol}: {data.get('error')}")
                continue
            
            price = data.get('price', 0)
            change_pct = data.get('chp', 0)
            
            if price and price > 0:
                result[key] = {
                    'usd': round(price, 2),
                    'usd_24h_change': change_pct,
                    'market_cap': supply * price,
                    'name': key
                }
                logger.info(f"{key} price (backup): ${price:.2f}")
                
        except Exception as e:
            logger.error(f"GoldAPI.io error for {symbol}: {str(e)}")
    
    return result


def get_commodity_prices() -> Dict:
    """
    Fetch gold, silver, and platinum prices
    Tries GoldAPI.io first, falls back to MetalpriceAPI if primary fails
    """
    global _commodity_cache
    
    now = datetime.now()
    if (_commodity_cache['data'] is not None and 
        _commodity_cache['timestamp'] is not None and
        now - _commodity_cache['timestamp'] < _commodity_cache['cache_duration']):
        logger.info("Returning cached commodity prices")
        return _commodity_cache['data']
    
    result = _fetch_from_goldapiio()
    
    if not result or len(result) < 3:
        logger.info("Primary API failed or incomplete, trying backup API")
        backup_result = _fetch_from_metalpriceapi()
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
