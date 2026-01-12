"""
Commodity price API client for Gold and Silver using Yahoo Finance
"""
import yfinance as yf
import logging
from typing import Dict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Cache for commodity prices (5 minutes)
_commodity_cache = {
    'data': None,
    'timestamp': None,
    'cache_duration': timedelta(minutes=5)
}

# Global commodity supply constants for market cap calculation
# Gold: ~216,265 metric tonnes = ~6.95 billion troy ounces
GOLD_SUPPLY_OUNCES = 6_950_000_000
# Silver: ~1.7 million metric tonnes = ~54.7 billion troy ounces
SILVER_SUPPLY_OUNCES = 54_700_000_000


def get_commodity_prices() -> Dict:
    """
    Fetch gold and silver prices from Yahoo Finance
    Returns dict with commodity price data in format compatible with crypto data
    """
    global _commodity_cache
    
    # Check cache first
    now = datetime.now()
    if (_commodity_cache['data'] is not None and 
        _commodity_cache['timestamp'] is not None and
        now - _commodity_cache['timestamp'] < _commodity_cache['cache_duration']):
        logger.info("Returning cached commodity prices")
        return _commodity_cache['data']
    
    result = {}
    
    try:
        # Fetch gold price (GC=F = Gold Futures)
        logger.info("Fetching gold price from Yahoo Finance: GC=F")
        gold = yf.Ticker("GC=F")
        gold_info = gold.info
        
        gold_price = gold_info.get('regularMarketPrice', 0) or gold_info.get('previousClose', 0)
        gold_prev_close = gold_info.get('regularMarketPreviousClose', gold_price) or gold_info.get('previousClose', gold_price)
        
        if gold_price and gold_prev_close:
            gold_change_pct = ((gold_price - gold_prev_close) / gold_prev_close) * 100
        else:
            gold_change_pct = 0
        
        gold_market_cap = GOLD_SUPPLY_OUNCES * gold_price if gold_price else 0
        
        result['GOLD'] = {
            'usd': gold_price,
            'usd_24h_change': gold_change_pct,
            'market_cap': gold_market_cap,
            'name': 'GOLD'
        }
        logger.info(f"Gold price: ${gold_price}, change: {gold_change_pct:.2f}%")
        
    except Exception as e:
        logger.error(f"Error fetching gold price: {str(e)}")
    
    try:
        # Fetch silver price (SI=F = Silver Futures)
        logger.info("Fetching silver price from Yahoo Finance: SI=F")
        silver = yf.Ticker("SI=F")
        silver_info = silver.info
        
        silver_price = silver_info.get('regularMarketPrice', 0) or silver_info.get('previousClose', 0)
        silver_prev_close = silver_info.get('regularMarketPreviousClose', silver_price) or silver_info.get('previousClose', silver_price)
        
        if silver_price and silver_prev_close:
            silver_change_pct = ((silver_price - silver_prev_close) / silver_prev_close) * 100
        else:
            silver_change_pct = 0
        
        silver_market_cap = SILVER_SUPPLY_OUNCES * silver_price if silver_price else 0
        
        result['SLVR'] = {
            'usd': silver_price,
            'usd_24h_change': silver_change_pct,
            'market_cap': silver_market_cap,
            'name': 'SLVR'
        }
        logger.info(f"Silver price: ${silver_price}, change: {silver_change_pct:.2f}%")
        
    except Exception as e:
        logger.error(f"Error fetching silver price: {str(e)}")
    
    # Update cache
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
