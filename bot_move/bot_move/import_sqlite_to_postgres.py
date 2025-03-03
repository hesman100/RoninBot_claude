#!/usr/bin/env python3
"""
SQLite to PostgreSQL Database Import Script

This script imports data from the countries.db SQLite database to a PostgreSQL database.
It creates the necessary tables and copies all data.

Requirements:
- psycopg2-binary (for PostgreSQL)
- sqlite3 (included in Python)

Usage:
1. Set the DATABASE_URL environment variable for your PostgreSQL connection
2. Run this script: python import_sqlite_to_postgres.py
"""

import os
import sqlite3
import psycopg2
import json
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
SQLITE_DB_PATH = Path('countries.db')  # Next to this script
PG_CONNECTION_STRING = os.environ.get('DATABASE_URL')

def connect_to_sqlite():
    """Connect to the SQLite database"""
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    return conn

def connect_to_postgres():
    """Connect to the PostgreSQL database"""
    if not PG_CONNECTION_STRING:
        raise ValueError("DATABASE_URL environment variable must be set")
    
    return psycopg2.connect(PG_CONNECTION_STRING)

def create_postgres_tables(pg_conn):
    """Create the necessary tables in PostgreSQL"""
    logger.info("Creating PostgreSQL tables...")
    
    with pg_conn.cursor() as cur:
        # Create countries table
        cur.execute('''
        CREATE TABLE IF NOT EXISTS countries (
            id SERIAL PRIMARY KEY,
            name JSONB NOT NULL,
            capital TEXT,
            population BIGINT,
            area FLOAT,
            region TEXT,
            subregion TEXT,
            currencies JSONB,
            languages JSONB,
            lat FLOAT,
            lng FLOAT,
            neighbors JSONB,
            neighbors_capital_city JSONB,
            hints JSONB,
            not_a_country BOOLEAN DEFAULT FALSE
        )
        ''')
        
        # Create maps table
        cur.execute('''
        CREATE TABLE IF NOT EXISTS maps (
            id SERIAL PRIMARY KEY,
            country_id INTEGER REFERENCES countries(id),
            url TEXT NOT NULL,
            map_type TEXT DEFAULT 'primary',
            UNIQUE(country_id, map_type)
        )
        ''')
        
        pg_conn.commit()
        logger.info("PostgreSQL tables created successfully")

def import_data(sqlite_conn, pg_conn):
    """Import data from SQLite to PostgreSQL"""
    logger.info("Starting data import...")
    
    # Get countries from SQLite
    sqlite_cur = sqlite_conn.cursor()
    sqlite_cur.execute("SELECT * FROM countries")
    countries = sqlite_cur.fetchall()
    
    # Insert countries into PostgreSQL
    with pg_conn.cursor() as pg_cur:
        logger.info(f"Importing {len(countries)} countries...")
        
        for country in countries:
            # Convert row to dict
            country_dict = {key: country[key] for key in country.keys()}
            
            # Prepare JSON fields
            json_fields = ['name', 'currencies', 'languages', 'neighbors', 'neighbors_capital_city', 'hints']
            for field in json_fields:
                if field in country_dict and country_dict[field]:
                    # If stored as string, parse it
                    if isinstance(country_dict[field], str):
                        try:
                            country_dict[field] = json.loads(country_dict[field])
                        except (json.JSONDecodeError, TypeError):
                            country_dict[field] = None
            
            # Insert country
            pg_cur.execute('''
            INSERT INTO countries (
                id, name, capital, population, area, region, subregion,
                currencies, languages, lat, lng, neighbors, 
                neighbors_capital_city, hints, not_a_country
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ''', (
                country_dict.get('id'),
                json.dumps(country_dict.get('name', {})),
                country_dict.get('capital'),
                country_dict.get('population'),
                country_dict.get('area'),
                country_dict.get('region'),
                country_dict.get('subregion'),
                json.dumps(country_dict.get('currencies', {})),
                json.dumps(country_dict.get('languages', {})),
                country_dict.get('lat'),
                country_dict.get('lng'),
                json.dumps(country_dict.get('neighbors', [])),
                json.dumps(country_dict.get('neighbors_capital_city', {})),
                json.dumps(country_dict.get('hints', {})),
                country_dict.get('not_a_country', False)
            ))
        
        pg_conn.commit()
        logger.info("Countries import completed")
    
    # Get maps from SQLite
    sqlite_cur.execute("SELECT * FROM maps")
    maps = sqlite_cur.fetchall()
    
    # Insert maps into PostgreSQL
    with pg_conn.cursor() as pg_cur:
        logger.info(f"Importing {len(maps)} maps...")
        
        for map_entry in maps:
            # Convert row to dict
            map_dict = {key: map_entry[key] for key in map_entry.keys()}
            
            # Insert map
            pg_cur.execute('''
            INSERT INTO maps (
                id, country_id, url, map_type
            ) VALUES (
                %s, %s, %s, %s
            )
            ''', (
                map_dict.get('id'),
                map_dict.get('country_id'),
                map_dict.get('url'),
                map_dict.get('map_type', 'primary')
            ))
        
        pg_conn.commit()
        logger.info("Maps import completed")

def main():
    """Run the import process"""
    logger.info("Starting SQLite to PostgreSQL import...")
    
    if not SQLITE_DB_PATH.exists():
        logger.error(f"SQLite database file not found: {SQLITE_DB_PATH}")
        return
    
    try:
        # Connect to databases
        sqlite_conn = connect_to_sqlite()
        pg_conn = connect_to_postgres()
        
        # Create tables
        create_postgres_tables(pg_conn)
        
        # Import data
        import_data(sqlite_conn, pg_conn)
        
        logger.info("Import completed successfully!")
    except Exception as e:
        logger.error(f"Error during import: {e}")
    finally:
        # Close connections
        if 'sqlite_conn' in locals():
            sqlite_conn.close()
        if 'pg_conn' in locals():
            pg_conn.close()

if __name__ == "__main__":
    main()
