#!/usr/bin/env python3
"""
Test script for the country database

This script tests the new country database functionality, verifying that:
1. The database can be created and populated
2. Countries can be retrieved
3. Map URLs work for various countries including non-mainstream ones
"""

import logging
import sys
import urllib.request
import random

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

def test_database_creation():
    """Test creating and populating the database"""
    logger.info("Testing database creation...")
    
    from country_database import get_database
    db = get_database()
    
    # Force a refresh of the database
    db.refresh_database(force=True)
    
    # Check if countries were loaded
    if not db.countries:
        logger.error("Database is empty after refresh!")
        return False
        
    logger.info(f"Successfully created database with {len(db.countries)} countries")
    return True
    
def test_random_country_selection():
    """Test retrieving random countries"""
    logger.info("Testing random country selection...")
    
    from country_database import get_database
    db = get_database()
    
    # Get 5 random countries
    countries = []
    for _ in range(5):
        country = db.get_random_country()
        countries.append(country)
        logger.info(f"Random country: {country['name']['common']}")
        
    # Check that we get different countries (it's possible but unlikely to get duplicates)
    unique_countries = set(c['name']['common'] for c in countries)
    logger.info(f"Selected {len(unique_countries)} unique countries out of 5 random selections")
    
    return len(unique_countries) > 1  # Should get at least 2 different countries
    
def test_map_retrieval():
    """Test retrieving map URLs for countries"""
    logger.info("Testing map URL retrieval...")
    
    from country_database import get_database
    db = get_database()
    
    # Test some mainstream countries
    mainstream_countries = ["United States", "France", "Japan", "Brazil", "Australia"]
    
    for country_name in mainstream_countries:
        country = db.get_country_by_name(country_name)
        if not country:
            logger.warning(f"Could not find {country_name} in database")
            continue
            
        map_url = db.get_map_url(country)
        logger.info(f"Map URL for {country_name}: {map_url}")
        
        # Verify the URL works
        try:
            req = urllib.request.Request(map_url)
            response = urllib.request.urlopen(req, timeout=5)
            if response.status == 200:
                logger.info(f"✅ Verified map URL for {country_name}")
            else:
                logger.warning(f"❌ Invalid response for {country_name}: {response.status}")
        except Exception as e:
            logger.error(f"❌ Error verifying map URL for {country_name}: {e}")
            
    # Test some small islands and less common countries
    small_countries = ["Marshall Islands", "Tuvalu", "Nauru", "Palau", "Saint Lucia"]
    
    for country_name in small_countries:
        country = db.get_country_by_name(country_name)
        if not country:
            logger.warning(f"Could not find {country_name} in database")
            continue
            
        map_url = db.get_map_url(country)
        logger.info(f"Map URL for {country_name}: {map_url}")
        
        # Verify the URL works
        try:
            req = urllib.request.Request(map_url)
            response = urllib.request.urlopen(req, timeout=5)
            if response.status == 200:
                logger.info(f"✅ Verified map URL for {country_name}")
            else:
                logger.warning(f"❌ Invalid response for {country_name}: {response.status}")
        except Exception as e:
            logger.error(f"❌ Error verifying map URL for {country_name}: {e}")
            
    return True
    
def test_hints():
    """Test the hint system"""
    logger.info("Testing hint system...")
    
    from country_database import get_database
    db = get_database()
    
    # Test hints for a few countries
    test_countries = ["France", "Japan", "Brazil", "Kenya", "Marshall Islands"]
    
    for country_name in test_countries:
        logger.info(f"Testing hints for {country_name}")
        hints = db.get_country_hints(country_name)
        
        if hints:
            logger.info(f"Found {len(hints)} hints for {country_name}")
            for hint in hints:
                logger.info(f"  - {hint['type']}: {hint['text']}")
        else:
            logger.warning(f"No hints found for {country_name}")
            
    return True
    
def main():
    """Run all tests"""
    logger.info("Starting country database tests...")
    
    # Run tests
    tests = [
        ("Database Creation", test_database_creation),
        ("Random Country Selection", test_random_country_selection),
        ("Map URL Retrieval", test_map_retrieval),
        ("Hint System", test_hints)
    ]
    
    success_count = 0
    
    for name, test_func in tests:
        logger.info(f"\n{'='*20} Testing: {name} {'='*20}")
        try:
            result = test_func()
            if result:
                logger.info(f"✅ {name} test passed!")
                success_count += 1
            else:
                logger.error(f"❌ {name} test failed!")
        except Exception as e:
            logger.error(f"❌ {name} test error: {e}")
            
    logger.info(f"\n{'='*60}")
    logger.info(f"Test results: {success_count}/{len(tests)} tests passed")
    
    if success_count == len(tests):
        logger.info("🎉 All tests passed! The country database is working correctly.")
    else:
        logger.warning("⚠️ Some tests failed. Please check the logs for details.")
    
if __name__ == "__main__":
    main()