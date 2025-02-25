from typing import Dict
from config import DEFAULT_CRYPTOCURRENCIES, SYMBOL_TO_DISPLAY
import logging


def format_price_message(crypto_data: Dict) -> str:
    """Format cryptocurrency price data into a readable message"""
    logger = logging.getLogger(__name__)
    logger.info(
        f"Formatting prices for cryptocurrencies: {list(crypto_data.keys())}")

    # Get header text based on number of coins
    if len(crypto_data) == 1:
        # For single coin, use its full name
        coin_symbol = next(iter(crypto_data.keys()))
        coin_data = crypto_data[coin_symbol]
        header_text = f"📊 {coin_data.get('name', 'Cryptocurrency')}"
    else:
        header_text = "📊 Cryptocurrency Prices"

    # Add header with exact column widths matching the data rows
    header = (
        f"{header_text}\n\n"
        "Coin    Price     24h\n"  # Coin is exactly 7 chars
        "──────────"  # Separator line matching content width
    )
    messages = [header]

    if len(crypto_data) == 1:
        # For single coin request, just process that coin
        symbol = next(iter(crypto_data.keys()))
        data = crypto_data[symbol]
        if symbol in SYMBOL_TO_DISPLAY:
            display_name = SYMBOL_TO_DISPLAY[
                symbol]  # Use predefined 7-char width name
        else:
            # Ensure exactly 7 chars width by truncating or padding
            symbol_trunc = symbol[:7]  # Take first 7 chars if longer
            display_name = f"{symbol_trunc:<7}"  # Left align and pad to exactly 7 chars

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
            f"{display_name}"  # Coin: exactly 7 chars, left-aligned
            f"{price_str:<9}"  # Price: exactly 9 chars, left-aligned
            f"{change_24h:>6.1f}%{change_24h_symbol}"  # 24h: percentage right-aligned (>6)
        )
        messages.append(message)
    else:
        # For multiple coins, process them in the order defined in DEFAULT_CRYPTOCURRENCIES
        for symbol in DEFAULT_CRYPTOCURRENCIES:
            if symbol in crypto_data:
                data = crypto_data[symbol]
                if symbol in SYMBOL_TO_DISPLAY:
                    display_name = SYMBOL_TO_DISPLAY[
                        symbol]  # Use predefined 7-char width name
                else:
                    # Ensure exactly 7 chars width by truncating or padding
                    symbol_trunc = symbol[:7]  # Take first 7 chars if longer
                    display_name = f"{symbol_trunc:<7}"  # Left align and pad to exactly 7 chars

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
                    f"{display_name}"  # Coin: exactly 7 chars, left-aligned
                    f"{price_str:<9}"  # Price: exactly 9 chars, left-aligned
                    f"{change_24h:>6.1f}%{change_24h_symbol}"  # 24h: percentage right-aligned (>6)
                )
                messages.append(message)

    final_message = "\n".join(messages)
    logger.debug(f"Final formatted message:\n{final_message}"
                 )  # Debug logging for final output
    return final_message


def format_error_message(error: Exception) -> str:
    """Format error message for user display"""
    return f"❌ Error: {str(error)}\nPlease try again later."
