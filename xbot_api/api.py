"""
XBot API Module - REST API for accessing Telegram Bot functionality
This module provides endpoints for:
- Fetching cryptocurrency prices
- Fetching stock prices
- Fetching Vietnam stock prices
- Interacting with country game (getting questions, submitting answers)
- Submitting game scores to the leaderboard
"""

import os
import json
import time
import uuid
import random
import logging
from typing import Dict, List, Optional, Any, Tuple
from functools import wraps

from flask import Flask, request, jsonify
from flask_cors import CORS

# Custom imports
from country_game.game_handler import GameHandler
from price_func.coinmarketcap_api import CoinMarketCapAPI
from price_func.alphavantage_api import AlphaVantageAPI
from price_func.finnhub_api import FinnhubAPI
from price_func.vietnam_stock_api import VietnamStockAPI
from xbot_api.utils import get_api_key, prepare_image_response, format_country_data

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all endpoints

# Initialize APIs
crypto_api = CoinMarketCapAPI()
stock_api = AlphaVantageAPI()
finnhub_api = FinnhubAPI()
vietnam_api = VietnamStockAPI()

# Initialize game handler
game_handler = GameHandler()

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Active games dictionary
active_games = {}

def validate_api_key(request_api_key: str) -> bool:
    """Validate the provided API key against the expected API key"""
    # Get the expected API key from utils to ensure consistency
    from xbot_api.utils import get_api_key
    expected_api_key = get_api_key()
    return expected_api_key == request_api_key

def require_api_key(func):
    """Decorator to require API key for certain routes"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Get API key from header or query parameters
        api_key = request.headers.get("X-API-Key") or request.args.get("api_key")
        
        # Validate API key
        if not api_key or not validate_api_key(api_key):
            return jsonify({"error": "Invalid or missing API key"}), 401
        
        return func(*args, **kwargs)
    return wrapper

# --- API Routes ---

@app.route("/", methods=["GET"])
def root():
    """Root endpoint for health checks"""
    return jsonify({
        "status": "ok",
        "message": "XBot API and Telegram Bot Service",
        "version": "1.0.0"
    })

@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint for automated monitoring"""
    return jsonify({
        "status": "ok",
        "message": "Service is running",
        "components": {
            "api": "ok",
            "bot": "ok"
        }
    })

@app.route("/api/health", methods=["GET"])
def health_check():
    """API-specific health check endpoint"""
    return jsonify({
        "status": "ok",
        "message": "XBot API is running"
    })

# --- Cryptocurrency Endpoints ---

@app.route("/api/crypto/price", methods=["GET"])
@require_api_key
def get_crypto_price():
    """Get cryptocurrency price information
    
    Query Parameters:
    - symbol: The cryptocurrency symbol (e.g., BTC, ETH)
    
    Returns:
    - JSON with price details or error message
    """
    symbol = request.args.get("symbol")
    if not symbol:
        return jsonify({"error": "Missing required parameter: symbol"}), 400
    
    try:
        result = crypto_api.get_price(symbol.upper())
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting crypto price: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/crypto/prices", methods=["GET"])
@require_api_key
def get_crypto_prices():
    """Get prices for multiple cryptocurrencies
    
    Query Parameters:
    - symbols: Comma-separated list of cryptocurrency symbols (optional)
    
    Returns:
    - JSON with price details for multiple cryptocurrencies
    """
    symbols_param = request.args.get("symbols")
    symbols = symbols_param.split(",") if symbols_param else []
    
    try:
        result = crypto_api.get_prices(symbols)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting crypto prices: {e}")
        return jsonify({"error": str(e)}), 500

# --- Stock Endpoints ---

@app.route("/api/stock/price", methods=["GET"])
@require_api_key
def get_stock_price():
    """Get stock price information
    
    Query Parameters:
    - symbol: The stock symbol (e.g., AAPL, MSFT)
    
    Returns:
    - JSON with price details or error message
    """
    symbol = request.args.get("symbol")
    if not symbol:
        return jsonify({"error": "Missing required parameter: symbol"}), 400
    
    try:
        # Try with Alpha Vantage first
        result = stock_api.get_stock_price(symbol.upper())
        
        # Fall back to Finnhub if Alpha Vantage fails or is rate limited
        if "error" in result:
            result = finnhub_api.get_stock_price(symbol.upper())
            
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting stock price: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/stock/prices", methods=["GET"])
@require_api_key
def get_stock_prices():
    """Get prices for multiple stocks
    
    Returns:
    - JSON with price details for default stock list
    """
    try:
        # Try with Alpha Vantage first
        result = stock_api.get_stock_prices()
        
        # Fall back to Finnhub if Alpha Vantage fails or is rate limited
        if "error" in result:
            result = finnhub_api.get_stock_prices()
            
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting stock prices: {e}")
        return jsonify({"error": str(e)}), 500

# --- Vietnam Stock Endpoints ---

@app.route("/api/vietnam/stock/price", methods=["GET"])
@require_api_key
def get_vietnam_stock_price():
    """Get Vietnam stock price information
    
    Query Parameters:
    - symbol: The Vietnam stock symbol
    
    Returns:
    - JSON with price details or error message
    """
    symbol = request.args.get("symbol")
    if not symbol:
        return jsonify({"error": "Missing required parameter: symbol"}), 400
    
    try:
        result = vietnam_api.get_stock_price(symbol.upper())
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting Vietnam stock price: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/vietnam/stock/prices", methods=["GET"])
@require_api_key
def get_vietnam_stock_prices():
    """Get prices for multiple Vietnam stocks
    
    Query Parameters:
    - symbols: Comma-separated list of Vietnam stock symbols (optional)
    
    Returns:
    - JSON with price details for Vietnam stocks
    """
    symbols_param = request.args.get("symbols")
    symbols = symbols_param.split(",") if symbols_param else []
    
    try:
        result = vietnam_api.get_stock_prices(symbols)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting Vietnam stock prices: {e}")
        return jsonify({"error": str(e)}), 500

# --- Game Endpoints ---

def get_database_connection():
    """
    Get a database connection safely
    
    Returns:
        sqlite3.Connection: Database connection
    """
    try:
        # Try to access the connection from game_handler
        return game_handler._conn
    except AttributeError:
        # If that fails, create a new connection
        try:
            import sqlite3
            conn = sqlite3.connect("country_game/database/countries.db")
            conn.row_factory = sqlite3.Row
            return conn
        except Exception as e:
            logger.error(f"Error creating database connection: {e}")
            return None

def get_countries():
    """
    Safely get the countries data from the game handler
    
    Returns:
        List[Dict]: List of country dictionaries
    """
    try:
        # Try to access the _countries attribute directly
        return game_handler._countries
    except AttributeError:
        # If that fails, try to access through the database connection
        try:
            conn = get_database_connection()
            if not conn:
                return []
                
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM countries")
            columns = [col[0] for col in cursor.description]
            
            countries = []
            for row in cursor.fetchall():
                country = dict(zip(columns, row))
                countries.append(country)
                
            return countries
        except Exception as e:
            logger.error(f"Error getting countries data: {e}")
            return []

def get_user_stats_data(user_id):
    """
    Safely get user stats from the game handler
    
    Args:
        user_id (int): User ID
        
    Returns:
        Dict: User stats dictionary
    """
    try:
        # Try to access user stats directly
        return game_handler._user_stats.get(user_id, {})
    except AttributeError:
        # If that fails, return an empty dict
        return {}

@app.route("/api/game/new", methods=["GET"])
@require_api_key
def get_new_game():
    """Get a new game question
    
    Query Parameters:
    - mode: Game mode ('map', 'flag', or 'cap')
    
    Returns:
    - JSON with game question details
    """
    mode = request.args.get("mode", "map")
    if mode not in ["map", "flag", "cap"]:
        return jsonify({"error": f"Invalid game mode: {mode}. Must be 'map', 'flag', or 'cap'"}), 400
    
    try:
        # Get countries data
        countries = get_countries()
        if not countries:
            return jsonify({"error": "Failed to get countries data"}), 500
            
        # Get a random country
        country = random.choice(countries)
        
        # Generate options - either use the method or create our own
        try:
            options = game_handler._generate_options(country, mode)
        except AttributeError:
            # Fallback if method is not accessible
            if mode in ["map", "flag"]:
                # For map/flag modes, options are country names
                country_names = [c["name"] for c in countries]
                options = [country["name"]]  # Add correct answer
                
                # Add random wrong answers
                other_countries = [c["name"] for c in countries if c["name"] != country["name"]]
                options.extend(random.sample(other_countries, min(4, len(other_countries))))
                random.shuffle(options)
            else:
                # For capital mode, options are capital cities
                capitals = [c["capital"] for c in countries if c["capital"]]
                options = [country["capital"]]  # Add correct answer
                
                # Add random wrong answers
                other_capitals = [c["capital"] for c in countries 
                                if c["capital"] and c["capital"] != country["capital"]]
                options.extend(random.sample(other_capitals, min(4, len(other_capitals))))
                random.shuffle(options)
        
        # Create a unique game ID
        game_id = int(time.time() * 1000)
        
        # Store the game data
        active_games[game_id] = {
            "country_id": country.get("id", 0),  # Use get with default to avoid KeyError
            "mode": mode,
            "correct_answer": country.get("name", "") if mode in ["map", "flag"] else country.get("capital", ""),
            "timestamp": time.time()
        }
        
        # Prepare response
        response = {
            "game_id": game_id,
            "mode": mode,
            "options": options,
            "country_id": country.get("id", 0),
            "question": (
                "Which country is highlighted on this map?" if mode == "map" 
                else "Which country does this flag belong to?" if mode == "flag"
                else f"What is the capital of {country.get('name', '')}?"
            ),
            "country": format_country_data(country)
        }
        
        # Add image data if needed
        try:
            if mode == "map":
                country_name = country.get("name", "")
                if country_name:
                    map_image_path = f"country_game/images/wiki_all_map_400pi/{country_name.replace(' ', '_')}_locator_map.png"
                    response.update(prepare_image_response(map_image_path))
            elif mode == "flag":
                country_name = country.get("name", "")
                if country_name:
                    flag_image_path = f"country_game/images/wiki_flag/{country_name.replace(' ', '_')}_flag.png"
                    response.update(prepare_image_response(flag_image_path))
        except Exception as img_err:
            logger.warning(f"Error preparing image response: {img_err}")
        
        return jsonify(response)
    except Exception as e:
        logger.error(f"Error creating new game: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/game/verify", methods=["POST"])
@require_api_key
def verify_answer():
    """Verify a game answer
    
    Request Body (JSON):
    - game_id: The game ID returned by the /api/game/new endpoint
    - country_id: The country ID
    - mode: Game mode ('map', 'flag', or 'cap')
    - answer: The user's answer
    - user_id: Unique identifier for the user
    - user_name: User's display name
    - login_method: How the user is authenticated (default: 'web')
    
    Returns:
    - JSON with verification result and country details
    """
    data = request.json
    if not data:
        return jsonify({"error": "Missing request body"}), 400
    
    required_fields = ["game_id", "country_id", "mode", "answer", "user_id"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    # Get game data
    game_id = data.get("game_id")
    game_data = active_games.get(game_id)
    
    if not game_data:
        return jsonify({"error": "Game not found or expired"}), 404
    
    # Verify answer
    user_answer = data.get("answer")
    correct_answer = game_data.get("correct_answer")
    is_correct = user_answer.lower() == correct_answer.lower()
    
    # Get country data
    country_id = data.get("country_id")
    countries = get_countries()
    country = next((c for c in countries if c.get("id", 0) == country_id), None)
    
    if not country:
        return jsonify({"error": f"Country with ID {country_id} not found"}), 404
    
    # Update user stats
    user_id = data.get("user_id")
    user_name = data.get("user_name", "Anonymous")
    login_method = data.get("login_method", "web")
    
    # Convert user_id to int for game_handler
    try:
        numeric_user_id = int(user_id)
    except ValueError:
        # If user_id is not an integer, hash it to create a numeric ID
        numeric_user_id = hash(user_id) % (10 ** 10)
    
    # Update user stats
    metadata = {
        "user_name": user_name,
        "login_method": login_method
    }
    
    # Add wallet_address if provided
    wallet_address = data.get("wallet_address")
    if wallet_address:
        metadata["wallet_address"] = wallet_address
    
    # Try to update stats in database using game_handler methods
    try:
        game_handler._update_user_stats(
            numeric_user_id, 
            is_correct, 
            data.get("mode"),
            user_name
        )
        
        # Save user stats to database
        user_stats = get_user_stats_data(numeric_user_id)
        game_mode = data.get("mode")
        
        # Get the specific game mode stats or create default if not exists
        if game_mode in user_stats:
            mode_stats = user_stats.get(game_mode, {"total": 1, "correct": 1 if is_correct else 0})
        else:
            # If we don't have stats for this mode yet, initialize with this game's result
            mode_stats = {"total": 1, "correct": 1 if is_correct else 0}
            
        game_handler._save_user_stats_to_database(
            numeric_user_id, 
            game_mode, 
            mode_stats,
            metadata
        )
    except Exception as e:
        # If that fails, directly update the database
        logger.warning(f"Failed to update stats using game_handler: {e}")
        try:
            conn = get_database_connection()
            if conn:
                cursor = conn.cursor()
                # Check if user exists
                cursor.execute(
                    "SELECT * FROM user_stats WHERE user_id = ? AND game_mode = ?",
                    (numeric_user_id, data.get("mode"))
                )
                row = cursor.fetchone()
                
                current_time = int(time.time())
                
                if row:
                    # Update existing record
                    cursor.execute(
                        """
                        UPDATE user_stats SET 
                            total = total + 1,
                            correct = correct + ?,
                            user_name = ?,
                            login_method = ?
                        WHERE user_id = ? AND game_mode = ?
                        """,
                        (1 if is_correct else 0, user_name, login_method, numeric_user_id, data.get("mode"))
                    )
                else:
                    # Insert new record
                    cursor.execute(
                        """
                        INSERT INTO user_stats (
                            user_id, game_mode, total, correct,
                            user_name, login_method, first_play_timestamp
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (numeric_user_id, data.get("mode"), 1, 1 if is_correct else 0,
                         user_name, login_method, current_time)
                    )
                
                # Add wallet address if provided
                if wallet_address:
                    cursor.execute(
                        "UPDATE user_stats SET wallet_address = ? WHERE user_id = ?",
                        (wallet_address, numeric_user_id)
                    )
                    
                conn.commit()
        except Exception as db_err:
            logger.error(f"Failed to update database directly: {db_err}")
    
    # Get updated user stats directly from database
    mode_stats = {"total": 0, "correct": 0}
    try:
        conn = get_database_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT total, correct FROM user_stats WHERE user_id = ? AND game_mode = ?",
                (numeric_user_id, data.get("mode"))
            )
            row = cursor.fetchone()
            if row:
                total, correct = row
                mode_stats = {"total": total, "correct": correct}
    except Exception as stats_err:
        logger.error(f"Failed to get user stats from database: {stats_err}")
    
    # Clean up game data
    del active_games[game_id]
    
    return jsonify({
        "is_correct": is_correct,
        "correct_answer": correct_answer,
        "country": format_country_data(country),
        "user_stats": {
            "total": mode_stats.get("total", 0),
            "correct": mode_stats.get("correct", 0),
            "accuracy": (mode_stats.get("correct", 0) / mode_stats.get("total", 1) * 100) if mode_stats.get("total", 0) > 0 else 0
        }
    })

@app.route("/api/game/leaderboard", methods=["GET"])
@require_api_key
def get_leaderboard():
    """Get the game leaderboard
    
    Query Parameters:
    - mode: Filter by game mode ('map', 'flag', 'cap', or 'all')
    - limit: Maximum number of entries to return (default: 10)
    
    Returns:
    - JSON with leaderboard data
    """
    mode = request.args.get("mode", "all")
    limit_str = request.args.get("limit", "10")
    
    try:
        limit = int(limit_str)
    except ValueError:
        return jsonify({"error": f"Invalid limit: {limit_str}. Must be a number."}), 400
    
    if mode not in ["map", "flag", "cap", "all"]:
        return jsonify({"error": f"Invalid game mode: {mode}. Must be 'map', 'flag', 'cap', or 'all'"}), 400
    
    try:
        # Query database for leaderboard data
        conn = get_database_connection()
        if not conn:
            return jsonify({"error": "Failed to connect to database"}), 500
        cursor = conn.cursor()
        
        if mode == "all":
            # For 'all' mode, get aggregate stats across all modes
            query = """
            SELECT 
                user_id, 
                user_name, 
                login_method,
                wallet_address,
                first_play_timestamp,
                SUM(total) as total, 
                SUM(correct) as correct
            FROM user_stats
            GROUP BY user_id
            ORDER BY correct DESC, total ASC
            LIMIT ?
            """
            cursor.execute(query, (limit,))
        else:
            # For specific mode, get stats for that mode only
            query = """
            SELECT 
                user_id, 
                user_name, 
                login_method,
                wallet_address,
                first_play_timestamp,
                total, 
                correct
            FROM user_stats
            WHERE game_mode = ?
            ORDER BY correct DESC, total ASC
            LIMIT ?
            """
            cursor.execute(query, (mode, limit))
        
        leaderboard_data = []
        for i, row in enumerate(cursor.fetchall()):
            user_id, user_name, login_method, wallet_address, joined, total, correct = row
            
            # Calculate accuracy
            accuracy = (correct / total * 100) if total > 0 else 0
            
            # Add entry to leaderboard
            leaderboard_data.append({
                "rank": i + 1,
                "user_id": user_id,
                "user_name": user_name or "Anonymous",
                "login_method": login_method or "unknown",
                "wallet_address": wallet_address,
                "joined": joined,
                "accuracy": accuracy,
                "total": total,
                "correct": correct
            })
            
            # Add mode-specific stats if 'all' mode
            if mode == "all":
                modes_data = {}
                for game_mode in ["map", "flag", "cap"]:
                    mode_query = """
                    SELECT 
                        total, 
                        correct
                    FROM user_stats
                    WHERE user_id = ? AND game_mode = ?
                    """
                    cursor.execute(mode_query, (user_id, game_mode))
                    mode_row = cursor.fetchone()
                    
                    if mode_row:
                        mode_total, mode_correct = mode_row
                        mode_accuracy = (mode_correct / mode_total * 100) if mode_total > 0 else 0
                        modes_data[game_mode] = {
                            "total": mode_total,
                            "correct": mode_correct,
                            "accuracy": mode_accuracy
                        }
                        
                leaderboard_data[i]["modes"] = modes_data
        
        return jsonify({"leaderboard": leaderboard_data})
    except Exception as e:
        logger.error(f"Error getting leaderboard: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/game/user-stats", methods=["GET"])
@require_api_key
def get_user_stats():
    """Get statistics for a specific user
    
    Query Parameters:
    - user_id: User ID to fetch stats for
    
    Returns:
    - JSON with user statistics
    """
    user_id_str = request.args.get("user_id")
    if not user_id_str:
        return jsonify({"error": "Missing required parameter: user_id"}), 400
    
    try:
        # Try to convert to int, but if it fails, use the string directly
        try:
            user_id = int(user_id_str)
        except ValueError:
            # If user_id is not an integer, hash it to create a numeric ID
            user_id = hash(user_id_str) % (10 ** 10)
        
        # Query database for user stats
        conn = get_database_connection()
        if not conn:
            return jsonify({"error": "Failed to connect to database"}), 500
        cursor = conn.cursor()
        
        # Get user metadata
        query = """
        SELECT 
            user_name, 
            login_method,
            wallet_address,
            first_play_timestamp
        FROM user_stats
        WHERE user_id = ?
        LIMIT 1
        """
        cursor.execute(query, (user_id,))
        metadata_row = cursor.fetchone()
        
        if not metadata_row:
            return jsonify({"error": f"User with ID {user_id_str} not found"}), 404
            
        user_name, login_method, wallet_address, joined = metadata_row
        
        # Get overall stats
        query = """
        SELECT 
            SUM(total) as total, 
            SUM(correct) as correct
        FROM user_stats
        WHERE user_id = ?
        """
        cursor.execute(query, (user_id,))
        overall_row = cursor.fetchone()
        
        if not overall_row or overall_row[0] is None:
            return jsonify({"error": f"No statistics found for user with ID {user_id_str}"}), 404
            
        overall_total, overall_correct = overall_row
        overall_accuracy = (overall_correct / overall_total * 100) if overall_total > 0 else 0
        
        # Get mode-specific stats
        modes_data = {}
        for game_mode in ["map", "flag", "cap"]:
            mode_query = """
            SELECT 
                total, 
                correct
            FROM user_stats
            WHERE user_id = ? AND game_mode = ?
            """
            cursor.execute(mode_query, (user_id, game_mode))
            mode_row = cursor.fetchone()
            
            if mode_row:
                mode_total, mode_correct = mode_row
                mode_accuracy = (mode_correct / mode_total * 100) if mode_total > 0 else 0
                modes_data[game_mode] = {
                    "total": mode_total,
                    "correct": mode_correct,
                    "accuracy": mode_accuracy
                }
        
        return jsonify({
            "user_id": user_id,
            "user_name": user_name or "Anonymous",
            "login_method": login_method or "unknown",
            "wallet_address": wallet_address,
            "joined": joined,
            "overall": {
                "total": overall_total,
                "correct": overall_correct,
                "accuracy": overall_accuracy
            },
            "modes": modes_data
        })
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        return jsonify({"error": str(e)}), 500