import os
import sqlite3
import logging
from typing import Dict, List, Optional, Tuple

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DB_PATH = "country_game/database/countries.db"
COUNTRY_LIST_PATH = "country_game/country_name.list"

def verify_database():
    """Verify the country database exists and has the correct data"""
    try:
        # Check if database exists
        if not os.path.exists(DB_PATH):
            logger.error(f"Database file not found at: {DB_PATH}")
            return False
        
        # Connect to database
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check if countries table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='countries'")
        if not cursor.fetchone():
            logger.error("Countries table does not exist in database")
            conn.close()
            return False
        
        # Count countries in the database
        cursor.execute("SELECT COUNT(*) FROM countries")
        count = cursor.fetchone()[0]
        logger.info(f"Database contains {count} countries")
        
        # Check original country list count
        with open(COUNTRY_LIST_PATH, 'r') as file:
            original_countries = [line.strip() for line in file if line.strip()]
        logger.info(f"Original country list contains {len(original_countries)} countries")
        
        # Verify all expected countries exist
        missing_countries = []
        for country in original_countries:
            formatted_name = country.replace(' ', '_')
            cursor.execute("SELECT name FROM countries WHERE name = ?", (formatted_name,))
            if not cursor.fetchone():
                missing_countries.append(country)
        
        if missing_countries:
            logger.warning(f"Missing {len(missing_countries)} countries in the database:")
            for country in missing_countries[:10]:  # Show just the first 10
                logger.warning(f"  - {country}")
            if len(missing_countries) > 10:
                logger.warning(f"  - ... and {len(missing_countries) - 10} more")
            
        # Check for countries with missing information (NULL values)
        cursor.execute("""
        SELECT name FROM countries 
        WHERE capital IS NULL OR capital = 'Unknown' 
        OR region IS NULL OR region = 'Unknown'
        """)
        missing_info_countries = [row['name'] for row in cursor.fetchall()]
        
        if missing_info_countries:
            logger.warning(f"{len(missing_info_countries)} countries have missing capital or region information")
            for country in missing_info_countries[:10]:  # Show just the first 10
                logger.warning(f"  - {country}")
            if len(missing_info_countries) > 10:
                logger.warning(f"  - ... and {len(missing_info_countries) - 10} more")
        
        # Check specifically for Guinea-Bissau and São Tomé and Príncipe
        for special_country in ["Guinea-Bissau", "São_Tomé_and_Príncipe"]:
            cursor.execute("SELECT flag_image_link FROM countries WHERE name = ?", (special_country,))
            row = cursor.fetchone()
            if row and row['flag_image_link']:
                logger.info(f"Country {special_country} has flag image: {row['flag_image_link']}")
            else:
                logger.warning(f"Country {special_country} is missing flag image")
        
        # Show a few random countries with their complete information
        cursor.execute("SELECT * FROM countries ORDER BY RANDOM() LIMIT 5")
        sample_countries = cursor.fetchall()
        logger.info("Sample countries from database:")
        for country in sample_countries:
            country_dict = dict(country)
            logger.info(f"  - {country_dict['name']}:")
            logger.info(f"    Capital: {country_dict['capital']}")
            logger.info(f"    Region: {country_dict['region']}")
            logger.info(f"    Population: {country_dict['population']}")
            logger.info(f"    Area: {country_dict['area']}")
            logger.info(f"    Map image: {country_dict['map_image_link']}")
            logger.info(f"    Flag image: {country_dict['flag_image_link']}")
        
        # Close connection
        conn.close()
        
        # Overall check
        if count >= len(original_countries) * 0.9:  # At least 90% of countries should be in the database
            logger.info("Database verification successful! Most countries are present.")
            return True
        else:
            logger.warning("Database verification shows significant missing countries.")
            return False
            
    except Exception as e:
        logger.error(f"Error verifying database: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting database verification")
    result = verify_database()
    if result:
        logger.info("Database verification completed successfully")
    else:
        logger.error("Database verification failed")
