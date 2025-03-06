import os
import logging
import sqlite3
from typing import List, Dict, Tuple

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DATABASE_PATH = "country_game/database/countries.db"
MAP_IMAGES_PATH = "country_game/images/wiki_all_map_400pi"
FLAG_IMAGES_PATH = "country_game/images/wiki_flag"

def get_countries_from_db() -> List[Dict]:
    """Load countries from the database"""
    countries = []
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM countries")
        rows = cursor.fetchall()

        # Get column names
        column_names = [description[0] for description in cursor.description]

        # Convert rows to dictionaries
        for row in rows:
            country = {}
            for i, value in enumerate(row):
                country[column_names[i]] = value
            countries.append(country)

        conn.close()
        logger.info(f"Loaded {len(countries)} countries from database")
        return countries
    except Exception as e:
        logger.error(f"Error loading countries from database: {e}")
        return []

def check_image_paths(countries: List[Dict]) -> Tuple[List[str], List[str], List[str]]:
    """Check if map and flag images exist for each country"""
    missing_maps = []
    missing_flags = []
    have_both = []
    
    # Get available files
    try:
        map_files = os.listdir(MAP_IMAGES_PATH) if os.path.exists(MAP_IMAGES_PATH) else []
        flag_files = os.listdir(FLAG_IMAGES_PATH) if os.path.exists(FLAG_IMAGES_PATH) else []
        
        logger.info(f"Found {len(map_files)} map images and {len(flag_files)} flag images")
    except Exception as e:
        logger.error(f"Error listing image directories: {e}")
        return [], [], []
    
    for country in countries:
        country_name = country.get('name', '')
        
        # Check three possible file name patterns for maps
        map_exists = False
        flag_exists = False
        
        # Try different map filename formats
        map_formats = [
            f"{country_name}.png",
            f"{country_name}_locator_map.png", 
            f"{country_name.replace(' ', '_')}_locator_map.png"
        ]
        
        for map_format in map_formats:
            if map_format in map_files or os.path.exists(os.path.join(MAP_IMAGES_PATH, map_format)):
                map_exists = True
                logger.info(f"Found map for {country_name}: {map_format}")
                break
        
        # Try different flag filename formats
        flag_formats = [
            f"{country_name}.png",
            f"{country_name}_flag.png",
            f"{country_name.replace(' ', '_')}_flag.png"
        ]
        
        for flag_format in flag_formats:
            if flag_format in flag_files or os.path.exists(os.path.join(FLAG_IMAGES_PATH, flag_format)):
                flag_exists = True
                logger.info(f"Found flag for {country_name}: {flag_format}")
                break
        
        # Record results
        if map_exists and flag_exists:
            have_both.append(country_name)
        elif not map_exists:
            missing_maps.append(country_name)
        elif not flag_exists:
            missing_flags.append(country_name)
    
    return missing_maps, missing_flags, have_both

def print_results(missing_maps: List[str], missing_flags: List[str], have_both: List[str], total_countries: int):
    """Print the results of the image path check"""
    print("\n=== COUNTRY IMAGE PATH TEST RESULTS ===")
    print(f"Total countries: {total_countries}")
    print(f"Countries with both images: {len(have_both)} ({round(len(have_both)/total_countries*100, 1)}%)")
    print(f"Countries missing map: {len(missing_maps)} ({round(len(missing_maps)/total_countries*100, 1)}%)")
    print(f"Countries missing flag: {len(missing_flags)} ({round(len(missing_flags)/total_countries*100, 1)}%)")
    
    if missing_maps:
        print("\nSample countries missing map images:")
        for country in missing_maps[:10]:
            print(f"  - {country}")
        if len(missing_maps) > 10:
            print(f"  - ...and {len(missing_maps) - 10} more")
    
    if missing_flags:
        print("\nSample countries missing flag images:")
        for country in missing_flags[:10]:
            print(f"  - {country}")
        if len(missing_flags) > 10:
            print(f"  - ...and {len(missing_flags) - 10} more")

def main():
    """Run the image path test"""
    countries = get_countries_from_db()
    if not countries:
        print("No countries found in the database!")
        return
    
    missing_maps, missing_flags, have_both = check_image_paths(countries)
    print_results(missing_maps, missing_flags, have_both, len(countries))

if __name__ == "__main__":
    main()
