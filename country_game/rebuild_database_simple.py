import os
import sqlite3
import time
import logging
from typing import Dict, List, Optional, Tuple

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

# Hardcoded data for some major countries' capitals
CAPITAL_DATA = {
    "United_States": "Washington D.C.",
    "United_Kingdom": "London",
    "France": "Paris",
    "Germany": "Berlin",
    "Japan": "Tokyo",
    "Australia": "Canberra",
    "Brazil": "Brasília",
    "Canada": "Ottawa",
    "China": "Beijing",
    "Russia": "Moscow",
    "India": "New Delhi",
    "Italy": "Rome",
    "Spain": "Madrid",
    "Mexico": "Mexico City",
    "South_Korea": "Seoul",
    "Argentina": "Buenos Aires",
    "South_Africa": "Pretoria",
    "Egypt": "Cairo",
    "Turkey": "Ankara",
    "Indonesia": "Jakarta",
    "Nigeria": "Abuja",
    "Vietnam": "Hanoi"
}

# Region data for continents
REGION_DATA = {
    "Afghanistan": "Asia",
    "Albania": "Europe",
    "Algeria": "Africa",
    "Andorra": "Europe",
    "Angola": "Africa",
    "Argentina": "South America",
    "Australia": "Oceania",
    "Austria": "Europe",
    "Brazil": "South America",
    "Canada": "North America",
    "China": "Asia",
    "Egypt": "Africa",
    "France": "Europe",
    "Germany": "Europe",
    "India": "Asia",
    "Italy": "Europe",
    "Japan": "Asia",
    "Mexico": "North America",
    "Russia": "Europe/Asia",
    "South_Africa": "Africa",
    "Spain": "Europe",
    "United_Kingdom": "Europe",
    "United_States": "North America"
}

class SimpleDatabaseBuilder:
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.countries = []
        self.missing_info = []
        self.map_images_found = 0
        self.flag_images_found = 0

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

    def check_image_exists(self, country_name: str) -> Tuple[bool, bool]:
        """Check if map and flag images exist for the country"""
        formatted_name = country_name.replace(' ', '_')
        map_path = os.path.join(MAP_IMAGES_DIR, f"{formatted_name}_locator_map.png")
        flag_path = os.path.join(FLAG_IMAGES_DIR, f"{formatted_name}_flag.png")
        
        map_exists = os.path.exists(map_path)
        flag_exists = os.path.exists(flag_path)
        
        return map_exists, flag_exists

    def get_capital(self, country_name: str) -> str:
        """Get capital city for the country from hardcoded data"""
        formatted_name = country_name.replace(' ', '_')
        return CAPITAL_DATA.get(formatted_name, "Unknown")

    def get_region(self, country_name: str) -> str:
        """Get region (continent) for the country from hardcoded data"""
        formatted_name = country_name.replace(' ', '_')
        return REGION_DATA.get(formatted_name, "Unknown")

    def populate_database(self):
        """Populate the database with country data"""
        for index, country_name in enumerate(self.countries, 1):
            try:
                # Format country name for image paths
                formatted_name = country_name.replace(' ', '_')
                
                # Define image links
                map_image_link = f"country_game/images/wiki_all_map_400pi/{formatted_name}_locator_map.png"
                flag_image_link = f"country_game/images/wiki_flag/{formatted_name}_flag.png"
                
                # Check if images exist
                map_exists, flag_exists = self.check_image_exists(formatted_name)
                
                if map_exists:
                    self.map_images_found += 1
                else:
                    logger.warning(f"Map image not found for {country_name}")
                    self.missing_info.append(f"{country_name} - Missing map image")
                    map_image_link = None
                
                if flag_exists:
                    self.flag_images_found += 1
                else:
                    logger.warning(f"Flag image not found for {country_name}")
                    self.missing_info.append(f"{country_name} - Missing flag image")
                    flag_image_link = None
                
                # Get capital and region from hardcoded data
                capital = self.get_capital(formatted_name)
                region = self.get_region(formatted_name)
                
                # Insert data into database
                self.cursor.execute('''
                INSERT INTO countries (
                    number, name, neighbor_country, map_image_link, flag_image_link, 
                    capital, neighbor_capital, region, area, population, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    index, 
                    formatted_name, 
                    None,  # neighbor_country
                    map_image_link,
                    flag_image_link,
                    capital,
                    None,  # neighbor_capital
                    region,
                    None,  # area
                    None,  # population
                    int(time.time())
                ))
                
                # Commit every 20 countries to avoid losing all data if there's an error
                if index % 20 == 0:
                    self.conn.commit()
                    logger.info(f"Progress: {index}/{len(self.countries)} countries processed")
                
            except Exception as e:
                logger.error(f"Error processing country {country_name}: {e}")
                self.missing_info.append(f"{country_name} - Error: {str(e)}")
                continue
        
        # Final commit
        self.conn.commit()
        logger.info(f"Database population completed. Found {self.map_images_found} maps and {self.flag_images_found} flags.")

    def close_connection(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

    def report_missing_info(self):
        """Report any missing information"""
        if self.missing_info:
            logger.warning(f"Missing information for {len(self.missing_info)} countries:")
            for info in self.missing_info[:20]:  # Show just the first 20 to avoid overwhelming
                logger.warning(f"  - {info}")
            if len(self.missing_info) > 20:
                logger.warning(f"  - ... and {len(self.missing_info) - 20} more")
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
    logger.info("Starting country database rebuild process (simple version)")
    builder = SimpleDatabaseBuilder()
    builder.run()
    logger.info("Country database rebuild completed")
