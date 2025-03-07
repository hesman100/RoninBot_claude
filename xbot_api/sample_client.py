"""
Sample client for the XBot API
This demonstrates how to use the API endpoints
"""

import requests
import json
import base64
import os
from PIL import Image
from io import BytesIO

# API configuration
API_BASE_URL = "http://localhost:5001/api"
API_KEY = os.environ.get("XBOT_API_KEY", "your_development_api_key")

# Set up headers with API key
HEADERS = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
}

def check_health():
    """Check if the API server is running"""
    response = requests.get(f"{API_BASE_URL}/health")
    print(f"Health check: {response.status_code}")
    print(response.json())
    return response.status_code == 200

def get_crypto_price(symbol):
    """Get cryptocurrency price"""
    response = requests.get(f"{API_BASE_URL}/crypto/price", 
                           params={"symbol": symbol},
                           headers=HEADERS)
    print(f"Crypto price for {symbol}: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    return response.json()

def get_stock_price(symbol):
    """Get stock price"""
    response = requests.get(f"{API_BASE_URL}/stock/price", 
                           params={"symbol": symbol},
                           headers=HEADERS)
    print(f"Stock price for {symbol}: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    return response.json()

def get_vietnam_stock_price(symbol):
    """Get Vietnam stock price"""
    response = requests.get(f"{API_BASE_URL}/vietnam/stock/price", 
                           params={"symbol": symbol},
                           headers=HEADERS)
    print(f"Vietnam stock price for {symbol}: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    return response.json()

def display_image(image_data):
    """Display an image from base64 encoded data"""
    try:
        img = Image.open(BytesIO(base64.b64decode(image_data)))
        img.show()
    except Exception as e:
        print(f"Error displaying image: {e}")

def get_new_game(mode="map"):
    """Get a new game question"""
    response = requests.get(f"{API_BASE_URL}/game/new", 
                           params={"mode": mode},
                           headers=HEADERS)
    print(f"New game ({mode}): {response.status_code}")
    data = response.json()
    print(json.dumps({k: v for k, v in data.items() if k != "image_data"}, indent=2))
    
    # Save and display the image if available
    if "image_data" in data:
        try:
            img_data = base64.b64decode(data["image_data"])
            with open(f"sample_{mode}_game.png", "wb") as f:
                f.write(img_data)
            print(f"Image saved to sample_{mode}_game.png")
            
            # Try to display the image
            img = Image.open(BytesIO(img_data))
            img.show()
        except Exception as e:
            print(f"Error handling image: {e}")
    
    return data

def verify_answer(game_data, answer, user_info=None):
    """Verify a game answer"""
    # Prepare request data
    data = {
        "game_id": game_data["game_id"],
        "country_id": game_data["country_id"],
        "mode": game_data["mode"],
        "answer": answer
    }
    
    # Add user info if provided
    if user_info:
        data.update(user_info)
    
    response = requests.post(f"{API_BASE_URL}/game/verify", 
                            json=data,
                            headers=HEADERS)
    print(f"Verify answer: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    return response.json()

def get_leaderboard(mode="all", limit=10):
    """Get the game leaderboard"""
    response = requests.get(f"{API_BASE_URL}/game/leaderboard", 
                           params={"mode": mode, "limit": limit},
                           headers=HEADERS)
    print(f"Leaderboard ({mode}): {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    return response.json()

def get_user_stats(user_id):
    """Get statistics for a specific user"""
    response = requests.get(f"{API_BASE_URL}/game/user-stats", 
                           params={"user_id": user_id},
                           headers=HEADERS)
    print(f"User stats for {user_id}: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    return response.json()

if __name__ == "__main__":
    # Check if the API is running
    if not check_health():
        print("API server is not running. Please start the server first.")
        exit(1)
    
    # Demo using price functions
    print("\n=== CRYPTOCURRENCY PRICES ===")
    get_crypto_price("BTC")
    
    print("\n=== STOCK PRICES ===")
    get_stock_price("AAPL")
    
    print("\n=== VIETNAM STOCK PRICES ===")
    get_vietnam_stock_price("VCB")
    
    # Demo using game functions
    print("\n=== MAP GAME ===")
    map_game = get_new_game("map")
    
    print("\n=== FLAG GAME ===")
    flag_game = get_new_game("flag")
    
    print("\n=== CAPITAL GAME ===")
    capital_game = get_new_game("cap")
    
    # Demo verifying answers
    if "correct_answer" in map_game:
        print("\n=== VERIFY CORRECT ANSWER ===")
        correct_answer = map_game["correct_answer"]
        user_info = {
            "user_id": "api_test_user",
            "user_name": "API Tester",
            "login_method": "web",
            "wallet_address": "0xapitest"
        }
        verify_answer(map_game, correct_answer, user_info)
        
        print("\n=== VERIFY INCORRECT ANSWER ===")
        incorrect_answer = "Wrong Country"
        verify_answer(map_game, incorrect_answer, user_info)
    
    # Demo leaderboard
    print("\n=== LEADERBOARD ===")
    get_leaderboard()
    
    # Demo user stats
    print("\n=== USER STATS ===")
    get_user_stats("api_test_user")