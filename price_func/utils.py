from typing import Dict
from .config import (DEFAULT_CRYPTOCURRENCIES, DEFAULT_STOCKS,
                    DEFAULT_VN_STOCKS, SYMBOL_TO_DISPLAY, STOCK_TO_DISPLAY,
                    VN_STOCK_TO_DISPLAY, STOCK_COMPANY_NAMES,
                    VN_STOCK_COMPANY_NAMES)
import logging
from datetime import datetime, timezone, timedelta


def format_price_message(crypto_data: Dict) -> str:
    """Format cryptocurrency or stock price data into a readable message"""
    logger = logging.getLogger(__name__)
    logger.info(f"Formatting prices for data: {list(crypto_data.keys())}")

    # Check if we're dealing with stocks, vietnam stocks, or crypto
    is_vn_stock = any(symbol in DEFAULT_VN_STOCKS
                      for symbol in crypto_data.keys()) or any(
                          symbol in VN_STOCK_COMPANY_NAMES
                          for symbol in crypto_data.keys())
    is_stocks = any(
        symbol in DEFAULT_STOCKS
        for symbol in crypto_data.keys()) if not is_vn_stock else False

    # Customize column header based on type (properly aligned)
    # Format: Name(6) + Price(9) + Change(7) + space + emoji = 24 chars total
    if is_vn_stock:
        column_header = f"{'Stock':<6}{'$vnd':>9}  {'24h':>7}\n"
    elif is_stocks:
        column_header = f"{'Stock':<6}{'$usd':>9}  {'24h':>7}\n"
    else:
        column_header = f"{'Coin':<6}{'$usd':>9}  {'24h':>7}\n"

    # Get header text based on number of coins/stocks and type (more compact)
    if len(crypto_data) == 1:
        # For single item, use its full name
        symbol = next(iter(crypto_data.keys()))

        if symbol in VN_STOCK_COMPANY_NAMES:
            header_text = f"📊 {VN_STOCK_COMPANY_NAMES.get(symbol, symbol)}"
        elif symbol in DEFAULT_STOCKS:
            header_text = f"📊 {STOCK_COMPANY_NAMES.get(symbol, symbol)}"
        else:
            coin_data = crypto_data[symbol]
            header_text = f"📊 {coin_data.get('name', symbol)}"
    else:
        if is_vn_stock:
            header_text = "📊 VN Stocks"
        elif is_stocks:
            header_text = "📊 Stocks"
        else:
            header_text = "📊 Crypto"

    # Add header with exact column widths matching the data rows (properly aligned)
    header = (
        f"{header_text}\n\n"
        f"{column_header}"
        "────────────────────────"  # 24 chars to match total column width
    )
    messages = [header]

    if len(crypto_data) == 1:
        # For single coin/stock request, just process that item
        symbol = next(iter(crypto_data.keys()))
        data = crypto_data[symbol]

        # Use the raw symbol, truncate and pad to exactly 6 characters
        symbol_truncated = symbol[:6]
        display_name = f"{symbol_truncated:<6}"  # Left-align and pad to 6 chars

        price = data.get('usd', 0)
        change_24h = data.get('usd_24h_change', 0)

        # Format price based on the value and type (more compact)
        if symbol in DEFAULT_VN_STOCKS or symbol in VN_STOCK_COMPANY_NAMES:
            # Remove $ sign completely for VN stocks, no decimals
            price_str = f"{price:,.0f}"
        else:
            # More compact formatting for non-VN stocks
            if price >= 1000:
                price_str = f"${price:,.0f}"
            elif price >= 100:
                price_str = f"${price:.0f}"  # Reduced decimal places
            elif price >= 1:
                price_str = f"${price:.1f}"  # Reduced from 2 to 1 decimal
            else:
                price_str = f"${price:.3f}"  # Reduced from 4 to 3 decimals

        # Format the change indicators with colored circles
        change_24h_symbol = "🟢" if change_24h > 0 else "🔴"

        # Format the change percentage - include % in width calculation
        if change_24h >= 0:
            change_str = f"{change_24h:5.1f}%"  # "  4.1%" - 6 chars total
        else:
            change_str = f"{change_24h:5.1f}%"  # " -2.8%" - 6 chars total

        # Fixed width columns with exact alignments: Name(6) + Price(9) + Change(7) + emoji
        message = (
            f"{display_name:<6}"  # Name: 6 chars, left-aligned
            f"{price_str:>9}"     # Price: 9 chars, right-aligned (increased for better spacing)
            f"{change_str:>7} {change_24h_symbol}"  # Change: 7 chars + space + emoji
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
                # Use the raw symbol, truncate and pad to exactly 6 characters
                symbol_truncated = symbol[:6]
                display_name = f"{symbol_truncated:<6}"  # Left-align and pad to 6 chars

                price = data.get('usd', 0)
                change_24h = data.get('usd_24h_change', 0)

                # Format price based on the value and type (more compact)
                if symbol in DEFAULT_VN_STOCKS or symbol in VN_STOCK_COMPANY_NAMES:
                    # Remove $ sign completely for VN stocks, no decimals
                    price_str = f"{price:,.0f}"
                else:
                    # More compact formatting for non-VN stocks
                    if price >= 1000:
                        price_str = f"${price:,.0f}"
                    elif price >= 100:
                        price_str = f"${price:.0f}"  # Reduced decimal places
                    elif price >= 1:
                        price_str = f"${price:.1f}"  # Reduced from 2 to 1 decimal
                    else:
                        price_str = f"${price:.3f}"  # Reduced from 4 to 3 decimals

                # Format the change indicators with colored circles
                change_24h_symbol = "🟢" if change_24h > 0 else "🔴"

                # Format the change percentage - include % in width calculation
                if change_24h >= 0:
                    change_str = f"{change_24h:5.1f}%"  # "  4.1%" - 6 chars total
                else:
                    change_str = f"{change_24h:5.1f}%"  # " -2.8%" - 6 chars total

                # Fixed width columns with exact alignments: Name(6) + Price(9) + Change(7) + emoji
                message = (
                    f"{display_name:<6}"  # Name: 6 chars, left-aligned
                    f"{price_str:>9}"     # Price: 9 chars, right-aligned (increased for better spacing)
                    f"{change_str:>7} {change_24h_symbol}"  # Change: 7 chars + space + emoji
                )
                messages.append(message)

    # Add timestamp at the end with GMT+7 timezone (more compact)
    gmt_plus_7 = timezone(timedelta(hours=7))
    current_time = datetime.now(gmt_plus_7).strftime("%d %b %Y, %H:%M")
    timestamp = f"\n\n🕐 {current_time} (GMT+7)"
    
    # Wrap in code block for monospace font alignment in Telegram
    final_message = "```\n" + "\n".join(messages) + "\n```" + timestamp
    logger.debug(f"Final formatted message:\n{final_message}"
                 )  # Debug logging for final output
    return final_message


def format_error_message(error: Exception) -> str:
    """Format error message for user display"""
    return f"❌ Error: {str(error)}\nPlease try again later."