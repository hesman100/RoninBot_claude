# API Documentation for Telegram Bot

This document describes the API endpoints provided by the Telegram bot service. These endpoints allow external applications, such as a web interface, to interact with the bot's functionality.

## Authentication

All API endpoints, except for the health check, require authentication using an API key. You can provide the API key in one of two ways:

1. As a Bearer token in the Authorization header:
   ```
   Authorization: Bearer YOUR_API_KEY
   ```

2. As a query parameter:
   ```
   ?api_key=YOUR_API_KEY
   ```

The API key is set in the environment variable `API_KEY`. If not set, a random key is generated when the server starts. The key is logged in the server log file.

## Base URL

The base URL for all API endpoints is:

```
http://your-server-address:5001/api
```

## Endpoints

### Health Check

```
GET /api/health
```

Check if the API server is running.

**Response:**
```json
{
  "status": "ok",
  "version": "1.3",
  "timestamp": "2025-03-06T12:34:56.789Z"
}
```

### Help

```
GET /api
```

Get information about available API endpoints.

**Response:**
```json
{
  "version": "1.3",
  "endpoints": [
    {
      "path": "/api/health",
      "method": "GET",
      "description": "Check the health of the API server"
    },
    {
      "path": "/api/prices/crypto",
      "method": "GET",
      "description": "Get prices for default cryptocurrencies"
    },
    ...
  ],
  "authentication": {
    "method": "Bearer token or api_key query parameter",
    "example": "Authorization: Bearer YOUR_API_KEY or ?api_key=YOUR_API_KEY"
  },
  "description": "This API provides access to the Telegram bot functionality, including price checks and country guessing games."
}
```

### Price Endpoints

#### Get Default Cryptocurrency Prices

```
GET /api/prices/crypto
```

Get prices for a default list of cryptocurrencies.

**Response:**
```json
{
  "status": "success",
  "data": {
    "BTC": {
      "symbol": "BTC",
      "price": 50000.0,
      "percent_change_24h": 2.5,
      "market_cap": 1000000000000,
      "volume_24h": 50000000000
    },
    ...
  },
  "message": "🪙 Cryptocurrency Prices 🪙\n\nBTC: $50,000.00 (+2.50%)\n..."
}
```

#### Get Specific Cryptocurrency Price

```
GET /api/prices/crypto/<symbol>
```

Get the price for a specific cryptocurrency by symbol.

**Parameters:**
- `symbol`: The cryptocurrency symbol (e.g., BTC, ETH)

**Response:**
```json
{
  "status": "success",
  "data": {
    "BTC": {
      "symbol": "BTC",
      "price": 50000.0,
      "percent_change_24h": 2.5,
      "market_cap": 1000000000000,
      "volume_24h": 50000000000
    }
  },
  "message": "BTC: $50,000.00 (+2.50%)\nMarket Cap: $1.00T\nVolume (24h): $50.00B"
}
```

#### Get Default Stock Prices

```
GET /api/prices/stock
```

Get prices for a default list of stocks.

**Response:**
```json
{
  "status": "success",
  "data": {
    "AAPL": {
      "symbol": "AAPL",
      "price": 150.0,
      "percent_change": 1.2,
      "volume": 100000000
    },
    ...
  },
  "message": "📈 Stock Prices 📈\n\nAAPL: $150.00 (+1.20%)\n..."
}
```

#### Get Specific Stock Price

```
GET /api/prices/stock/<symbol>
```

Get the price for a specific stock by symbol.

**Parameters:**
- `symbol`: The stock symbol (e.g., AAPL, TSLA)

**Response:**
```json
{
  "status": "success",
  "data": {
    "AAPL": {
      "symbol": "AAPL",
      "price": 150.0,
      "percent_change": 1.2,
      "volume": 100000000
    }
  },
  "message": "AAPL: $150.00 (+1.20%)\nVolume: 100,000,000"
}
```

#### Get Default Vietnam Stock Prices

```
GET /api/prices/vn
```

Get prices for a default list of Vietnam stocks.

**Response:**
```json
{
  "status": "success",
  "data": {
    "VNM": {
      "symbol": "VNM",
      "price": 80000.0,
      "percent_change": 0.5,
      "volume": 1000000
    },
    ...
  },
  "message": "🇻🇳 Vietnam Stock Prices 🇻🇳\n\nVNM: 80,000 đ (+0.50%)\n..."
}
```

#### Get Specific Vietnam Stock Price

```
GET /api/prices/vn/<symbol>
```

Get the price for a specific Vietnam stock by symbol.

**Parameters:**
- `symbol`: The stock symbol (e.g., VNM, HPG)

**Response:**
```json
{
  "status": "success",
  "data": {
    "VNM": {
      "symbol": "VNM",
      "price": 80000.0,
      "percent_change": 0.5,
      "volume": 1000000
    }
  },
  "message": "VNM: 80,000 đ (+0.50%)\nVolume: 1,000,000"
}
```

### Game Endpoints

#### Start a Game

```
GET /api/game/<mode>
```

Start a new game in the specified mode.

**Parameters:**
- `mode`: The game mode (map, flag, capital, cap)

**Response:**
```json
{
  "status": "success",
  "data": {
    "session_id": "1a2b3c4d5e6f7g8h",
    "mode": "map",
    "question": {
      "options": ["Country1", "Country2", "Country3", "Country4"],
      "image_url": "/static/assets/placeholder_map.png",
      "timer": 30
    }
  }
}
```

#### Submit an Answer

```
POST /api/game/answer
```

Submit an answer for a game.

**Request Body:**
```json
{
  "session_id": "1a2b3c4d5e6f7g8h",
  "answer": "Country1"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "is_correct": true,
    "correct_answer": "Country1",
    "explanation": "The correct answer is Country1",
    "country_details": {
      "name": "Country1",
      "capital": "Capital City",
      "region": "Region",
      "population": 1000000,
      "area": 100000
    }
  }
}
```

#### Get Leaderboard

```
GET /api/game/leaderboard
```

Get the game leaderboard.

**Response:**
```json
{
  "status": "success",
  "data": {
    "leaderboard": [
      {
        "user_id": 123456789,
        "user_name": "Player1",
        "score": 100,
        "games_played": 10,
        "win_rate": 80.0,
        "avg_time": 10.5
      },
      ...
    ]
  }
}
```

#### Get Game Help

```
GET /api/game/help
```

Get help information for the game.

**Response:**
```json
{
  "status": "success",
  "data": {
    "modes": {
      "map": "Guess the country from its map outline",
      "flag": "Guess the country from its flag",
      "capital": "Guess the country from its capital city"
    },
    "instructions": "Select the correct answer from the options provided. You have 30 seconds to answer each question.",
    "commands": [
      {
        "name": "/g map",
        "description": "Play the map guessing game"
      },
      ...
    ]
  }
}
```

### User Endpoints

#### Create Guest User

```
POST /api/user/guest
```

Create a new guest user.

**Response:**
```json
{
  "status": "success",
  "data": {
    "user_id": "guest_1a2b3c4d5e6f7g8h",
    "user_name": "Guest_1a2b"
  }
}
```

## Error Responses

API errors will be returned in the following format:

```json
{
  "error": "Error type",
  "message": "Detailed error message"
}
```

Common error status codes:
- 400: Bad Request - The request was malformed or missing required parameters
- 401: Unauthorized - Invalid or missing API key
- 404: Not Found - The requested resource or endpoint was not found
- 500: Internal Server Error - An unexpected error occurred on the server

## Rate Limits

The API currently does not implement rate limiting, but excessive requests may be throttled by the underlying API providers (e.g., CoinMarketCap, AlphaVantage, Finnhub).

## Example Usage

### cURL

```bash
# Get health status
curl http://your-server-address:5001/api/health

# Get Bitcoin price
curl -H "Authorization: Bearer YOUR_API_KEY" http://your-server-address:5001/api/prices/crypto/BTC

# Start a map game
curl -H "Authorization: Bearer YOUR_API_KEY" http://your-server-address:5001/api/game/map

# Submit an answer
curl -X POST -H "Authorization: Bearer YOUR_API_KEY" -H "Content-Type: application/json" \
  -d '{"session_id": "1a2b3c4d5e6f7g8h", "answer": "Country1"}' \
  http://your-server-address:5001/api/game/answer
```

### JavaScript

```javascript
// Get health status
fetch('http://your-server-address:5001/api/health')
  .then(response => response.json())
  .then(data => console.log(data));

// Get Bitcoin price
fetch('http://your-server-address:5001/api/prices/crypto/BTC', {
  headers: {
    'Authorization': 'Bearer YOUR_API_KEY'
  }
})
  .then(response => response.json())
  .then(data => console.log(data));

// Start a map game
fetch('http://your-server-address:5001/api/game/map', {
  headers: {
    'Authorization': 'Bearer YOUR_API_KEY'
  }
})
  .then(response => response.json())
  .then(data => console.log(data));

// Submit an answer
fetch('http://your-server-address:5001/api/game/answer', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer YOUR_API_KEY',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    session_id: '1a2b3c4d5e6f7g8h',
    answer: 'Country1'
  })
})
  .then(response => response.json())
  .then(data => console.log(data));
```
