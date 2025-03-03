#!/usr/bin/env python3
"""
Migration Package Preparation Script

This script creates ZIP archives of the necessary resources for the country guessing bot:
1. Database file
2. Flag images
3. Map images

Running this script will create three zip files in the bot_move directory:
- database.zip - Contains the countries.db file
- wiki_flag.zip - Contains all country flag images
- wiki_all_map_400pi.zip - Contains all country map images
"""

import os
import shutil
import zipfile
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Base paths
WORKSPACE_PATH = Path('/home/runner/workspace')
BOT_MOVE_PATH = WORKSPACE_PATH / 'bot_move'
DATABASE_PATH = WORKSPACE_PATH / 'countries.db'
FLAG_PATH = WORKSPACE_PATH / 'wiki_flag'
MAP_PATH = WORKSPACE_PATH / 'wiki_all_map_400pi'

def create_database_zip():
    """Copy and zip the database file"""
    logger.info("Creating database.zip...")
    
    # Create a directory for the database
    db_dir = BOT_MOVE_PATH / 'database'
    db_dir.mkdir(exist_ok=True)
    
    # Copy the database file
    db_copy_path = db_dir / 'countries.db'
    shutil.copy(DATABASE_PATH, db_copy_path)
    
    # Create the zip file
    with zipfile.ZipFile(BOT_MOVE_PATH / 'database.zip', 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(db_copy_path, arcname='countries.db')
    
    logger.info(f"Created database.zip: {os.path.getsize(BOT_MOVE_PATH / 'database.zip') / 1024:.2f} KB")

def create_flag_zip():
    """Zip all flag images"""
    logger.info("Creating wiki_flag.zip...")
    
    # Create the zip file
    with zipfile.ZipFile(BOT_MOVE_PATH / 'wiki_flag.zip', 'w', zipfile.ZIP_DEFLATED) as zipf:
        for flag_file in FLAG_PATH.glob('*_flag.png'):
            zipf.write(flag_file, arcname=f'wiki_flag/{flag_file.name}')
    
    logger.info(f"Created wiki_flag.zip: {os.path.getsize(BOT_MOVE_PATH / 'wiki_flag.zip') / 1024:.2f} KB")

def create_map_zip():
    """Zip all map images"""
    logger.info("Creating wiki_all_map_400pi.zip...")
    
    # Create the zip file
    with zipfile.ZipFile(BOT_MOVE_PATH / 'wiki_all_map_400pi.zip', 'w', zipfile.ZIP_DEFLATED) as zipf:
        for map_file in MAP_PATH.glob('*_locator_map.png'):
            zipf.write(map_file, arcname=f'wiki_all_map_400pi/{map_file.name}')
    
    logger.info(f"Created wiki_all_map_400pi.zip: {os.path.getsize(BOT_MOVE_PATH / 'wiki_all_map_400pi.zip') / 1024 / 1024:.2f} MB")

def create_usage_instructions():
    """Create a file with instructions on how to use the migration package"""
    logger.info("Creating migration package instructions...")
    
    instructions = """# Migration Package Instructions

This migration package contains everything you need to transfer the country guessing game to your CryptoPriceBot project.

## Contents
- `database.zip` - Contains the countries.db SQLite database
- `wiki_flag.zip` - Contains flag images for all countries
- `wiki_all_map_400pi.zip` - Contains map images for all countries
- Various Python files and documentation

## Setup Instructions

### 1. Extract the Image Files
Extract the image ZIP files to your CryptoPriceBot project directory:
```
unzip wiki_flag.zip -d /path/to/CryptoPriceBot/
unzip wiki_all_map_400pi.zip -d /path/to/CryptoPriceBot/
```

### 2. Setup the Database
You have two options for the database:

#### Option A: Use the SQLite Database
1. Extract the database.zip file:
```
unzip database.zip -d /path/to/CryptoPriceBot/
```
2. Update your `country_database.py` file to use this SQLite database instead of PostgreSQL

#### Option B: Import to PostgreSQL (Recommended)
1. Create a new PostgreSQL database
2. Use the SQL scripts in the sql/ directory to create the schema
3. Import the data from the countries.db file:
```
python import_sqlite_to_postgres.py
```

### 3. Follow the Migration Guide
See MIGRATION_GUIDE.md for detailed instructions on integrating the bot functionality.

## Testing Your Setup
After setup, run the check_bot_status.py script to verify everything is working:
```
python check_bot_status.py
```

If you encounter any issues, please refer to the troubleshooting section in MIGRATION_GUIDE.md.
"""
    
    # Write instructions to file
    with open(BOT_MOVE_PATH / 'MIGRATION_PACKAGE_INSTRUCTIONS.md', 'w') as f:
        f.write(instructions)
    
    logger.info("Created migration package instructions")

def create_sqlite_to_postgres_script():
    """Create a script to import the SQLite database to PostgreSQL"""
    logger.info("Creating import_sqlite_to_postgres.py script...")
    
    script = """#!/usr/bin/env python3
\"\"\"
SQLite to PostgreSQL Database Import Script

This script imports data from the countries.db SQLite database to a PostgreSQL database.
It creates the necessary tables and copies all data.

Requirements:
- psycopg2-binary (for PostgreSQL)
- sqlite3 (included in Python)

Usage:
1. Set the DATABASE_URL environment variable for your PostgreSQL connection
2. Run this script: python import_sqlite_to_postgres.py
\"\"\"

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
    \"\"\"Connect to the SQLite database\"\"\"
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    return conn

def connect_to_postgres():
    \"\"\"Connect to the PostgreSQL database\"\"\"
    if not PG_CONNECTION_STRING:
        raise ValueError("DATABASE_URL environment variable must be set")
    
    return psycopg2.connect(PG_CONNECTION_STRING)

def create_postgres_tables(pg_conn):
    \"\"\"Create the necessary tables in PostgreSQL\"\"\"
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
    \"\"\"Import data from SQLite to PostgreSQL\"\"\"
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
    \"\"\"Run the import process\"\"\"
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
"""
    
    # Write script to file
    with open(BOT_MOVE_PATH / 'import_sqlite_to_postgres.py', 'w') as f:
        f.write(script)
    
    logger.info("Created import_sqlite_to_postgres.py script")

def main():
    """Run all package preparation steps"""
    logger.info("=== Preparing Migration Package ===")
    
    # Create zip files
    create_database_zip()
    create_flag_zip()
    create_map_zip()
    
    # Create helper files
    create_usage_instructions()
    create_sqlite_to_postgres_script()
    
    logger.info("=== Migration Package Preparation Complete ===")
    logger.info(f"All files are available in: {BOT_MOVE_PATH}")

if __name__ == "__main__":
    main()