import time
import sys
import logging
from price_func.alphavantage_api import AlphaVantageAPI
from price_func.finnhub_api import FinnhubAPI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger("test_stock_api")

def test_alphavantage():
    """Test Alpha Vantage API response time"""
    logger.info("Testing AlphaVantage API")
    
    api = AlphaVantageAPI()
    
    # Test single stock
    logger.info("Testing single stock with AlphaVantage (AAPL)")
    start_time = time.time()
    result = api.get_stock_price("AAPL")
    end_time = time.time()
    logger.info(f"AlphaVantage single stock response time: {end_time - start_time:.2f} seconds")
    logger.info(f"Result: {result}")
    
    # Test all stocks
    logger.info("Testing all stocks with AlphaVantage")
    start_time = time.time()
    result = api.get_stock_prices()
    end_time = time.time()
    logger.info(f"AlphaVantage all stocks response time: {end_time - start_time:.2f} seconds")
    logger.info(f"Number of stocks returned: {len(result) if isinstance(result, dict) and 'error' not in result else 0}")
    
    return result

def test_finnhub():
    """Test Finnhub API response time"""
    logger.info("Testing Finnhub API")
    
    api = FinnhubAPI()
    
    # Test single stock
    logger.info("Testing single stock with Finnhub (AAPL)")
    start_time = time.time()
    result = api.get_stock_price("AAPL")
    end_time = time.time()
    logger.info(f"Finnhub single stock response time: {end_time - start_time:.2f} seconds")
    logger.info(f"Result: {result}")
    
    # Test all stocks
    logger.info("Testing all stocks with Finnhub")
    start_time = time.time()
    result = api.get_stock_prices()
    end_time = time.time()
    logger.info(f"Finnhub all stocks response time: {end_time - start_time:.2f} seconds")
    logger.info(f"Number of stocks returned: {len(result) if isinstance(result, dict) and 'error' not in result else 0}")
    
    return result

if __name__ == "__main__":
    logger.info("Starting API response time tests")
    
    # Test AlphaVantage first
    alpha_result = test_alphavantage()
    
    # Test Finnhub next
    finnhub_result = test_finnhub()
    
    logger.info("Tests completed")