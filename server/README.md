# Telegram Bot API Server

This directory contains the API server implementation for the Telegram bot. The API server provides a REST API that allows external applications, such as a web interface, to interact with the bot's functionality.

## Overview

The API server exposes the following functionality:

1. **Price Checking**: Get cryptocurrency, stock, and Vietnam stock prices
2. **Country Guessing Game**: Play the map, flag, and capital guessing games
3. **Leaderboard**: View the game leaderboard
4. **User Management**: Create guest users and (future) authenticate with wallets

## Files

- `api_server.py`: The main API server implementation
- `API_DOCUMENTATION.md`: Detailed documentation of the API endpoints
- `README.md`: This file

## Getting Started

The API server is automatically started alongside the main bot. It runs on port 5001 by default, but you can change this by setting the `API_PORT` environment variable.

To get the API key, you can make a request to the bot's HTTP server (port 5000) at `/api-key`, but only from localhost:

```bash
curl http://localhost:5000/api-key
```

This will return the API key that you need to use for authentication.

## Authentication

All API endpoints (except for the health check) require authentication using an API key. You can provide the API key in one of two ways:

1. As a Bearer token in the Authorization header:
   ```
   Authorization: Bearer YOUR_API_KEY
   ```

2. As a query parameter:
   ```
   ?api_key=YOUR_API_KEY
   ```

## API Documentation

For detailed documentation of the API endpoints, see the [API_DOCUMENTATION.md](API_DOCUMENTATION.md) file.

## Example Usage

Here's a simple example of how to use the API to get the price of Bitcoin:

```bash
# Get Bitcoin price
curl -H "Authorization: Bearer YOUR_API_KEY" http://your-server-address:5001/api/prices/crypto/BTC
```

Here's how to start a map game:

```bash
# Start a map game
curl -H "Authorization: Bearer YOUR_API_KEY" http://your-server-address:5001/api/game/map
```

## Building a Web Interface

If you're building a web interface that will connect to this API, here are some tips:

1. Use the `/api/health` endpoint to check if the API server is running.
2. Use the `/api/user/guest` endpoint to create a guest user session.
3. Use the `/api/game/<mode>` endpoint to start a game in the specified mode.
4. Use the `/api/game/answer` endpoint to submit an answer for a game.

## Security Considerations

The API key is generated when the server starts and is printed in the logs. For production use, you should set a fixed API key using the `API_KEY` environment variable.

For a public-facing API, consider implementing rate limiting and further authentication measures.

## Future Enhancements

1. **User Authentication**: Implement wallet-based authentication for persistent user sessions
2. **Rate Limiting**: Add rate limiting to prevent abuse
3. **WebSocket Support**: Add WebSocket support for real-time updates
4. **Swagger Documentation**: Add interactive API documentation with Swagger
