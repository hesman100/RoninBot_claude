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
        "Coin    Price    24h    7days\n"
        "─────────────────────────────"
    )
    messages = [header]

    # Process cryptocurrencies in the order defined in DEFAULT_CRYPTOCURRENCIES
    for crypto_id in DEFAULT_CRYPTOCURRENCIES:
        if crypto_id in crypto_data and crypto_id in display_name:
            data = crypto_data[crypto_id]
            price = data.get('usd', 0)
            change_24h = data.get('usd_24h_change', 0)
            change_7d = data.get('usd_7d_change', 0)  # Get 7-day change

            # Format price based on the coin
            if crypto_id in ['bitcoin', 'ethereum', 'solana']:
                price_str = f"${price:,.0f}"  # No decimals for BTC, ETH, SOL
            elif price < 0.01:
                price_str = f"${price:.4f}"
            elif price < 1:
                price_str = f"${price:.3f}"
            else:
                price_str = f"${price:.2f}"

            # Format the change indicators
            change_24h_symbol = "📈" if change_24h > 0 else "📉"
            change_7d_symbol = "📈" if change_7d > 0 else "📉"

            # Right-align all columns with fixed widths
            message = (
                f"{display_name[crypto_id]:>4}"  # Coin: 4 chars, right-aligned
                f"{price_str:>8}"                # Price: 8 chars, right-aligned
                f"{change_24h_symbol}{change_24h:>6.1f}%"  # 24h: 7 chars, right-aligned
                f"{change_7d_symbol}{change_7d:>6.1f}%"    # 7days: 7 chars, right-aligned
            )
            messages.append(message)

    logger.info(f"Formatted message contains {len(messages)-1} cryptocurrencies")
    final_message = "\n".join(messages)
    logger.info(f"Final formatted message:\n{final_message}")  # Added debug log
    return final_message

def format_error_message(error: Exception) -> str:
    """Format error message for user display"""
    return f"❌ Error: {str(error)}\nPlease try again later."