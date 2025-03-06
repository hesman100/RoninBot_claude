#!/usr/bin/env python3
import os
import logging
import random
import sys

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)
logger = logging.getLogger(__name__)

# Import config variables
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from country_game.config import MAP_IMAGES_PATH, FLAG_IMAGES_PATH

def sanity_check():
    """Run a sanity check on the image paths"""
    logger.info("Running country game sanity check...")
    
    # Check if image directories exist
    logger.info(f"Checking map images directory: {MAP_IMAGES_PATH}")
    if not os.path.exists(MAP_IMAGES_PATH):
        logger.error(f"Map images directory not found: {MAP_IMAGES_PATH}")
        return False
    
    logger.info(f"Checking flag images directory: {FLAG_IMAGES_PATH}")
    if not os.path.exists(FLAG_IMAGES_PATH):
        logger.error(f"Flag images directory not found: {FLAG_IMAGES_PATH}")
        return False
    
    # List files in directories
    try:
        map_files = os.listdir(MAP_IMAGES_PATH)
        flag_files = os.listdir(FLAG_IMAGES_PATH)
        
        logger.info(f"Found {len(map_files)} files in map directory")
        logger.info(f"Found {len(flag_files)} files in flag directory")
        
        # Check if files follow expected pattern
        map_pattern_count = sum(1 for f in map_files if f.endswith("_locator_map.png"))
        flag_pattern_count = sum(1 for f in flag_files if f.endswith("_flag.png"))
        
        logger.info(f"Files matching map pattern (_locator_map.png): {map_pattern_count}")
        logger.info(f"Files matching flag pattern (_flag.png): {flag_pattern_count}")
        
        # Test a few specific countries
        test_countries = ["Vietnam", "United_States", "France", "Japan", "Brazil"]
        
        for country in test_countries:
            # Test map image
            map_path = os.path.join(MAP_IMAGES_PATH, f"{country}_locator_map.png")
            if os.path.exists(map_path):
                logger.info(f"✅ Map found for {country}")
            else:
                logger.warning(f"❌ Map NOT found for {country}")
            
            # Test flag image
            flag_path = os.path.join(FLAG_IMAGES_PATH, f"{country}_flag.png")
            if os.path.exists(flag_path):
                logger.info(f"✅ Flag found for {country}")
            else:
                logger.warning(f"❌ Flag NOT found for {country}")
        
        # If at least some files match the pattern, consider the check passed
        if map_pattern_count > 0 and flag_pattern_count > 0:
            logger.info("✅ Sanity check PASSED: Found files matching expected patterns")
            return True
        else:
            logger.error("❌ Sanity check FAILED: No files match expected patterns")
            return False
            
    except Exception as e:
        logger.error(f"Error during sanity check: {e}")
        return False

if __name__ == "__main__":
    result = sanity_check()
    if result:
        print("\n✅ Country game sanity check PASSED")
        sys.exit(0)
    else:
        print("\n❌ Country game sanity check FAILED")
        sys.exit(1)
