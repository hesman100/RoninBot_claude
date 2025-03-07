#!/usr/bin/env python3
"""
Comprehensive test script for all game modes and API functionality.
"""

import json
import base64
from io import BytesIO
from PIL import Image
import xbot_api.sample_client as client

def test_game_mode(mode):
    """Test a specific game mode and verify image dimensions if applicable."""
    print(f"\n==== Testing {mode.upper()} mode ====")
    
    # Get a new game
    game = client.get_new_game(mode)
    
    # Print basic game info
    print(f"Question: {game.get('question', 'No question')}")
    print(f"Options: {', '.join(game.get('options', []))}")
    
    # Check for image dimensions
    if "width" in game and "height" in game:
        print(f"Image dimensions (reported): {game['width']}x{game['height']}")
    
    # If there's image data, verify dimensions by decoding
    if "image_data" in game:
        try:
            image_bytes = base64.b64decode(game["image_data"])
            with Image.open(BytesIO(image_bytes)) as img:
                print(f"Image dimensions (actual): {img.width}x{img.height}")
                
                # Verify that width is standardized to 320px
                assert img.width == 320, f"Expected width 320px, got {img.width}px"
                print("✅ Image width is standardized to 320px")
                
                # Check aspect ratio based on mode
                if mode == 'map':
                    assert img.height == 320, f"Expected square aspect ratio for map (320x320), got {img.width}x{img.height}"
                    print("✅ Map has square aspect ratio")
        except Exception as e:
            print(f"❌ Error checking image: {e}")
    else:
        print("No image data in response (expected for capital mode)")
    
    # Verify answer
    try:
        if mode == 'cap':
            # For capital mode, the correct answer is the capital, not the country name
            answer = game.get("options", [])[0]  # Just use the first option for testing
            for option in game.get("options", []):
                if option in game.get("question", ""):
                    answer = option
                    break
        else:
            answer = game.get("country", {}).get("name", "")
        
        if answer:
            print(f"Submitting answer: {answer}")
            result = client.verify_answer(game, answer)
            print(f"Result: {'✅ Correct' if result.get('is_correct') else '❌ Incorrect'}")
            print(f"Updated stats: {json.dumps(result.get('user_stats', {}), indent=2)}")
        else:
            print("❌ Cannot verify answer: no valid answer found in response")
    except Exception as e:
        print(f"❌ Error verifying answer: {e}")

def test_price_endpoints():
    """Test the price-related API endpoints."""
    print("\n==== Testing Price Endpoints ====")
    
    # Test cryptocurrency prices
    btc = client.get_crypto_price("BTC")
    print(f"Bitcoin price: ${btc.get('BTC', {}).get('usd', 'N/A')}")
    
    # Test stock prices
    aapl = client.get_stock_price("AAPL")
    print(f"Apple stock price: ${aapl.get('AAPL', {}).get('usd', 'N/A')}")
    
    # Test Vietnam stock prices
    vnm = client.get_vietnam_stock_price("VNM")
    print(f"VNM stock price: ${vnm.get('VNM', {}).get('usd', 'N/A')}")

def test_leaderboard():
    """Test the leaderboard endpoint."""
    print("\n==== Testing Leaderboard ====")
    
    leaderboard = client.get_leaderboard(limit=3)
    if "leaderboard" in leaderboard:
        print(f"Top 3 players:")
        for i, player in enumerate(leaderboard["leaderboard"][:3], 1):
            print(f"{i}. {player.get('user_name', 'Unknown')} - Score: {player.get('correct', 0)}/{player.get('total', 0)} ({player.get('accuracy', 0)}%)")
    else:
        print("❌ Error fetching leaderboard")

def main():
    """Run all tests."""
    # Test API health
    health = client.check_health()
    print(f"API Health: {health.get('status', 'unknown')}")
    
    # Test all game modes
    for mode in ['map', 'flag', 'cap']:
        test_game_mode(mode)
    
    # Test price endpoints
    test_price_endpoints()
    
    # Test leaderboard
    test_leaderboard()
    
    print("\n==== All tests completed ====")

if __name__ == "__main__":
    main()