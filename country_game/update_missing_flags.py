import os
import sqlite3
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DB_PATH = "country_game/database/countries.db"

# Missing flag mappings
MISSING_FLAGS = {
    "Guinea-Bissau": "country_game/images/wiki_flag/GuineaBissau_flag.png",
    "São Tomé and Príncipe": "country_game/images/wiki_flag/So_Tom_and_Prncipe_flag.png"
}

def update_missing_flags():
    """Update the missing flag images in the database"""
    try:
        # Connect to the database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if the files exist
        for country, flag_path in MISSING_FLAGS.items():
            if os.path.exists(flag_path):
                logger.info(f"Flag image exists for {country} at {flag_path}")
            else:
                logger.warning(f"Flag image does not exist for {country} at {flag_path}")
                # We'll still update the database with the path, even if the file doesn't exist yet
        
        # Update each country's flag image
        for country, flag_path in MISSING_FLAGS.items():
            formatted_name = country.replace(' ', '_')
            # Update the flag_image_link for this country
            cursor.execute(
                "UPDATE countries SET flag_image_link = ? WHERE name LIKE ?",
                (flag_path, formatted_name)
            )
            
            if cursor.rowcount > 0:
                logger.info(f"Updated flag image for {country}")
            else:
                # Try without replacing spaces with underscores
                cursor.execute(
                    "UPDATE countries SET flag_image_link = ? WHERE name LIKE ?",
                    (flag_path, country)
                )
                if cursor.rowcount > 0:
                    logger.info(f"Updated flag image for {country} (without formatting)")
                else:
                    logger.warning(f"Could not find country {country} in database")
        
        # Commit the changes
        conn.commit()
        logger.info("Database updates committed successfully")
        
        # Verify the updates
        for country in MISSING_FLAGS.keys():
            formatted_name = country.replace(' ', '_')
            cursor.execute(
                "SELECT flag_image_link FROM countries WHERE name LIKE ? OR name LIKE ?",
                (country, formatted_name)
            )
            result = cursor.fetchone()
            if result:
                logger.info(f"Verified {country} now has flag image: {result[0]}")
            else:
                logger.warning(f"Could not verify {country} in database")
        
    except Exception as e:
        logger.error(f"Error updating missing flags: {e}")
        raise
    finally:
        if conn:
            conn.close()
            logger.info("Database connection closed")

if __name__ == "__main__":
    logger.info("Starting update of missing flag images")
    update_missing_flags()
    logger.info("Update of missing flag images completed")
