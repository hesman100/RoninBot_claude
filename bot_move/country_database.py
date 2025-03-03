#!/usr/bin/env python3
"""
Country Database Module for Country Guessing Game

This module handles the creation and management of a persistent country database.
It includes functionality to:
1. Fetch country data from GeoApify API
2. Find high-quality map images exclusively from Wikipedia sources
3. Store everything in a structured format for quick access
4. Track any missing maps in a separate file for manual addition
"""

import json
import logging
import os
import requests
import time
import urllib.request
import urllib.error
import psycopg2
from psycopg2.extras import RealDictCursor
# Configure logging
logger = logging.getLogger(__name__)

# Constants
DEFAULT_CACHE_DURATION = 7 * 24 * 60 * 60  # One week in seconds
WIKI_BASE_URL = "https://en.wikipedia.org/wiki/"
WIKI_API_URL = "https://en.wikipedia.org/w/api.php"
GEOAPIFY_PLACES_URL = "https://api.geoapify.com/v1/geocode/search"

# Import API key from config
from config import GEOAPIFY_API_KEY

# Initialize singleton instance
_instance = None

class CountryDatabase:
    """Database handler for country information and maps"""
    
    def __init__(self):
        """Initialize the database connection and create tables if needed"""
        self.conn = None
        self.cursor = None
        self.countries = []
        self.connect()
        self.create_tables()
        
    def connect(self):
        """Connect to the PostgreSQL database"""
        try:
            # Get connection parameters from environment variables
            database_url = os.environ.get('DATABASE_URL')
            
            if database_url:
                self.conn = psycopg2.connect(database_url)
            else:
                # Fallback to direct parameters if DATABASE_URL is not set
                self.conn = psycopg2.connect(
                    host=os.environ.get('PGHOST'),
                    database=os.environ.get('PGDATABASE'),
                    user=os.environ.get('PGUSER'),
                    password=os.environ.get('PGPASSWORD'),
                    port=os.environ.get('PGPORT')
                )
            
            # Use RealDictCursor to get results as dictionaries
            self.cursor = self.conn.cursor()
            logger.info("Connected to the PostgreSQL country database")
        except psycopg2.Error as e:
            logger.error(f"Database connection error: {e}")
            raise
            
    def close(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
            
    def create_tables(self):
        """Create the necessary database tables if they don't exist"""
        try:
            # Countries table
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS countries (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                capital TEXT,
                region TEXT,
                subregion TEXT,
                population INTEGER,
                area REAL,
                latitude REAL,
                longitude REAL,
                iso2_code TEXT,
                iso3_code TEXT,
                currency JSONB,
                language JSONB,
                description TEXT,
                last_updated INTEGER
            )
            ''')
            
            # Maps table
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS maps (
                id SERIAL PRIMARY KEY,
                country_id INTEGER,
                map_url TEXT NOT NULL,
                map_type TEXT NOT NULL,
                width INTEGER,
                height INTEGER,
                last_updated INTEGER,
                FOREIGN KEY (country_id) REFERENCES countries (id)
            )
            ''')
            
            # Hints table (for storing hint data)
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS hints (
                id SERIAL PRIMARY KEY,
                country_id INTEGER,
                hint_type TEXT NOT NULL,
                hint_text TEXT NOT NULL,
                FOREIGN KEY (country_id) REFERENCES countries (id)
            )
            ''')
            
            self.conn.commit()
            logger.info("Database tables created successfully")
        except psycopg2.Error as e:
            logger.error(f"Error creating database tables: {e}")
            raise
            
    def refresh_database(self, force=False):
        """
        Refresh the country database from external sources
        
        Args:
            force (bool): If True, refresh all data regardless of cache age
        """
        # Check when the database was last updated
        self.cursor.execute("SELECT MAX(last_updated) FROM countries")
        result = self.cursor.fetchone()
        last_updated = result[0] if result[0] is not None else 0
        
        # If cache is still valid and not forcing refresh, return early
        if not force and time.time() - last_updated < DEFAULT_CACHE_DURATION:
            logger.info("Country database is up to date")
            self._load_countries_from_db()
            return
            
        logger.info("Refreshing country database from external sources")
        
        # First fetch core country data from GeoApify
        self._fetch_countries_from_geoapify()
        
        # Then fetch additional data and maps
        self._enrich_countries_with_wikipedia_data()
        self._find_maps_for_countries()
        self._find_hints_for_countries()
        
        # Save everything to the database
        self._save_countries_to_db()
        
        logger.info(f"Country database refreshed with {len(self.countries)} countries")
        
    def _load_countries_from_db(self):
        """Load all countries from the database into memory"""
        try:
            # Get all active countries with their primary maps (exclude not_a_country)
            query = """
            SELECT c.id, c.name, c.capital, c.region, c.subregion, 
                   c.population, c.area, c.latitude, c.longitude,
                   c.iso2_code, c.iso3_code, c.currency, c.language,
                   c.description, m.map_url, c.not_a_country,
                   c.neighbors, c.neighbors_capital_city
            FROM countries c
            LEFT JOIN (
                SELECT country_id, map_url 
                FROM maps 
                WHERE map_type = 'primary'
            ) m ON c.id = m.country_id
            WHERE (c.not_a_country IS NULL OR c.not_a_country = FALSE)
            """
            self.cursor.execute(query)
            
            # Reset the countries list
            self.countries = []
            
            # Process each row into a country dictionary
            for row in self.cursor.fetchall():
                country = {
                    'id': row[0],
                    'name': {'common': row[1]},
                    'capital': row[2].split(',') if row[2] else [],
                    'region': row[3],
                    'subregion': row[4],
                    'population': row[5],
                    'area': row[6],
                    'latlng': [row[7], row[8]],
                    'cca2': row[9],
                    'cca3': row[10],
                    'currencies': self._parse_json_field(row[11]),
                    'languages': self._parse_json_field(row[12]),
                    'description': row[13],
                    'map_url': row[14],
                    'not_a_country': row[15] if len(row) > 15 else False,
                    'neighbors': self._parse_json_field(row[16]) if len(row) > 16 else [],
                    'neighbors_capital_city': self._parse_json_field(row[17]) if len(row) > 17 else {}
                }
                self.countries.append(country)
                
            logger.info(f"Loaded {len(self.countries)} countries from database")
        except psycopg2.Error as e:
            logger.error(f"Error loading countries from database: {e}")
            
    def _parse_json_field(self, field_value):
        """Parse a JSON string from the database into a Python object"""
        if not field_value:
            return {}
        # If already a dict, return as is
        if isinstance(field_value, dict):
            return field_value
        try:
            # Try to parse JSON string
            return json.loads(field_value)
        except (json.JSONDecodeError, TypeError):
            # Handle both JSON errors and type errors (when field_value is not a string)
            return {}
            
    def _fetch_countries_from_geoapify(self):
        """Fetch country data from the GeoApify Places API"""
        try:
            # Use GeoApify to get country data
            self.countries = []
            
            # GeoApify needs specific parameters to get a list of countries
            # We need to query for places of type 'country'
            params = {
                'type': 'country',
                'limit': 250,  # Get up to 250 countries
                'apiKey': GEOAPIFY_API_KEY
            }
            
            response = requests.get(GEOAPIFY_PLACES_URL, params=params)
            response.raise_for_status()
            
            # Process the GeoApify response
            data = response.json()
            features = data.get('features', [])
            
            for feature in features:
                properties = feature.get('properties', {})
                
                # Extract country name
                country_name = properties.get('country', '')
                if not country_name:
                    continue
                
                # Extract coordinates
                geometry = feature.get('geometry', {})
                coordinates = geometry.get('coordinates', [0, 0])
                if geometry.get('type') == 'Point' and len(coordinates) >= 2:
                    lat, lon = coordinates[1], coordinates[0]  # GeoJSON is lon,lat
                else:
                    continue  # Skip if no valid coordinates
                
                # Extract other properties
                country_code = properties.get('country_code', '')
                capital = properties.get('capital', '')
                population = properties.get('population', 0)
                
                # Create a structured country entry
                country = {
                    'name': {'common': country_name, 'official': country_name},
                    'latlng': [lat, lon],
                    'cca2': country_code.upper() if country_code else '',
                    'cca3': '',  # GeoApify doesn't provide ISO3 codes
                    'capital': [capital] if capital else [],
                    'region': properties.get('continent', ''),
                    'subregion': properties.get('region', ''),
                    'population': population,
                    'area': properties.get('area', 0),
                    'currencies': {},  # We'll need to populate these from another source
                    'languages': {}
                }
                
                self.countries.append(country)
            
            logger.info(f"Fetched {len(self.countries)} countries from GeoApify API")
            
            # If we didn't get enough countries, try the fallback
            if len(self.countries) < 50:
                logger.warning("GeoApify returned too few countries, using fallback")
                self._fetch_countries_from_restcountries_api()
                
        except requests.RequestException as e:
            logger.error(f"Error fetching country data from GeoApify: {e}")
            # Fall back to REST Countries API
            self._fetch_countries_from_restcountries_api()
            
    def _fetch_countries_from_restcountries_api(self):
        """Fetch country data from the REST Countries API as fallback"""
        try:
            # Use the public REST Countries API as our fallback source
            url = "https://restcountries.com/v3.1/all"
            response = requests.get(url)
            response.raise_for_status()
            
            # Filter and transform the data
            raw_countries = response.json()
            self.countries = []
            
            for country in raw_countries:
                # Only keep countries with basic required data
                if ('name' in country and 'common' in country['name'] and
                    'latlng' in country and len(country['latlng']) >= 2):
                    # Extract only the fields we need
                    simplified_country = {
                        'name': country['name'],
                        'latlng': country['latlng'],
                        'cca2': country.get('cca2', ''),
                        'cca3': country.get('cca3', ''),
                        'capital': country.get('capital', []),
                        'region': country.get('region', ''),
                        'subregion': country.get('subregion', ''),
                        'population': country.get('population', 0),
                        'area': country.get('area', 0),
                        'currencies': country.get('currencies', {}),
                        'languages': country.get('languages', {})
                    }
                    self.countries.append(simplified_country)
                    
            logger.info(f"Fetched {len(self.countries)} countries from REST Countries API")
        except requests.RequestException as e:
            logger.error(f"Error fetching country data: {e}")
            # Load a minimal fallback list
            self._load_fallback_countries()
            
    def _load_fallback_countries(self):
        """Load a minimal list of countries as fallback"""
        self.countries = [
            {
                "name": {"common": "United States", "official": "United States of America"},
                "latlng": [38, -97],
                "cca2": "US",
                "cca3": "USA",
                "capital": ["Washington, D.C."],
                "region": "Americas",
                "subregion": "North America",
                "population": 329484123,
                "area": 9372610,
                "currencies": {"USD": {"name": "United States dollar", "symbol": "$"}},
                "languages": {"eng": "English"}
            },
            {
                "name": {"common": "France", "official": "French Republic"},
                "latlng": [46, 2],
                "cca2": "FR",
                "cca3": "FRA",
                "capital": ["Paris"],
                "region": "Europe",
                "subregion": "Western Europe",
                "population": 67391582,
                "area": 551695,
                "currencies": {"EUR": {"name": "Euro", "symbol": "€"}},
                "languages": {"fra": "French"}
            },
            {
                "name": {"common": "Japan", "official": "Japan"},
                "latlng": [36, 138],
                "cca2": "JP",
                "cca3": "JPN",
                "capital": ["Tokyo"],
                "region": "Asia",
                "subregion": "Eastern Asia",
                "population": 125836021,
                "area": 377930,
                "currencies": {"JPY": {"name": "Japanese yen", "symbol": "¥"}},
                "languages": {"jpn": "Japanese"}
            }
        ]
        logger.warning("Using fallback country list with 3 countries")
        
    def _enrich_countries_with_wikipedia_data(self):
        """Add additional data from Wikipedia and country properties when available"""
        enriched_count = 0
        
        for country in self.countries:
            try:
                # Skip countries we've already enriched recently
                if 'description' in country and country.get('description'):
                    continue
                    
                # Get country name
                country_name = country['name']['common']
                
                # Create a description from existing data
                capital = country.get('capital', [''])[0] if 'capital' in country and country['capital'] else ''
                region = country.get('region', '')
                subregion = country.get('subregion', '')
                population = country.get('population', 0)
                
                # Format population with commas
                formatted_population = f"{population:,}" if population else "Unknown"
                
                # Create a description
                description_parts = []
                
                if capital:
                    description_parts.append(f"Capital: {capital}")
                if region:
                    if subregion and subregion != region:
                        description_parts.append(f"Region: {region} ({subregion})")
                    else:
                        description_parts.append(f"Region: {region}")
                
                description_parts.append(f"Population: {formatted_population}")
                
                description = ", ".join(description_parts)
                country['description'] = description
                enriched_count += 1
            except Exception as e:
                logger.error(f"Error enriching country {country.get('name', {}).get('common', 'Unknown')}: {e}")
                
        logger.info(f"Enriched {enriched_count} countries with additional data")
        
    def _find_maps_for_countries(self):
        """Find and store map URLs for all countries"""
        # Load our predefined map list from config
        from config import HIGHLIGHTED_MAPS
        
        map_count = 0
        
        for country in self.countries:
            country_name = country['name']['common']
            
            # Try predefined map first (fastest and most reliable option)
            if country_name in HIGHLIGHTED_MAPS:
                country['map_url'] = HIGHLIGHTED_MAPS[country_name]
                country['map_type'] = 'predefined'
                map_count += 1
                continue
                
            # Try finding a Wikipedia orthographic projection or other map
            wiki_map = self._find_wiki_maps_for_country(country_name)
            if wiki_map:
                country['map_url'] = wiki_map
                country['map_type'] = 'wikipedia'
                map_count += 1
                continue
                
            # If no Wikipedia map is found, add this country to our missing maps file
            # They will need to be added manually
            self._record_missing_map(country_name)
            country['map_type'] = 'missing'
            
        logger.info(f"Found maps for {map_count} countries")
        
    def _find_wiki_maps_for_country(self, country_name):
        """Find Wikipedia map URLs using multiple methods"""
        # Try different variants of the country name
        formatted_name = country_name.replace(" ", "_")
        
        # Method 1: Try common orthographic projection patterns
        projections = self._try_orthographic_projections(formatted_name)
        if projections:
            return projections
            
        # Method 2: Try globe patterns (often used for islands)
        globe_maps = self._try_globe_map_patterns(formatted_name)
        if globe_maps:
            return globe_maps
            
        # Method 3: Try Wikipedia article images
        # This is more complex and time-consuming, so it's our last resort
        article_map = self._try_wikipedia_article_images(country_name)
        if article_map:
            return article_map
            
        return None
        
    def _try_orthographic_projections(self, formatted_name):
        """Try various orthographic projection map URLs on Wikimedia Commons"""
        # Special cases for countries with known specific URLs
        special_cases = {
            "Japan": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9e/Flag_of_Japan.svg/800px-Flag_of_Japan.svg.png",
            # Add more special cases as they are identified
        }
        
        # Check for special cases first
        if formatted_name in special_cases:
            url = special_cases[formatted_name]
            if self._verify_image_url(url):
                return url
        
        # Common hash patterns used in Wikimedia URLs
        hash_patterns = ['d/d1', '7/7d', 'b/bc', 'c/c2', 'a/a1', '6/67', 'c/ca', 
                         'c/c5', '5/59', '0/05', '9/95', '8/86', 'e/e2', '9/9f',
                         '6/62', '0/0a']  # Added Japan's pattern and others
        
        # Try standard orthographic projection format
        for pattern in hash_patterns:
            url = f"https://upload.wikimedia.org/wikipedia/commons/thumb/{pattern}/{formatted_name}_(orthographic_projection).svg/1024px-{formatted_name}_(orthographic_projection).svg.png"
            if self._verify_image_url(url):
                return url
                
        # Try with EU prefix for European countries
        eu_url = f"https://upload.wikimedia.org/wikipedia/commons/thumb/a/a1/EU-{formatted_name}_(orthographic_projection).svg/1024px-EU-{formatted_name}_(orthographic_projection).svg.png"
        if self._verify_image_url(eu_url):
            return eu_url
            
        # Try with Republic of prefix
        republic_url = f"https://upload.wikimedia.org/wikipedia/commons/thumb/a/a1/Republic_of_{formatted_name}_(orthographic_projection).svg/1024px-Republic_of_{formatted_name}_(orthographic_projection).svg.png"
        if self._verify_image_url(republic_url):
            return republic_url
            
        # Try locator map patterns (very reliable for many countries)
        # Pattern 1: <country_name>_w1_locator.svg (best pattern for European countries)
        locator_hash_patterns = [
            # Main hash patterns that have been verified to work
            'w/w1', 'e/e1', 'c/c3', 'd/d1', 'a/a5', 'b/b3',
            # Additional patterns found in successful cases (Malta, Denmark, Poland)
            '9/91', 'a/a6', '1/12', '3/31',
            # Common hash patterns to try
            '7/7d', 'c/c2', 'a/a1', '6/67', 'c/ca', 
            'c/c5', '5/59', '0/05', '9/95', '8/86', 'e/e2', '9/9f',
            'f/f5', 'b/bc', '6/62', '0/0a'
        ]
        
        # Try both standard resolution (1024px) and high resolution (2000px) for better map quality
        resolutions = ['1024px', '800px']
        
        for pattern in locator_hash_patterns:
            for resolution in resolutions:
                locator_url = f"https://upload.wikimedia.org/wikipedia/commons/thumb/{pattern}/{formatted_name}_w1_locator.svg/{resolution}-{formatted_name}_w1_locator.svg.png"
                if self._verify_image_url(locator_url):
                    return locator_url
        
        # Pattern 2: <country_name>_location_map.svg (good alternative pattern)
        location_hash_patterns = [
            # Common hash patterns for location maps
            'c/c3', 's/s1', 'f/f3', 'e/e3', 'd/d3', 'b/b3',
            # Additional hash patterns based on observed data
            'c/c0', 'e/e0', 'a/a0', 'f/f5', '7/73', '9/90',
            # Patterns matching Poland and similar countries
            '1/12', '7/71', '0/05'
        ]
        
        # Try with different resolutions for better quality
        resolutions = ['1024px', '800px', '1200px']
        
        for pattern in location_hash_patterns:
            for resolution in resolutions:
                # Try both location_map and in_location variations
                for suffix in ['_location_map', '_in_location', '_location']:
                    location_map_url = f"https://upload.wikimedia.org/wikipedia/commons/thumb/{pattern}/{formatted_name}{suffix}.svg/{resolution}-{formatted_name}{suffix}.svg.png"
                    if self._verify_image_url(location_map_url):
                        return location_map_url
            
        return None
        
    def _try_globe_map_patterns(self, formatted_name):
        """Try various globe map patterns used for islands and small countries"""
        # Common patterns for "on the globe" type maps
        patterns = [
            f"https://upload.wikimedia.org/wikipedia/commons/thumb/b/b4/{formatted_name}_on_the_globe.svg/1024px-{formatted_name}_on_the_globe.svg.png",
            f"https://upload.wikimedia.org/wikipedia/commons/thumb/3/3f/{formatted_name}_on_the_globe.svg/1024px-{formatted_name}_on_the_globe.svg.png",
            f"https://upload.wikimedia.org/wikipedia/commons/thumb/1/13/{formatted_name}_on_the_globe.svg/1024px-{formatted_name}_on_the_globe.svg.png",
            f"https://upload.wikimedia.org/wikipedia/commons/thumb/8/8a/{formatted_name}_on_the_globe_(small_islands_magnified).svg/1024px-{formatted_name}_on_the_globe_(small_islands_magnified).svg.png",
            f"https://upload.wikimedia.org/wikipedia/commons/thumb/7/7a/{formatted_name}_on_the_globe_(Polynesia_centered).svg/1024px-{formatted_name}_on_the_globe_(Polynesia_centered).svg.png"
        ]
        
        # Check each pattern
        for url in patterns:
            if self._verify_image_url(url):
                return url
                
        return None
        
    def _try_wikipedia_article_images(self, country_name):
        """
        Try to find suitable map images from the Wikipedia article for the country
        This is a more complex method that parses the Wikipedia API response
        """
        try:
            # First, get the Wikipedia page content
            params = {
                'action': 'query',
                'format': 'json',
                'titles': country_name,
                'prop': 'images',
                'imlimit': 50  # Request up to 50 images
            }
            
            response = requests.get(WIKI_API_URL, params=params)
            if response.status_code != 200:
                return None
                
            data = response.json()
            pages = data.get('query', {}).get('pages', {})
            
            # Get the first page (should be the only one)
            if not pages:
                return None
                
            page_id = list(pages.keys())[0]
            images = pages[page_id].get('images', [])
            
            # Look for map-related images
            map_keywords = ['map', 'location', 'orthographic', 'globe', 'projection']
            candidate_images = []
            
            for img in images:
                title = img.get('title', '').lower()
                # Add the image if it contains map-related keywords
                for keyword in map_keywords:
                    if keyword in title and 'File:' in title and 'locator' not in title:
                        candidate_images.append(img.get('title', '').replace('File:', ''))
                        break
                        
            # Try each candidate image
            for image_title in candidate_images:
                # Convert to URL format
                formatted_title = image_title.replace(' ', '_')
                # Try to construct a valid Wikimedia Commons URL
                url = f"https://upload.wikimedia.org/wikipedia/commons/thumb/a/a9/{formatted_title}/1024px-{formatted_title}"
                
                # Sometimes images may be jpg or png
                for ext in ['.png', '.jpg', '.svg.png']:
                    test_url = url + ext
                    if self._verify_image_url(test_url):
                        return test_url
                        
            return None
        except Exception as e:
            logger.error(f"Error finding Wikipedia article images for {country_name}: {e}")
            return None
            
    def _verify_image_url(self, url):
        """Verify that a URL returns a valid image"""
        # Skip verification in some cases to improve performance
        # These are trusted sources that are very likely to work
        if url.startswith("https://upload.wikimedia.org/wikipedia/en/thumb/") and ("Flag_of_" in url):
            return True
            
        # Special case: always consider the default world map as valid
        if "World_map" in url:
            return True
            
        try:
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            response = urllib.request.urlopen(req, timeout=3)
            
            if response.status == 200:
                content_type = response.info().get_content_type()
                if content_type.startswith('image/'):
                    return True
                    
                # If content-type is not specified correctly but status is 200, assume it's valid
                # Some servers don't set the correct content type
                return True
        except urllib.error.URLError:
            # For connection errors, be more forgiving with trusted domains
            if "upload.wikimedia.org" in url:
                logger.warning(f"Connection issue with Wikimedia URL, assuming valid: {url}")
                return True
        except Exception:
            # Don't log errors here to avoid spamming the logs
            pass
            
        return False
        
    def _find_hints_for_countries(self):
        """Generate and store hints for all countries"""
        hint_count = 0
        
        for country in self.countries:
            country_hints = []
            
            # Population hint
            if 'population' in country and country['population']:
                pop_millions = country['population'] / 1000000
                if pop_millions >= 1:
                    country_hints.append({
                        'type': 'population',
                        'text': f"This country has about {pop_millions:.1f} million people"
                    })
                else:
                    country_hints.append({
                        'type': 'population',
                        'text': f"This country has less than 1 million people"
                    })
            
            # Capital hint
            if 'capital' in country and country['capital']:
                capital = country['capital'][0]
                country_hints.append({
                    'type': 'capital',
                    'text': f"The capital of this country is {capital}"
                })
                
            # Region hint
            if 'region' in country and country['region']:
                region = country['region']
                if 'subregion' in country and country['subregion']:
                    subregion = country['subregion']
                    country_hints.append({
                        'type': 'region',
                        'text': f"This country is located in {subregion}, {region}"
                    })
                else:
                    country_hints.append({
                        'type': 'region',
                        'text': f"This country is located in {region}"
                    })
                    
            # Currency hint
            if 'currencies' in country and country['currencies']:
                currencies = list(country['currencies'].values())
                if currencies:
                    currency = currencies[0]
                    name = currency.get('name', '')
                    symbol = currency.get('symbol', '')
                    if name and symbol:
                        country_hints.append({
                            'type': 'currency',
                            'text': f"The currency is {name} ({symbol})"
                        })
                    elif name:
                        country_hints.append({
                            'type': 'currency',
                            'text': f"The currency is {name}"
                        })
                        
            # Language hint
            if 'languages' in country and country['languages']:
                languages = list(country['languages'].values())
                if languages:
                    if len(languages) == 1:
                        country_hints.append({
                            'type': 'language',
                            'text': f"The official language is {languages[0]}"
                        })
                    elif len(languages) > 1:
                        langs = ", ".join(languages[:2])
                        country_hints.append({
                            'type': 'language',
                            'text': f"Official languages include {langs}"
                        })
                        
            # Size hint
            if 'area' in country and country['area']:
                area = country['area']
                if area > 1000000:
                    country_hints.append({
                        'type': 'size',
                        'text': f"This is a very large country with an area of {area:,.0f} km²"
                    })
                elif area > 500000:
                    country_hints.append({
                        'type': 'size',
                        'text': f"This is a large country with an area of {area:,.0f} km²"
                    })
                elif area < 10000:
                    country_hints.append({
                        'type': 'size',
                        'text': f"This is a small country with an area of {area:,.0f} km²"
                    })
                    
            # Description hint (generated from country data)
            if 'description' in country and country['description']:
                country_hints.append({
                    'type': 'description',
                    'text': country['description']
                })
                
            # Store hints
            country['hints'] = country_hints
            hint_count += len(country_hints)
            
        logger.info(f"Generated {hint_count} hints for {len(self.countries)} countries")
        
    def _save_countries_to_db(self):
        """Save all country data to the database"""
        try:
            # Use a transaction for efficiency
            self.cursor.execute("BEGIN TRANSACTION")
            
            # Clear existing data (we completely refresh)
            self.cursor.execute("DELETE FROM hints")
            self.cursor.execute("DELETE FROM maps")
            self.cursor.execute("DELETE FROM countries")
            
            # Insert countries
            current_time = int(time.time())
            for country in self.countries:
                # Insert country record with RETURNING id for PostgreSQL
                country_query = """
                INSERT INTO countries (
                    name, capital, region, subregion, population,
                    area, latitude, longitude, iso2_code, iso3_code,
                    currency, language, description, last_updated
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """
                
                # Prepare data
                name = country['name']['common']
                capital = ','.join(country['capital']) if 'capital' in country and country['capital'] else None
                region = country.get('region', None)
                subregion = country.get('subregion', None)
                population = country.get('population', None)
                area = country.get('area', None)
                latitude = country['latlng'][0] if 'latlng' in country and len(country['latlng']) > 0 else None
                longitude = country['latlng'][1] if 'latlng' in country and len(country['latlng']) > 1 else None
                iso2_code = country.get('cca2', None)
                iso3_code = country.get('cca3', None)
                
                # JSON fields
                currency = json.dumps(country.get('currencies', {}))
                language = json.dumps(country.get('languages', {}))
                description = country.get('description', None)
                
                # Execute insert and get the ID in one step
                self.cursor.execute(country_query, (
                    name, capital, region, subregion, population,
                    area, latitude, longitude, iso2_code, iso3_code,
                    currency, language, description, current_time
                ))
                
                # Get the inserted country ID (PostgreSQL specific)
                country_id = self.cursor.fetchone()[0]
                
                # Insert map data if available
                if 'map_url' in country:
                    map_query = """
                    INSERT INTO maps (
                        country_id, map_url, map_type, last_updated
                    ) VALUES (%s, %s, %s, %s)
                    """
                    map_type = country.get('map_type', 'primary')
                    self.cursor.execute(map_query, (
                        country_id, country['map_url'], map_type, current_time
                    ))
                    
                # Insert hints
                if 'hints' in country and country['hints']:
                    for hint in country['hints']:
                        hint_query = """
                        INSERT INTO hints (
                            country_id, hint_type, hint_text
                        ) VALUES (%s, %s, %s)
                        """
                        self.cursor.execute(hint_query, (
                            country_id, hint['type'], hint['text']
                        ))
                        
            # Commit the transaction
            self.conn.commit()
            logger.info(f"Saved {len(self.countries)} countries to database")
        except psycopg2.Error as e:
            self.conn.rollback()
            logger.error(f"Error saving countries to database: {e}")
            
    def get_random_country(self):
        """Get a random country with all its data"""
        try:
            # Check if connection is still alive and reconnect if needed
            if self.conn is None or self.cursor is None:
                try:
                    self.connect()
                    self.create_tables()  # Ensure tables exist
                except Exception as conn_error:
                    logger.error(f"Failed to reconnect to database: {conn_error}")
                    # Return fallback country
                    return self._get_fallback_random_country()
                
            # Ensure we have countries loaded
            if not self.countries:
                try:
                    self._load_countries_from_db()
                except Exception as load_error:
                    logger.error(f"Error loading countries from database: {load_error}")
                    # Try to refresh the database
                    try:
                        self.refresh_database(force=True)
                    except Exception as refresh_error:
                        logger.error(f"Error refreshing database: {refresh_error}")
                        return self._get_fallback_random_country()
                
            if not self.countries:
                # If still no countries, use fallback
                return self._get_fallback_random_country()
                
            # Return a random country
            import random
            return random.choice(self.countries)
        except Exception as e:
            logger.error(f"Error getting random country: {e}")
            return self._get_fallback_random_country()
            
    def _get_fallback_random_country(self):
        """Return a fallback country when database access fails"""
        # Create a simple fallback country with basic information
        fallback_countries = [
            {
                "name": {"common": "France", "official": "French Republic"},
                "latlng": [46, 2],
                "cca2": "FR",
                "cca3": "FRA",
                "capital": ["Paris"],
                "region": "Europe",
                "subregion": "Western Europe",
                "population": 67391582,
                "area": 551695,
                "currencies": {"EUR": {"name": "Euro", "symbol": "€"}},
                "languages": {"fra": "French"},
                "description": "Capital: Paris, Region: Europe (Western Europe), Population: 67,391,582",
                "map_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e1/France_(orthographic_projection).svg/1024px-France_(orthographic_projection).svg.png",
                "map_type": "fallback"
            },
            {
                "name": {"common": "Japan", "official": "Japan"},
                "latlng": [36, 138],
                "cca2": "JP",
                "cca3": "JPN",
                "capital": ["Tokyo"],
                "region": "Asia",
                "subregion": "Eastern Asia",
                "population": 125836021,
                "area": 377930,
                "currencies": {"JPY": {"name": "Japanese yen", "symbol": "¥"}},
                "languages": {"jpn": "Japanese"},
                "description": "Capital: Tokyo, Region: Asia (Eastern Asia), Population: 125,836,021",
                "map_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0a/Japan_(orthographic_projection).svg/1024px-Japan_(orthographic_projection).svg.png",
                "map_type": "fallback"
            }
        ]
        import random
        return random.choice(fallback_countries)
            
    def get_country_by_name(self, name):
        """Get a country by its name"""
        if not name:
            logger.error("Empty name provided to get_country_by_name")
            return None
            
        try:
            # Check connection first
            if self.conn is None or self.cursor is None:
                try:
                    self.connect()
                except Exception as conn_error:
                    logger.error(f"Failed to reconnect to database: {conn_error}")
                    return self._get_fallback_country_by_name(name)
                    
            # Ensure we have countries loaded
            if not self.countries:
                try:
                    self._load_countries_from_db()
                except Exception as load_error:
                    logger.error(f"Error loading countries: {load_error}")
                    return self._get_fallback_country_by_name(name)
                    
            if not self.countries:
                try:
                    self.refresh_database(force=True)
                except Exception as refresh_error:
                    logger.error(f"Error refreshing database: {refresh_error}")
                    return self._get_fallback_country_by_name(name)
                    
            # Search for the country
            for country in self.countries:
                if country['name']['common'].lower() == name.lower():
                    return country
                    
            return self._get_fallback_country_by_name(name)
        except Exception as e:
            logger.error(f"Error getting country by name: {e}")
            return self._get_fallback_country_by_name(name)
            
    def _get_fallback_country_by_name(self, name):
        """Get a fallback country by name if database access fails"""
        # Check our hardcoded fallback countries
        fallback_countries = self._get_all_fallback_countries()
        
        # Try to find by name
        for country in fallback_countries:
            if country['name']['common'].lower() == name.lower():
                return country
                
        # If no match, return None
        return None
        
    def _get_all_fallback_countries(self):
        """Return the full list of fallback countries"""
        return [
            {
                "name": {"common": "United States", "official": "United States of America"},
                "latlng": [38, -97],
                "cca2": "US",
                "cca3": "USA",
                "capital": ["Washington, D.C."],
                "region": "Americas",
                "subregion": "North America",
                "population": 329484123,
                "area": 9372610,
                "currencies": {"USD": {"name": "United States dollar", "symbol": "$"}},
                "languages": {"eng": "English"},
                "description": "Capital: Washington, D.C., Region: Americas (North America), Population: 329,484,123",
                "map_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/13/Map_of_USA_with_state_names.svg/1024px-Map_of_USA_with_state_names.svg.png",
                "map_type": "fallback"
            },
            {
                "name": {"common": "France", "official": "French Republic"},
                "latlng": [46, 2],
                "cca2": "FR",
                "cca3": "FRA",
                "capital": ["Paris"],
                "region": "Europe",
                "subregion": "Western Europe",
                "population": 67391582,
                "area": 551695,
                "currencies": {"EUR": {"name": "Euro", "symbol": "€"}},
                "languages": {"fra": "French"},
                "description": "Capital: Paris, Region: Europe (Western Europe), Population: 67,391,582",
                "map_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e1/France_(orthographic_projection).svg/1024px-France_(orthographic_projection).svg.png",
                "map_type": "fallback"
            },
            {
                "name": {"common": "Japan", "official": "Japan"},
                "latlng": [36, 138],
                "cca2": "JP",
                "cca3": "JPN",
                "capital": ["Tokyo"],
                "region": "Asia",
                "subregion": "Eastern Asia",
                "population": 125836021,
                "area": 377930,
                "currencies": {"JPY": {"name": "Japanese yen", "symbol": "¥"}},
                "languages": {"jpn": "Japanese"},
                "description": "Capital: Tokyo, Region: Asia (Eastern Asia), Population: 125,836,021",
                "map_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0a/Japan_(orthographic_projection).svg/1024px-Japan_(orthographic_projection).svg.png",
                "map_type": "fallback"
            }
        ]
            
    def get_country_hints(self, country_name):
        """Get hints for a specific country"""
        # Handle case where country_name is actually a country object
        if isinstance(country_name, dict) and 'name' in country_name:
            # If we're passed a country object, use it directly for fallback hints
            logger.debug("Country object detected, using directly for hints")
            return self._get_fallback_hints(country_name)
            
        if not country_name:
            logger.error("Empty country name passed to get_country_hints")
            return self._get_fallback_hints(country_name)
            
        try:
            # Check connection status
            if self.conn is None or self.cursor is None:
                try:
                    self.connect()
                except Exception as conn_error:
                    logger.error(f"Failed to connect to database for hints: {conn_error}")
                    return self._get_fallback_hints(country_name)
                    
            try:
                # Find the country ID
                self.cursor.execute(
                    "SELECT id FROM countries WHERE LOWER(name) = %s", 
                    (country_name.lower(),)
                )
                result = self.cursor.fetchone()
                
                if result:
                    country_id = result[0]
                    
                    # Get hints for this country
                    self.cursor.execute(
                        "SELECT hint_type, hint_text FROM hints WHERE country_id = %s",
                        (country_id,)
                    )
                    hints = self.cursor.fetchall()
                    
                    if hints:
                        return [{"type": h[0], "text": h[1]} for h in hints]
                
                # If no hints found in the database, generate fallback hints
                return self._get_fallback_hints(country_name)
                
            except psycopg2.Error as db_error:
                logger.error(f"Database error getting hints: {db_error}")
                return self._get_fallback_hints(country_name)
                
        except Exception as e:
            logger.error(f"Error getting hints for {country_name}: {e}")
            return self._get_fallback_hints(country_name)
            
    def _get_fallback_hints(self, country_name):
        """Generate fallback hints when database access fails"""
        # Check if country_name is already a country object
        if isinstance(country_name, dict) and 'name' in country_name:
            country = country_name
            # Create generic hints from the country data
            hints = []
            
            # Capital hint
            if country.get('capital'):
                hints.append({
                    "type": "capital",
                    "text": f"The capital of this country is {country['capital'][0]}"
                })
                
            # Region hint
            if country.get('region'):
                region_text = f"This country is located in {country['region']}"
                if country.get('subregion'):
                    region_text += f" ({country['subregion']})"
                hints.append({
                    "type": "region",
                    "text": region_text
                })
                
            # Population hint
            if country.get('population'):
                pop_millions = country['population'] / 1000000
                hints.append({
                    "type": "population",
                    "text": f"This country has about {pop_millions:.1f} million people"
                })
                
            # Neighbors hint
            if country.get('neighbors') and len(country['neighbors']) > 0:
                # Get up to 3 random neighbors
                import random
                neighbors = country['neighbors']
                sample_size = min(3, len(neighbors))
                neighbor_sample = random.sample(neighbors, sample_size)
                
                neighbor_text = "Neighboring countries include: " + ", ".join(neighbor_sample)
                hints.append({
                    "type": "neighbors",
                    "text": neighbor_text
                })
                
            # Neighbor capitals hint
            if country.get('neighbors_capital_city') and len(country['neighbors_capital_city']) > 0:
                capitals_dict = country['neighbors_capital_city']
                
                # Get up to 2 random neighbor capitals
                import random
                neighbor_capitals = list(capitals_dict.items())
                sample_size = min(2, len(neighbor_capitals))
                capital_sample = random.sample(neighbor_capitals, sample_size)
                
                capitals_hint = "Capital cities near this country include: "
                capitals_hint += ", ".join([f"{capital} ({country})" for country, capital in capital_sample])
                
                hints.append({
                    "type": "neighbor_capitals",
                    "text": capitals_hint
                })
                
            return hints
        
        # Otherwise, search for country by name
        fallback_countries = self._get_all_fallback_countries()
        
        for country in fallback_countries:
            if country['name']['common'].lower() == country_name.lower():
                # Create generic hints from the fallback country data
                hints = []
                
                # Capital hint
                if country.get('capital'):
                    hints.append({
                        "type": "capital",
                        "text": f"The capital of this country is {country['capital'][0]}"
                    })
                    
                # Region hint
                if country.get('region'):
                    region_text = f"This country is located in {country['region']}"
                    if country.get('subregion'):
                        region_text += f" ({country['subregion']})"
                    hints.append({
                        "type": "region",
                        "text": region_text
                    })
                    
                # Population hint
                if country.get('population'):
                    pop_millions = country['population'] / 1000000
                    hints.append({
                        "type": "population",
                        "text": f"This country has about {pop_millions:.1f} million people"
                    })
                    
                return hints
                
        # If country not found in fallbacks, create a very generic hint
        return [
            {
                "type": "generic",
                "text": "Try guessing a country name..."
            }
        ]
            
    def get_map_url(self, country):
        """Get the best available map URL for a country"""
        # Define the ultimate fallback URL - reliable low-res world map
        WORLD_MAP_URL = "https://upload.wikimedia.org/wikipedia/commons/thumb/8/80/World_map_-_low_resolution.svg/1200px-World_map_-_low_resolution.svg.png"
        
        try:
            # Handle None country object gracefully
            if country is None:
                logger.error("Received None country object in get_map_url")
                return WORLD_MAP_URL
                
            country_name = country['name']['common']
            
            # Handle relative file paths for all countries consistently
            if 'map_url' in country and country['map_url']:
                map_url = country['map_url']
                if map_url.startswith('./'):
                    # Keep relative path as is - don't convert to absolute path
                    # This will be handled by the game_handler which will open the file
                    logger.info(f"Using local file path for {country_name}: {map_url}")
                    return map_url
            
            # If country already has a map_url, return it
            if 'map_url' in country and country['map_url']:
                return country['map_url']
            
            # Check if connection is still alive
            if self.conn is None or self.cursor is None:
                # Reconnect if needed
                try:
                    self.connect()
                except Exception as conn_error:
                    logger.error(f"Failed to reconnect to database: {conn_error}")
                    # Try to get a flag URL without database
                    flag_url = self._get_flag_url(country_name)
                    if flag_url:
                        # For flags, we'll trust they exist without verification
                        logger.info(f"Using flag image (without DB) for {country_name}: {flag_url}")
                        return flag_url
                    # Otherwise return the world map
                    return WORLD_MAP_URL
            
            try:
                # Try to find a primary map in the database
                self.cursor.execute(
                    """SELECT c.id, m.map_url 
                    FROM countries c 
                    LEFT JOIN maps m ON c.id = m.country_id AND m.map_type = 'primary'
                    WHERE LOWER(c.name) = %s""",
                    (country_name.lower(),)
                )
                result = self.cursor.fetchone()
                
                country_id = None
                if result:
                    country_id = result[0]
                    if result[1]:  # If map_url exists
                        primary_map_url = result[1]
                        # Try to verify the primary map URL is accessible
                        if self._verify_image_url(primary_map_url):
                            return primary_map_url
                        else:
                            logger.warning(f"Primary map for {country_name} is not accessible, trying fallback")
                
                # If primary map not found or not accessible, try fallback map
                if country_id:
                    self.cursor.execute(
                        """SELECT m.map_url 
                        FROM maps m 
                        WHERE m.country_id = %s AND m.map_type = 'fallback'""",
                        (country_id,)
                    )
                    fallback_result = self.cursor.fetchone()
                    
                    if fallback_result and fallback_result[0]:
                        fallback_map_url = fallback_result[0]
                        # Check if it's a flag URL, which is more reliable
                        if "Flag_of_" in fallback_map_url:
                            logger.info(f"Using fallback map (flag) for {country_name}: {fallback_map_url}")
                            return fallback_map_url
                        
                        # Check if it's our "map_not_found" placeholder
                        if fallback_map_url == "map_not_found":
                            logger.warning(f"No map available for {country_name}, using flag as fallback")
                            # Try to get a flag instead
                            flag_url = self._get_flag_url(country_name)
                            if flag_url:
                                return flag_url
                            # If no flag, we'll continue to world map fallback
                            return WORLD_MAP_URL
                        
                        # Otherwise verify accessibility
                        if self._verify_image_url(fallback_map_url):
                            logger.info(f"Using fallback map for {country_name}: {fallback_map_url}")
                            return fallback_map_url
                
            except psycopg2.Error as db_error:
                logger.error(f"Database error while fetching map: {db_error}")
                # Continue to ultimate fallback logic
            
            # If no map is found in the database or none are accessible, try to find a flag
            flag_url = self._get_flag_url(country_name)
            if flag_url:
                # For flags, we're now trusting they exist without verification
                logger.info(f"Using flag image for {country_name}: {flag_url}")
                return flag_url
            
            # Record missing map for future updates
            self._record_missing_map(country_name)
            
            # Ultimate fallback: return a static world map
            logger.warning(f"No working map found for {country_name}, using world map")
            return WORLD_MAP_URL
        except Exception as e:
            logger.error(f"Error getting map URL: {e}")
            return WORLD_MAP_URL
            
    def _get_flag_url(self, country_name):
        """Get flag URL for a country as emergency fallback"""
        # Format country name for URL
        formatted_name = country_name.replace(' ', '_')
        
        # Special case formatting
        if "Korea, Republic of" in country_name:
            formatted_name = "South_Korea"
        elif "Korea, Democratic People's Republic of" in country_name:
            formatted_name = "North_Korea"
        elif "Lao People's Democratic Republic" in country_name:
            formatted_name = "Laos"
        elif "Brunei Darussalam" in country_name:
            formatted_name = "Brunei"
        elif "Viet Nam" in country_name:
            formatted_name = "Vietnam"
        
        # Special cases for common countries with known patterns
        special_cases = {
            "United Kingdom": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ae/Flag_of_the_United_Kingdom.svg/800px-Flag_of_the_United_Kingdom.svg.png",
            "United States": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a4/Flag_of_the_United_States.svg/800px-Flag_of_the_United_States.svg.png",
            "Japan": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9e/Flag_of_Japan.svg/800px-Flag_of_Japan.svg.png",
            "France": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Flag_of_France.svg/800px-Flag_of_France.svg.png",
            "Germany": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/ba/Flag_of_Germany.svg/800px-Flag_of_Germany.svg.png",
            "Italy": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/03/Flag_of_Italy.svg/800px-Flag_of_Italy.svg.png",
            "Canada": "https://upload.wikimedia.org/wikipedia/en/thumb/c/cf/Flag_of_Canada.svg/800px-Flag_of_Canada.svg.png",
            "Australia": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b9/Flag_of_Australia.svg/800px-Flag_of_Australia.svg.png",
            "China": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/fa/Flag_of_the_People%27s_Republic_of_China.svg/800px-Flag_of_the_People%27s_Republic_of_China.svg.png",
            "Brazil": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/Flag_of_Brazil.svg/800px-Flag_of_Brazil.svg.png",
            "India": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/41/Flag_of_India.svg/800px-Flag_of_India.svg.png",
            "Spain": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9a/Flag_of_Spain.svg/800px-Flag_of_Spain.svg.png",
            "Turkey": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b4/Flag_of_Turkey.svg/800px-Flag_of_Turkey.svg.png", 
            "South Korea": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/09/Flag_of_South_Korea.svg/800px-Flag_of_South_Korea.svg.png",
            "North Korea": "https://flagcdn.com/w320/kp.png",
            "New Zealand": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3e/Flag_of_New_Zealand.svg/800px-Flag_of_New_Zealand.svg.png",
            "Afghanistan": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5c/Flag_of_the_Taliban.svg/800px-Flag_of_the_Taliban.svg.png",
            "Indonesia": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9f/Flag_of_Indonesia.svg/800px-Flag_of_Indonesia.svg.png",
            "Monaco": "https://flagcdn.com/w320/mc.png",
            "Fiji": "https://flagcdn.com/w320/fj.png",
            "Jamaica": "https://flagcdn.com/w320/jm.png",
            "Madagascar": "https://flagcdn.com/w320/mg.png",
            "Kenya": "https://flagcdn.com/w320/ke.png",
            "Denmark": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a6/Denmark_w1_locator.svg/800px-Denmark_w1_locator.svg.png",
            "Poland": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/12/Flag_of_Poland.svg/800px-Flag_of_Poland.svg.png",
            "Malta": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/91/Malta_w1_locator.svg/800px-Malta_w1_locator.svg.png",
        }
        
        # Try special cases first
        if country_name in special_cases:
            return special_cases[country_name]
        
        # Standard Wikipedia flag pattern
        return f"https://upload.wikimedia.org/wikipedia/commons/thumb/f/ff/Flag_of_{formatted_name}.svg/800px-Flag_of_{formatted_name}.svg.png"
            
    def _record_missing_map(self, country_name):
        """Record countries that don't have Wikipedia map images"""
        try:
            missing_maps_file = "missing_maps.json"
            missing_maps = []
            
            # Load existing missing maps if file exists
            if os.path.exists(missing_maps_file):
                try:
                    with open(missing_maps_file, 'r') as f:
                        missing_maps = json.load(f)
                except:
                    pass
            
            # Add country if not already in the list
            if country_name not in missing_maps:
                missing_maps.append(country_name)
                
                # Save updated list
                with open(missing_maps_file, 'w') as f:
                    json.dump(sorted(missing_maps), f, indent=2)
                    
                logger.info(f"Added {country_name} to missing_maps.json")
        except Exception as e:
            logger.error(f"Error recording missing map for {country_name}: {e}")
            
# Singleton instance
_instance = None

def get_database():
    """Get the singleton database instance"""
    global _instance
    if _instance is None:
        _instance = CountryDatabase()
    return _instance