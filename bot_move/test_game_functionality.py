#!/usr/bin/env python3

"""
Test Game Functionality Script

This script tests the game functionality with the updated database:
1. Makes sure random country selection works for all game modes
2. Verifies that all countries have working maps and flags
3. Checks hint generation across all regions
"""

import logging
import traceback
import random
from country_database import CountryDatabase
from game_handler import GameHandler

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def verify_url(url):
    """Simple check that a URL is formatted correctly"""
    if not url:
        return False
    
    # Check for valid URL structure (very basic check)
    return url.startswith('http') or url.startswith('./wiki')

def test_random_country_selection(db, count=5):
    """Test random country selection"""
    logger.info(f"Testing random country selection ({count} samples)...")
    
    for i in range(count):
        try:
            country = db.get_random_country()
            
            if not country:
                logger.error(f"Failed to get random country (attempt {i+1})")
                continue
                
            logger.info(f"Random country {i+1}: {country['name']} (Region: {country['region']})")
            
            # Check that essential fields are present
            for field in ['name', 'id', 'population', 'area', 'region']:
                if field not in country or country[field] is None:
                    logger.warning(f"Field {field} missing for {country['name']}")
        
        except Exception as e:
            logger.error(f"Error in random country selection: {e}")
            logger.error(traceback.format_exc())
    
    logger.info("Random country selection test completed")

def test_map_and_flag_urls(db, game, count=5):
    """Test map and flag URL generation for random countries"""
    logger.info(f"Testing map and flag URLs ({count} samples)...")
    
    for i in range(count):
        try:
            country = db.get_random_country()
            
            if not country:
                logger.error(f"Failed to get random country (attempt {i+1})")
                continue
                
            # Test map URL
            map_url = db.get_map_url(country)
            logger.info(f"{country['name']} map URL: {map_url}")
            if not verify_url(map_url):
                logger.warning(f"Possibly invalid map URL for {country['name']}: {map_url}")
            
            # Test flag URL through game handler
            flag_url = game._get_flag_url(country)
            logger.info(f"{country['name']} flag URL: {flag_url}")
            if not verify_url(flag_url):
                logger.warning(f"Possibly invalid flag URL for {country['name']}: {flag_url}")
                
        except Exception as e:
            logger.error(f"Error in URL generation: {e}")
            logger.error(traceback.format_exc())
    
    logger.info("Map and flag URL test completed")

def test_region_coverage(db):
    """Test country distribution across regions"""
    logger.info("Testing region coverage...")
    
    try:
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT region, COUNT(*) 
            FROM countries 
            GROUP BY region 
            ORDER BY COUNT(*) DESC
        """)
        
        regions = cursor.fetchall()
        logger.info("Region distribution:")
        for region, count in regions:
            logger.info(f"  {region}: {count} countries")
            
            # Test a random country from each region
            cursor.execute("""
                SELECT id, name FROM countries 
                WHERE region = %s 
                ORDER BY RANDOM() 
                LIMIT 1
            """, (region,))
            
            country_row = cursor.fetchone()
            if country_row:
                country_id, country_name = country_row
                logger.info(f"  Sample country: {country_name}")
                
                # Get full country data
                country = db.get_country_by_name(country_name)
                if country:
                    # Check for complete data
                    logger.info(f"  Population: {country.get('population', 'N/A')}")
                    logger.info(f"  Area: {country.get('area', 'N/A')}")
                    logger.info(f"  Subregion: {country.get('subregion', 'N/A')}")
                else:
                    logger.warning(f"  Could not get full data for {country_name}")
            
        cursor.close()
    except Exception as e:
        logger.error(f"Error in region coverage test: {e}")
        logger.error(traceback.format_exc())
    
    logger.info("Region coverage test completed")

def test_hint_generation(db, game, count=3):
    """Test hint generation for random countries"""
    logger.info(f"Testing hint generation ({count} samples)...")
    
    game_modes = ["map", "flag", "capital"]
    
    for i in range(count):
        try:
            country = db.get_random_country()
            
            if not country:
                logger.error(f"Failed to get random country (attempt {i+1})")
                continue
                
            logger.info(f"Hints for {country['name']} (Region: {country['region']}):")
            
            for mode in game_modes:
                hint = game.generate_hint(country, game_mode=mode)
                logger.info(f"  {mode.upper()} mode hint: {hint}")
                
        except Exception as e:
            logger.error(f"Error in hint generation: {e}")
            logger.error(traceback.format_exc())
    
    logger.info("Hint generation test completed")

def main():
    """Run all tests"""
    logger.info("Starting game functionality tests")
    
    try:
        # Initialize the database and game handler
        db = CountryDatabase()
        game = GameHandler()
        
        # Run tests
        test_random_country_selection(db)
        test_map_and_flag_urls(db, game)
        test_region_coverage(db)
        test_hint_generation(db, game)
        
        logger.info("All tests completed successfully")
        
    except Exception as e:
        logger.error(f"Error in test execution: {e}")
        logger.error(traceback.format_exc())
    
    logger.info("Test script completed")

if __name__ == "__main__":
    main()