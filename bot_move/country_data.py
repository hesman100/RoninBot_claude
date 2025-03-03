import requests
import random
import logging
import json
import os
import time
import urllib.request
import urllib.error
from config import (
    COUNTRIES_API_URL, MAPTILER_API_URL, YANDEX_API_URL, 
    GEOAPIFY_API_URL, GEOAPIFY_API_KEY, CACHE_DURATION, HIGHLIGHTED_MAPS
)

logger = logging.getLogger(__name__)

class CountryData:
    def __init__(self):
        self.countries = []
        self.map_cache = {}  # Cache for map URLs
        
        # Always clear all cache files on startup for fresh maps
        self._clear_all_caches()
        
        # Initialize the data
        self.fetch_countries()

    def _clear_all_caches(self):
        """Clear all cache files to ensure fresh map data"""
        # Reset the in-memory cache
        self.map_cache = {}
        
        # Remove existing cache files
        cache_files = ['map_cache.json', 'countries_cache.json']
        for cache_file in cache_files:
            if os.path.exists(cache_file):
                try:
                    os.remove(cache_file)
                    logger.info(f"Cleared {cache_file} to refresh maps cache and prioritize Wikipedia orthographic projections")
                except OSError as e:
                    logger.error(f"Error removing {cache_file}: {e}")
        
        logger.info("Starting with a fresh map cache prioritizing high-quality Wikipedia orthographic projections")
        
    def load_cache(self):
        """Load cached map URLs from file if available (legacy method, kept for compatibility)"""
        # This method is kept for backward compatibility
        # We now always clear caches on startup
        self._clear_all_caches()

    def save_cache(self):
        """Save map URLs to cache file"""
        try:
            with open('map_cache.json', 'w') as f:
                json.dump({
                    'timestamp': time.time(),
                    'maps': self.map_cache
                }, f)
            logger.info(f"Saved {len(self.map_cache)} map URLs to cache")
        except Exception as e:
            logger.error(f"Error saving cache: {e}")

    def fetch_countries(self):
        """Fetch countries data from REST Countries API"""
        cache_file = 'countries_cache.json'
        
        # Try to load from cache first
        try:
            if os.path.exists(cache_file):
                with open(cache_file, 'r') as f:
                    cache_data = json.load(f)
                    
                    # Check if cache is still valid (using CACHE_DURATION too)
                    if time.time() - cache_data.get('timestamp', 0) < CACHE_DURATION:
                        self.countries = cache_data.get('countries', [])
                        logger.info(f"Loaded {len(self.countries)} countries from cache")
                        return
                    else:
                        logger.info("Countries cache expired, fetching from API")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid countries cache format, regenerating: {e}")
            # Remove corrupted cache file
            try:
                os.remove(cache_file)
            except OSError:
                pass
        except Exception as e:
            logger.error(f"Error loading countries cache: {e}")
            
        # Cache miss or error, fetch from API
        try:
            response = requests.get(COUNTRIES_API_URL)
            response.raise_for_status()  # Raise exception for HTTP errors
            
            # Filter out countries without necessary data
            self.countries = [
                country for country in response.json()
                if 'name' in country 
                and 'common' in country['name']
                and 'latlng' in country
                and len(country['latlng']) >= 2
            ]
            
            # Save to cache
            try:
                with open(cache_file, 'w') as f:
                    json.dump({
                        'timestamp': time.time(),
                        'countries': self.countries
                    }, f)
            except Exception as e:
                logger.error(f"Error saving countries cache: {e}")
                
            logger.info(f"Successfully loaded {len(self.countries)} countries from API")
        except requests.RequestException as e:
            logger.error(f"Error fetching countries: {e}")
            # Initialize with a small set of fallback countries
            self.countries = [
                {
                    "name": {"common": "United States"},
                    "latlng": [38, -97]
                },
                {
                    "name": {"common": "France"},
                    "latlng": [46, 2]
                },
                {
                    "name": {"common": "Japan"},
                    "latlng": [36, 138]
                },
                {
                    "name": {"common": "Brazil"},
                    "latlng": [-10, -55]
                },
                {
                    "name": {"common": "Australia"},
                    "latlng": [-27, 133]
                },
                {
                    "name": {"common": "India"},
                    "latlng": [20, 77]
                },
                {
                    "name": {"common": "South Africa"},
                    "latlng": [-29, 24]
                }
            ]
            logger.info("Using fallback countries list")

    def get_random_country(self):
        """Return a random country from the list"""
        if not self.countries:
            self.fetch_countries()
        return random.choice(self.countries)

    def get_country_map_url(self, country):
        """Generate a map URL for the given country with marker-based identification"""
        country_name = country['name']['common']
        
        # Check if URL is in cache
        if country_name in self.map_cache:
            logger.debug(f"Map URL for {country_name} found in cache")
            return self.map_cache[country_name]
            
        # Generate new URL
        lat, lng = country['latlng'][0], country['latlng'][1]
        
        # Create map URL with appropriate zoom level based on country size
        # Default zoom level
        zoom = 4  # Slightly zoomed out by default to show more context
        
        # Adjust zoom for very large countries
        large_countries = ['Russia', 'Canada', 'United States', 'China', 'Brazil', 'Australia', 'India']
        if country_name in large_countries:
            zoom = 3
            
        # Adjust zoom for medium countries
        medium_countries = ['Mexico', 'Argentina', 'Algeria', 'Saudi Arabia', 'Kazakhstan']
        if country_name in medium_countries:
            zoom = 4
            
        # Adjust zoom for small countries
        small_countries = ['United Kingdom', 'Italy', 'Germany', 'Japan', 'Philippines']
        if country_name in small_countries:
            zoom = 5
            
        # Adjust zoom for very small countries
        very_small_countries = ['Monaco', 'Vatican City', 'San Marino', 'Liechtenstein', 'Malta', 'Luxembourg', 'Bahrain']
        if country_name in very_small_countries:
            zoom = 8
        
        # PRIORITIZE PRE-RENDERED MAPS - First try using pre-defined maps from config
        prerendered_map = self._get_prerendered_map(country_name)
        if prerendered_map:
            # Periodically save cache
            if len(self.map_cache) % 10 == 0:
                self.save_cache()
            return prerendered_map
        
        # NEXT TRY: Find wiki orthographic projection maps with pattern matching
        # This greatly expands our coverage of pre-rendered maps
        wiki_map = self._generate_wiki_orthographic_url(country_name)
        if wiki_map:
            # Periodically save cache
            if len(self.map_cache) % 10 == 0:
                self.save_cache()
            return wiki_map
        
        # If no pre-rendered map is available, try GeoApify map with marker
        logger.info(f"No pre-rendered map available for {country_name}, trying GeoApify with marker identification")
        
        # Use GeoApify to generate a map with a clear marker at the country's center
        # This requires an API key but provides good quality
        if GEOAPIFY_API_KEY and not GEOAPIFY_API_KEY.startswith("YOUR_"):
            try:
                # Get the country ISO code if available (for more precise boundary marking)
                iso2_code = None
                if 'cca2' in country:
                    iso2_code = country['cca2']
                
                # GeoApify URL with marker if we have the ISO code
                if iso2_code:
                    # Use OpenStreetMap with GeoApify API as the provider
                    # Configure for completely clean maps with no labels
                    geoapify_url = (
                        f"{GEOAPIFY_API_URL}"
                        f"?style=osm-bright"  # OpenStreetMap style
                        f"&width=600"  # Image width
                        f"&height=400"  # Image height
                        f"&center=lonlat:{lng},{lat}"  # Center point
                        f"&zoom={zoom}"  # Zoom level
                        f"&apiKey={GEOAPIFY_API_KEY}"  # API key
                        # Simple red marker at the center for highlighting the country
                        f"&marker=lonlat:{lng},{lat};type:circle;color:red;size:large"
                        # Disable all labels and text elements completely
                        f"&text=false"  # No text labels
                        f"&landcover=false"  # No land cover details
                        f"&poi=false"  # No points of interest
                        f"&labels=false"  # No labels of any kind
                        f"&housenumbers=false"  # No house numbers
                        f"&streets=false"  # Hide street names
                    )
                    
                    logger.info(f"Trying GeoApify with marker highlighting for {country_name}...")
                    req = urllib.request.Request(geoapify_url)
                    response = urllib.request.urlopen(req, timeout=5)
                    
                    if response.status == 200:
                        content_type = response.info().get_content_type()
                        if content_type.startswith('image/'):
                            logger.info(f"GeoApify map with marker successful for {country_name}")
                            self.map_cache[country_name] = geoapify_url
                            return geoapify_url
            except Exception as e:
                logger.error(f"Error with GeoApify map service: {e}")
        
        # Only use OpenStreetMap via GeoApify - no fallback to other map providers
        # If OpenStreetMap fails, use a clean OpenStreetMap static fallback image
        fallback_url = (
            f"https://tile.openstreetmap.org/4/{lng}/{lat}.png"  # Clean OpenStreetMap static image
            f"?country={country_name}"  # Add country name as a query parameter to make URL unique
        )
        
        # Log the fallback
        logger.warning(f"All map providers failed for {country_name}, using static OpenStreetMap fallback (no pre-rendered map available)")
        
        # Still cache the fallback to avoid repeated failures
        self.map_cache[country_name] = fallback_url
        return fallback_url

    def _get_prerendered_map(self, country_name):
        """Try to get a pre-rendered map for the country"""
        # First check our predefined dictionary
        if country_name in HIGHLIGHTED_MAPS:
            highlighted_url = HIGHLIGHTED_MAPS[country_name]
            logger.info(f"Using pre-rendered map for {country_name}: {highlighted_url}")
            
            # Verify the URL returns a valid image
            try:
                req = urllib.request.Request(highlighted_url)
                response = urllib.request.urlopen(req, timeout=2)
                
                if response.status == 200:
                    content_type = response.info().get_content_type()
                    if content_type.startswith('image/'):
                        logger.info(f"Pre-rendered map URL validation successful for {country_name}")
                        # Cache this URL
                        self.map_cache[country_name] = highlighted_url
                        return highlighted_url
            except Exception as e:
                logger.error(f"Error validating pre-rendered map URL: {e}")
                
        return None
        
    def _generate_wiki_orthographic_url(self, country_name):
        """Generate and try a Wikipedia orthographic projection URL format"""
        # Format country name for URL
        formatted_name = country_name.replace(" ", "_")
        
        # Try common formats for Wikimedia Commons orthographic projections
        # These cover various hash patterns in the URL and file naming conventions on Wikipedia
        potential_urls = [
            # Common hash patterns in URLs (d/d1, 7/7d, b/bc, etc.)
            f"https://upload.wikimedia.org/wikipedia/commons/thumb/d/d1/{formatted_name}_(orthographic_projection).svg/1024px-{formatted_name}_(orthographic_projection).svg.png",
            f"https://upload.wikimedia.org/wikipedia/commons/thumb/7/7d/{formatted_name}_(orthographic_projection).svg/1024px-{formatted_name}_(orthographic_projection).svg.png",
            f"https://upload.wikimedia.org/wikipedia/commons/thumb/b/bc/{formatted_name}_(orthographic_projection).svg/1024px-{formatted_name}_(orthographic_projection).svg.png",
            f"https://upload.wikimedia.org/wikipedia/commons/thumb/c/c2/{formatted_name}_(orthographic_projection).svg/1024px-{formatted_name}_(orthographic_projection).svg.png",
            f"https://upload.wikimedia.org/wikipedia/commons/thumb/a/a1/{formatted_name}_(orthographic_projection).svg/1024px-{formatted_name}_(orthographic_projection).svg.png",
            f"https://upload.wikimedia.org/wikipedia/commons/thumb/6/67/{formatted_name}_(orthographic_projection).svg/1024px-{formatted_name}_(orthographic_projection).svg.png",
            f"https://upload.wikimedia.org/wikipedia/commons/thumb/c/ca/{formatted_name}_(orthographic_projection).svg/1024px-{formatted_name}_(orthographic_projection).svg.png",
            f"https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/{formatted_name}_(orthographic_projection).svg/1024px-{formatted_name}_(orthographic_projection).svg.png",
            f"https://upload.wikimedia.org/wikipedia/commons/thumb/5/59/{formatted_name}_(orthographic_projection).svg/1024px-{formatted_name}_(orthographic_projection).svg.png",
            f"https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/{formatted_name}_(orthographic_projection).svg/1024px-{formatted_name}_(orthographic_projection).svg.png",
            f"https://upload.wikimedia.org/wikipedia/commons/thumb/9/95/{formatted_name}_(orthographic_projection).svg/1024px-{formatted_name}_(orthographic_projection).svg.png",
            f"https://upload.wikimedia.org/wikipedia/commons/thumb/8/86/{formatted_name}_(orthographic_projection).svg/1024px-{formatted_name}_(orthographic_projection).svg.png",
            f"https://upload.wikimedia.org/wikipedia/commons/thumb/e/e2/{formatted_name}_(orthographic_projection).svg/1024px-{formatted_name}_(orthographic_projection).svg.png",
            f"https://upload.wikimedia.org/wikipedia/commons/thumb/9/9f/{formatted_name}_(orthographic_projection).svg/1024px-{formatted_name}_(orthographic_projection).svg.png",
            
            # Other map formats and variations
            f"https://upload.wikimedia.org/wikipedia/commons/thumb/b/b4/{formatted_name}_on_the_globe.svg/1024px-{formatted_name}_on_the_globe.svg.png",
            f"https://upload.wikimedia.org/wikipedia/commons/thumb/3/3f/{formatted_name}_on_the_globe.svg/1024px-{formatted_name}_on_the_globe.svg.png",
            f"https://upload.wikimedia.org/wikipedia/commons/thumb/1/13/{formatted_name}_on_the_globe.svg/1024px-{formatted_name}_on_the_globe.svg.png"
        ]
        
        # Try with EU prefix for European countries
        eu_url = f"https://upload.wikimedia.org/wikipedia/commons/thumb/a/a1/EU-{formatted_name}_(orthographic_projection).svg/1024px-EU-{formatted_name}_(orthographic_projection).svg.png"
        potential_urls.append(eu_url)
        
        # Try with Republic of prefix for countries that might use it
        republic_url = f"https://upload.wikimedia.org/wikipedia/commons/thumb/a/a1/Republic_of_{formatted_name}_(orthographic_projection).svg/1024px-Republic_of_{formatted_name}_(orthographic_projection).svg.png"
        potential_urls.append(republic_url)
        
        # Try each URL
        for url in potential_urls:
            try:
                req = urllib.request.Request(url)
                response = urllib.request.urlopen(req, timeout=2)
                
                if response.status == 200:
                    content_type = response.info().get_content_type()
                    if content_type.startswith('image/'):
                        logger.info(f"Found orthographic projection for {country_name}: {url}")
                        # Cache this URL
                        self.map_cache[country_name] = url
                        return url
            except Exception:
                # Don't log errors here, just try the next URL
                pass
                
        return None
        
    def is_correct_answer(self, user_answer, correct_country):
        """Check if the user's answer is correct"""
        user_answer = user_answer.lower().strip()
        correct_name = correct_country['name']['common'].lower()
        
        # Simple exact match
        if user_answer == correct_name:
            return True
            
        # Check for alternative names if available
        if 'altSpellings' in correct_country:
            for alt in correct_country['altSpellings']:
                if alt and user_answer == alt.lower():
                    return True
                    
        # Check native names if available
        if 'name' in correct_country and 'nativeName' in correct_country['name']:
            for _, native_name in correct_country['name']['nativeName'].items():
                if 'common' in native_name and user_answer == native_name['common'].lower():
                    return True
                    
        # Handle special cases with "the" in the name
        if user_answer == f"the {correct_name}" or user_answer == correct_name.replace("the ", ""):
            return True
            
        # Fuzzy matching for minor typos (accept answer if it's close enough)
        if self._similarity_score(user_answer, correct_name) > 0.85:
            return True
            
        return False
        
    def _similarity_score(self, str1, str2):
        """Calculate simple similarity between two strings (0-1)"""
        # Simple Levenshtein distance implementation
        if not str1 or not str2:
            return 0
            
        if str1 == str2:
            return 1.0
            
        len1, len2 = len(str1), len(str2)
        max_len = max(len1, len2)
        
        if max_len == 0:
            return 1.0
            
        # Calculate Levenshtein distance
        distance = self._levenshtein_distance(str1, str2)
        
        # Convert to similarity score (0-1)
        return 1 - (distance / max_len)
        
    def _levenshtein_distance(self, s1, s2):
        """Calculate Levenshtein distance between two strings"""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)
            
        if len(s2) == 0:
            return len(s1)
            
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
            
        return previous_row[-1]
