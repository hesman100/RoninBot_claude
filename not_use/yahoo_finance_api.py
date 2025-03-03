import requests
import logging
import time
from typing import Dict, List, Optional
from config import DEFAULT_STOCKS, REQUEST_TIMEOUT, MAX_RETRIES, RETRY_DELAY

logger = logging.getLogger(__name__)

class YahooFinanceAPI:
    def __init__(self):
        self.base_url = "https://query1.finance.yahoo.com/v8/finance/chart"
        self.session = requests.Session()

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make a request to Yahoo Finance API with retry logic"""
        url = f"{self.base_url}/{endpoint}"
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
                logger.info(f"Successful response received")
                return data
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed (attempt {attempt + 1}/{MAX_RETRIES}): {str(e)}")
                if attempt == MAX_RETRIES - 1:
                    return {"error": str(e)}
                time.sleep(RETRY_DELAY * (attempt + 1))

        return {"error": "Maximum retries exceeded"}

    def get_stock_price(self, symbol: str) -> Dict:
        """Get current price for a single stock"""
        logger.info(f"Fetching price for stock: {symbol}")

        try:
            params = {
                'interval': '1d',
                'range': '1d',
                'includePrePost': 'false'
            }

            data = self._make_request(symbol, params)

            if "error" in data:
                return data

            if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
                result = data['chart']['result'][0]
                meta = result['meta']

                # Get the latest price and previous close
                price = meta.get('regularMarketPrice', 0)
                prev_close = meta.get('chartPreviousClose', meta.get('previousClose', price))

                # Calculate 24h change
                change_percent = ((price - prev_close) / prev_close) * 100 if prev_close else 0

                formatted_data = {
                    symbol.upper(): {
                        "usd": price,
                        "usd_24h_change": change_percent,
                        "name": symbol.upper()
                    }
                }
                logger.info(f"Formatted stock data: {formatted_data}")
                return formatted_data

            return {"error": f"No data found for {symbol}"}

        except Exception as e:
            logger.error(f"Error fetching stock price: {str(e)}")
            return {"error": str(e)}

    def get_stock_prices(self) -> Dict:
        """Get current prices for multiple stocks"""
        logger.info(f"Fetching prices for default stocks: {DEFAULT_STOCKS}")

        all_data = {}
        for symbol in DEFAULT_STOCKS:
            try:
                data = self.get_stock_price(symbol)
                if "error" not in data:
                    all_data.update(data)
                time.sleep(0.2)  # Small delay between requests
            except Exception as e:
                logger.error(f"Error fetching price for {symbol}: {str(e)}")
                continue

        return all_data if all_data else {"error": "No stock data available"}