import os
import sqlite3
import requests
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
COUNTRY_LIST_PATH = "country_game/country_name.list"
DB_PATH = "country_game/database/countries.db"
GEOAPIFY_API_KEY = os.getenv("GEOAPIFY_API_KEY")

def get_country_data_from_geoapify(country_name):
    """Fetch country data using GeoAPIfy API."""
    url = f"https://api.geoapify.com/v1/geocode/search?text={country_name}&apiKey={GEOAPIFY_API_KEY}"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        if data['features']:
            features = data['features'][0]
            return {
                "neighbor_country": features['properties'].get('neighboring_countries'),
                "capital": features['properties'].get('capital'),
                "neighbor_capital": features['properties'].get('neighboring_capitals'),
                "region": features['properties'].get('region'),
                "population": features['properties'].get('population'),
                "area": features['properties'].get('area')
            }
    else:
        logger.error(f"Failed to fetch data for {country_name}. Status: {response.status_code}")
    return {}

def update_countries_data():
    """Update countries database with additional details from GeoAPIfy."""
    if not os.path.exists(DB_PATH):
        logger.error(f"Database file not found at {DB_PATH}")
        return
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        with open(COUNTRY_LIST_PATH, 'r') as file:
            countries = [line.strip() for line in file if line.strip()]

        for country_name in countries:
            logger.info(f"Fetching data for {country_name} from GeoAPIfy")
            country_data = get_country_data_from_geoapify(country_name)
            if country_data:
                # Update country details in the database
                cursor.execute('''
                    UPDATE countries 
                    SET neighbor_country = ?, capital = ?, neighbor_capital = ?, 
                        region = ?, population = ?, area = ?
                    WHERE name = ?''', (
                    country_data.get("neighbor_country"), 
                    country_data.get("capital"), 
                    country_data.get("neighbor_capital"), 
                    country_data.get("region"),
                    country_data.get("population"), 
                    country_data.get("area"),
                    country_name
                ))
            else:
                logger.warning(f"No data found for {country_name}")

        conn.commit()
        logger.info("Countries data updated successfully")
        
    except Exception as e:
        logger.error(f"Error updating countries data: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    logger.info("Starting countries data update process")
    update_countries_data()
    logger.info("Countries data update completed")
