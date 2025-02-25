from typing import Dict
from config import DEFAULT_CRYPTOCURRENCIES, SYMBOL_TO_DISPLAY
import logging

def format_price_message(crypto_data: Dict) -> str:
    """Format cryptocurrency price data into a readable message"""
    logger = logging.getLogger(__name__)
    logger.info(f"Formatting prices for cryptocurrencies: {list(crypto_data.keys())}")

    # Add header with exact column widths matching the data rows
    header = (
        "📊 Cryptocurrency Prices\n\n"
        "Coin Price     24h\n"
        "─────────────────"  # Separator line matching content width
    )
    messages = [header]

    # Process each cryptocurrency
    for symbol, data in crypto_data.items():
        # Get display name (use mapped name or pad symbol to 5 chars)
        display_name = SYMBOL_TO_DISPLAY.get(symbol, f"{symbol:<5}")

        price = data.get('usd', 0)
        change_24h = data.get('usd_24h_change', 0)

        # Format price based on the value
        if symbol in ['BTC', 'ETH', 'SOL']:
            price_str = f"${price:,.0f}"  # No decimals for BTC, ETH, SOL
        elif price < 0.01:
            price_str = f"${price:.4f}"
        elif price < 1:
            price_str = f"${price:.3f}"
        else:
            price_str = f"${price:.2f}"

        # Format the change indicators with arrow immediately after
        change_24h_symbol = "📈" if change_24h > 0 else "📉"

        # Fixed width columns with exact alignments
        message = (
            f"{display_name}"      # Coin: exactly 5 chars, already padded
            f"{price_str:<9}"      # Price: exactly 9 chars, left-aligned
            f"{change_24h:6.1f}%{change_24h_symbol}"  # 24h: percentage with arrow
        )
        messages.append(message)
        logger.debug(f"Formatted row: '{message}'")  # Debug logging for each row

    final_message = "\n".join(messages)
    logger.debug(f"Final formatted message:\n{final_message}")  # Debug logging for final output
    return final_message

def format_error_message(error: Exception) -> str:
    """Format error message for user display"""
    return f"❌ Error: {str(error)}\nPlease try again later."
