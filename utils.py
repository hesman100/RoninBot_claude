from typing import Dict
from config import DEFAULT_CRYPTOCURRENCIES
import logging

def format_price_message(crypto_data: Dict) -> str:
    """Format cryptocurrency price data into a readable message"""
    logger = logging.getLogger(__name__)

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

    # Add header
    header = (
        "📊 Cryptocurrency Prices\n\n"
        "Coin    Price         24h Change    3d Change\n"
        "─────────────────────────────────────────────"
    )
    messages = [header]

    # Process cryptocurrencies in the order defined in DEFAULT_CRYPTOCURRENCIES
    for crypto_id in DEFAULT_CRYPTOCURRENCIES:
        if crypto_id in crypto_data and crypto_id in display_name:
            data = crypto_data[crypto_id]
            price = data.get('usd', 0)
            change_24h = data.get('usd_24h_change', 0)
            change_3d = data.get('usd_3d_change', 0)  # Get 3-day change

            # Format price with appropriate scaling
            if price < 0.01:
                price_str = f"${price:.8f}"
            elif price < 1:
                price_str = f"${price:.4f}"
            else:
                price_str = f"${price:,.2f}"

            # Format the change indicators
            change_24h_symbol = "📈" if change_24h > 0 else "📉"
            change_3d_symbol = "📈" if change_3d > 0 else "📉"

            # Pad the coin name and price for alignment
            coin_padding = 8 - len(display_name[crypto_id])
            price_padding = 13 - len(price_str)

            message = (
                f"{display_name[crypto_id]}{' ' * coin_padding}"
                f"{price_str}{' ' * price_padding}"
                f"{change_24h_symbol}{change_24h:>6.1f}%     "
                f"{change_3d_symbol}{change_3d:>6.1f}%"
            )
            messages.append(message)

    logger.info(f"Formatted message contains {len(messages)-1} cryptocurrencies")
    final_message = "\n".join(messages)
    logger.info(f"Final formatted message:\n{final_message}")  # Added debug log
    return final_message

def format_error_message(error: Exception) -> str:
    """Format error message for user display"""
    return f"❌ Error: {str(error)}\nPlease try again later."