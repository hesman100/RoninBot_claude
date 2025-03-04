import os
import sqlite3
import requests
import json
import time
import logging
from typing import Dict, List, Optional, Tuple, Any

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
COUNTRY_LIST_PATH = "country_game/country_name.list"
DB_PATH = "country_game/database/countries.db"
MAP_IMAGES_DIR = "country_game/images/wiki_all_map_400pi"
FLAG_IMAGES_DIR = "country_game/images/wiki_flag"

# Custom flag paths for countries with missing flags
CUSTOM_FLAG_PATHS = {
    "Guinea-Bissau": "country_game/images/wiki_flag/GuineaBissau_flag.png",
    "São Tomé and Príncipe": "country_game/images/wiki_flag/So_Tom_and_Prncipe_flag.png"
}

# GeoAPIfy API configuration
GEOAPIFY_API_KEY = os.environ.get("GEOAPIFY_API_KEY")
GEOAPIFY_BASE_URL = "https://api.geoapify.com/v1/geocode/search"

class DatabaseBuilder:
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.countries = []
        self.missing_info = []
        self.request_count = 0
        self.api_limit = 300  # Conservative limit for free tier

    def connect_to_database(self):
        """Connect to SQLite database, creating the directory if needed"""
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
        logger.info(f"Connected to database at {DB_PATH}")

    def delete_existing_data(self):
        """Delete all existing data from the database"""
        try:
            self.cursor.execute("DROP TABLE IF EXISTS countries")
            self.cursor.execute("DROP TABLE IF EXISTS maps")
            self.cursor.execute("DROP TABLE IF EXISTS hints")
            self.conn.commit()
            logger.info("Deleted existing tables")
        except Exception as e:
            logger.error(f"Error deleting existing data: {e}")
            raise

    def create_schema(self):
        """Create the new database schema"""
        try:
            # Create the countries table with all required columns
            self.cursor.execute('''
            CREATE TABLE countries (
                number INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                neighbor_country TEXT,
                map_image_link TEXT,
                flag_image_link TEXT,
                capital TEXT,
                neighbor_capital TEXT,
                region TEXT,
                area REAL,
                population INTEGER,
                last_updated INTEGER
            )
            ''')
            self.conn.commit()
            logger.info("Created new database schema")
        except Exception as e:
            logger.error(f"Error creating schema: {e}")
            raise

    def load_country_list(self):
        """Load the list of countries from file"""
        try:
            with open(COUNTRY_LIST_PATH, 'r') as file:
                self.countries = [line.strip() for line in file if line.strip()]
            logger.info(f"Loaded {len(self.countries)} countries from {COUNTRY_LIST_PATH}")
        except Exception as e:
            logger.error(f"Error loading country list: {e}")
            raise

    def get_country_data_from_geoapify(self, country_name: str) -> Dict:
        """Get country data from GeoAPIfy API"""
        # Check if we're approaching the API limit
        if self.request_count >= self.api_limit:
            logger.warning(f"Reached API limit of {self.api_limit} requests. Skipping API calls for remaining countries.")
            return {}
        
        params = {
            'text': country_name.replace('_', ' '),
            'type': 'country',
            'format': 'json',
            'apiKey': GEOAPIFY_API_KEY
        }
        
        try:
            self.request_count += 1
            logger.info(f"Making API request {self.request_count}/{self.api_limit} for {country_name}")
            
            response = requests.get(GEOAPIFY_BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get('features') and len(data['features']) > 0:
                feature = data['features'][0]
                properties = feature.get('properties', {})
                
                # Extract relevant data
                result = {
                    'capital': properties.get('country_capital'),
                    'region': properties.get('continent'),
                    'area': properties.get('area'),
                    'population': properties.get('population'),
                }
                
                # Find neighbors (GeoAPIfy doesn't directly provide this, would need another source)
                result['neighbor_country'] = None
                result['neighbor_capital'] = None
                
                logger.info(f"Retrieved data for {country_name}: capital={result.get('capital')}, region={result.get('region')}")
                return result
            else:
                logger.warning(f"No data found for country: {country_name}")
                return {}
        except Exception as e:
            logger.error(f"Error fetching data for {country_name}: {e}")
            return {}

    def check_image_exists(self, country_name: str) -> Tuple[bool, bool]:
        """Check if map and flag images exist for the country"""
        formatted_name = country_name.replace(' ', '_')
        map_path = os.path.join(MAP_IMAGES_DIR, f"{formatted_name}_locator_map.png")
        flag_path = os.path.join(FLAG_IMAGES_DIR, f"{formatted_name}_flag.png")
        
        # Check for custom flag path
        if country_name in CUSTOM_FLAG_PATHS:
            flag_path = CUSTOM_FLAG_PATHS[country_name]
        
        map_exists = os.path.exists(map_path)
        flag_exists = os.path.exists(flag_path)
        
        return map_exists, flag_exists

    def populate_database(self):
        """Populate the database with country data"""
        for index, country_name in enumerate(self.countries, 1):
            try:
                # Format country name for image paths
                formatted_name = country_name.replace(' ', '_')
                
                # Define image links
                map_image_link = f"country_game/images/wiki_all_map_400pi/{formatted_name}_locator_map.png"
                
                # Use custom flag path if available
                if country_name in CUSTOM_FLAG_PATHS:
                    flag_image_link = CUSTOM_FLAG_PATHS[country_name]
                else:
                    flag_image_link = f"country_game/images/wiki_flag/{formatted_name}_flag.png"
                
                # Check if images exist
                map_exists, flag_exists = self.check_image_exists(country_name)
                if not map_exists:
                    logger.warning(f"Map image not found for {country_name}")
                    self.missing_info.append(f"{country_name} - Missing map image")
                
                if not flag_exists:
                    logger.warning(f"Flag image not found for {country_name}")
                    self.missing_info.append(f"{country_name} - Missing flag image")
                
                # Get additional data from GeoAPIfy
                geo_data = self.get_country_data_from_geoapify(country_name)
                
                # Insert data into database
                self.cursor.execute('''
                INSERT INTO countries (
                    number, name, neighbor_country, map_image_link, flag_image_link, 
                    capital, neighbor_capital, region, area, population, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    index, 
                    formatted_name, 
                    geo_data.get('neighbor_country'),
                    map_image_link if map_exists else None,
                    flag_image_link if flag_exists or country_name in CUSTOM_FLAG_PATHS else None,
                    geo_data.get('capital'),
                    geo_data.get('neighbor_capital'),
                    geo_data.get('region'),
                    geo_data.get('area'),
                    geo_data.get('population'),
                    int(time.time())
                ))
                
                # Commit every 10 countries to avoid losing all data if there's an error
                if index % 10 == 0:
                    self.conn.commit()
                    logger.info(f"Progress: {index}/{len(self.countries)} countries processed")
                
                # Add a small delay to avoid hitting API rate limits
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error processing country {country_name}: {e}")
                self.missing_info.append(f"{country_name} - Error: {str(e)}")
                continue
        
        # Final commit
        self.conn.commit()
        logger.info("Database population completed")

    def close_connection(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

    def report_missing_info(self):
        """Report any missing information"""
        if self.missing_info:
            logger.warning(f"Missing information for {len(self.missing_info)} countries:")
            for info in self.missing_info:
                logger.warning(f"  - {info}")
        else:
            logger.info("All country information successfully added to database")

    def run(self):
        """Run the full database rebuild process"""
        try:
            self.connect_to_database()
            self.delete_existing_data()
            self.create_schema()
            self.load_country_list()
            self.populate_database()
            self.report_missing_info()
        finally:
            self.close_connection()

if __name__ == "__main__":
    if not GEOAPIFY_API_KEY:
        logger.error("GEOAPIFY_API_KEY environment variable is not set. Please set it and try again.")
        exit(1)
        
    logger.info("Starting country database rebuild process with GeoAPIfy API")
    builder = DatabaseBuilder()
    builder.run()
    logger.info("Country database rebuild completed")
