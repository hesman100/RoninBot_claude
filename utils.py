from typing import Dict
from config import DEFAULT_CRYPTOCURRENCIES, SYMBOL_TO_DISPLAY, STOCK_TO_DISPLAY, DEFAULT_STOCKS
import logging

def format_price_message(crypto_data: Dict) -> str:
    """Format cryptocurrency or stock price data into a readable message"""
    logger = logging.getLogger(__name__)
    logger.info(
        f"Formatting prices for cryptocurrencies: {list(crypto_data.keys())}")

    # Determine if we're dealing with stocks
    is_stocks = DEFAULT_STOCKS[0] in crypto_data  # Check if first stock is in the data

    # Get header text based on number of items and type
    if len(crypto_data) == 1:
        # For single item, use its full name
        symbol = next(iter(crypto_data.keys()))
        item_data = crypto_data[symbol]
        header_text = f"📊 {item_data.get('name', symbol)}"
    else:
        header_text = "📊 Stock Prices" if is_stocks else "📊 Cryptocurrency Prices"

    # Add header with exact column widths matching the data rows
    column_name = "Stock   " if is_stocks else "Coin    "  # Both exactly 7 chars
    header = (
        f"{header_text}\n\n"
        f"{column_name}Price     24h\n"
        "──────────"  # Separator line matching content width
    )
    messages = [header]

    if len(crypto_data) == 1:
        # For single item request, just process that item
        symbol = next(iter(crypto_data.keys()))
        data = crypto_data[symbol]

        # Choose display format based on whether it's a stock or crypto
        if symbol in STOCK_TO_DISPLAY:
            display_name = STOCK_TO_DISPLAY[symbol]
        elif symbol in SYMBOL_TO_DISPLAY:
            display_name = SYMBOL_TO_DISPLAY[symbol]
        else:
            # Ensure exactly 7 chars width by truncating or padding
            symbol_trunc = symbol[:7]  # Take first 7 chars if longer
            display_name = f"{symbol_trunc:<7}"  # Left align and pad to exactly 7 chars

        price = data.get('usd', 0)
        change_24h = data.get('usd_24h_change', 0)

        # Format price based on the value
        if price >= 1000:
            price_str = f"${price:,.0f}"  # No decimals for high values
        elif price >= 100:
            price_str = f"${price:.1f}"  # 1 decimal for medium values
        elif price >= 1:
            price_str = f"${price:.2f}"  # 2 decimals for normal values
        else:
            price_str = f"${price:.4f}"  # 4 decimals for small values

        # Format the change indicators with arrow
        change_24h_symbol = "📈" if change_24h > 0 else "📉"

        # Fixed width columns with exact alignments
        message = (
            f"{display_name}"  # Item: exactly 7 chars, left-aligned
            f"{price_str:<9}"  # Price: exactly 9 chars, left-aligned
            f"{change_24h:>6.1f}%{change_24h_symbol}"  # 24h: percentage right-aligned (>6)
        )
        messages.append(message)
    else:
        # Get appropriate list and display mapping based on data type
        default_list = DEFAULT_STOCKS if is_stocks else DEFAULT_CRYPTOCURRENCIES
        display_map = STOCK_TO_DISPLAY if is_stocks else SYMBOL_TO_DISPLAY

        # Process items in the defined order
        for symbol in default_list:
            if symbol in crypto_data:
                data = crypto_data[symbol]
                display_name = display_map.get(symbol, f"{symbol:<7}")

                price = data.get('usd', 0)
                change_24h = data.get('usd_24h_change', 0)

                # Format price based on the value
                if price >= 1000:
                    price_str = f"${price:,.0f}"
                elif price >= 100:
                    price_str = f"${price:.1f}"
                elif price >= 1:
                    price_str = f"${price:.2f}"
                else:
                    price_str = f"${price:.4f}"

                # Format the change indicators with arrow
                change_24h_symbol = "📈" if change_24h > 0 else "📉"

                # Fixed width columns with exact alignments
                message = (
                    f"{display_name}"  # Item: exactly 7 chars, left-aligned
                    f"{price_str:<9}"  # Price: exactly 9 chars, left-aligned
                    f"{change_24h:>6.1f}%{change_24h_symbol}"  # 24h: percentage right-aligned (>6)
                )
                messages.append(message)

    final_message = "\n".join(messages)
    logger.debug(f"Final formatted message:\n{final_message}")  # Debug logging for final output
    return final_message


def format_error_message(error: Exception) -> str:
    """Format error message for user display"""
    return f"❌ Error: {str(error)}\nPlease try again later."