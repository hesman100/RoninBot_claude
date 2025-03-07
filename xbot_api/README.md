# XBot API

This API provides a way for external applications to access the functionality of the Telegram bot, including price information for various financial instruments and the country guessing game.

## Latest Updates (March 2025)

- Fixed database schema alignment issues - all database queries now correctly use 'total' and 'correct' column names
- Enhanced user stats tracking with proper game mode separation
- Improved error handling for all API endpoints
- Optimized image data handling in game endpoints
- Updated API response formats to match actual implementation
- Ensured proper authentication with API key validation

## Features

- **Price Information**:
  - Cryptocurrency prices via CoinMarketCap
  - Stock prices via Alpha Vantage and Finnhub
  - Vietnam stock prices via VN APIs

- **Country Game**:
  - Get new game questions with multiple-choice options
  - Verify answers and update user statistics
  - Access the game leaderboard
  - Retrieve user statistics

## Getting Started

### Prerequisites

- Python 3.8+
- Flask
- Requests
- The main Telegram bot code

### Installation

1. Clone or access the repository
2. Install the required packages:
```bash
pip install -r requirements.txt
```

### Running the API Server

```bash
python run_api_server.py
```

The server will start on port 5001 by default. You can change this by setting the `API_PORT` environment variable.

### API Authentication

All API endpoints (except the health check) require an API key to be included in the `X-API-Key` header. The API key is generated when the server starts if the `XBOT_API_KEY` environment variable is not set.

## API Reference

### Health Check

```
GET /api/health
```

Checks if the API server is running.

**Response**:
```json
{
  "status": "ok",
  "message": "XBot API is running"
}
```

### Cryptocurrency Prices

#### Get Price for a Single Cryptocurrency

```
GET /api/crypto/price?symbol=BTC
```

**Parameters**:
- `symbol` (required): The cryptocurrency symbol (e.g., BTC, ETH)

**Headers**:
- `X-API-Key`: Your API key

**Response**:
```json
{
  "name": "Bitcoin",
  "symbol": "BTC",
  "price": 50000.0,
  "price_change_24h": 1.5,
  "volume_24h": 10000000000,
  "market_cap": 1000000000000,
  "last_updated": "2025-03-06T14:30:00Z"
}
```

#### Get Prices for Multiple Cryptocurrencies

```
GET /api/crypto/prices?symbols=BTC,ETH,XRP
```

**Parameters**:
- `symbols` (optional): Comma-separated list of cryptocurrency symbols

**Headers**:
- `X-API-Key`: Your API key

**Response**:
```json
{
  "BTC": {
    "name": "Bitcoin",
    "symbol": "BTC",
    "price": 50000.0,
    "price_change_24h": 1.5
  },
  "ETH": {
    "name": "Ethereum",
    "symbol": "ETH",
    "price": 3000.0,
    "price_change_24h": 2.1
  },
  "XRP": {
    "name": "XRP",
    "symbol": "XRP",
    "price": 0.5,
    "price_change_24h": -0.3
  }
}
```

### Stock Prices

#### Get Price for a Single Stock

```
GET /api/stock/price?symbol=AAPL
```

**Parameters**:
- `symbol` (required): The stock symbol (e.g., AAPL, MSFT)

**Headers**:
- `X-API-Key`: Your API key

**Response**:
```json
{
  "symbol": "AAPL",
  "price": 150.0,
  "price_change": 1.2,
  "price_change_percent": "0.8%",
  "last_updated": "2025-03-06T14:30:00Z"
}
```

#### Get Prices for Multiple Stocks

```
GET /api/stock/prices
```

**Headers**:
- `X-API-Key`: Your API key

**Response**:
```json
{
  "AAPL": {
    "symbol": "AAPL",
    "price": 150.0,
    "price_change": 1.2,
    "price_change_percent": "0.8%"
  },
  "MSFT": {
    "symbol": "MSFT",
    "price": 300.0,
    "price_change": 2.5,
    "price_change_percent": "0.84%"
  }
}
```

### Vietnam Stock Prices

#### Get Price for a Single Vietnam Stock

```
GET /api/vietnam/stock/price?symbol=VCB
```

**Parameters**:
- `symbol` (required): The Vietnam stock symbol

**Headers**:
- `X-API-Key`: Your API key

**Response**:
```json
{
  "symbol": "VCB",
  "price": 55000.0,
  "price_change": 500.0,
  "price_change_percent": "0.92%",
  "last_updated": "2025-03-06T14:30:00Z"
}
```

#### Get Prices for Multiple Vietnam Stocks

```
GET /api/vietnam/stock/prices?symbols=VCB,VNM,FPT
```

**Parameters**:
- `symbols` (optional): Comma-separated list of Vietnam stock symbols

**Headers**:
- `X-API-Key`: Your API key

**Response**:
```json
{
  "VCB": {
    "symbol": "VCB",
    "price": 55000.0,
    "price_change": 500.0,
    "price_change_percent": "0.92%"
  },
  "VNM": {
    "symbol": "VNM",
    "price": 80000.0,
    "price_change": -200.0,
    "price_change_percent": "-0.25%"
  },
  "FPT": {
    "symbol": "FPT",
    "price": 65000.0,
    "price_change": 1000.0,
    "price_change_percent": "1.56%"
  }
}
```

### Country Game

#### Get a New Game Question

```
GET /api/game/new?mode=map
```

**Parameters**:
- `mode` (optional): Game mode (`map`, `flag`, or `cap`). Defaults to `map`.

**Headers**:
- `X-API-Key`: Your API key

**Response**:
```json
{
  "game_id": 123456789,
  "mode": "map",
  "options": ["France", "Germany", "Italy", "Spain", "United Kingdom"],
  "country_id": 42,
  "question": "Which country is highlighted on this map?",
  "correct_answer": "France",
  "image_path": "country_game/images/wiki_all_map_400pi/France_locator_map.png",
  "country": {
    "name": "France",
    "capital": "Paris",
    "region": "Europe",
    "population": 67000000,
    "area": 551695
  }
}
```

#### Verify a Game Answer

```
POST /api/game/verify
```

**Headers**:
- `Content-Type`: `application/json`
- `X-API-Key`: Your API key

**Request Body**:
```json
{
  "game_id": 123456789,
  "country_id": 42,
  "mode": "map",
  "answer": "France",
  "user_id": "user123",
  "user_name": "John Doe",
  "login_method": "web",
  "wallet_address": "0xabc123"
}
```

**Response**:
```json
{
  "is_correct": true,
  "correct_answer": "France",
  "country": {
    "name": "France",
    "capital": "Paris",
    "region": "Europe",
    "population": 67000000,
    "area": 551695
  },
  "user_stats": {
    "total": 10,
    "correct": 8,
    "accuracy": 80.0
  }
}
```

#### Get Leaderboard

```
GET /api/game/leaderboard?mode=all&limit=10
```

**Parameters**:
- `mode` (optional): Game mode to filter by (`map`, `flag`, `cap`, or `all`). Defaults to `all`.
- `limit` (optional): Maximum number of entries to return. Defaults to 10.

**Headers**:
- `X-API-Key`: Your API key

**Response**:
```json
{
  "leaderboard": [
    {
      "rank": 1,
      "user_id": "user123",
      "user_name": "John Doe",
      "login_method": "web",
      "wallet_address": "0xabc123",
      "joined": 1646579897,
      "accuracy": 90.0,
      "total": 20,
      "correct": 18,
      "modes": {
        "map": {
          "total": 10,
          "correct": 9,
          "accuracy": 90.0
        },
        "flag": {
          "total": 8,
          "correct": 7,
          "accuracy": 87.5
        },
        "cap": {
          "total": 2,
          "correct": 2,
          "accuracy": 100.0
        }
      }
    },
    {
      "rank": 2,
      "user_id": "user456",
      "user_name": "Jane Smith",
      "login_method": "tele",
      "wallet_address": "0xtele",
      "joined": 1646669897,
      "accuracy": 85.0,
      "total": 40,
      "correct": 34,
      "modes": {
        "map": {
          "total": 20,
          "correct": 18,
          "accuracy": 90.0
        },
        "flag": {
          "total": 15,
          "correct": 12,
          "accuracy": 80.0
        },
        "cap": {
          "total": 5,
          "correct": 4,
          "accuracy": 80.0
        }
      }
    }
  ]
}
```

#### Get User Statistics

```
GET /api/game/user-stats?user_id=user123
```

**Parameters**:
- `user_id` (required): User ID to fetch stats for

**Headers**:
- `X-API-Key`: Your API key

**Response**:
```json
{
  "user_id": "user123",
  "user_name": "John Doe",
  "login_method": "web",
  "wallet_address": "0xabc123",
  "joined": 1646579897,
  "overall": {
    "total": 20,
    "correct": 18,
    "accuracy": 90.0
  },
  "modes": {
    "map": {
      "total": 10,
      "correct": 9,
      "accuracy": 90.0
    },
    "flag": {
      "total": 8,
      "correct": 7,
      "accuracy": 87.5
    },
    "cap": {
      "total": 2,
      "correct": 2,
      "accuracy": 100.0
    }
  }
}
```

## Integration Example

Here's a simple Python script that demonstrates how to use the API:

```python
import requests
import json

# API configuration
API_BASE_URL = "http://localhost:5001/api"
API_KEY = "your_api_key"

# Set up headers with API key
HEADERS = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
}

# Get cryptocurrency price
def get_crypto_price(symbol):
    response = requests.get(f"{API_BASE_URL}/crypto/price", 
                           params={"symbol": symbol},
                           headers=HEADERS)
    return response.json()

# Get a new game
def get_new_game(mode="map"):
    response = requests.get(f"{API_BASE_URL}/game/new", 
                           params={"mode": mode},
                           headers=HEADERS)
    return response.json()

# Verify a game answer
def verify_answer(game_data, answer, user_info):
    data = {
        "game_id": game_data["game_id"],
        "country_id": game_data["country_id"],
        "mode": game_data["mode"],
        "answer": answer,
        **user_info
    }
    
    response = requests.post(f"{API_BASE_URL}/game/verify", 
                            json=data,
                            headers=HEADERS)
    return response.json()

# Example usage
btc_price = get_crypto_price("BTC")
print(f"Bitcoin price: ${btc_price['BTC']['usd']}")

game = get_new_game("map")
print(f"New game question: {game['question']}")
print(f"Options: {', '.join(game['options'])}")

user_info = {
    "user_id": "user123",
    "user_name": "John Doe",
    "login_method": "web",
    "wallet_address": "0xabc123"
}

# In a real application, you'd ask the user for their answer
# Here we're just using the correct answer for demonstration
country_name = game.get("country", {}).get("name", "")
result = verify_answer(game, country_name, user_info)
print(f"Correct answer: {result['is_correct']}")
print(f"User stats: {result['user_stats']}")
```

## Error Handling

All API endpoints return appropriate HTTP status codes:

- `200 OK`: Request successful
- `400 Bad Request`: Missing or invalid parameters
- `401 Unauthorized`: Invalid or missing API key
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

Error responses include a JSON object with an `error` field:

```json
{
  "error": "Error message describing the issue"
}
```

## Limitations and Known Issues

- The API does not support real-time updates; clients need to poll for new data
- The game images are served as base64-encoded strings, which may increase response size
- API rate limiting is not implemented in this version
- There is a harmless warning in the game_handler.py log about 'total' access when saving user stats. This does not affect functionality and stats are properly saved
- When the API server restarts, a new API key is generated unless XBOT_API_KEY environment variable is set

## Security Considerations

- The API key should be kept secret and not shared
- In production, use HTTPS to secure API requests
- Consider implementing rate limiting for production use

## Support

For issues or questions, please contact the repository maintainers.