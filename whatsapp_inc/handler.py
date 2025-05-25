"""
WhatsApp Message Handler
This module processes incoming WhatsApp messages and routes them to the appropriate handlers.
"""

import logging
import json
import re
from typing import Dict, List, Optional, Any, Tuple

# Import from existing project modules to reuse functionality
from price_func.alphavantage_api import AlphaVantageAPI
from price_func.finnhub_api import FinnhubAPI
from price_func.coinmarketcap_api import CoinMarketCapAPI
from price_func.vietnam_stock_api import VietnamStockAPI
from price_func.utils import format_price_message, format_error_message
from country_game.game_handler import GameHandler

# Import WhatsApp specific modules
from whatsapp_inc.client import WhatsAppClient
from whatsapp_inc.config import (
    COMMAND_PREFIX,
    WELCOME_MESSAGE,
    HELP_MESSAGE,
    ERROR_MESSAGE
)

# Set up logging
logger = logging.getLogger(__name__)

class WhatsAppMessageHandler:
    """Handler for processing incoming WhatsApp messages"""
    
    def __init__(self):
        """Initialize the WhatsApp message handler"""
        self.client = WhatsAppClient()
        
        # Initialize API clients
        self.finnhub_api = FinnhubAPI()
        self.stock_api = AlphaVantageAPI()
        self.crypto_api = CoinMarketCapAPI()
        self.vietnam_api = VietnamStockAPI()
        
        # Initialize game handler
        self.game_handler = GameHandler()
        
        # Track active game sessions by phone number
        self.active_games = {}
        
        logger.info("WhatsApp message handler initialized")
    
    def process_message(self, from_number: str, message_body: str, media_url: Optional[str] = None) -> Dict:
        """Process an incoming WhatsApp message
        
        Args:
            from_number (str): Sender's phone number
            message_body (str): Message text content
            media_url (str, optional): URL of any media attached to the message
            
        Returns:
            Dict: Response information
        """
        logger.info(f"Processing message from {from_number}: {message_body[:50]}...")
        
        try:
            # Check if this is a command
            if message_body and message_body.startswith(COMMAND_PREFIX):
                return self._handle_command(from_number, message_body, media_url)
            
            # If not a command, check if user is in an active game
            if from_number in self.active_games:
                return self._handle_game_answer(from_number, message_body)
            
            # Default response for non-command messages
            response = "Hi there! I'm your XBot WhatsApp assistant. Type /help to see what I can do."
            self.client.send_message(from_number, response)
            return {"success": True, "message": "Default response sent"}
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            self.client.send_message(from_number, ERROR_MESSAGE)
            return {"error": str(e)}
    
    def _handle_command(self, from_number: str, command_text: str, media_url: Optional[str] = None) -> Dict:
        """Handle a command message
        
        Args:
            from_number (str): Sender's phone number
            command_text (str): Full command text
            media_url (str, optional): URL of any media attached to the message
            
        Returns:
            Dict: Command handling result
        """
        # Extract the command and arguments
        parts = command_text.strip().split(' ', 1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ''
        
        logger.info(f"Handling command: {command} with args: {args}")
        
        # Route to the appropriate handler
        if command == '/start' or command == '/help':
            return self._handle_help_command(from_number)
        elif command == '/s':
            return self._handle_stock_command(from_number, args)
        elif command == '/c':
            return self._handle_crypto_command(from_number, args)
        elif command == '/vn':
            return self._handle_vietnam_stock_command(from_number, args)
        elif command == '/g':
            return self._handle_game_command(from_number, args)
        else:
            # Unknown command
            response = f"Unknown command: {command}. Type /help to see available commands."
            self.client.send_message(from_number, response)
            return {"success": False, "message": "Unknown command"}
    
    def _handle_help_command(self, from_number: str) -> Dict:
        """Handle help command
        
        Args:
            from_number (str): Sender's phone number
            
        Returns:
            Dict: Command handling result
        """
        self.client.send_message(from_number, HELP_MESSAGE)
        return {"success": True, "message": "Help message sent"}
    
    def _handle_stock_command(self, from_number: str, args: str) -> Dict:
        """Handle stock price command
        
        Args:
            from_number (str): Sender's phone number
            args (str): Command arguments (stock symbol)
            
        Returns:
            Dict: Command handling result
        """
        try:
            if not args:
                # Get all default stocks
                logger.info("Getting all default stocks")
                
                # Try Finnhub first as it's significantly faster
                price_data = self.finnhub_api.get_stock_prices()
                
                # If Finnhub fails, fall back to AlphaVantage
                if isinstance(price_data, dict) and "error" in price_data:
                    logger.info("Finnhub API failed, falling back to AlphaVantage")
                    price_data = self.stock_api.get_stock_prices()
            else:
                # Get specific stock
                stock_symbol = args.upper().strip()
                logger.info(f"Getting stock price for {stock_symbol}")
                
                # Try Finnhub first
                price_data = self.finnhub_api.get_stock_price(stock_symbol)
                
                # If Finnhub fails, try AlphaVantage
                if isinstance(price_data, dict) and "error" in price_data:
                    logger.info(f"Finnhub failed for {stock_symbol}, trying AlphaVantage")
                    price_data = self.stock_api.get_stock_price(stock_symbol)
            
            # Format and send the message
            if isinstance(price_data, dict) and "error" in price_data:
                error_msg = price_data["error"]
                if "rate limit" in error_msg.lower():
                    error_msg = "⚠️ API rate limit reached\nPlease try again in a few minutes."
                
                self.client.send_message(from_number, f"Error: {error_msg}")
                return {"success": False, "error": error_msg}
            else:
                # Format the price data
                message = format_price_message(price_data)
                self.client.send_message(from_number, message)
                return {"success": True, "data": price_data}
                
        except Exception as e:
            logger.error(f"Error handling stock command: {str(e)}")
            self.client.send_message(from_number, f"Error getting stock data: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _handle_crypto_command(self, from_number: str, args: str) -> Dict:
        """Handle cryptocurrency price command
        
        Args:
            from_number (str): Sender's phone number
            args (str): Command arguments (crypto symbol)
            
        Returns:
            Dict: Command handling result
        """
        try:
            if not args:
                # Get default list of cryptocurrencies
                price_data = self.crypto_api.get_prices([])
            else:
                # Get specific cryptocurrency
                crypto_symbol = args.upper().strip()
                price_data = self.crypto_api.get_price(crypto_symbol)
            
            # Check for errors
            if isinstance(price_data, dict) and "error" in price_data:
                self.client.send_message(from_number, f"Error: {price_data['error']}")
                return {"success": False, "error": price_data["error"]}
            
            # Format and send the message
            message = format_price_message(price_data)
            self.client.send_message(from_number, message)
            return {"success": True, "data": price_data}
            
        except Exception as e:
            logger.error(f"Error handling crypto command: {str(e)}")
            self.client.send_message(from_number, f"Error getting cryptocurrency data: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _handle_vietnam_stock_command(self, from_number: str, args: str) -> Dict:
        """Handle Vietnam stock price command
        
        Args:
            from_number (str): Sender's phone number
            args (str): Command arguments (stock symbol)
            
        Returns:
            Dict: Command handling result
        """
        try:
            if not args:
                # Get default Vietnam stocks
                price_data = self.vietnam_api.get_stock_prices([])
            else:
                # Get specific Vietnam stock
                stock_symbol = args.upper().strip()
                price_data = self.vietnam_api.get_stock_price(stock_symbol)
            
            # Check for errors
            if isinstance(price_data, dict) and "error" in price_data:
                self.client.send_message(from_number, f"Error: {price_data['error']}")
                return {"success": False, "error": price_data["error"]}
            
            # Format and send the message
            message = format_price_message(price_data)
            self.client.send_message(from_number, message)
            return {"success": True, "data": price_data}
            
        except Exception as e:
            logger.error(f"Error handling Vietnam stock command: {str(e)}")
            self.client.send_message(from_number, f"Error getting Vietnam stock data: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _handle_game_command(self, from_number: str, args: str) -> Dict:
        """Handle country guessing game command
        
        Args:
            from_number (str): Sender's phone number
            args (str): Command arguments (game mode)
            
        Returns:
            Dict: Command handling result
        """
        try:
            # Parse game mode
            mode = args.strip().lower() if args else "map"
            
            if mode not in ["map", "flag", "cap"]:
                self.client.send_message(from_number, 
                    "Invalid game mode. Please use one of: map, flag, cap")
                return {"success": False, "error": "Invalid game mode"}
            
            # Get a random country for the game
            country = self.game_handler._get_random_country()
            
            # Store the game session
            self.active_games[from_number] = {
                "country": country,
                "mode": mode,
                "attempts": 0,
                "max_attempts": 3  # Allow 3 attempts per question
            }
            
            # Prepare the game message based on mode
            if mode == "map":
                # For map mode, send the map image with options
                map_path = f"country_game/images/wiki_all_map_400pi/{country['name'].replace(' ', '_')}_locator_map.png"
                message = "🗺️ Guess the country shown on this map:"
                
                # Generate options (would need to be adapted for WhatsApp)
                options = self.game_handler._generate_options(country, mode)
                options_text = "\n".join([f"{i+1}. {option}" for i, option in enumerate(options)])
                
                # For now, we'll send the options as text
                full_message = f"{message}\n\n{options_text}\n\nReply with the number or name of the country."
                
                # In a real implementation, we would need to host this image and get a URL
                # For now, let's assume we have a URL for demonstration
                media_url = f"https://example.com/maps/{country['name'].replace(' ', '_')}_map.png"
                
                # Send media with caption
                # Note: In a real implementation, you would need to host the images or use a service
                self.client.send_message(from_number, full_message)
                # self.client.send_media(from_number, media_url, "🗺️ Guess the country shown on this map:")
                
            elif mode == "flag":
                # For flag mode, send the flag image with options
                flag_path = f"country_game/images/wiki_flag/{country['name'].replace(' ', '_')}_flag.png"
                message = "🏳️ Guess the country this flag belongs to:"
                
                # Generate options
                options = self.game_handler._generate_options(country, mode)
                options_text = "\n".join([f"{i+1}. {option}" for i, option in enumerate(options)])
                
                full_message = f"{message}\n\n{options_text}\n\nReply with the number or name of the country."
                
                # In a real implementation, we would need to host this image and get a URL
                media_url = f"https://example.com/flags/{country['name'].replace(' ', '_')}_flag.png"
                
                # Send media with caption
                self.client.send_message(from_number, full_message)
                # self.client.send_media(from_number, media_url, "🏳️ Guess the country this flag belongs to:")
                
            else:  # cap mode
                # For capital mode, ask about the capital
                message = f"🏙️ What is the capital city of {country['name']}?"
                
                # Generate options
                options = self.game_handler._generate_options(country, mode)
                options_text = "\n".join([f"{i+1}. {option}" for i, option in enumerate(options)])
                
                full_message = f"{message}\n\n{options_text}\n\nReply with the number or name of the capital."
                
                self.client.send_message(from_number, full_message)
            
            return {
                "success": True, 
                "game_started": True,
                "mode": mode,
                "country": country["name"]
            }
            
        except Exception as e:
            logger.error(f"Error handling game command: {str(e)}")
            self.client.send_message(from_number, f"Error starting game: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _handle_game_answer(self, from_number: str, answer: str) -> Dict:
        """Handle a game answer
        
        Args:
            from_number (str): Sender's phone number
            answer (str): User's answer
            
        Returns:
            Dict: Answer handling result
        """
        # Get the active game for this user
        game = self.active_games.get(from_number)
        if not game:
            self.client.send_message(from_number, "You don't have an active game. Start one with /g map, /g flag, or /g cap")
            return {"success": False, "error": "No active game"}
        
        # Process the answer
        country = game["country"]
        mode = game["mode"]
        
        # Check if the answer is correct
        is_correct = False
        correct_answer = ""
        
        if mode in ["map", "flag"]:
            correct_answer = country["name"]
            
            # Check if the answer is correct (either by number or text)
            if answer.isdigit():
                # User answered with a number
                options = self.game_handler._generate_options(country, mode)
                try:
                    selected_option = options[int(answer) - 1]
                    is_correct = selected_option.lower() == correct_answer.lower()
                except (IndexError, ValueError):
                    is_correct = False
            else:
                # User answered with text
                is_correct = answer.lower() == correct_answer.lower()
                
        else:  # cap mode
            correct_answer = country["capital"]
            
            # Check if the answer is correct (either by number or text)
            if answer.isdigit():
                # User answered with a number
                options = self.game_handler._generate_options(country, mode)
                try:
                    selected_option = options[int(answer) - 1]
                    is_correct = selected_option.lower() == correct_answer.lower()
                except (IndexError, ValueError):
                    is_correct = False
            else:
                # User answered with text
                is_correct = answer.lower() == correct_answer.lower()
        
        # Increment attempts
        game["attempts"] += 1
        
        # Prepare response based on correctness
        if is_correct:
            if mode in ["map", "flag"]:
                response = f"✅ Correct! That is indeed {correct_answer}.\n\n"
                response += f"Population: {self.game_handler._format_population(country['population'])}\n"
                response += f"Area: {self.game_handler._format_area(country['area'])}\n"
                response += f"Capital: {country['capital']}\n"
                response += f"Continent: {country['continent']}"
                
                # Update user stats (would be stored in database in real implementation)
                self.game_handler._update_user_stats(from_number, True, mode)
                
            else:  # cap mode
                response = f"✅ Correct! {correct_answer} is the capital of {country['name']}.\n\n"
                response += f"Population: {self.game_handler._format_population(country['population'])}\n"
                response += f"Area: {self.game_handler._format_area(country['area'])}\n"
                response += f"Continent: {country['continent']}"
                
                # Update user stats
                self.game_handler._update_user_stats(from_number, True, mode)
                
            # Remove the active game
            del self.active_games[from_number]
            
        else:
            # Check if max attempts reached
            if game["attempts"] >= game["max_attempts"]:
                if mode in ["map", "flag"]:
                    response = f"❌ Wrong answer. You've used all your attempts.\n\nThe correct answer is {correct_answer}."
                else:  # cap mode
                    response = f"❌ Wrong answer. You've used all your attempts.\n\nThe capital of {country['name']} is {correct_answer}."
                
                # Update user stats
                self.game_handler._update_user_stats(from_number, False, mode)
                
                # Remove the active game
                del self.active_games[from_number]
                
            else:
                # User still has attempts left
                attempts_left = game["max_attempts"] - game["attempts"]
                response = f"❌ Wrong answer. You have {attempts_left} attempt(s) left."
        
        # Send the response
        self.client.send_message(from_number, response)
        
        # If game ended, offer to play again
        if is_correct or game["attempts"] >= game["max_attempts"]:
            play_again_msg = "Want to play again? Send:\n/g map - for map game\n/g flag - for flag game\n/g cap - for capital game"
            self.client.send_message(from_number, play_again_msg)
            
        return {
            "success": True,
            "correct": is_correct,
            "attempts": game["attempts"] if from_number in self.active_games else game["max_attempts"],
            "game_active": from_number in self.active_games
        }