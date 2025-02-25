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

    logger.info(f"Formatting prices for cryptocurrencies: {list(crypto_data.keys())}")

    # Add header with exact column widths
    header = (
        "📊 Cryptocurrency Prices\n\n"
        "Coin  Price     24h   \n"
        "─────────────────"  # Separator line matching content width
    )
    messages = [header]

    # Process cryptocurrencies in the order defined in DEFAULT_CRYPTOCURRENCIES
    for crypto_id in DEFAULT_CRYPTOCURRENCIES:
        if crypto_id in crypto_data and crypto_id in display_name:
            data = crypto_data[crypto_id]
            price = data.get('usd', 0)
            change_24h = data.get('usd_24h_change', 0)

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

            # Fixed width columns with specified alignments
            message = (
                f"{display_name[crypto_id]:<5}"  # Coin: 5 chars, left-aligned
                f"{price_str:<9}"                # Price: 9 chars, left-aligned
                f"{change_24h_symbol}{change_24h:<6.1f}%"  # 24h: 7 chars, left-aligned
            )
            messages.append(message)
            logger.debug(f"Formatted row: '{message}'")  # Debug logging for each row

    final_message = "\n".join(messages)
    logger.debug(f"Final formatted message:\n{final_message}")  # Debug logging for final output
    return final_message

def format_error_message(error: Exception) -> str:
    """Format error message for user display"""
    return f"❌ Error: {str(error)}\nPlease try again later."