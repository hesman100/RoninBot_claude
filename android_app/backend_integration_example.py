"""
Example implementation of REST API endpoints that adapt the existing
game handler for direct consumption by the Android app
"""

from flask import Flask, request, jsonify, send_file
import os
import time
import uuid
import logging
from PIL import Image
from io import BytesIO
import random

# Import the existing game handler
from country_game.game_handler import GameHandler

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Initialize the game handler
game_handler = GameHandler()

# In-memory storage for active games
# In production, use a proper database
active_games = {}

# Simple API key for basic security
API_KEY = os.environ.get("APP_API_KEY", "test_api_key_change_me")

# Base paths for country images
MAP_IMAGES_PATH = os.path.join("country_game", "images", "wiki_all_map_400pi")
FLAG_IMAGES_PATH = os.path.join("country_game", "images", "wiki_flag")

# Simple API key validation
def validate_api_key():
    api_key = request.headers.get('X-API-Key')
    if not api_key or api_key != API_KEY:
        return False
    return True

@app.route('/api/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": time.time()})

@app.route('/api/game/start', methods=['GET'])
def start_game():
    """Initialize a new game session"""
    # Validate API key
    if not validate_api_key():
        return jsonify({"error": "Unauthorized"}), 401
    
    # Get game mode from query parameters
    mode = request.args.get('mode', 'map')
    if mode not in ['map', 'flag', 'capital', 'cap']:
        return jsonify({"error": f"Invalid game mode: {mode}"}), 400
    
    try:
        # Create a unique game ID
        game_id = str(uuid.uuid4())
        
        # Get a random country from the database
        country_data = game_handler._get_random_country()
        
        # Prepare game options based on mode
        if mode == 'map' or mode == 'flag':
            # Get neighboring countries for options
            options = [country_data["name"]]
            hint_countries = game_handler._get_hint_countries(country_data)
            for country in hint_countries:
                if len(options) < 10:  # Get up to 10 options
                    options.append(country["name"])
            
            # Shuffle options
            random.shuffle(options)
            
            # Determine correct answer index
            correct_index = options.index(country_data["name"])
            
            # Determine image path
            if mode == 'map':
                image_filename = f"{country_data['id']}.png"
                image_path = os.path.join(MAP_IMAGES_PATH, image_filename)
                image_url = f"/api/images/map/{country_data['id']}"
            else:  # flag mode
                image_filename = f"{country_data['id']}.png"
                image_path = os.path.join(FLAG_IMAGES_PATH, image_filename)
                image_url = f"/api/images/flag/{country_data['id']}"
        
        elif mode == 'capital' or mode == 'cap':
            # For capital mode, the options are capital cities
            options = [country_data["capital"]]
            hint_countries = game_handler._get_hint_countries(country_data)
            for country in hint_countries:
                if len(options) < 10 and "capital" in country:
                    options.append(country["capital"])
            
            # Fill with random capitals if needed
            while len(options) < 10:
                rand_country = game_handler._get_random_country()
                if "capital" in rand_country and rand_country["capital"] not in options:
                    options.append(rand_country["capital"])
            
            # Shuffle options
            random.shuffle(options)
            
            # Determine correct answer index
            correct_index = options.index(country_data["capital"])
            
            # For cap mode, we show the map
            if mode == 'cap':
                image_filename = f"{country_data['id']}.png"
                image_path = os.path.join(MAP_IMAGES_PATH, image_filename)
                image_url = f"/api/images/map/{country_data['id']}"
            else:
                # For capital mode, we don't show an image, just the country name
                image_url = None
        
        # Store game state
        game_state = {
            "id": game_id,
            "mode": mode,
            "country": country_data,
            "options": options,
            "correct_index": correct_index,
            "start_time": time.time(),
            "expires_at": time.time() + 15  # 15 second timeout
        }
        
        active_games[game_id] = game_state
        
        # Return the game initialization data to the client
        response_data = {
            "game_id": game_id,
            "mode": mode,
            "options": options,
            "timeout": 15,  # 15 seconds
            "expires_at": int(game_state["expires_at"])
        }
        
        # Add image URL if applicable
        if image_url:
            response_data["image_url"] = image_url
        
        # For capital mode, include the country name instead of an image
        if mode == 'capital':
            response_data["country_name"] = country_data["name"]
        
        return jsonify(response_data)
    
    except Exception as e:
        logging.error(f"Error starting game: {str(e)}")
        return jsonify({"error": f"Failed to start game: {str(e)}"}), 500

@app.route('/api/game/answer', methods=['POST'])
def submit_answer():
    """Process a player's answer submission"""
    # Validate API key
    if not validate_api_key():
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        # Get request data
        data = request.json
        if not data:
            return jsonify({"error": "Missing request body"}), 400
        
        game_id = data.get('game_id')
        selected_option = data.get('selected_option')
        player_name = data.get('player_name', 'Guest')
        
        if not game_id or not selected_option:
            return jsonify({"error": "Missing required fields"}), 400
        
        # Check if game exists and is not expired
        if game_id not in active_games:
            return jsonify({"error": "Game not found or expired"}), 404
        
        game = active_games[game_id]
        
        # Check if game has expired
        if time.time() > game["expires_at"]:
            del active_games[game_id]
            return jsonify({
                "error": "Game has expired",
                "correct_answer": game["options"][game["correct_index"]],
                "country_details": {
                    "name": game["country"]["name"],
                    "capital": game["country"].get("capital", "Unknown"),
                    "region": game["country"].get("region", "Unknown"),
                    "population": game["country"].get("population", 0),
                    "area": game["country"].get("area", 0)
                }
            }), 410
        
        # Check if the answer is correct
        is_correct = (selected_option == game["options"][game["correct_index"]])
        
        # Calculate elapsed time
        elapsed_time = round(time.time() - game["start_time"], 2)
        
        # Update leaderboard if correct
        if is_correct:
            mode = game["mode"]
            game_handler._update_user_stats(player_name, True, mode)
        
        # Prepare response
        country = game["country"]
        response = {
            "correct": is_correct,
            "correct_answer": game["options"][game["correct_index"]],
            "elapsed_time": elapsed_time,
            "country_details": {
                "name": country["name"],
                "capital": country.get("capital", "Unknown"),
                "region": country.get("region", "Unknown"),
                "population": country.get("population", 0),
                "area": country.get("area", 0)
            }
        }
        
        # Clean up the game
        del active_games[game_id]
        
        return jsonify(response)
    
    except Exception as e:
        logging.error(f"Error processing answer: {str(e)}")
        return jsonify({"error": f"Failed to process answer: {str(e)}"}), 500

@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    """Retrieve the game leaderboard"""
    # Validate API key
    if not validate_api_key():
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        # Get parameters
        mode = request.args.get('mode', 'all')
        limit = int(request.args.get('limit', 10))
        
        # Get leaderboard data
        leaderboard = game_handler._get_leaderboard(mode, limit)
        
        return jsonify({"leaderboard": leaderboard})
    
    except Exception as e:
        logging.error(f"Error retrieving leaderboard: {str(e)}")
        return jsonify({"error": f"Failed to retrieve leaderboard: {str(e)}"}), 500

@app.route('/api/images/<image_type>/<country_id>', methods=['GET'])
def serve_image(image_type, country_id):
    """Serve country images (maps or flags)"""
    try:
        # Determine image path based on type
        if image_type == 'map':
            image_path = os.path.join(MAP_IMAGES_PATH, f"{country_id}.png")
        elif image_type == 'flag':
            image_path = os.path.join(FLAG_IMAGES_PATH, f"{country_id}.png")
        else:
            return jsonify({"error": "Invalid image type"}), 400
        
        # Check if image exists
        if not os.path.exists(image_path):
            return jsonify({"error": "Image not found"}), 404
        
        # Get optional resize parameters
        width = request.args.get('width')
        height = request.args.get('height')
        
        # If resizing is requested
        if width or height:
            img = Image.open(image_path)
            
            # Calculate new dimensions
            if width and height:
                new_size = (int(width), int(height))
            elif width:
                wpercent = (int(width) / float(img.size[0]))
                hsize = int((float(img.size[1]) * float(wpercent)))
                new_size = (int(width), hsize)
            else:  # height only
                hpercent = (int(height) / float(img.size[1]))
                wsize = int((float(img.size[0]) * float(hpercent)))
                new_size = (wsize, int(height))
            
            # Resize image
            img = img.resize(new_size, Image.LANCZOS)
            
            # Serve from memory
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)
            
            return send_file(buffer, mimetype='image/png')
        
        # If no resizing, serve the original
        return send_file(image_path, mimetype='image/png')
    
    except Exception as e:
        logging.error(f"Error serving image: {str(e)}")
        return jsonify({"error": f"Failed to serve image: {str(e)}"}), 500

if __name__ == '__main__':
    # Run the API server
    app.run(host='0.0.0.0', port=5001, debug=True)
