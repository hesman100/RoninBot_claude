# Migration Package Instructions

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
