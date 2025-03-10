"""
Combined starter script for both the API server and the Telegram bot
Use this as the main entry point for deployment to ensure both services are running
"""

import os
import sys
import subprocess
import logging
import signal
import time

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('combined_server.log')
    ])
logger = logging.getLogger(__name__)

# Process handles
api_process = None
bot_process = None

def signal_handler(sig, frame):
    """Handle termination signals gracefully"""
    logger.info("Termination signal received, shutting down services...")
    if api_process:
        api_process.terminate()
    if bot_process:
        bot_process.terminate()
    sys.exit(0)

def main():
    """Run both the API server and the Telegram bot"""
    global api_process, bot_process

    # Set your custom API key here
    os.environ["XBOT_API_KEY"] = "geo-841e2b00e535e71f"  # Replace with your API key

    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Clean up the leaderboard at startup
        logger.info("Cleaning up leaderboard database (removing test users)...")
        try:
            # Create a simplified version of the cleanup that doesn't try to restart the bot
            # since it's not running yet
            import sqlite3
            
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
            else:
                logger.warning(f"Database not found at {db_path}, skipping leaderboard cleanup")
                
        except Exception as e:
            logger.error(f"Error cleaning leaderboard: {str(e)}")
            # Continue with startup even if cleanup fails
        
        # Start the API server as a subprocess
        logger.info("Starting API server...")
        api_process = subprocess.Popen(
            [sys.executable, "run_api_server.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Give the API server a moment to start
        time.sleep(2)
        logger.info(f"API server started with PID: {api_process.pid}")
        
        # Start the Telegram bot as a subprocess
        logger.info("Starting Telegram bot...")
        bot_process = subprocess.Popen(
            [sys.executable, "bot.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        logger.info(f"Telegram bot started with PID: {bot_process.pid}")
        
        # Monitor both processes and forward their output
        while True:
            # Check if API server is still running
            api_status = api_process.poll()
            if api_status is not None:
                logger.error(f"API server exited with code: {api_status}")
                logger.info("Restarting API server...")
                api_process = subprocess.Popen(
                    [sys.executable, "run_api_server.py"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    bufsize=1
                )
            
            # Check if bot is still running
            bot_status = bot_process.poll()
            if bot_status is not None:
                logger.error(f"Telegram bot exited with code: {bot_status}")
                logger.info("Restarting Telegram bot...")
                bot_process = subprocess.Popen(
                    [sys.executable, "bot.py"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    bufsize=1
                )
            
            # Forward output from API server
            try:
                api_line = api_process.stdout.readline()
                if api_line:
                    logger.info(f"[API] {api_line.strip()}")
            except:
                pass
                
            # Forward output from bot
            try:
                bot_line = bot_process.stdout.readline()
                if bot_line:
                    logger.info(f"[BOT] {bot_line.strip()}")
            except:
                pass
            
            # Prevent CPU hogging
            time.sleep(0.1)
            
    except Exception as e:
        logger.error(f"Error in main process: {str(e)}")
        if api_process:
            api_process.terminate()
        if bot_process:
            bot_process.terminate()
        sys.exit(1)

if __name__ == "__main__":
    main()