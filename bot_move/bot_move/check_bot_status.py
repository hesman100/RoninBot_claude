#!/usr/bin/env python3
"""
Bot Status Checker

This script verifies that all components of the Country Guessing Bot are working properly.
It's a lightweight version of the comprehensive test that focuses on just the core
functionality needed for migration.
"""

import logging
import sys
import os
import json
from datetime import datetime

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Add the current directory to the path so we can import the modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from country_database import get_database, CountryDatabase
    logger.info("✅ Successfully imported CountryDatabase")
except ImportError as e:
    logger.error(f"❌ Failed to import CountryDatabase: {e}")
    sys.exit(1)

try:
    from game_handler import GameHandler
    logger.info("✅ Successfully imported GameHandler")
except ImportError as e:
    logger.error(f"❌ Failed to import GameHandler: {e}")
    sys.exit(1)

def check_database_connection():
    """Verify database connection and schema"""
    logger.info("Checking database connection...")
    try:
        db = get_database()
        logger.info("✅ Successfully connected to database")
        
        # Check tables exist by trying to load countries
        country = db.get_random_country()
        if country and 'name' in country:
            logger.info(f"✅ Successfully retrieved random country: {country['name'].get('common', 'Unknown')}")
        else:
            logger.error("❌ Failed to retrieve random country with proper structure")
            return False
        
        return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False

def check_game_handler():
    """Verify game handler initialization"""
    logger.info("Checking game handler...")
    try:
        handler = GameHandler()
        logger.info("✅ Successfully initialized GameHandler")
        
        # Check if conversation handler was created
        conv_handler = handler.get_conversation_handler()
        if conv_handler:
            logger.info("✅ Successfully created conversation handler")
        else:
            logger.error("❌ Failed to create conversation handler")
            return False
        
        return True
    except Exception as e:
        logger.error(f"❌ Game handler initialization failed: {e}")
        return False

def check_map_and_flag_urls():
    """Verify map and flag URL generation"""
    logger.info("Checking map and flag URL generation...")
    try:
        db = get_database()
        game = GameHandler()
        
        # Test with a few different countries
        test_countries = [
            "United States", 
            "Japan", 
            "Brazil", 
            "Kenya", 
            "France"
        ]
        
        for country_name in test_countries:
            country = db.get_country_by_name(country_name)
            if not country:
                logger.warning(f"⚠️ Could not find country: {country_name}")
                continue
                
            map_url = db.get_map_url(country)
            if map_url:
                logger.info(f"✅ Map URL for {country_name}: {map_url}")
            else:
                logger.error(f"❌ Failed to get map URL for {country_name}")
                
            flag_url = game._get_flag_url(country)
            if flag_url:
                logger.info(f"✅ Flag URL for {country_name}: {flag_url}")
            else:
                logger.error(f"❌ Failed to get flag URL for {country_name}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Map and flag URL check failed: {e}")
        return False

def check_hint_generation():
    """Verify hint generation for countries"""
    logger.info("Checking hint generation...")
    try:
        db = get_database()
        game = GameHandler()
        
        country = db.get_country_by_name("Germany")
        if not country:
            logger.error("❌ Could not find Germany for hint test")
            return False
            
        # Test different game modes
        for mode in ["map", "flag", "capital"]:
            hint = game.generate_hint(country, game_mode=mode)
            if hint:
                logger.info(f"✅ Generated hint for {mode} mode: {hint[:50]}...")
            else:
                logger.error(f"❌ Failed to generate hint for {mode} mode")
        
        return True
    except Exception as e:
        logger.error(f"❌ Hint generation check failed: {e}")
        return False

def main():
    """Run all checks and report status"""
    logger.info("=== Country Guessing Bot Status Check ===")
    logger.info(f"Starting checks at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run all checks
    db_status = check_database_connection()
    game_status = check_game_handler()
    url_status = check_map_and_flag_urls()
    hint_status = check_hint_generation()
    
    # Report overall status
    if all([db_status, game_status, url_status, hint_status]):
        logger.info("🎉 All checks passed! The bot is ready for migration.")
    else:
        logger.error("⚠️ Some checks failed. Please review the logs above.")
        
    logger.info("=== Status Check Complete ===")

if __name__ == "__main__":
    main()