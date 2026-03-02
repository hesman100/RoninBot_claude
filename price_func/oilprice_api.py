import requests
import logging
from typing import Dict
from .config import REQUEST_TIMEOUT

logger = logging.getLogger(__name__)

OILPRICE_CACHE_URL = "https://s3.amazonaws.com/oilprice.com/oilprices/blend_cache.json"
WTI_ID = "45"
NATURAL_GAS_ID = "51"
LNG_FACTOR = 1000 / 28.3  # Natural Gas MMBtu -> USD/1000m3


class OilPriceAPI:
    def get_prices(self) -> Dict:
        """Fetch WTI Crude and Natural Gas prices from oilprice.com S3 cache."""
        try:
            response = requests.get(OILPRICE_CACHE_URL, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()

            result = {}

            wti = data.get(WTI_ID, {})
            if wti:
                lp = wti.get("last_price", [{}])[0]
                result["OIL"] = {
                    "usd": float(lp.get("price", 0)),
                    "usd_24h_change": float(lp.get("change_percent", 0)),
                    "market_cap": 0,
                    "name": "WTI Crude Oil",
                }

            ng = data.get(NATURAL_GAS_ID, {})
            if ng:
                lp = ng.get("last_price", [{}])[0]
                ng_price = float(lp.get("price", 0))
                result["LNG"] = {
                    "usd": ng_price * LNG_FACTOR,
                    "usd_24h_change": float(lp.get("change_percent", 0)),
                    "market_cap": 0,
                    "name": "LNG (Natural Gas)",
                }

            return result

        except Exception as e:
            logger.error(f"Failed to fetch oil prices: {e}")
            return {"error": str(e)}
