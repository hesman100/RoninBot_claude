#!/usr/bin/env python3
"""
Setup script for quotes database
"""

import sys
import logging
from quotes_collector import QuotesCollector

def main():
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Initializing quotes database...")
        
        # Create collector instance
        collector = QuotesCollector()
        
        # Populate database with initial quotes
        collector.populate_database()
        
        # Display statistics
        total_quotes = collector.db.get_quote_count()
        categories = collector.get_categories()
        
        logger.info(f"Database setup completed successfully!")
        logger.info(f"Total quotes: {total_quotes}")
        logger.info(f"Categories: {', '.join(categories)}")
        
        # Test functionality
        logger.info("Testing quote retrieval...")
        
        # Get random Vietnamese quote
        vn_quote = collector.get_random_quote(language='vi')
        if vn_quote:
            logger.info(f"Random Vietnamese quote: {vn_quote['quote_text'][:50]}... - {vn_quote['author']}")
        
        # Get random English quote
        en_quote = collector.get_random_quote(language='en')
        if en_quote:
            logger.info(f"Random English quote: {en_quote['quote_text'][:50]}... - {en_quote['author']}")
        
        logger.info("Quotes database is ready for use!")
        
    except Exception as e:
        logger.error(f"Failed to setup quotes database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()