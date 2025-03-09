"""
Integrated Server for both Telegram Bot and API
This script runs both the Telegram Bot and the API server in a single process
"""

import os
import sys
import logging
import threading
import signal
import time
from http.server import HTTPServer
import flask

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('integrated_server.log')
    ])
logger = logging.getLogger(__name__)

# Flag to indicate when the server should shut down
shutdown_requested = False

def signal_handler(sig, frame):
    """Handle termination signals gracefully"""
    global shutdown_requested
    logger.info("Termination signal received, shutting down services...")
    shutdown_requested = True
    sys.exit(0)

def run_bot():
    """Run the Telegram Bot in a separate thread"""
    try:
        import bot
        bot.main()
    except Exception as e:
        logger.error(f"Error in bot thread: {e}")

def run_api_server():
    """Run the API server in a separate thread"""
    try:
        from xbot_api import server
        server.main()
    except Exception as e:
        logger.error(f"Error in API server thread: {e}")

def main():
    """Run both the Telegram Bot and API server"""
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start the bot in a separate thread
        logger.info("Starting Telegram bot...")
        bot_thread = threading.Thread(target=run_bot)
        bot_thread.daemon = True
        bot_thread.start()
        
        # Start the API server in the main thread
        # API server uses Flask which will block the main thread
        logger.info("Starting API server...")
        run_api_server()
        
    except Exception as e:
        logger.error(f"Error in main process: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()