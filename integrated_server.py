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
            
            # Delete common test users by name pattern
            cursor.execute('''
                DELETE FROM user_stats 
                WHERE user_name LIKE '%Test%' 
                OR user_name LIKE '%Sample%'
                OR user_name LIKE '%Anonymous%'
                OR user_name LIKE '%Demo%'
                OR user_name LIKE '%Example%'
                OR user_name = 'user123'
                OR user_name = 'John Doe'
                OR user_name = 'Jane Smith'
            ''')
            logger.info(f"Deleted {cursor.rowcount} entries matching test user name patterns")
            
            # Delete low-activity users (likely test accounts)
            cursor.execute('''
                DELETE FROM user_stats 
                WHERE total < 5 AND login_method != 'tele'
            ''')
            logger.info(f"Deleted {cursor.rowcount} entries for low-activity users")
            
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
        # Clean up the leaderboard at startup
        logger.info("Cleaning up leaderboard database (removing test users)...")
        clean_result = clean_leaderboard()
        if clean_result:
            logger.info("Leaderboard cleanup completed successfully")
        else:
            logger.warning("Leaderboard cleanup may not have completed successfully")
        
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