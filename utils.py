from typing import Dict
from config import DEFAULT_CRYPTOCURRENCIES
import logging

def format_price_message(crypto_data: Dict) -> str:
    """Format cryptocurrency price data into a readable message"""
    logger = logging.getLogger(__name__)
    messages = []

    # Fixed display name mapping
    display_name = {
        'bitcoin': 'BTC',
        'ethereum': 'ETH',
        'solana': 'SOL',
        'ronin': 'RON',
        'axie-infinity': 'AXS',
        'pi-network': 'PI'
    }

    logger.info(f"Formatting prices for cryptocurrencies: {DEFAULT_CRYPTOCURRENCIES}")

    # Process cryptocurrencies in the order defined in DEFAULT_CRYPTOCURRENCIES
    for crypto_id in DEFAULT_CRYPTOCURRENCIES:
        if crypto_id in crypto_data and crypto_id in display_name:
            data = crypto_data[crypto_id]
            price = data.get('usd', 0)
            change_24h = data.get('usd_24h_change', 0)
            market_cap = data.get('usd_market_cap', 0)

            # Format the price change indicator
            change_symbol = "📈" if change_24h > 0 else "📉"

            message = (
                f"💰 {display_name[crypto_id]}\n"
                f"Price: ${price:,.2f}\n"
                f"24h Change: {change_symbol} {change_24h:.2f}%\n"
                f"Market Cap: ${market_cap:,.0f}\n"
            )
            messages.append(message)

    logger.info(f"Formatted message contains {len(messages)} cryptocurrencies")
    return "\n".join(messages)

def format_error_message(error: Exception) -> str:
    """Format error message for user display"""
    return f"❌ Error: {str(error)}\nPlease try again later."