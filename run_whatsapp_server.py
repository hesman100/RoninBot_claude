"""
Run WhatsApp Webhook Server
This script starts the WhatsApp webhook server to handle incoming messages.
"""

import logging
import threading
import sys
import os
import signal
from whatsapp_inc.server import run_server
from whatsapp_inc.client import WhatsAppClient

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("whatsapp_server.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def signal_handler(sig, frame):
    """Handle termination signals gracefully"""
    logger.info("Terminating WhatsApp server...")
    sys.exit(0)

def check_twilio_credentials():
    """Check if Twilio credentials are set"""
    required_env_vars = [
        "TWILIO_ACCOUNT_SID",
        "TWILIO_AUTH_TOKEN",
        "TWILIO_PHONE_NUMBER"
    ]
    
    missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please set these variables before running the WhatsApp server.")
        return False
    
    # Test the WhatsApp client
    client = WhatsAppClient()
    if not client.client:
        logger.error("Failed to initialize WhatsApp client. Please check your credentials.")
        return False
    
    logger.info("Twilio credentials verified successfully.")
    return True

def main():
    """Main entry point for the WhatsApp webhook server"""
    logger.info("Starting WhatsApp webhook server...")
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Check credentials
    if not check_twilio_credentials():
        logger.error("Exiting due to missing or invalid credentials.")
        sys.exit(1)
    
    # Create media directory if it doesn't exist
    os.makedirs("whatsapp_inc/media", exist_ok=True)
    
    # Run the server
    run_server()

if __name__ == "__main__":
    main()