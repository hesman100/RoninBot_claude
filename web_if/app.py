"""
Country Guessing Game - Web Interface

This Flask application provides a web interface for the country guessing game,
allowing users to play the game without using Telegram.
"""

import os
import logging
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import secrets
import sys

# Add the parent directory to the path so we can import from the country_game module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask application
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', secrets.token_hex(16))

# Import game service (will be implemented later)
# This service will adapt the existing game logic for web use
class GameService:
    """Placeholder for the game service that will be implemented"""
    def __init__(self, bot_version):
        self.bot_version = bot_version
        # This will be connected to the existing GameHandler

# Set the bot version to match the main bot
BOT_VERSION = "1.3"

# Initialize the game service
game_service = GameService(BOT_VERSION)

# Routes
@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html', version=BOT_VERSION)

@app.route('/help')
def help_page():
    """Render the help page"""
    return render_template('help.html', version=BOT_VERSION)

@app.route('/leaderboard')
def leaderboard():
    """Render the leaderboard page"""
    # In the future, this will connect to the existing leaderboard database
    return render_template('leaderboard.html', version=BOT_VERSION)

@app.route('/game/<mode>')
def game(mode):
    """Render the game page for the specified mode"""
    if mode not in ['map', 'flag', 'capital']:
        return redirect(url_for('index'))

    # Initialize a guest session if not already done
    if 'user_id' not in session:
        session['user_id'] = f"guest_{secrets.token_hex(8)}"
        session['user_name'] = f"Guest_{secrets.token_hex(4)}"

    return render_template('game.html', mode=mode, version=BOT_VERSION)

# API Routes
@app.route('/api/game/<mode>', methods=['GET'])
def api_start_game(mode):
    """API endpoint to start a new game"""
    if mode not in ['map', 'flag', 'capital']:
        return jsonify({'error': 'Invalid game mode'}), 400

    # This will eventually connect to the existing game handler logic
    # For now, return a placeholder response
    return jsonify({
        'status': 'success',
        'message': f'Started {mode} game',
        'image_url': f'/static/assets/placeholder/{mode}.svg',
        'options': ['Country1', 'Country2', 'Country3', 'Country4', 'Country5'],
        'timer': 30
    })

@app.route('/api/game/answer', methods=['POST'])
def api_submit_answer():
    """API endpoint to submit an answer"""
    data = request.json
    answer = data.get('answer', '')

    # This will eventually connect to the game handler's answer validation
    # For now, return a placeholder response
    return jsonify({
        'status': 'success',
        'correct': True,  # Placeholder
        'correct_answer': 'CountryName',
        'country_details': {
            'name': 'CountryName',
            'capital': 'CapitalCity',
            'region': 'Region',
            'population': 1000000,
            'area': 100000
        },
        'version': BOT_VERSION
    })

@app.route('/api/leaderboard', methods=['GET'])
def api_leaderboard():
    """API endpoint to get leaderboard data"""
    try:
        # Import the leaderboard module to get real data
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from country_game import leaderboard_db

        # Get the actual leaderboard data (top 10 users)
        leaderboard_data = leaderboard_db.get_leaderboard(limit=10)

        # Format the data to match what the frontend expects
        formatted_data = []
        for entry in leaderboard_data:
            formatted_data.append({
                'rank': entry['rank'],
                'name': entry['name'],
                'score': entry['score'],
                'accuracy': entry['accuracy'],
                'login_method': entry['login_method'],
                'wallet_addr': entry['wallet_addr'],
                'language': entry['language'],
                'first_login': entry['first_time_login']
            })

        # Define BOT_VERSION if it's not imported
        BOT_VERSION = os.environ.get('BOT_VERSION', '1.4')

        return jsonify({
            'leaderboard': formatted_data,
            'version': BOT_VERSION
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': str(e),
            'leaderboard': [],
            'version': os.environ.get('BOT_VERSION', '1.4')
        }), 500

@app.route('/api/help', methods=['GET'])
def api_help():
    """API endpoint to get help information"""
    return jsonify({
        'game_modes': {
            'map': 'Guess the country from its map',
            'flag': 'Guess the country from its flag',
            'capital': 'Guess the capital city of a country'
        },
        'instructions': 'You have 30 seconds to answer each question.',
        'version': BOT_VERSION
    })

# Guest session management
@app.route('/api/user/guest', methods=['POST'])
def create_guest_session():
    """Create a new guest session"""
    session['user_id'] = f"guest_{secrets.token_hex(8)}"
    session['user_name'] = f"Guest_{secrets.token_hex(4)}"
    return jsonify({
        'status': 'success',
        'user_id': session['user_id'],
        'user_name': session['user_name']
    })

# Wallet connection placeholder (for future implementation)
@app.route('/api/wallet/connect', methods=['POST'])
def connect_wallet():
    """Placeholder for wallet connection"""
    return jsonify({
        'status': 'not_implemented',
        'message': 'Wallet connection will be implemented in a future update'
    })

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', version=BOT_VERSION), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html', version=BOT_VERSION), 500

if __name__ == '__main__':
    # For local development
    app.run(host='0.0.0.0', port=5000, debug=True)