import os
import sqlite3
import requests
import json
import time
import logging
import random
from typing import Dict, List, Optional, Tuple, Any, Set

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
REST_COUNTRIES_API_URL = "https://restcountries.com/v3.1/all"

# Number of neighbor countries to include
MIN_NEIGHBORS = 9

# Custom flag paths for countries with missing flags
CUSTOM_FLAG_PATHS = {
    "Guinea-Bissau": "country_game/images/wiki_flag/GuineaBissau_flag.png",
    "São Tomé and Príncipe": "country_game/images/wiki_flag/So_Tom_and_Prncipe_flag.png"
}

# Name mappings between our list and REST Countries API
NAME_MAPPINGS = {
    "United_States": "United States of America",
    "Russia": "Russian Federation",
    "North_Macedonia": "Macedonia",
    "Eswatini": "Swaziland",
    "Democratic_Republic_of_the_Congo": "DR Congo",
    "Republic_of_the_Congo": "Congo",
    "Vatican_City": "Holy See",
    "East_Timor": "Timor-Leste",
    "Cape_Verde": "Cabo Verde",
    "South_Korea": "Korea, Republic of",
    "North_Korea": "Korea, Democratic People's Republic of",
    "Ivory_Coast": "Côte d'Ivoire",
    "Czech_Republic": "Czechia",
    "São_Tomé_and_Príncipe": "Sao Tome and Principe",
    "Guinea-Bissau": "Guinea Bissau"
}

class RestCountriesDatabaseBuilder:
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.countries = []
        self.missing_info = []
        self.map_images_found = 0
        self.flag_images_found = 0
        self.rest_countries_data = {}  # API data keyed by country name
        self.country_mappings = {}     # Mappings from our names to API names
        self.api_country_by_cca3 = {}  # API data keyed by country code
        self.countries_by_region = {}  # Countries grouped by region
        self.all_api_countries = []    # All countries from API for random selection
        self.our_country_to_api = {}   # Mapping from our country names to API country objects
        self.known_capitals = []       # List of valid capitals for replacing "Unknown" values

    def connect_to_database(self):
        """Connect to SQLite database, creating the directory if needed"""
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
        logger.info(f"Connected to database at {DB_PATH}")

    def delete_existing_data(self):
        """Delete all existing data from the database"""
        try:
            if self.cursor is None:
                raise ValueError("Database connection not established. Call connect_to_database() first.")

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
            if self.cursor is None:
                raise ValueError("Database connection not established. Call connect_to_database() first.")

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

    def fetch_rest_countries_data(self):
        """Fetch country data from REST Countries API"""
        try:
            logger.info(f"Fetching country data from REST Countries API: {REST_COUNTRIES_API_URL}")
            response = requests.get(REST_COUNTRIES_API_URL)
            response.raise_for_status()

            countries_data = response.json()
            logger.info(f"Received data for {len(countries_data)} countries from REST Countries API")

            # Store all countries for later use
            self.all_api_countries = countries_data

            # Create mappings from country name to data
            for country in countries_data:
                name = country.get('name', {}).get('common')
                if name:
                    self.rest_countries_data[name] = country
                    # Also add official name as alternative
                    official_name = country.get('name', {}).get('official')
                    if official_name and official_name != name:
                        self.rest_countries_data[official_name] = country

                # Add alternative names
                alt_spellings = country.get('altSpellings', [])
                for alt_name in alt_spellings:
                    if alt_name and alt_name not in self.rest_countries_data:
                        self.rest_countries_data[alt_name] = country

                # Add to CCA3 index for border lookups
                cca3 = country.get('cca3')
                if cca3:
                    self.api_country_by_cca3[cca3] = country

            # Create reverse mappings from our country names to API names
            for our_name, api_name in NAME_MAPPINGS.items():
                self.country_mappings[our_name] = api_name

            # Group countries by region for neighbor filling
            for country in countries_data:
                region = country.get('region')
                if region:
                    if region not in self.countries_by_region:
                        self.countries_by_region[region] = []
                    self.countries_by_region[region].append(country)

            # Collect all valid capitals
            for country in countries_data:
                capitals = country.get('capital', [])
                if capitals and capitals[0]:
                    self.known_capitals.append(capitals[0])

            logger.info(f"Created mappings for {len(self.country_mappings)} country names")
            logger.info(f"Grouped countries into {len(self.countries_by_region)} regions")
            logger.info(f"Collected {len(self.known_capitals)} valid capital cities")
            return True
        except Exception as e:
            logger.error(f"Error fetching data from REST Countries API: {e}")
            return False

    def check_image_exists(self, country_name: str) -> Tuple[bool, bool]:
        """Check if map and flag images exist for the country"""
        formatted_name = country_name.replace(' ', '_')
        map_path = os.path.join(MAP_IMAGES_DIR, f"{formatted_name}_locator_map.png")
        flag_path = os.path.join(FLAG_IMAGES_DIR, f"{formatted_name}_flag.png")

        # Check for custom flag path
        if country_name in CUSTOM_FLAG_PATHS:
            flag_path = CUSTOM_FLAG_PATHS[country_name]
        elif formatted_name in CUSTOM_FLAG_PATHS:
            flag_path = CUSTOM_FLAG_PATHS[formatted_name]

        map_exists = os.path.exists(map_path)
        flag_exists = os.path.exists(flag_path)

        return map_exists, flag_exists

    def find_country_in_api(self, country_name: str) -> Optional[Dict]:
        """Find country data in the REST Countries API data"""
        # Try direct lookup with our name
        formatted_name = country_name.replace('_', ' ')
        if formatted_name in self.rest_countries_data:
            return self.rest_countries_data[formatted_name]

        # Try using our mappings
        if country_name in self.country_mappings:
            api_name = self.country_mappings[country_name]
            if api_name in self.rest_countries_data:
                return self.rest_countries_data[api_name]

        # Try with formatted name in mappings
        if formatted_name in self.country_mappings:
            api_name = self.country_mappings[formatted_name]
            if api_name in self.rest_countries_data:
                return self.rest_countries_data[api_name]

        # Try common variations
        for key in self.rest_countries_data.keys():
            if key.lower() == formatted_name.lower() or formatted_name.lower() in key.lower():
                return self.rest_countries_data[key]

        logger.warning(f"Could not find country '{country_name}' in REST Countries API data")
        return None

    def get_country_data(self, country_name: str) -> Dict:
        """Get country data from REST Countries API"""
        country_data = self.find_country_in_api(country_name)
        result = {
            'capital': None,
            'neighbor_country': None,
            'neighbor_capital': None,
            'region': None,
            'area': None,
            'population': None
        }

        if country_data:
            # Store this mapping for later neighbor processing
            self.our_country_to_api[country_name] = country_data

            # Get capital city
            capitals = country_data.get('capital', [])
            result['capital'] = capitals[0] if capitals else None

            # Get region (continent)
            result['region'] = country_data.get('region', None)

            # Get area
            result['area'] = country_data.get('area', None)

            # Get population
            result['population'] = country_data.get('population', None)

            # Neighbor information will be filled in a separate pass

        return result

    def get_random_capital(self) -> str:
        """Get a random capital city from our known capitals"""
        if not self.known_capitals:
            # Fallback capitals if the API didn't provide any
            fallback_capitals = ["London", "Paris", "Berlin", "Tokyo", "Washington D.C.", 
                                "Beijing", "Moscow", "Rome", "Madrid", "Ottawa", 
                                "Canberra", "Brasília", "Seoul", "New Delhi", "Cairo"]
            return random.choice(fallback_capitals)
        return random.choice(self.known_capitals)

    def get_neighbor_data(self, country_name: str, formatted_name: str) -> Tuple[str, str]:
        """Get neighbor countries and their capitals"""
        # Start with empty lists for neighbor countries and capitals
        neighbor_countries = []
        neighbor_capitals = []

        # Get the API country data for this country
        api_country = self.our_country_to_api.get(country_name)

        if api_country:
            # Get the region for region-based neighbor filling
            region = api_country.get('region')

            # Get real border countries first (if any)
            borders = api_country.get('borders', [])
            border_countries = []

            # Add real bordering countries first
            for border_code in borders:
                border_country = self.api_country_by_cca3.get(border_code)
                if border_country:
                    border_name = border_country.get('name', {}).get('common')
                    if border_name:
                        border_countries.append(border_country)

            # If we have real bordering countries, use them (up to MIN_NEIGHBORS)
            for border_country in border_countries[:MIN_NEIGHBORS]:
                neighbor_name = border_country.get('name', {}).get('common')
                capitals = border_country.get('capital', [])
                capital = capitals[0] if capitals and capitals[0] else self.get_random_capital()

                if neighbor_name and capital:
                    neighbor_countries.append(neighbor_name)
                    neighbor_capitals.append(capital)

            # If we don't have enough real neighbors, add countries from the same region
            if len(neighbor_countries) < MIN_NEIGHBORS and region in self.countries_by_region:
                region_countries = self.countries_by_region[region]
                # Shuffle to get random countries from the region
                random_region_countries = region_countries.copy()
                random.shuffle(random_region_countries)

                for region_country in random_region_countries:
                    # Skip if it's the country itself or already in neighbors
                    region_country_name = region_country.get('name', {}).get('common')
                    if (region_country_name == api_country.get('name', {}).get('common') or 
                        region_country_name in neighbor_countries):
                        continue

                    # Add the region country as a neighbor
                    capitals = region_country.get('capital', [])
                    capital = capitals[0] if capitals and capitals[0] else self.get_random_capital()

                    if region_country_name and capital:
                        neighbor_countries.append(region_country_name)
                        neighbor_capitals.append(capital)

                        # Stop if we have enough neighbors
                        if len(neighbor_countries) >= MIN_NEIGHBORS:
                            break

        # If we still don't have enough neighbors, add random countries
        if len(neighbor_countries) < MIN_NEIGHBORS:
            # Shuffle all countries to get random additions
            random_countries = self.all_api_countries.copy()
            random.shuffle(random_countries)

            for random_country in random_countries:
                # Skip if it's the country itself or already in neighbors
                random_country_name = random_country.get('name', {}).get('common')
                if (random_country_name == country_name or 
                    random_country_name in neighbor_countries):
                    continue

                # Add the random country as a neighbor
                capitals = random_country.get('capital', [])
                capital = capitals[0] if capitals and capitals[0] else self.get_random_capital()

                if random_country_name and capital:
                    neighbor_countries.append(random_country_name)
                    neighbor_capitals.append(capital)

                    # Stop if we have enough neighbors
                    if len(neighbor_countries) >= MIN_NEIGHBORS:
                        break

        # Join the neighbor countries and capitals into comma-separated strings
        neighbor_country_str = ",".join(neighbor_countries[:MIN_NEIGHBORS])
        neighbor_capital_str = ",".join(neighbor_capitals[:MIN_NEIGHBORS])

        return neighbor_country_str, neighbor_capital_str

    def populate_database(self):
        """Populate the database with country data"""
        total_processed = 0

        # First pass: Add all countries with basic data (excluding neighbors)
        for index, country_name in enumerate(self.countries, 1):
            try:
                # Log progress
                logger.info(f"Processing country {index}/{len(self.countries)}: {country_name}")

                # Format country name for image paths
                formatted_name = country_name.replace(' ', '_')

                # Define image links
                map_image_link = f"country_game/images/wiki_all_map_400pi/{formatted_name}_locator_map.png"

                # Use custom flag path if available
                if country_name in CUSTOM_FLAG_PATHS:
                    flag_image_link = CUSTOM_FLAG_PATHS[country_name]
                elif formatted_name in CUSTOM_FLAG_PATHS:
                    flag_image_link = CUSTOM_FLAG_PATHS[formatted_name]
                else:
                    flag_image_link = f"country_game/images/wiki_flag/{formatted_name}_flag.png"

                # Check if images exist
                map_exists, flag_exists = self.check_image_exists(country_name)

                if map_exists:
                    self.map_images_found += 1
                else:
                    logger.warning(f"Map image not found for {country_name}")
                    self.missing_info.append(f"{country_name} - Missing map image")
                    map_image_link = None

                if flag_exists:
                    self.flag_images_found += 1
                else:
                    # Try with custom flag paths
                    custom_path = None
                    if country_name in CUSTOM_FLAG_PATHS:
                        custom_path = CUSTOM_FLAG_PATHS[country_name]
                    elif formatted_name in CUSTOM_FLAG_PATHS:
                        custom_path = CUSTOM_FLAG_PATHS[formatted_name]

                    if custom_path and os.path.exists(custom_path):
                        flag_exists = True
                        self.flag_images_found += 1
                        flag_image_link = custom_path
                    else:
                        if custom_path:
                            logger.warning(f"Custom flag image not found for {country_name} at {custom_path}")
                            self.missing_info.append(f"{country_name} - Missing custom flag image")
                        else:
                            logger.warning(f"Flag image not found for {country_name}")
                            self.missing_info.append(f"{country_name} - Missing flag image")
                        flag_image_link = None

                # Get data from REST Countries API
                country_api_data = self.get_country_data(country_name)

                # Insert data into database
                if self.cursor is None:
                    raise ValueError("Database connection not established. Call connect_to_database() first.")

                self.cursor.execute('''
                INSERT INTO countries (
                    number, name, neighbor_country, map_image_link, flag_image_link, 
                    capital, neighbor_capital, region, area, population, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    index, 
                    formatted_name, 
                    None,  # neighbor_country will be updated in second pass
                    map_image_link,
                    flag_image_link,
                    country_api_data.get('capital'),
                    None,  # neighbor_capital will be updated in second pass
                    country_api_data.get('region'),
                    country_api_data.get('area'),
                    country_api_data.get('population'),
                    int(time.time())
                ))

                total_processed += 1

                # Commit every 20 countries to avoid losing all data if there's an error
                if index % 20 == 0:
                    self.conn.commit()
                    logger.info(f"Progress: {index}/{len(self.countries)} countries processed")

            except Exception as e:
                logger.error(f"Error processing country {country_name}: {e}")
                self.missing_info.append(f"{country_name} - Error: {str(e)}")
                continue

        # Commit the first pass
        self.conn.commit()
        logger.info("First pass completed. Now adding neighbor countries and capitals...")

        # Second pass: Update neighbor country and capital information
        for index, country_name in enumerate(self.countries, 1):
            try:
                # Format country name for database lookup
                formatted_name = country_name.replace(' ', '_')

                # Get neighbor data
                neighbor_countries, neighbor_capitals = self.get_neighbor_data(country_name, formatted_name)

                # Update the database record with neighbor information
                self.cursor.execute('''
                UPDATE countries 
                SET neighbor_country = ?, neighbor_capital = ?
                WHERE name = ?
                ''', (neighbor_countries, neighbor_capitals, formatted_name))

                # Commit every 20 countries
                if index % 20 == 0:
                    self.conn.commit()
                    logger.info(f"Neighbor data progress: {index}/{len(self.countries)} countries updated")

            except Exception as e:
                logger.error(f"Error updating neighbor data for {country_name}: {e}")
                self.missing_info.append(f"{country_name} - Error updating neighbors: {str(e)}")
                continue

        # Final commit
        self.conn.commit()
        logger.info(f"Database population completed. Processed {total_processed}/{len(self.countries)} countries. Found {self.map_images_found} maps and {self.flag_images_found} flags.")

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

            # Fetch data from REST Countries API
            if not self.fetch_rest_countries_data():
                logger.error("Failed to fetch data from REST Countries API. Aborting database rebuild.")
                return

            self.populate_database()
            self.report_missing_info()
        finally:
            self.close_connection()

if __name__ == "__main__":
    logger.info("Starting country database rebuild with REST Countries API")
    builder = RestCountriesDatabaseBuilder()
    builder.run()
    logger.info("Country database rebuild completed")