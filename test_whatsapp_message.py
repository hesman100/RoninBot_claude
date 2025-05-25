"""
Test WhatsApp Message Sender
This script sends a test message to verify your WhatsApp integration is working.
"""

import os
import sys
from whatsapp_inc.client import WhatsAppClient

def send_test_message():
    # Initialize WhatsApp client
    client = WhatsAppClient()
    
    # Get destination phone number from command line or use default
    to_number = sys.argv[1] if len(sys.argv) > 1 else "+84973560589"
    
    # Ensure it has WhatsApp prefix
    if not to_number.startswith("whatsapp:"):
        to_number = f"whatsapp:{to_number}"
        
    # Get the from number from environment variable
    from_number = os.environ.get("TWILIO_PHONE_NUMBER")
    print(f"Sending from: {from_number}")
    
    # Message to send
    message = """Hello! This is a test message from your XBot WhatsApp integration.

Available commands:
/help - Show this help message
/s AAPL - Get Apple stock price
/c BTC - Get Bitcoin price
/g map - Play country guessing game with maps
/g flag - Play country guessing game with flags
/g cap - Play country guessing game with capitals

Reply to this message to start interacting with the bot!"""
    
    # Send the message
    print(f"Sending test message to {to_number}...")
    result = client.send_message(to_number, message)
    
    # Check result
    if "success" in result and result["success"]:
        print(f"Message sent successfully! SID: {result.get('sid')}")
    else:
        print(f"Failed to send message: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    send_test_message()