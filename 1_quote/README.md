# Quotes Database System

This module provides a complete quotes management system with PostgreSQL database backend and detailed source tracking.

## Files Overview

- `quotes_database.py` - Core database management class for quotes
- `quotes_collector.py` - Basic quotes collection from various sources  
- `enhanced_quotes_collector.py` - Advanced collector with detailed source information
- `setup_quotes_db.py` - Database initialization and setup script

## Database Schema

### Main Tables

**quotes** - Primary quotes storage
- `id` - Auto-increment primary key
- `quote_text` - The actual quote content (TEXT)
- `author` - Quote author (VARCHAR 255)
- `source` - Detailed source description (TEXT)
- `category` - Quote category (VARCHAR 100)
- `language` - Language code (VARCHAR 10, default 'vi')
- `source_type` - Type of source (VARCHAR 50)
- `source_url` - Reference URL (VARCHAR 500)
- `created_at` - Creation timestamp
- `updated_at` - Last update timestamp

**quote_categories** - Category definitions
- Category management and descriptions

**quote_sources** - Source tracking
- Source validation and management

## Features

### Database Operations
- Insert quotes with full source attribution
- Random quote retrieval by category/language
- Keyword search across quotes, authors, and categories
- Author-based quote filtering
- Category management

### Source Types Supported
- `book` - Published books and literature
- `speech` - Public speeches and addresses
- `declaration` - Official declarations and documents
- `letter` - Personal or official correspondence
- `folklore` - Traditional sayings and proverbs
- `interview` - Media interviews
- `song` - Song lyrics and musical works
- `research` - Academic research and papers
- `ancient_text` - Historical philosophical texts

### Data Sources
- Vietnamese cultural quotes and sayings
- International wisdom and motivational quotes
- Historical speeches and documents
- Literature and poetry
- Philosophical texts

## Usage Examples

```python
from quotes_database import QuotesDatabase
from enhanced_quotes_collector import EnhancedQuotesCollector

# Initialize database
db = QuotesDatabase()
db.create_tables()

# Get random quote
quote = db.get_random_quote(language='vi', category='Giáo dục')

# Search quotes
results = db.search_quotes('thành công', language='vi')

# Enhanced collection with sources
collector = EnhancedQuotesCollector()
collector.populate_enhanced_database()
```

## Database Setup

1. Ensure PostgreSQL is available
2. Run setup script: `python setup_quotes_db.py`
3. For enhanced sources: `python enhanced_quotes_collector.py`

## Current Statistics

- 25+ quotes across multiple categories
- Vietnamese and English language support
- Detailed source attribution including URLs
- Multiple source types for authenticity verification