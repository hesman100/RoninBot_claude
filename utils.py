from typing import Dict
from config import (
    DEFAULT_CRYPTOCURRENCIES, DEFAULT_STOCKS, DEFAULT_VN_STOCKS,
    SYMBOL_TO_DISPLAY, STOCK_TO_DISPLAY, VN_STOCK_TO_DISPLAY,
    STOCK_COMPANY_NAMES, VN_STOCK_COMPANY_NAMES
)
import logging

def format_price_message(crypto_data: Dict) -> str:
    """Format cryptocurrency or stock price data into a readable message"""
    logger = logging.getLogger(__name__)
    logger.info(f"Formatting prices for data: {list(crypto_data.keys())}")

    # Check if we're dealing with stocks, vietnam stocks, or crypto
    is_vn_stock = any(symbol in DEFAULT_VN_STOCKS for symbol in crypto_data.keys())
    is_stocks = any(symbol in DEFAULT_STOCKS for symbol in crypto_data.keys()) if not is_vn_stock else False

    # Customize column header based on type
    if is_vn_stock:
        column_header = "Stock   $vnd     24h\n"  # Changed from "Price" to "$vnd"
    else:
        column_header = "Coin    Price     24h\n"  # Keep original for non-VN stocks

    # Get header text based on number of coins/stocks and type
    if len(crypto_data) == 1:
        # For single item, use its full name
        symbol = next(iter(crypto_data.keys()))

        if symbol in DEFAULT_VN_STOCKS:
            header_text = f"📊 {VN_STOCK_COMPANY_NAMES.get(symbol, symbol)}"
        elif symbol in DEFAULT_STOCKS:
            header_text = f"📊 {STOCK_COMPANY_NAMES.get(symbol, symbol)}"
        else:
            coin_data = crypto_data[symbol]
            header_text = f"📊 {coin_data.get('name', symbol)}"
    else:
        if is_vn_stock:
            header_text = "📊 Vietnam Stock Prices"
        elif is_stocks:
            header_text = "📊 Stock Prices"
        else:
            header_text = "📊 Cryptocurrency Prices"

    # Add header with exact column widths matching the data rows
    header = (
        f"{header_text}\n\n"
        f"{column_header}"
        "──────────"  # Separator line matching content width
    )
    messages = [header]

    if len(crypto_data) == 1:
        # For single coin/stock request, just process that item
        symbol = next(iter(crypto_data.keys()))
        data = crypto_data[symbol]

        # Choose display format based on whether it's a stock, vn stock, or crypto
        if symbol in VN_STOCK_TO_DISPLAY:
            display_name = VN_STOCK_TO_DISPLAY[symbol]
        elif symbol in STOCK_TO_DISPLAY:
            display_name = STOCK_TO_DISPLAY[symbol]
        elif symbol in SYMBOL_TO_DISPLAY:
            display_name = SYMBOL_TO_DISPLAY[symbol]
        else:
            symbol_trunc = symbol[:7]  # Take first 7 chars if longer
            display_name = f"{symbol_trunc:<7}"  # Left align and pad to exactly 7 chars

        price = data.get('usd', 0)
        change_24h = data.get('usd_24h_change', 0)

        # Format price based on the value and type
        if symbol in DEFAULT_VN_STOCKS:
            price_str = f"{price:,.0f}"  # No $ sign for VN stocks, no decimals
        else:
            # Original formatting for non-VN stocks
            if price >= 1000:
                price_str = f"${price:,.0f}"
            elif price >= 100:
                price_str = f"${price:.1f}"
            elif price >= 1:
                price_str = f"${price:.2f}"
            else:
                price_str = f"${price:.4f}"

        # Format the change indicators with colored circles
        change_24h_symbol = "🟢" if change_24h > 0 else "🔴"

        # Fixed width columns with exact alignments
        message = (
            f"{display_name}"  # Name: exactly 7 chars, left-aligned
            f"{price_str:<9}"  # Price: exactly 9 chars, left-aligned
            f"{change_24h:>6.1f}%{change_24h_symbol}"  # 24h: percentage right-aligned (>6)
        )
        messages.append(message)
    else:
        # Get appropriate list and display mapping based on data type
        if is_vn_stock:
            default_list = DEFAULT_VN_STOCKS
            display_map = VN_STOCK_TO_DISPLAY
        elif is_stocks:
            default_list = DEFAULT_STOCKS
            display_map = STOCK_TO_DISPLAY
        else:
            default_list = DEFAULT_CRYPTOCURRENCIES
            display_map = SYMBOL_TO_DISPLAY

        # Process items in the defined order
        for symbol in default_list:
            if symbol in crypto_data:
                data = crypto_data[symbol]
                display_name = display_map.get(symbol, f"{symbol:<7}")

                price = data.get('usd', 0)
                change_24h = data.get('usd_24h_change', 0)

                # Format price based on the value and type
                if symbol in DEFAULT_VN_STOCKS:
                    price_str = f"{price:,.0f}"  # No $ sign for VN stocks, no decimals
                else:
                    # Original formatting for non-VN stocks
                    if price >= 1000:
                        price_str = f"${price:,.0f}"
                    elif price >= 100:
                        price_str = f"${price:.1f}"
                    elif price >= 1:
                        price_str = f"${price:.2f}"
                    else:
                        price_str = f"${price:.4f}"

                # Format the change indicators with colored circles
                change_24h_symbol = "🟢" if change_24h > 0 else "🔴"

                # Fixed width columns with exact alignments
                message = (
                    f"{display_name}"  # Name: exactly 7 chars, left-aligned
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