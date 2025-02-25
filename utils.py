from typing import Dict

def format_price_message(crypto_data: Dict) -> str:
    """Format cryptocurrency price data into a readable message"""
    messages = []
    
    for crypto_id, data in crypto_data.items():
        price = data.get('usd', 0)
        change_24h = data.get('usd_24h_change', 0)
        market_cap = data.get('usd_market_cap', 0)
        
        # Format the price change indicator
        change_symbol = "📈" if change_24h > 0 else "📉"
        
        message = (
            f"💰 {crypto_id.upper()}\n"
            f"Price: ${price:,.2f}\n"
            f"24h Change: {change_symbol} {change_24h:.2f}%\n"
            f"Market Cap: ${market_cap:,.0f}\n"
        )
        messages.append(message)
    
    return "\n".join(messages)

def format_error_message(error: Exception) -> str:
    """Format error message for user display"""
    return f"❌ Error: {str(error)}\nPlease try again later."
