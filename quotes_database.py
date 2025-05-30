"""
Database management for quotes collection from open sources
"""

import psycopg2
import os
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class QuotesDatabase:
    def __init__(self):
        self.connection = None
        self.connect()
        
    def connect(self):
        """Connect to PostgreSQL database"""
        try:
            self.connection = psycopg2.connect(
                host=os.environ.get('PGHOST'),
                database=os.environ.get('PGDATABASE'),
                user=os.environ.get('PGUSER'),
                password=os.environ.get('PGPASSWORD'),
                port=os.environ.get('PGPORT')
            )
            self.connection.autocommit = True
            logger.info("Connected to PostgreSQL database")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
            
    def create_tables(self):
        """Create tables for quotes database"""
        cursor = self.connection.cursor()
        
        # Create quotes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quotes (
                id SERIAL PRIMARY KEY,
                quote_text TEXT NOT NULL,
                author VARCHAR(255),
                source VARCHAR(255),
                category VARCHAR(100),
                language VARCHAR(10) DEFAULT 'vi',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create categories table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quote_categories (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) UNIQUE NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create sources table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quote_sources (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) UNIQUE NOT NULL,
                url VARCHAR(500),
                description TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_quotes_author ON quotes(author)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_quotes_category ON quotes(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_quotes_language ON quotes(language)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_quotes_source ON quotes(source)")
        
        cursor.close()
        logger.info("Database tables created successfully")
        
    def insert_quote(self, quote_text: str, author: str = None, source: str = None, 
                    category: str = None, language: str = 'vi', source_type: str = None, 
                    source_url: str = None) -> int:
        """Insert a new quote into the database"""
        cursor = self.connection.cursor()
        
        cursor.execute("""
            INSERT INTO quotes (quote_text, author, source, category, language, source_type, source_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (quote_text, author, source, category, language, source_type, source_url))
        
        quote_id = cursor.fetchone()[0]
        cursor.close()
        logger.info(f"Inserted quote with ID: {quote_id}")
        return quote_id
        
    def get_random_quote(self, category: str = None, language: str = 'vi') -> Optional[Dict]:
        """Get a random quote from the database"""
        cursor = self.connection.cursor()
        
        if category:
            cursor.execute("""
                SELECT id, quote_text, author, source, category
                FROM quotes 
                WHERE language = %s AND category = %s
                ORDER BY RANDOM()
                LIMIT 1
            """, (language, category))
        else:
            cursor.execute("""
                SELECT id, quote_text, author, source, category
                FROM quotes 
                WHERE language = %s
                ORDER BY RANDOM()
                LIMIT 1
            """, (language,))
            
        result = cursor.fetchone()
        cursor.close()
        
        if result:
            return {
                'id': result[0],
                'quote_text': result[1],
                'author': result[2],
                'source': result[3],
                'category': result[4]
            }
        return None
        
    def search_quotes(self, keyword: str, language: str = 'vi') -> List[Dict]:
        """Search quotes by keyword"""
        cursor = self.connection.cursor()
        
        cursor.execute("""
            SELECT id, quote_text, author, source, category
            FROM quotes 
            WHERE language = %s AND (
                quote_text ILIKE %s OR 
                author ILIKE %s OR 
                category ILIKE %s
            )
            ORDER BY created_at DESC
            LIMIT 20
        """, (language, f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'))
        
        results = cursor.fetchall()
        cursor.close()
        
        quotes = []
        for result in results:
            quotes.append({
                'id': result[0],
                'quote_text': result[1],
                'author': result[2],
                'source': result[3],
                'category': result[4]
            })
        return quotes
        
    def get_quotes_by_author(self, author: str, language: str = 'vi') -> List[Dict]:
        """Get all quotes by a specific author"""
        cursor = self.connection.cursor()
        
        cursor.execute("""
            SELECT id, quote_text, author, source, category
            FROM quotes 
            WHERE language = %s AND author ILIKE %s
            ORDER BY created_at DESC
        """, (language, f'%{author}%'))
        
        results = cursor.fetchall()
        cursor.close()
        
        quotes = []
        for result in results:
            quotes.append({
                'id': result[0],
                'quote_text': result[1],
                'author': result[2],
                'source': result[3],
                'category': result[4]
            })
        return quotes
        
    def get_categories(self) -> List[str]:
        """Get all available categories"""
        cursor = self.connection.cursor()
        
        cursor.execute("SELECT DISTINCT category FROM quotes WHERE category IS NOT NULL")
        results = cursor.fetchall()
        cursor.close()
        
        return [result[0] for result in results if result[0]]
        
    def get_quote_count(self) -> int:
        """Get total number of quotes in database"""
        cursor = self.connection.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM quotes")
        count = cursor.fetchone()[0]
        cursor.close()
        
        return count
        
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")