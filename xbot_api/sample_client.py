"""
Sample client for the XBot API
This demonstrates how to use the API endpoints
"""

import os
import json
import base64
import requests
from io import BytesIO
from typing import Dict, Any, List, Optional
from PIL import Image

# API configuration
API_BASE_URL = "http://localhost:5001/api"
API_KEY = "631c0ea5-427b-4df6-8a18-fa43924854b7"  # Generated API key from server logs

# Set up headers with API key
HEADERS = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
}

def check_health():
    """Check if the API server is running"""
    response = requests.get(f"{API_BASE_URL}/health")
    return response.json()

def get_crypto_price(symbol):
    """Get cryptocurrency price"""
    response = requests.get(
        f"{API_BASE_URL}/crypto/price", 
        params={"symbol": symbol},
        headers=HEADERS
    )
    return response.json()

def get_crypto_prices(symbols=None):
    """Get prices for multiple cryptocurrencies"""
    params = {}
    if symbols:
        if isinstance(symbols, list):
            params["symbols"] = ",".join(symbols)
        else:
            params["symbols"] = symbols
            
    response = requests.get(
        f"{API_BASE_URL}/crypto/prices", 
        params=params,
        headers=HEADERS
    )
    return response.json()

def get_stock_price(symbol):
    """Get stock price"""
    response = requests.get(
        f"{API_BASE_URL}/stock/price", 
        params={"symbol": symbol},
        headers=HEADERS
    )
    return response.json()

def get_stock_prices():
    """Get prices for multiple stocks"""
    response = requests.get(
        f"{API_BASE_URL}/stock/prices", 
        headers=HEADERS
    )
    return response.json()

def get_vietnam_stock_price(symbol):
    """Get Vietnam stock price"""
    response = requests.get(
        f"{API_BASE_URL}/vietnam/stock/price", 
        params={"symbol": symbol},
        headers=HEADERS
    )
    return response.json()

def get_vietnam_stock_prices(symbols=None):
    """Get prices for multiple Vietnam stocks"""
    params = {}
    if symbols:
        if isinstance(symbols, list):
            params["symbols"] = ",".join(symbols)
        else:
            params["symbols"] = symbols
            
    response = requests.get(
        f"{API_BASE_URL}/vietnam/stock/prices", 
        params=params,
        headers=HEADERS
    )
    return response.json()

def display_image(image_data):
    """Display an image from base64 encoded data"""
    try:
        # This requires a GUI environment to display,
        # but we show how to decode the image for processing
        image_bytes = base64.b64decode(image_data)
        image = Image.open(BytesIO(image_bytes))
        
        # In a real application, you might save or display the image
        # image.show()  # This will open the image in a default viewer
        
        # For this sample, we just return the size
        return f"Image loaded successfully. Size: {image.size[0]}x{image.size[1]}"
    except Exception as e:
        return f"Error displaying image: {e}"

def get_new_game(mode="map"):
    """Get a new game question"""
    response = requests.get(
        f"{API_BASE_URL}/game/new", 
        params={"mode": mode},
        headers=HEADERS
    )
    game_data = response.json()
    
    # If there's image data in the response, we can display it
    if "image_data" in game_data:
        print(f"Received image data ({len(game_data['image_data'])} bytes)")
        # Uncomment to display the image (requires GUI)
        # display_image(game_data["image_data"])
        
    return game_data

def verify_answer(game_data, answer, user_info=None):
    """Verify a game answer"""
    if user_info is None:
        user_info = {
            "user_id": "sample_user_123",
            "user_name": "Sample User",
            "login_method": "web"
        }
        
    data = {
        "game_id": game_data["game_id"],
        "country_id": game_data["country_id"],
        "mode": game_data["mode"],
        "answer": answer,
        **user_info
    }
    
    response = requests.post(
        f"{API_BASE_URL}/game/verify", 
        json=data,
        headers=HEADERS
    )
    return response.json()

def get_leaderboard(mode="all", limit=10):
    """Get the game leaderboard"""
    response = requests.get(
        f"{API_BASE_URL}/game/leaderboard", 
        params={"mode": mode, "limit": limit},
        headers=HEADERS
    )
    return response.json()

def get_user_stats(user_id):
    """Get statistics for a specific user"""
    response = requests.get(
        f"{API_BASE_URL}/game/user-stats", 
        params={"user_id": user_id},
        headers=HEADERS
    )
    return response.json()

def main():
    """Run some sample API calls"""
    # Health check
    health = check_health()
    print(f"API Health: {health}")
    
    # Crypto price
    btc_price = get_crypto_price("BTC")
    print(f"\nBitcoin price: {json.dumps(btc_price, indent=2)}")
    
    # Stock price
    aapl_price = get_stock_price("AAPL")
    print(f"\nApple stock price: {json.dumps(aapl_price, indent=2)}")
    
    # Vietnam stock price
    vnm_price = get_vietnam_stock_price("VNM")
    print(f"\nVNM stock price: {json.dumps(vnm_price, indent=2)}")
    
    # Game functionality
    print("\nStarting a new game...")
    game = get_new_game("map")
    
    if "error" in game:
        print(f"Error: {game['error']}")
    else:
        print(f"Game question: {game.get('question', 'No question available')}")
        print(f"Options: {', '.join(game.get('options', []))}")
        
        # Display image dimensions if available
        if "width" in game and "height" in game:
            print(f"Image dimensions: {game['width']}x{game['height']}")
        elif "image_data" in game:
            # Decode the image to get dimensions
            try:
                image_bytes = base64.b64decode(game["image_data"])
                with Image.open(BytesIO(image_bytes)) as img:
                    print(f"Image dimensions from data: {img.width}x{img.height}")
            except Exception as e:
                print(f"Error getting image dimensions: {e}")
        
        # For demonstration, we'll provide the correct answer
        print("\nVerifying the answer...")
        try:
            correct_answer = game.get("country", {}).get("name", "")
            if correct_answer:
                result = verify_answer(game, correct_answer)
                print(f"Correct answer: {result.get('is_correct', False)}")
                print(f"User stats: {json.dumps(result.get('user_stats', {}), indent=2)}")
            else:
                print("Cannot verify answer: no country name found in response")
        except Exception as e:
            print(f"Error verifying answer: {e}")
    
    # Get leaderboard
    print("\nFetching leaderboard...")
    leaderboard = get_leaderboard()
    if "error" in leaderboard:
        print(f"Error fetching leaderboard: {leaderboard['error']}")
    else:
        print(f"Leaderboard: {json.dumps(leaderboard, indent=2)}")
    
    # Get user stats
    print("\nFetching user stats...")
    stats = get_user_stats("sample_user_123")
    if "error" in stats:
        print(f"Error fetching user stats: {stats['error']}")
    else:
        print(f"User stats: {json.dumps(stats, indent=2)}")
    
if __name__ == "__main__":
    main()