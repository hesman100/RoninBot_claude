#!/usr/bin/env python3
"""
Sanity test for price functions after reorganization"""
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting price function sanity test")
    
    try:
        # Import the API classes from the price_func package
        from price_func import (
            AlphaVantageAPI, 
            CoinMarketCapAPI, 
            FinnhubAPI,
            VietnamStockAPI
        )
        logger.info("✅ Successfully imported API classes from price_func")
        
        # Initialize each API client
        logger.info("Initializing API clients...")
        crypto_api = CoinMarketCapAPI()
        stock_api = AlphaVantageAPI()
        finnhub_api = FinnhubAPI()
        vietnam_stock_api = VietnamStockAPI()
        logger.info("✅ Successfully initialized API clients")
        
        # Test CoinMarketCap API
        logger.info("Testing CoinMarketCap API...")
        try:
            btc_price = crypto_api.get_price("BTC")
            if isinstance(btc_price, dict) and not "error" in btc_price:
                logger.info(f"✅ CoinMarketCap API returned: {btc_price}")
            else:
                logger.warning(f"⚠️ CoinMarketCap API returned error or unexpected format: {btc_price}")
        except Exception as e:
            logger.error(f"❌ Error testing CoinMarketCap API: {str(e)}")
        
        # Test AlphaVantage API
        logger.info("Testing AlphaVantage API...")
        try:
            aapl_price = stock_api.get_stock_price("AAPL")
            if isinstance(aapl_price, dict) and not "error" in aapl_price:
                logger.info(f"✅ AlphaVantage API returned: {aapl_price}")
            else:
                logger.warning(f"⚠️ AlphaVantage API returned error or unexpected format: {aapl_price}")
        except Exception as e:
            logger.error(f"❌ Error testing AlphaVantage API: {str(e)}")
        
        # Test Finnhub API
        logger.info("Testing Finnhub API...")
        try:
            tsla_price = finnhub_api.get_stock_price("TSLA")
            if isinstance(tsla_price, dict) and not "error" in tsla_price:
                logger.info(f"✅ Finnhub API returned: {tsla_price}")
            else:
                logger.warning(f"⚠️ Finnhub API returned error or unexpected format: {tsla_price}")
        except Exception as e:
            logger.error(f"❌ Error testing Finnhub API: {str(e)}")
        
        # Test Vietnam Stock API
        logger.info("Testing Vietnam Stock API...")
        try:
            vnm_price = vietnam_stock_api.get_stock_price("VNM")
            if isinstance(vnm_price, dict) and not "error" in vnm_price:
                logger.info(f"✅ Vietnam Stock API returned: {vnm_price}")
            else:
                logger.warning(f"⚠️ Vietnam Stock API returned error or unexpected format: {vnm_price}")
        except Exception as e:
            logger.error(f"❌ Error testing Vietnam Stock API: {str(e)}")
        
        logger.info("Price function sanity test completed")
        return 0
    
    except ImportError as e:
        logger.error(f"❌ Import error: {str(e)}")
        logger.error("This indicates there might be issues with the reorganization of price_func modules")
        return 1
    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
