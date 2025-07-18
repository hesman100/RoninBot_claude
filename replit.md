# XBot API - Telegram Bot with REST API

## Overview

This project is a comprehensive Telegram bot with an integrated REST API that provides both interactive chat functionality and programmatic access to financial data and country guessing games. The system uses a consolidated server approach, running both the Telegram bot and API server on the same port (5000) for streamlined deployment.

## User Preferences

```
Preferred communication style: Simple, everyday language.
```

## System Architecture

### Architecture Pattern
- **Monolithic with Service Separation**: Single process hosting both Telegram bot and Flask API
- **Event-driven Bot**: Uses python-telegram-bot for handling Telegram updates
- **RESTful API**: Flask-based API with CORS support for external access
- **SQLite Database**: Local file-based database for game data and user statistics

### Key Technologies
- **Backend**: Python with Flask, python-telegram-bot
- **Database**: SQLite for game data, user statistics, and quotes
- **External APIs**: CoinMarketCap, Alpha Vantage, Finnhub, Vietnam Stock APIs
- **Image Processing**: PIL for image manipulation and standardization
- **Caching**: In-memory caching for API responses and game data

## Key Components

### 1. Telegram Bot (`bot.py`)
- Handles Telegram commands and interactions
- Provides cryptocurrency, stock, and Vietnam stock price information
- Manages interactive country guessing games
- Tracks user statistics and leaderboards

### 2. REST API (`xbot_api/api.py`)
- Exposes all bot functionality via HTTP endpoints
- Supports API key authentication (header or query parameter)
- Implements request deduplication to prevent duplicate responses
- Provides consistent game data across multiple requests

### 3. Country Game System (`country_game/`)
- **Game Handler**: Manages game logic, statistics, and image processing
- **Database**: SQLite database with country data, capitals, regions, populations
- **Image Assets**: Map images (320x320px) and flag images (320x160px)
- **Game Modes**: Map guessing, flag guessing, capital guessing

### 4. Price Functions (`price_func/`)
- **CoinMarketCap API**: Cryptocurrency price data
- **Alpha Vantage API**: US stock market data
- **Finnhub API**: Alternative stock data source
- **Vietnam Stock API**: Vietnamese stock market data using Yahoo Finance

## Data Flow

### Game Request Flow
1. Client generates unique request ID
2. API checks cache for existing response
3. If cache miss, generates new game data
4. Game data stored with deterministic ID
5. Images standardized to 320px width
6. Response cached to prevent duplicates

### Price Data Flow
1. Client requests price information
2. API checks internal cache (60 seconds for stocks, 300 seconds for crypto)
3. If cache miss, fetches from external APIs
4. Data formatted and returned to client
5. Results cached for subsequent requests

### User Statistics Flow
1. Game answers submitted to API
2. Statistics calculated and stored in SQLite
3. User rankings updated in real-time
4. Leaderboard data accessible via API

## External Dependencies

### Required APIs
- **CoinMarketCap**: Cryptocurrency price data (requires API key)
- **Alpha Vantage**: Stock market data (requires API key)
- **Finnhub**: Alternative stock data (requires API key)
- **Telegram Bot API**: Bot token for Telegram integration

### Optional APIs
- **GeoAPIfy**: Country data enrichment (used in database building)

### Environment Variables
- `TELEGRAM_BOT_TOKEN`: Telegram bot authentication
- `COINMARKETCAP_API_KEY`: CoinMarketCap API access
- `ALPHAVANTAGE_API_KEY`: Alpha Vantage API access
- `FINNHUB_API_KEY`: Finnhub API access
- `XBOT_API_KEY`: Custom API key for REST API access

## Deployment Strategy

### Single Process Deployment
- **Entry Point**: `bot.py` or `run_all.py`
- **Port**: 5000 (configurable via environment)
- **Services**: Both Telegram bot and API server in same process

### Database Initialization
- SQLite databases created automatically on first run
- Country data populated from static files and API calls
- User statistics tables created as needed

### Image Asset Management
- Map images: 400x400px originals standardized to 320x320px
- Flag images: Various sizes standardized to 320x160px
- Images served as base64-encoded data in API responses

### Error Handling
- Comprehensive logging throughout the system
- Graceful degradation when external APIs fail
- Automatic retries with exponential backoff
- Cache fallbacks for improved reliability

### Security Considerations
- API key authentication for all endpoints (except health check)
- Request rate limiting via caching mechanisms
- Input validation and sanitization
- CORS configuration for web client access

### Scalability Features
- In-memory caching to reduce external API calls
- Deterministic game ID generation for consistency
- Efficient database queries with proper indexing
- Memory cleanup for long-running processes