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

def clean_leaderboard():
    """Clean up the leaderboard by removing test users"""
    try:
        import sqlite3
        import os
        
        # Path to the database
        db_path = 'country_game/database/countries.db'
        
        # Ensure the database exists
        if os.path.exists(db_path):
            # Connect to the database
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Only remove specific test user names to avoid affecting legitimate users
            cursor.execute('''
                DELETE FROM user_stats 
                WHERE user_name = 'Test User'
                OR user_name = 'TestUser'
                OR user_name = 'Sample User'
                OR user_name = 'Anonymous'
                OR user_name = 'Anonymous User' 
                OR user_name = 'user123'
                OR user_name = 'John Doe'
                OR user_name = 'Jane Smith'
            ''')
            logger.info(f"Deleted {cursor.rowcount} entries matching specific test user names")
            
            # Commit changes
            conn.commit()
            logger.info("Leaderboard cleanup completed successfully")
            conn.close()
            return True
        else:
            logger.warning(f"Database not found at {db_path}, skipping leaderboard cleanup")
            return False
            
    except Exception as e:
        logger.error(f"Error cleaning leaderboard: {str(e)}")
        return False

def main():
    """Run both the Telegram Bot and API server"""
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Removed automatic leaderboard cleanup at startup
        # to prevent affecting legitimate users after deployment
        # Use clean_leaderboard.py script manually when needed
        
        logger.info("Starting services without automatic leaderboard cleanup")
        
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