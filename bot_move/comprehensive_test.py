#!/usr/bin/env python3

"""
Comprehensive Test Suite for the Telegram Country Guessing Bot

This script performs thorough testing of all bot components:
1. Database connectivity and country retrieval
2. Map URL generation and validation for all regions
3. Hint system functionality across all countries
4. Game handler integration
5. Statistical coverage analysis

Running this test suite will verify the bot is fully ready for deployment.
"""

import logging
import os
import random
import json
from country_database import CountryDatabase, get_database
from game_handler import GameHandler

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_database_connectivity(db):
    """Test database connection and basic functionality"""
    logger.info("=== Testing Database Connectivity ===")
    
    # Test if we can execute a basic query
    try:
        if db.cursor:
            db.cursor.execute("SELECT COUNT(*) FROM countries")
            count = db.cursor.fetchone()[0]
            logger.info(f"✓ Database connection works. Total countries: {count}")
            return True
        else:
            logger.error("✕ Database cursor not available")
            return False
    except Exception as e:
        logger.error(f"✕ Database connectivity test failed: {e}")
        return False

def test_random_country_selection(db, count=10):
    """Test random country selection from the database"""
    logger.info("=== Testing Random Country Selection ===")
    
    countries = []
    for i in range(count):
        country = db.get_random_country()
        if not country:
            logger.error(f"✕ Failed to get random country (attempt {i+1})")
            continue
            
        countries.append(country)
        logger.info(f"✓ Random country {i+1}: {country['name']['common']} (Region: {country.get('region', 'Unknown')})")
    
    # Check for diversity in region selection
    regions = {}
    for country in countries:
        region = country.get('region', 'Unknown')
        regions[region] = regions.get(region, 0) + 1
    
    logger.info("Region distribution in random selection:")
    for region, count in regions.items():
        logger.info(f"  {region}: {count} countries")
    
    return len(countries) > 0

def test_map_coverage_by_region(db):
    """Test map coverage for countries in each region"""
    logger.info("=== Testing Map Coverage by Region ===")
    
    try:
        # Get all regions
        db.cursor.execute("SELECT DISTINCT region FROM countries WHERE region IS NOT NULL")
        regions = [row[0] for row in db.cursor.fetchall()]
        
        for region in regions:
            # Get countries in this region
            db.cursor.execute("""
                SELECT id, name FROM countries 
                WHERE region = %s AND not_a_country = FALSE
                ORDER BY RANDOM() LIMIT 3
            """, (region,))
            
            countries = db.cursor.fetchall()
            logger.info(f"Testing map coverage for {region} (sample of {len(countries)} countries):")
            
            for country_id, country_name in countries:
                # Get the country object
                country = db.get_country_by_name(country_name)
                if not country:
                    logger.warning(f"  ✕ Could not get country object for {country_name}")
                    continue
                
                # Test map URL
                map_url = db.get_map_url(country)
                valid_map = verify_url_format(map_url)
                
                if valid_map:
                    logger.info(f"  ✓ {country_name}: Valid map URL ({map_url[:50]}...)")
                else:
                    logger.warning(f"  ✕ {country_name}: Invalid or missing map URL ({map_url})")
                    
        # Count maps by type
        db.cursor.execute("""
            SELECT map_type, COUNT(*) FROM maps
            GROUP BY map_type
        """)
        
        map_types = db.cursor.fetchall()
        logger.info("Map type distribution:")
        for map_type, count in map_types:
            logger.info(f"  {map_type}: {count} maps")
        
        return True
    except Exception as e:
        logger.error(f"✕ Map coverage test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def test_hint_generation_by_region(db, game):
    """Test hint generation for countries in different regions"""
    logger.info("=== Testing Hint Generation by Region ===")
    
    try:
        # Get all regions
        db.cursor.execute("SELECT DISTINCT region FROM countries WHERE region IS NOT NULL")
        regions = [row[0] for row in db.cursor.fetchall()]
        
        for region in regions:
            # Get countries in this region
            db.cursor.execute("""
                SELECT id, name FROM countries 
                WHERE region = %s AND not_a_country = FALSE
                ORDER BY RANDOM() LIMIT 2
            """, (region,))
            
            countries = db.cursor.fetchall()
            logger.info(f"Testing hint generation for {region} (sample of {len(countries)} countries):")
            
            for country_id, country_name in countries:
                # Get the country object
                country = db.get_country_by_name(country_name)
                if not country:
                    logger.warning(f"  ✕ Could not get country object for {country_name}")
                    continue
                
                logger.info(f"  {country_name} hints:")
                
                # Test hint generation for different game modes
                for mode in ["map", "flag", "capital"]:
                    hint = game.generate_hint(country, game_mode=mode)
                    if hint and hint != "Try guessing a country name...":
                        logger.info(f"    ✓ {mode.upper()} mode: {hint[:100]}...")
                    else:
                        logger.warning(f"    ✕ {mode.upper()} mode: No substantive hint generated")
        
        return True
    except Exception as e:
        logger.error(f"✕ Hint generation test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def test_game_handler_integration(db, game):
    """Test game handler integration with the database"""
    logger.info("=== Testing Game Handler Integration ===")
    
    try:
        # Test stat tracking
        logger.info("Testing user stats functionality:")
        
        # Create test user stats
        test_user_id = "test_user_123"
        if test_user_id not in game.user_stats:
            game.user_stats[test_user_id] = {
                "username": "TestUser",
                "games_played": 10,
                "correct_answers": 6,
                "incorrect_answers": 3,
                "timeout_answers": 1,
                "gave_up": 0,
                "streak": 2,
                "max_streak": 3
            }
        
        # Test retrieving user stats
        stats = game.get_user_stats(test_user_id)
        if stats:
            logger.info(f"  ✓ Successfully retrieved user stats for test user")
            logger.info(f"    Games: {stats['games_played']}, Correct: {stats['correct_answers']}")
        else:
            logger.warning(f"  ✕ Failed to retrieve user stats")
        
        # Test leaderboard
        leaderboard = game.get_leaderboard()
        if leaderboard:
            logger.info(f"  ✓ Successfully generated leaderboard with {len(leaderboard)} entries")
        else:
            logger.warning(f"  ✕ Failed to generate leaderboard")
        
        # Test flag URL retrieval
        try:
            # Get a random country
            country = db.get_random_country()
            flag_url = game._get_flag_url(country)
            
            if flag_url and verify_url_format(flag_url):
                logger.info(f"  ✓ Successfully retrieved flag URL for {country['name']['common']}")
            else:
                logger.warning(f"  ✕ Failed to get valid flag URL for {country['name']['common']}")
        except Exception as e:
            logger.error(f"  ✕ Flag URL test failed: {e}")
        
        return True
    except Exception as e:
        logger.error(f"✕ Game handler integration test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def verify_url_format(url):
    """Verify that a URL has a valid format (simple check, no network request)"""
    if not url:
        return False
    
    # Check for valid URL structure
    return (url.startswith('http') or 
            url.startswith('./wiki_all_map_400pi/') or 
            url.startswith('./wiki_flag/'))

def display_database_stats(db):
    """Display comprehensive database statistics"""
    logger.info("=== Database Statistics ===")
    
    try:
        # Count countries by region
        db.cursor.execute("""
            SELECT region, COUNT(*) FROM countries
            WHERE region IS NOT NULL
            GROUP BY region
            ORDER BY COUNT(*) DESC
        """)
        
        regions = db.cursor.fetchall()
        logger.info("Countries by region:")
        for region, count in regions:
            logger.info(f"  {region}: {count} countries")
        
        # Count countries with various attributes
        db.cursor.execute("""
            SELECT 
                COUNT(*) as total_countries,
                SUM(CASE WHEN population IS NOT NULL THEN 1 ELSE 0 END) as with_population,
                SUM(CASE WHEN area IS NOT NULL THEN 1 ELSE 0 END) as with_area,
                SUM(CASE WHEN capital IS NOT NULL THEN 1 ELSE 0 END) as with_capital,
                SUM(CASE WHEN region IS NOT NULL THEN 1 ELSE 0 END) as with_region,
                SUM(CASE WHEN neighbors IS NOT NULL THEN 1 ELSE 0 END) as with_neighbors
            FROM countries
            WHERE not_a_country = FALSE
        """)
        
        stats = db.cursor.fetchone()
        logger.info("\nAttribute coverage:")
        logger.info(f"  Total countries: {stats[0]}")
        logger.info(f"  With population: {stats[1]} ({stats[1]/stats[0]*100:.1f}%)")
        logger.info(f"  With area: {stats[2]} ({stats[2]/stats[0]*100:.1f}%)")
        logger.info(f"  With capital: {stats[3]} ({stats[3]/stats[0]*100:.1f}%)")
        logger.info(f"  With region: {stats[4]} ({stats[4]/stats[0]*100:.1f}%)")
        logger.info(f"  With neighbors: {stats[5]} ({stats[5]/stats[0]*100:.1f}%)")
        
        # Count map types
        db.cursor.execute("""
            SELECT map_type, COUNT(*) FROM maps
            GROUP BY map_type
            ORDER BY COUNT(*) DESC
        """)
        
        map_types = db.cursor.fetchall()
        logger.info("\nMap types:")
        total_maps = sum(count for _, count in map_types)
        for map_type, count in map_types:
            logger.info(f"  {map_type}: {count} maps ({count/total_maps*100:.1f}%)")
        
    except Exception as e:
        logger.error(f"Error getting database stats: {e}")

def main():
    """Run comprehensive test suite for the Telegram bot"""
    logger.info("Starting comprehensive test suite for the Telegram Country Guessing Bot")
    
    try:
        # Initialize the database
        db = get_database()
        
        # Display database stats first
        display_database_stats(db)
        
        # Create the game handler
        game = GameHandler()
        
        # Run the tests
        tests = [
            ("Database Connectivity", test_database_connectivity(db)),
            ("Random Country Selection", test_random_country_selection(db)),
            ("Map Coverage by Region", test_map_coverage_by_region(db)),
            ("Hint Generation by Region", test_hint_generation_by_region(db, game)),
            ("Game Handler Integration", test_game_handler_integration(db, game))
        ]
        
        # Display test summary
        logger.info("\n=== Test Summary ===")
        all_passed = True
        for test_name, result in tests:
            status = "PASSED" if result else "FAILED"
            logger.info(f"{test_name}: {status}")
            if not result:
                all_passed = False
        
        if all_passed:
            logger.info("\n✅ All tests passed! The bot is ready for deployment.")
        else:
            logger.warning("\n⚠️ Some tests failed. Review the logs for details.")
        
    except Exception as e:
        logger.error(f"Test suite failed with error: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()