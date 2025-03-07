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
import logging
from typing import Dict, List, Optional, Union
from flask import Flask, request, jsonify
from flask_cors import CORS

# Import price functions
from price_func.coinmarketcap_api import CoinMarketCapAPI
from price_func.alphavantage_api import AlphaVantageAPI
from price_func.finnhub_api import FinnhubAPI
from price_func.vietnam_stock_api import VietnamStockAPI
from price_func.utils import format_price_message, format_error_message

# Import country game functionality
import sys
sys.path.append('.')  # Add the current directory to path
from country_game.game_handler import GameHandler

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('xbot_api')

# Initialize API clients
coin_api = CoinMarketCapAPI()
alpha_api = AlphaVantageAPI()
finnhub_api = FinnhubAPI()
vietnam_api = VietnamStockAPI()
game_handler = GameHandler()

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Create a secret API key (should be stored securely in production)
API_KEY = os.environ.get("XBOT_API_KEY", "your_development_api_key")

# Helper function to validate API key
def validate_api_key(request_api_key: str) -> bool:
    """Validate the provided API key against the expected API key"""
    return request_api_key == API_KEY

# Middleware to check API key for protected routes
def require_api_key(func):
    """Decorator to require API key for certain routes"""
    def wrapper(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key or not validate_api_key(api_key):
            return jsonify({"error": "Invalid or missing API key"}), 401
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

# Define API routes
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "ok", "message": "XBot API is running"})

@app.route('/api/crypto/price', methods=['GET'])
@require_api_key
def get_crypto_price():
    """Get cryptocurrency price information
    
    Query Parameters:
    - symbol: The cryptocurrency symbol (e.g., BTC, ETH)
    
    Returns:
    - JSON with price details or error message
    """
    symbol = request.args.get('symbol')
    if not symbol:
        return jsonify({"error": "Missing 'symbol' parameter"}), 400
    
    try:
        result = coin_api.get_price(symbol)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error fetching crypto price: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/crypto/prices', methods=['GET'])
@require_api_key
def get_crypto_prices():
    """Get prices for multiple cryptocurrencies
    
    Query Parameters:
    - symbols: Comma-separated list of cryptocurrency symbols (optional)
    
    Returns:
    - JSON with price details for multiple cryptocurrencies
    """
    symbols_str = request.args.get('symbols')
    symbols = symbols_str.split(',') if symbols_str else None
    
    try:
        result = coin_api.get_prices(symbols)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error fetching crypto prices: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/stock/price', methods=['GET'])
@require_api_key
def get_stock_price():
    """Get stock price information
    
    Query Parameters:
    - symbol: The stock symbol (e.g., AAPL, MSFT)
    
    Returns:
    - JSON with price details or error message
    """
    symbol = request.args.get('symbol')
    if not symbol:
        return jsonify({"error": "Missing 'symbol' parameter"}), 400
    
    try:
        # Try different APIs in sequence
        try:
            result = finnhub_api.get_stock_price(symbol)
        except Exception:
            result = alpha_api.get_stock_price(symbol)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error fetching stock price: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/stock/prices', methods=['GET'])
@require_api_key
def get_stock_prices():
    """Get prices for multiple stocks
    
    Returns:
    - JSON with price details for default stock list
    """
    try:
        # Try different APIs in sequence
        try:
            result = finnhub_api.get_stock_prices()
        except Exception:
            result = alpha_api.get_stock_prices()
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error fetching stock prices: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/vietnam/stock/price', methods=['GET'])
@require_api_key
def get_vietnam_stock_price():
    """Get Vietnam stock price information
    
    Query Parameters:
    - symbol: The Vietnam stock symbol
    
    Returns:
    - JSON with price details or error message
    """
    symbol = request.args.get('symbol')
    if not symbol:
        return jsonify({"error": "Missing 'symbol' parameter"}), 400
    
    try:
        result = vietnam_api.get_stock_price(symbol)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error fetching Vietnam stock price: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/vietnam/stock/prices', methods=['GET'])
@require_api_key
def get_vietnam_stock_prices():
    """Get prices for multiple Vietnam stocks
    
    Query Parameters:
    - symbols: Comma-separated list of Vietnam stock symbols (optional)
    
    Returns:
    - JSON with price details for Vietnam stocks
    """
    symbols_str = request.args.get('symbols')
    symbols = symbols_str.split(',') if symbols_str else None
    
    try:
        result = vietnam_api.get_stock_prices(symbols)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error fetching Vietnam stock prices: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/game/new', methods=['GET'])
@require_api_key
def get_new_game():
    """Get a new game question
    
    Query Parameters:
    - mode: Game mode ('map', 'flag', or 'cap')
    
    Returns:
    - JSON with game question details
    """
    mode = request.args.get('mode', 'map')
    if mode not in ['map', 'flag', 'cap']:
        return jsonify({"error": "Invalid game mode. Use 'map', 'flag', or 'cap'"}), 400
    
    try:
        # Get a random country for the game
        country = game_handler._get_random_country()
        
        # Generate options
        options = game_handler._generate_options(country, mode)
        
        # Format the response based on game mode
        response = {
            "game_id": hash(str(country) + str(options)),
            "mode": mode,
            "options": options,
            "country_id": country.get("id")
        }
        
        # Add country-specific information based on the mode
        if mode == 'map' or mode == 'cap':
            map_path = ""
            # Try to find the correct image path
            name_formats = [
                country['name'],
                country['name'].replace(' ', '_')
            ]
            
            for name in name_formats:
                test_path = f"country_game/images/wiki_all_map_400pi/{name}_locator_map.png"
                if os.path.exists(test_path):
                    map_path = test_path
                    break
            
            if not map_path:
                return jsonify({"error": f"Map image not found for {country['name']}"}), 404
                
            response["image_path"] = map_path
            response["question"] = "Which country is highlighted on this map?" if mode == 'map' else "What is the capital city of this country?"
            response["correct_answer"] = country["name"] if mode == 'map' else country["capital"]
            
        elif mode == 'flag':
            flag_path = ""
            # Try to find the correct image path
            name_formats = [
                country['name'],
                country['name'].replace(' ', '_')
            ]
            
            for name in name_formats:
                test_path = f"country_game/images/wiki_flag/{name}_flag.png"
                if os.path.exists(test_path):
                    flag_path = test_path
                    break
            
            if not flag_path:
                return jsonify({"error": f"Flag image not found for {country['name']}"}), 404
                
            response["image_path"] = flag_path
            response["question"] = "Which country does this flag belong to?"
            response["correct_answer"] = country["name"]
        
        # Store the correct answer and country details for verification
        response["country"] = {
            "name": country["name"],
            "capital": country["capital"],
            "region": country.get("region", "Unknown"),
            "population": country.get("population", 0),
            "area": country.get("area", 0)
        }
        
        return jsonify(response)
    except Exception as e:
        logger.error(f"Error creating new game: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/game/verify', methods=['POST'])
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
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Missing request body"}), 400
        
        required_fields = ['game_id', 'country_id', 'mode', 'answer']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Get the country from the database
        country = None
        for c in game_handler.countries:
            if c.get('id') == data['country_id']:
                country = c
                break
        
        if not country:
            return jsonify({"error": "Country not found"}), 404
        
        # Determine the correct answer based on the mode
        mode = data['mode']
        correct_answer = country["name"] if mode not in ['cap'] else country["capital"]
        
        # Check if the answer is correct
        is_correct = data['answer'] == correct_answer
        
        # Update user stats if user_id is provided
        user_id = data.get('user_id')
        user_name = data.get('user_name', 'API User')
        login_method = data.get('login_method', 'web')
        
        if user_id:
            # Convert to integer if it's a number
            try:
                user_id = int(user_id)
            except:
                user_id = hash(user_id)  # Use hash for non-integer IDs
            
            # Update the game stats
            game_handler._update_user_stats(user_id, is_correct, mode, user_name)
            
            # Update metadata if login_method is provided
            if login_method and user_id in game_handler.user_stats:
                if "metadata" not in game_handler.user_stats[user_id]:
                    game_handler.user_stats[user_id]["metadata"] = {
                        "login_method": login_method,
                        "user_name": user_name,
                        "wallet_address": data.get('wallet_address', '0xweb'),
                        "first_play_timestamp": int(data.get('timestamp', 0))
                    }
                else:
                    game_handler.user_stats[user_id]["metadata"]["login_method"] = login_method
                    if user_name:
                        game_handler.user_stats[user_id]["metadata"]["user_name"] = user_name
                    if 'wallet_address' in data:
                        game_handler.user_stats[user_id]["metadata"]["wallet_address"] = data['wallet_address']
            
            # Save the updated stats to the database
            game_handler._save_user_stats_to_database(
                user_id, 
                mode, 
                game_handler.user_stats[user_id].get(mode, {'total': 0, 'correct': 0}),
                game_handler.user_stats[user_id].get('metadata', {})
            )
        
        # Format response
        response = {
            "is_correct": is_correct,
            "correct_answer": correct_answer,
            "country": {
                "name": country["name"],
                "capital": country["capital"],
                "region": country.get("region", "Unknown"),
                "population": country.get("population", 0),
                "area": country.get("area", 0)
            }
        }
        
        # Include user stats if user_id was provided
        if user_id and user_id in game_handler.user_stats and mode in game_handler.user_stats[user_id]:
            response["user_stats"] = {
                "total": game_handler.user_stats[user_id][mode]["total"],
                "correct": game_handler.user_stats[user_id][mode]["correct"],
                "accuracy": (game_handler.user_stats[user_id][mode]["correct"] / 
                            game_handler.user_stats[user_id][mode]["total"] * 100) 
                            if game_handler.user_stats[user_id][mode]["total"] > 0 else 0
            }
        
        return jsonify(response)
    except Exception as e:
        logger.error(f"Error verifying answer: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/game/leaderboard', methods=['GET'])
@require_api_key
def get_leaderboard():
    """Get the game leaderboard
    
    Query Parameters:
    - mode: Filter by game mode ('map', 'flag', 'cap', or 'all')
    - limit: Maximum number of entries to return (default: 10)
    
    Returns:
    - JSON with leaderboard data
    """
    mode = request.args.get('mode', 'all')
    limit = min(int(request.args.get('limit', 10)), 100)  # Cap at 100 entries
    
    try:
        # Reload user stats from database to ensure fresh data
        game_handler._load_user_stats_from_database()
        
        # Calculate totals and accuracy for each user
        user_totals = {}
        for user_id, modes in game_handler.user_stats.items():
            user_totals[user_id] = {"total": 0, "correct": 0, "modes": {}}
            
            # Store user metadata if available
            if "metadata" in modes:
                user_totals[user_id]["metadata"] = modes["metadata"]
            
            # Calculate totals across all game modes or specific mode
            for m, stats in modes.items():
                if m == "metadata" or m == "capital":
                    continue  # Skip metadata and deprecated capital mode
                
                if mode != 'all' and m != mode:
                    continue  # Skip modes that don't match filter
                
                # Make sure this is a game stats dictionary
                if isinstance(stats, dict) and "total" in stats and "correct" in stats:
                    user_totals[user_id]["total"] += stats["total"]
                    user_totals[user_id]["correct"] += stats["correct"]

                    # Calculate accuracy for this mode
                    accuracy = (stats["correct"] / stats["total"] *
                                100) if stats["total"] > 0 else 0
                    user_totals[user_id]["modes"][m] = {
                        "total": stats["total"],
                        "correct": stats["correct"],
                        "accuracy": accuracy
                    }
            
            # Calculate overall accuracy
            user_totals[user_id]["accuracy"] = (
                user_totals[user_id]["correct"] /
                user_totals[user_id]["total"] *
                100) if user_totals[user_id]["total"] > 0 else 0
        
        # Sort users by overall accuracy (highest first)
        sorted_users = sorted(user_totals.items(),
                            key=lambda x: x[1]["accuracy"],
                            reverse=True)
        
        # Format the leaderboard
        leaderboard = []
        for rank, (user_id, stats) in enumerate(sorted_users[:limit], 1):
            # Skip users with no games played
            if stats["total"] == 0:
                continue
                
            user_entry = {
                "rank": rank,
                "user_id": user_id,
                "accuracy": stats["accuracy"],
                "total": stats["total"],
                "correct": stats["correct"],
                "modes": stats["modes"]
            }
            
            # Add metadata if available
            if "metadata" in stats:
                user_entry["user_name"] = stats["metadata"].get("user_name", f"User {user_id}")
                user_entry["login_method"] = stats["metadata"].get("login_method", "unknown")
                user_entry["wallet_address"] = stats["metadata"].get("wallet_address", "")
                
                # Add join date if available
                if "first_play_timestamp" in stats["metadata"]:
                    user_entry["joined"] = stats["metadata"]["first_play_timestamp"]
            
            leaderboard.append(user_entry)
        
        return jsonify({"leaderboard": leaderboard})
    except Exception as e:
        logger.error(f"Error fetching leaderboard: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/game/user-stats', methods=['GET'])
@require_api_key
def get_user_stats():
    """Get statistics for a specific user
    
    Query Parameters:
    - user_id: User ID to fetch stats for
    
    Returns:
    - JSON with user statistics
    """
    user_id_str = request.args.get('user_id')
    if not user_id_str:
        return jsonify({"error": "Missing 'user_id' parameter"}), 400
    
    try:
        # Convert to integer if possible
        try:
            user_id = int(user_id_str)
        except:
            user_id = hash(user_id_str)  # Use hash for non-integer IDs
        
        # Reload user stats from database
        game_handler._load_user_stats_from_database()
        
        if user_id not in game_handler.user_stats:
            return jsonify({"error": "User not found"}), 404
        
        # Get user data
        user_data = game_handler.user_stats[user_id]
        
        # Format response
        response = {
            "user_id": user_id,
            "modes": {}
        }
        
        # Add metadata if available
        if "metadata" in user_data:
            response["user_name"] = user_data["metadata"].get("user_name", f"User {user_id}")
            response["login_method"] = user_data["metadata"].get("login_method", "unknown")
            response["wallet_address"] = user_data["metadata"].get("wallet_address", "")
            
            # Add join date if available
            if "first_play_timestamp" in user_data["metadata"]:
                response["joined"] = user_data["metadata"]["first_play_timestamp"]
        
        # Add game mode stats
        for mode, stats in user_data.items():
            if mode == "metadata" or mode == "capital":
                continue  # Skip metadata dict and deprecated capital mode
            
            # Calculate accuracy
            accuracy = (stats["correct"] / stats["total"] * 
                        100) if stats["total"] > 0 else 0
            
            response["modes"][mode] = {
                "total": stats["total"],
                "correct": stats["correct"],
                "accuracy": accuracy
            }
        
        # Calculate overall stats
        total_games = sum(stats["total"] for mode, stats in user_data.items() 
                          if mode != "metadata" and mode != "capital")
        total_correct = sum(stats["correct"] for mode, stats in user_data.items() 
                           if mode != "metadata" and mode != "capital")
        
        response["overall"] = {
            "total": total_games,
            "correct": total_correct,
            "accuracy": (total_correct / total_games * 100) if total_games > 0 else 0
        }
        
        return jsonify(response)
    except Exception as e:
        logger.error(f"Error fetching user stats: {e}")
        return jsonify({"error": str(e)}), 500

# Run the API server
if __name__ == '__main__':
    port = int(os.environ.get("API_PORT", 5001))
    app.run(host='0.0.0.0', port=port)