"""
Sample client for the XBot API
This demonstrates how to use the API endpoints

Note: This sample client has been updated to use port 5000 (consolidated with the Telegram bot)
and supports both header-based and query parameter API key authentication.

IMPORTANT: Client Request ID Implementation
--------------------------------------------
This client includes support for client request IDs to prevent duplicate responses.
When making requests to the game API, you should:

1. Generate a unique client_request_id for each new game request
2. Include this ID in subsequent related requests 
3. Reuse the same ID when retrying a failed request

This ensures that even if you make the same request multiple times
(e.g., due to network issues or retries), you'll always get the same
response with the same game data, preventing UI flickering issues.
"""

import os
import json
import base64
import uuid
import requests
from io import BytesIO
from typing import Dict, Any, List, Optional
from PIL import Image

# API configuration
API_BASE_URL = "http://localhost:5000/api"
API_KEY = "xbot-default-api-key-9876543210"  # Default API key

# Set up headers with API key
HEADERS = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
}

def check_health():
    """Check if the API server is running"""
    response = requests.get(f"{API_BASE_URL}/health")
    return response.json()

def get_crypto_price(symbol, use_query_param=False):
    """Get cryptocurrency price"""
    params = {"symbol": symbol}
    headers = HEADERS.copy()
    
    # Optionally use query parameter instead of header for API key
    if use_query_param:
        params["api_key"] = API_KEY
        # Remove API key from headers when using query parameter
        if "X-API-Key" in headers:
            del headers["X-API-Key"]
    
    response = requests.get(
        f"{API_BASE_URL}/crypto/price", 
        params=params,
        headers=headers
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

def get_new_game(mode="map", client_request_id=None):
    """Get a new game question
    
    Args:
        mode (str): Game mode - 'map', 'flag', or 'cap'
        client_request_id (str, optional): Unique client request ID for deduplication
    """
    # Generate a client request ID if not provided
    if client_request_id is None:
        client_request_id = str(uuid.uuid4())
        
    params = {
        "mode": mode,
        "client_request_id": client_request_id
    }
    
    response = requests.get(
        f"{API_BASE_URL}/game/new", 
        params=params,
        headers=HEADERS
    )
    game_data = response.json()
    
    # Store the client request ID in the game data for future reference
    game_data["client_request_id"] = client_request_id
    
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
    
    # Crypto price - using header-based API key authentication
    btc_price = get_crypto_price("BTC")
    print(f"\nBitcoin price (header auth): {json.dumps(btc_price, indent=2)}")
    
    # Crypto price - using query parameter API key authentication
    btc_price_query = get_crypto_price("BTC", use_query_param=True)
    print(f"\nBitcoin price (query param auth): {json.dumps(btc_price_query, indent=2)}")
    
    # Stock price
    aapl_price = get_stock_price("AAPL")
    print(f"\nApple stock price: {json.dumps(aapl_price, indent=2)}")
    
    # Vietnam stock price
    vnm_price = get_vietnam_stock_price("VNM")
    print(f"\nVNM stock price: {json.dumps(vnm_price, indent=2)}")
    
    # Game functionality
    print("\nTesting deduplication with multiple requests using the same client_request_id...")
    client_request_id = str(uuid.uuid4())
    print(f"Using client_request_id: {client_request_id}")
    
    # First request
    print("\nMaking first request...")
    game1 = get_new_game("map", client_request_id)
    
    if "error" in game1:
        print(f"Error in first request: {game1['error']}")
    else:
        print(f"First request - Game ID: {game1.get('game_id')}")
        print(f"First request - Country: {game1.get('country', {}).get('name', 'Unknown')}")
        print(f"First request - Mode: {game1.get('mode')}")
        print(f"First request - Question: {game1.get('question', 'No question available')}")
        
        # Make a second request with the same client_request_id
        print("\nMaking second request with same client_request_id...")
        game2 = get_new_game("map", client_request_id)
        
        if "error" in game2:
            print(f"Error in second request: {game2['error']}")
        else:
            print(f"Second request - Game ID: {game2.get('game_id')}")
            print(f"Second request - Country: {game2.get('country', {}).get('name', 'Unknown')}")
        
        # Check if the two responses are identical
        if game1.get('game_id') == game2.get('game_id') and game1.get('country', {}).get('name') == game2.get('country', {}).get('name'):
            print("\n✅ Deduplication successful! Both requests returned the same game data.")
        else:
            print("\n❌ Deduplication failed! Requests returned different game data.")
            print(f"First game_id: {game1.get('game_id')}, Second game_id: {game2.get('game_id')}")
            print(f"First country: {game1.get('country', {}).get('name')}, Second country: {game2.get('country', {}).get('name')}")
        
        # Make a third request with a new client_request_id
        print("\nMaking third request with new client_request_id...")
        new_client_request_id = str(uuid.uuid4())
        game3 = get_new_game("map", new_client_request_id)
        
        if "error" in game3:
            print(f"Error in third request: {game3['error']}")
        else:
            print(f"Third request - Game ID: {game3.get('game_id')}")
            print(f"Third request - Country: {game3.get('country', {}).get('name', 'Unknown')}")
            
            # Check if the new request has different data
            if game1.get('game_id') != game3.get('game_id'):
                print("\n✅ New client_request_id successfully generated different game data.")
            else:
                print("\n❌ New client_request_id failed to generate different game data.")
        
        # For demonstration, we'll provide the correct answer
        print("\nVerifying the answer...")
        try:
            correct_answer = game1.get("country", {}).get("name", "")
            if correct_answer:
                result = verify_answer(game1, correct_answer)
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