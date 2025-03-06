"""
API Server for Telegram Bot

This module provides a REST API that exposes the functionality of the Telegram bot
for use by external applications, such as a web interface.
"""

import os
import json
import logging
import secrets
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import threading
import sys
import time
from datetime import datetime

# Add the parent directory to the path to import from the bot's modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import bot-related modules
from price_func.coinmarketcap_api import CoinMarketCapAPI
from price_func.alphavantage_api import AlphaVantageAPI
from price_func.finnhub_api import FinnhubAPI
from price_func.vietnam_stock_api import VietnamStockAPI
from price_func.utils import format_price_message
from country_game.game_handler import GameHandler
from country_game import leaderboard_db

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('api_server.log')
    ])
logger = logging.getLogger(__name__)

# Bot version from the main bot
BOT_VERSION = "1.3"

# Initialize API clients
try:
    crypto_api = CoinMarketCapAPI()
    stock_api = AlphaVantageAPI()
    finnhub_api = FinnhubAPI()
    vietnam_stock_api = VietnamStockAPI()
    game_handler = GameHandler(bot_version=BOT_VERSION)
except Exception as e:
    logger.error(f"Failed to initialize API clients: {str(e)}")
    raise

# API key for authentication
# In production, this should be stored securely
API_KEY = os.environ.get('API_KEY', secrets.token_hex(16))
logger.info(f"API Server initialized with API key: {API_KEY[:5]}...")

# Store active game sessions
game_sessions = {}


class APIRequestHandler(BaseHTTPRequestHandler):
    """Handler for API requests"""

    def _send_response(self, status_code, content, content_type="application/json"):
        """Send a response with the specified status code and content"""
        self.send_response(status_code)
        self.send_header('Content-type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')  # Allow CORS
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

        if isinstance(content, dict):
            content = json.dumps(content)

        self.wfile.write(content.encode())

    def _verify_api_key(self):
        """Verify that the API key is valid"""
        auth_header = self.headers.get('Authorization')
        query_components = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        query_api_key = query_components.get('api_key', [None])[0]

        if auth_header and auth_header.startswith('Bearer '):
            provided_key = auth_header.split(' ')[1]
        elif query_api_key:
            provided_key = query_api_key
        else:
            return False

        return provided_key == API_KEY

    def _parse_json_body(self):
        """Parse the JSON body of a request"""
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length > 0:
            body = self.rfile.read(content_length)
            return json.loads(body)
        return {}

    def _handle_health(self):
        """Handle health check requests"""
        response = {
            "status": "ok",
            "version": BOT_VERSION,
            "timestamp": datetime.now().isoformat()
        }
        self._send_response(200, response)

    def _handle_crypto_price(self, path_parts):
        """Handle cryptocurrency price requests"""
        if len(path_parts) > 4:
            # Get price for a specific cryptocurrency
            symbol = path_parts[4].upper()
            try:
                logger.info(f"API: Fetching price for cryptocurrency: {symbol}")
                price_data = crypto_api.get_price(symbol)
                logger.info(f"API: Received crypto price data: {price_data}")
                if not price_data or "error" in price_data:
                    error_msg = f"Could not find cryptocurrency: {symbol}"
                    logger.error(f"API: {error_msg}")
                    self._send_response(404, {
                        "error": error_msg,
                        "message": "Try using the cryptocurrency symbol (e.g., BTC, BNB)"
                    })
                    return

                response = {
                    "status": "success",
                    "data": price_data,
                    "message": format_price_message(price_data)
                }
                self._send_response(200, response)
            except Exception as e:
                logger.error(f"Error getting crypto price: {str(e)}")
                self._send_response(500, {"error": str(e)})
        else:
            # Get prices for default cryptocurrencies
            try:
                logger.info("API: Fetching prices for default cryptocurrencies")
                price_data = crypto_api.get_prices()
                logger.info(f"API: Received crypto prices data: {price_data}")
                response = {
                    "status": "success",
                    "data": price_data,
                    "message": format_price_message(price_data)
                }
                self._send_response(200, response)
            except Exception as e:
                logger.error(f"Error getting crypto prices: {str(e)}")
                self._send_response(500, {"error": str(e)})

    def _handle_stock_price(self, path_parts):
        """Handle stock price requests"""
        if len(path_parts) > 4:
            # Get price for a specific stock
            symbol = path_parts[4].upper()
            logger.info(f"API: Fetching price for stock: {symbol}")
            try:
                price_data = stock_api.get_stock_price(symbol)
                logger.info(f"API: Received stock price data: {price_data}")

                # If AlphaVantage fails or hits rate limit, try Finnhub
                if isinstance(price_data, dict) and "error" in price_data and "rate limit" in price_data["error"].lower():
                    logger.info("AlphaVantage rate limited, falling back to Finnhub")
                    price_data = finnhub_api.get_stock_price(symbol)
                    logger.info(f"API: Finnhub data: {price_data}")

                if isinstance(price_data, dict) and "error" in price_data:
                    self._send_response(404, {
                        "error": f"Could not find stock: {symbol}",
                        "message": "Try using the stock symbol (e.g., AAPL, TSLA)"
                    })
                    return

                response = {
                    "status": "success",
                    "data": price_data,
                    "message": format_price_message(price_data)
                }
                self._send_response(200, response)
            except Exception as e:
                logger.error(f"Error getting stock price: {str(e)}")
                self._send_response(500, {"error": str(e)})
        else:
            # Get prices for default stocks
            try:
                logger.info("API: Fetching prices for default stocks")
                price_data = stock_api.get_stock_prices()
                logger.info(f"API: Received stock prices data: {price_data}")

                # Check for rate limit or incomplete data
                is_rate_limited = (isinstance(price_data, dict) and "error" in price_data and "rate limit" in price_data["error"].lower())

                if is_rate_limited:
                    logger.info("AlphaVantage rate limited, falling back to Finnhub")
                    finnhub_data = finnhub_api.get_stock_prices()
                    logger.info(f"API: Finnhub data: {finnhub_data}")

                    # If Finnhub data is valid, use it
                    if isinstance(finnhub_data, dict) and "error" not in finnhub_data:
                        price_data = finnhub_data

                response = {
                    "status": "success",
                    "data": price_data,
                    "message": format_price_message(price_data)
                }
                self._send_response(200, response)
            except Exception as e:
                logger.error(f"Error getting stock prices: {str(e)}")
                self._send_response(500, {"error": str(e)})

    def _handle_vn_stock_price(self, path_parts):
        """Handle Vietnam stock price requests"""
        if len(path_parts) > 4:
            # Get price for a specific Vietnam stock
            symbol = path_parts[4].upper()
            logger.info(f"API: Fetching price for Vietnam stock: {symbol}")
            try:
                price_data = vietnam_stock_api.get_stock_price(symbol)
                logger.info(f"API: Received Vietnam stock price data: {price_data}")

                if isinstance(price_data, dict) and "error" in price_data:
                    self._send_response(404, {
                        "error": f"Could not find Vietnam stock: {symbol}",
                        "message": "Try using the stock symbol (e.g., VNM, HPG)"
                    })
                    return

                response = {
                    "status": "success",
                    "data": price_data,
                    "message": format_price_message(price_data)
                }
                self._send_response(200, response)
            except Exception as e:
                logger.error(f"Error getting Vietnam stock price: {str(e)}")
                self._send_response(500, {"error": str(e)})
        else:
            # Get prices for default Vietnam stocks
            try:
                logger.info("API: Fetching prices for default Vietnam stocks")
                from price_func.config import DEFAULT_VN_STOCKS
                price_data = vietnam_stock_api.get_stock_prices(DEFAULT_VN_STOCKS)
                logger.info(f"API: Received Vietnam stock prices data: {price_data}")

                response = {
                    "status": "success",
                    "data": price_data,
                    "message": format_price_message(price_data)
                }
                self._send_response(200, response)
            except Exception as e:
                logger.error(f"Error getting Vietnam stock prices: {str(e)}")
                self._send_response(500, {"error": str(e)})

    def _handle_game(self, path_parts, method):
        """Handle game-related requests"""
        if method == "GET":
            if len(path_parts) > 3:
                game_mode = path_parts[3].lower()
                if game_mode in ["map", "flag", "capital", "cap"]:
                    # Create a new game session
                    session_id = secrets.token_hex(8)

                    # In a full implementation, we would need to:
                    # 1. Create a game session
                    # 2. Generate a question
                    # 3. Return the question data

                    # For now, we'll return placeholder data
                    game_data = {
                        "session_id": session_id,
                        "mode": game_mode,
                        "question": {
                            "options": ["Country1", "Country2", "Country3", "Country4"],
                            "image_url": f"/static/assets/placeholder_{game_mode}.png",
                            "timer": 30
                        }
                    }

                    # Store the session
                    game_sessions[session_id] = {
                        "mode": game_mode,
                        "created_at": time.time(),
                        "correct_answer": "Country1"  # Placeholder
                    }

                    self._send_response(200, {
                        "status": "success",
                        "data": game_data
                    })
                elif game_mode == "leaderboard" or game_mode == "lb":
                    # Get leaderboard data
                    try:
                        leaderboard_data = leaderboard_db.get_leaderboard(limit=10)
                        self._send_response(200, {
                            "status": "success",
                            "data": {
                                "leaderboard": leaderboard_data
                            }
                        })
                    except Exception as e:
                        logger.error(f"Error getting leaderboard: {str(e)}")
                        self._send_response(500, {"error": str(e)})
                elif game_mode == "help":
                    # Return game help information
                    help_data = {
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
                            {
                                "name": "/g flag",
                                "description": "Play the flag guessing game"
                            },
                            {
                                "name": "/g cap",
                                "description": "Play the capital guessing game"
                            },
                            {
                                "name": "/g lb",
                                "description": "View the leaderboard"
                            }
                        ]
                    }
                    self._send_response(200, {
                        "status": "success",
                        "data": help_data
                    })
                else:
                    self._send_response(400, {
                        "error": "Invalid game mode",
                        "message": "Valid modes are: map, flag, capital, cap, leaderboard, lb, help"
                    })
            else:
                self._send_response(400, {
                    "error": "Missing game mode",
                    "message": "Please specify a game mode: /api/game/<mode>"
                })
        elif method == "POST":
            # Handle answer submission
            if len(path_parts) > 3 and path_parts[3] == "answer":
                body = self._parse_json_body()
                session_id = body.get("session_id")
                answer = body.get("answer")

                if not session_id or not answer:
                    self._send_response(400, {
                        "error": "Missing required parameters",
                        "message": "session_id and answer are required"
                    })
                    return

                # Check if the session exists
                if session_id not in game_sessions:
                    self._send_response(404, {
                        "error": "Session not found",
                        "message": "The game session may have expired"
                    })
                    return

                # In a full implementation, we would:
                # 1. Validate the answer against the current game
                # 2. Update the user's stats if the user is authenticated
                # 3. Return the result

                session = game_sessions[session_id]
                is_correct = answer == session["correct_answer"]  # Placeholder logic

                # Return result
                self._send_response(200, {
                    "status": "success",
                    "data": {
                        "is_correct": is_correct,
                        "correct_answer": session["correct_answer"],
                        "explanation": f"The correct answer is {session['correct_answer']}",
                        "country_details": {
                            "name": session["correct_answer"],
                            "capital": "Capital City",
                            "region": "Region",
                            "population": 1000000,
                            "area": 100000
                        }
                    }
                })

                # Clean up the session
                del game_sessions[session_id]
            else:
                self._send_response(400, {
                    "error": "Invalid endpoint",
                    "message": "Valid POST endpoints: /api/game/answer"
                })

    def _handle_help(self):
        """Handle help requests"""
        help_data = {
            "version": BOT_VERSION,
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
                {
                    "path": "/api/prices/crypto/<symbol>",
                    "method": "GET",
                    "description": "Get price for a specific cryptocurrency"
                },
                {
                    "path": "/api/prices/stock",
                    "method": "GET",
                    "description": "Get prices for default stocks"
                },
                {
                    "path": "/api/prices/stock/<symbol>",
                    "method": "GET",
                    "description": "Get price for a specific stock"
                },
                {
                    "path": "/api/prices/vn",
                    "method": "GET",
                    "description": "Get prices for default Vietnam stocks"
                },
                {
                    "path": "/api/prices/vn/<symbol>",
                    "method": "GET",
                    "description": "Get price for a specific Vietnam stock"
                },
                {
                    "path": "/api/game/<mode>",
                    "method": "GET",
                    "description": "Start a new game (mode: map, flag, capital, cap) or get leaderboard/help (mode: leaderboard, lb, help)"
                },
                {
                    "path": "/api/game/answer",
                    "method": "POST",
                    "description": "Submit an answer for a game",
                    "body": {
                        "session_id": "string",
                        "answer": "string"
                    }
                }
            ],
            "authentication": {
                "method": "Bearer token or api_key query parameter",
                "example": "Authorization: Bearer YOUR_API_KEY or ?api_key=YOUR_API_KEY"
            },
            "description": "This API provides access to the Telegram bot functionality, including price checks and country guessing games."
        }
        self._send_response(200, help_data)

    def _handle_user(self, path_parts, method):
        """Handle user-related requests"""
        if method == "POST":
            if len(path_parts) > 3 and path_parts[3] == "guest":
                # Create a new guest user
                user_id = f"guest_{secrets.token_hex(8)}"
                user_name = f"Guest_{secrets.token_hex(4)}"

                self._send_response(200, {
                    "status": "success",
                    "data": {
                        "user_id": user_id,
                        "user_name": user_name
                    }
                })
            else:
                self._send_response(400, {
                    "error": "Invalid endpoint",
                    "message": "Valid POST endpoints: /api/user/guest"
                })
        else:
            self._send_response(405, {
                "error": "Method not allowed",
                "message": "Only POST is supported for this endpoint"
            })

    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def do_GET(self):
        """Handle GET requests"""
        try:
            path = urllib.parse.urlparse(self.path).path
            path_parts = path.split('/')

            # Public endpoints that don't require authentication
            if path == '/api/health':
                self._handle_health()
                return

            # All other endpoints require authentication
            if not self._verify_api_key():
                self._send_response(401, {
                    "error": "Unauthorized",
                    "message": "Invalid or missing API key"
                })
                return

            # API endpoints
            if path == '/api' or path == '/api/':
                self._handle_help()
            elif path.startswith('/api/prices/crypto'):
                self._handle_crypto_price(path_parts)
            elif path.startswith('/api/prices/stock'):
                self._handle_stock_price(path_parts)
            elif path.startswith('/api/prices/vn'):
                self._handle_vn_stock_price(path_parts)
            elif path.startswith('/api/game'):
                self._handle_game(path_parts, "GET")
            elif path == '/api/help':
                self._handle_help()
            else:
                self._send_response(404, {
                    "error": "Not found",
                    "message": f"Endpoint {path} not found"
                })
        except Exception as e:
            logger.error(f"Error handling GET request: {str(e)}")
            self._send_response(500, {"error": str(e)})

    def do_POST(self):
        """Handle POST requests"""
        try:
            path = urllib.parse.urlparse(self.path).path
            path_parts = path.split('/')

            # All POST endpoints require authentication
            if not self._verify_api_key():
                self._send_response(401, {
                    "error": "Unauthorized",
                    "message": "Invalid or missing API key"
                })
                return

            # API endpoints
            if path.startswith('/api/game'):
                self._handle_game(path_parts, "POST")
            elif path.startswith('/api/user'):
                self._handle_user(path_parts, "POST")
            else:
                self._send_response(404, {
                    "error": "Not found",
                    "message": f"Endpoint {path} not found"
                })
        except Exception as e:
            logger.error(f"Error handling POST request: {str(e)}")
            self._send_response(500, {"error": str(e)})


def run_api_server(port=5001):
    """Run the API server on the specified port"""
    try:
        server = HTTPServer(('0.0.0.0', port), APIRequestHandler)
        logger.info(f"Starting API server on port {port}")
        server.serve_forever()
    except Exception as e:
        logger.error(f"Failed to start API server: {str(e)}")
        raise


def start_api_server_thread(port=5001):
    """Start the API server in a separate thread"""
    api_thread = threading.Thread(target=run_api_server, args=(port,), daemon=True)
    api_thread.start()
    logger.info("API server thread started")
    return api_thread


if __name__ == "__main__":
    # If run directly, start the API server
    run_api_server()