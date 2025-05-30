#!/usr/bin/env python3
"""
Test script for the quotes database system
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from quotes_database import QuotesDatabase
import logging

def test_quotes_system():
    """Test the quotes database functionality"""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize database
        db = QuotesDatabase()
        
        # Get statistics
        total_quotes = db.get_quote_count()
        categories = db.get_categories()
        
        logger.info(f"Database contains {total_quotes} quotes")
        logger.info(f"Available categories: {', '.join(categories)}")
        
        # Test random quote retrieval
        print("\n=== Random Vietnamese Quote ===")
        vn_quote = db.get_random_quote(language='vi')
        if vn_quote:
            print(f"Quote: {vn_quote['quote_text']}")
            print(f"Author: {vn_quote['author']}")
            print(f"Category: {vn_quote['category']}")
            if vn_quote.get('source'):
                print(f"Source: {vn_quote['source']}")
            if vn_quote.get('source_type'):
                print(f"Source Type: {vn_quote['source_type']}")
            if vn_quote.get('source_url'):
                print(f"URL: {vn_quote['source_url']}")
        
        print("\n=== Random English Quote ===")
        en_quote = db.get_random_quote(language='en')
        if en_quote:
            print(f"Quote: {en_quote['quote_text']}")
            print(f"Author: {en_quote['author']}")
            print(f"Category: {en_quote['category']}")
            if en_quote.get('source'):
                print(f"Source: {en_quote['source']}")
            if en_quote.get('source_type'):
                print(f"Source Type: {en_quote['source_type']}")
            if en_quote.get('source_url'):
                print(f"URL: {en_quote['source_url']}")
        
        # Test search functionality
        print("\n=== Search Results for 'học' ===")
        search_results = db.search_quotes('học', language='vi')
        for i, quote in enumerate(search_results[:3], 1):
            print(f"{i}. {quote['quote_text']} - {quote['author']}")
        
        # Test category filtering
        if 'Giáo dục' in categories:
            print("\n=== Education Category Quote ===")
            edu_quote = db.get_random_quote(category='Giáo dục', language='vi')
            if edu_quote:
                print(f"Quote: {edu_quote['quote_text']}")
                print(f"Author: {edu_quote['author']}")
        
        db.close()
        logger.info("Quotes system test completed successfully!")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_quotes_system()
    sys.exit(0 if success else 1)