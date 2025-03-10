# Telegram Bot with Integrated REST API

This project combines a Telegram bot with a REST API service, providing both interactive chat functionality and programmatic access to the same features. The project uses a consolidated server approach running on a single port (5000) for simpler deployment.

## Features

### Telegram Bot
- Cryptocurrency price information via commands like `/price BTC`
- Stock price information via commands like `/stock AAPL`
- Vietnam stock price information via commands like `/vnstock VNM`
- Interactive country guessing game with multiple modes:
  - Map mode: guess the country from a map image
  - Flag mode: guess the country from a flag image
  - Capital mode: guess the country's capital city
- Comprehensive user statistics tracking
- Global leaderboard

### REST API
- Complete API access to all bot functionality
- Cryptocurrency price endpoints
- Stock price endpoints
- Vietnam stock price endpoints
- Country game endpoints (new game, verify answer)
- User statistics and leaderboard endpoints
- Supports both header-based and query parameter API key authentication

## Getting Started

### Prerequisites
- Python 3.8+
- Required packages listed in `pyproject.toml`

### Running the Project
The project can be run using:

```bash
python bot.py
```

This will start both the Telegram bot and API server on port 5000.

Alternatively, you can use:

```bash
python run_all.py
```

### API Authentication

All API endpoints (except the health check) require an API key, which can be provided in two ways:

1. As an HTTP header: `X-API-Key: xbot-default-api-key-9876543210`
2. As a query parameter: `?api_key=xbot-default-api-key-9876543210`

Default API key: `xbot-default-api-key-9876543210`

## Project Structure

- `bot.py` - Main Telegram bot code
- `integrated_server.py` - Consolidates the Telegram bot and API server
- `run_all.py` - Alternative starter script
- `xbot_api/` - API-related code
  - `api.py` - API endpoints
  - `utils.py` - Utility functions
  - `server.py` - API server
  - `sample_client.py` - Example API client
- `price_func/` - Price-related functionality
- `country_game/` - Country guessing game functionality

## API Documentation

For detailed API documentation, see [API README](xbot_api/README.md)

## Implementation Details

- Both the Telegram bot and API server run on port 5000
- The same code is used for both bot commands and API endpoints
- User statistics are stored in an SQLite database
- Image processing standardizes all images to 320px width

## Security Considerations

- The API key should be kept secret in production environments
- For production, set the `XBOT_API_KEY` environment variable to a custom value
- Use HTTPS in production environments