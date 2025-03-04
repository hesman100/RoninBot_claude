import sqlite3
import os
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database path
DB_PATH = "country_game/database/countries.db"

def update_flag_links():
    """Update missing flag links in the database"""
    # Define the flag paths to update
    updates = {
        "Guinea-Bissau": "country_game/images/wiki_flag/GuineaBissau_flag.png",
        "São Tomé and Príncipe": "country_game/images/wiki_flag/So_Tom_and_Prncipe_flag.png"
    }
    
    # Connect to the database
    if not os.path.exists(DB_PATH):
        logger.error(f"Database file not found at {DB_PATH}")
        return
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Update each country's flag link
        for country_name, flag_path in updates.items():
            cursor.execute("SELECT name FROM countries WHERE name = ? OR name = ?", 
                          (country_name, country_name.replace(' ', '_')))
            result = cursor.fetchone()
            
            if result:
                db_country_name = result[0]
                logger.info(f"Updating flag link for {db_country_name}")
                
                cursor.execute(
                    "UPDATE countries SET flag_image_link = ? WHERE name = ?", 
                    (flag_path, db_country_name)
                )
                
                if not os.path.exists(flag_path):
                    logger.warning(f"Flag image file does not exist at {flag_path}.")
            else:
                logger.warning(f"Country '{country_name}' not found in database")
        
        conn.commit()
        logger.info("Flag links updated successfully")
        
    except Exception as e:
        logger.error(f"Error updating flag links: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    logger.info("Starting flag links update process")
    update_flag_links()
    logger.info("Flag links update completed")
