import os
import logging
from typing import Dict, List, Tuple

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
COUNTRY_LIST_PATH = "country_game/country_name.list"
MAP_IMAGES_DIR = "country_game/images/wiki_all_map_400pi"
FLAG_IMAGES_DIR = "country_game/images/wiki_flag"

def load_country_list() -> List[str]:
    """Load the list of countries from file"""
    try:
        with open(COUNTRY_LIST_PATH, 'r') as file:
            countries = [line.strip() for line in file if line.strip()]
        logger.info(f"Loaded {len(countries)} countries from {COUNTRY_LIST_PATH}")
        return countries
    except Exception as e:
        logger.error(f"Error loading country list: {e}")
        return []

def get_available_images() -> Tuple[List[str], List[str]]:
    """Get lists of available map and flag images"""
    try:
        map_images = os.listdir(MAP_IMAGES_DIR) if os.path.exists(MAP_IMAGES_DIR) else []
        flag_images = os.listdir(FLAG_IMAGES_DIR) if os.path.exists(FLAG_IMAGES_DIR) else []
        
        # Filter out non-image files
        map_images = [img for img in map_images if img.endswith('_locator_map.png')]
        flag_images = [img for img in flag_images if img.endswith('_flag.png')]
        
        logger.info(f"Found {len(map_images)} map images and {len(flag_images)} flag images")
        return map_images, flag_images
    except Exception as e:
        logger.error(f"Error getting available images: {e}")
        return [], []

def check_image_availability(countries: List[str], map_images: List[str], flag_images: List[str]) -> Dict:
    """Check image availability for each country"""
    results = {
        "countries_with_both_images": [],
        "countries_missing_map": [],
        "countries_missing_flag": [],
        "countries_missing_both": [],
        "total_countries": len(countries),
        "total_maps_found": 0,
        "total_flags_found": 0
    }
    
    for country in countries:
        formatted_name = country.replace(' ', '_')
        map_filename = f"{formatted_name}_locator_map.png"
        flag_filename = f"{formatted_name}_flag.png"
        
        has_map = map_filename in map_images
        has_flag = flag_filename in flag_images
        
        if has_map:
            results["total_maps_found"] += 1
        
        if has_flag:
            results["total_flags_found"] += 1
        
        if has_map and has_flag:
            results["countries_with_both_images"].append(country)
        elif has_map and not has_flag:
            results["countries_missing_flag"].append(country)
        elif not has_map and has_flag:
            results["countries_missing_map"].append(country)
        else:
            results["countries_missing_both"].append(country)
    
    return results

def print_summary(results: Dict):
    """Print a summary of the image availability"""
    print("\n=== COUNTRY IMAGE AVAILABILITY SUMMARY ===")
    print(f"Total countries: {results['total_countries']}")
    print(f"Total map images found: {results['total_maps_found']} ({round(results['total_maps_found']/results['total_countries']*100, 1)}%)")
    print(f"Total flag images found: {results['total_flags_found']} ({round(results['total_flags_found']/results['total_countries']*100, 1)}%)")
    print(f"Countries with both images: {len(results['countries_with_both_images'])} ({round(len(results['countries_with_both_images'])/results['total_countries']*100, 1)}%)")
    print(f"Countries missing map only: {len(results['countries_missing_map'])} ({round(len(results['countries_missing_map'])/results['total_countries']*100, 1)}%)")
    print(f"Countries missing flag only: {len(results['countries_missing_flag'])} ({round(len(results['countries_missing_flag'])/results['total_countries']*100, 1)}%)")
    print(f"Countries missing both images: {len(results['countries_missing_both'])} ({round(len(results['countries_missing_both'])/results['total_countries']*100, 1)}%)")
    
    # Print some examples of missing images
    if results['countries_missing_map']:
        print("\nSample countries missing map images:")
        for country in results['countries_missing_map'][:10]:
            print(f"  - {country}")
        if len(results['countries_missing_map']) > 10:
            print(f"  - ...and {len(results['countries_missing_map']) - 10} more")
    
    if results['countries_missing_flag']:
        print("\nSample countries missing flag images:")
        for country in results['countries_missing_flag'][:10]:
            print(f"  - {country}")
        if len(results['countries_missing_flag']) > 10:
            print(f"  - ...and {len(results['countries_missing_flag']) - 10} more")
    
    if results['countries_missing_both']:
        print("\nSample countries missing both images:")
        for country in results['countries_missing_both'][:10]:
            print(f"  - {country}")
        if len(results['countries_missing_both']) > 10:
            print(f"  - ...and {len(results['countries_missing_both']) - 10} more")

def main():
    """Run the image check"""
    countries = load_country_list()
    map_images, flag_images = get_available_images()
    results = check_image_availability(countries, map_images, flag_images)
    print_summary(results)

if __name__ == "__main__":
    main()
