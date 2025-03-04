import os
import random
import sqlite3
import logging
import time
from typing import Dict, List, Optional, Tuple, Set, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackContext
import asyncio

# Set up logging
logger = logging.getLogger(__name__)

# Game constants
GAME_TIMEOUT = 15  # 15 seconds to answer
NUM_OPTIONS = 10   # Number of answer options to provide

class GameHandler:
    """Handles the country guessing game functionality"""

    def __init__(self):
        """Initialize the game handler"""
        # Load countries from the database
        self.countries = self.load_countries()
        # Store active games by user_id
        self.active_games = {}
        # Game stats by user_id
        self.user_stats = {}
        # Timer tasks for active games
        self.timer_tasks = {}
        self.current_game_mode = None # Added to track the current game mode

    async def _game_timeout_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int) -> None:
        """Handle game timeout"""
        try:
            await asyncio.sleep(GAME_TIMEOUT)
            
            # Check if the game is still active
            if user_id not in self.active_games:
                return
                
            # Get the game data
            game = self.active_games[user_id]
            correct_country = game["country"]
            correct_country_name = correct_country["name"].replace("_", " ")
            
            # Build timeout message
            timeout_msg = f"⏱️ Time's up! The correct answer was *{correct_country_name}*.\n\n"
            
            # Add country details
            timeout_msg += f"🏳️ {correct_country_name}\n"
            timeout_msg += f"📊 Quick Facts:\n"
            timeout_msg += f"🏙️ Capital: {correct_country.get('capital', 'Unknown')}\n"
            
            # Get region information
            region = self._get_mock_region(correct_country["name"])
            subregion = self._get_mock_subregion(correct_country["name"])
            timeout_msg += f"🌍 Region: {region}"
            if subregion:
                timeout_msg += f" ({subregion})"
            timeout_msg += "\n"
            
            # Get population and area information
            population = self._get_mock_population(correct_country["name"])
            area = self._get_mock_area(correct_country["name"])
            timeout_msg += f"👥 Population: {self._format_population(population)}\n"
            timeout_msg += f"📏 Area: {self._format_area(area)}"

            # Send timeout message
            chat_id = update.effective_chat.id
            
            # Get message ID and mode
            message_id = game.get("message_id")
            current_mode = game.get("mode", "map")
            
            # Try to edit the existing message with the timeout information
            try:
                if current_mode in ["map", "flag"]:
                    await context.bot.edit_message_caption(
                        chat_id=chat_id,
                        message_id=message_id,
                        caption=timeout_msg,
                        parse_mode="Markdown"
                    )
                else:  # Capital mode
                    await context.bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=message_id,
                        text=timeout_msg,
                        parse_mode="Markdown"
                    )
            except Exception as e:
                logger.error(f"Error editing timeout message: {e}")
                # Fallback to sending a new message
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=timeout_msg,
                    parse_mode="Markdown"
                )
                
            # Update stats
            self._update_user_stats(user_id, False)
            
            # Remove the active game
            del self.active_games[user_id]
            
            # Send navigation buttons for next game
            await self._send_game_navigation(update, context)
                
        except asyncio.CancelledError:
            logger.info(f"Timer for user {user_id} was cancelled")
        except Exception as e:
            logger.error(f"Error in game timeout callback: {e}")

    def _get_random_country(self, game_mode: str = "map") -> Dict:
        """
        Get a random country that has appropriate assets for the specified game mode
        """
        logger.info(f"Getting random country for game mode: {game_mode}")
        
        # Filter countries based on game mode
        suitable_countries = []
        
        if game_mode == "map":
            # For map mode, check if country has a map image
            for country in self.countries:
                map_path = os.path.join("country_game", "images", "wiki_all_map_400pi", f"{country['name']}_locator_map.png")
                if os.path.exists(map_path):
                    suitable_countries.append(country)
                    
        elif game_mode == "flag":
            # For flag mode, check if country has a flag image
            for country in self.countries:
                flag_path = os.path.join("country_game", "images", "wiki_flag", f"{country['name']}_flag.png")
                if os.path.exists(flag_path):
                    suitable_countries.append(country)
                    
        elif game_mode == "capital":
            # For capital mode, only include countries with known capitals
            for country in self.countries:
                if country.get("capital") and country["capital"] != "Unknown":
                    suitable_countries.append(country)
        
        # Log the number of suitable countries
        logger.info(f"Found {len(suitable_countries)} suitable countries for {game_mode} mode")
        
        # If no suitable countries were found, return None
        if not suitable_countries:
            logger.warning(f"No suitable countries found for {game_mode} mode")
            return None
            
        # Pick a random country from the suitable ones
        country = random.choice(suitable_countries)
        logger.info(f"Selected random country: {country['name']}")
        
        return country


    def load_countries(self) -> List[Dict]:
        """Load countries from database or fall back to sample data"""
        try:
            # Try to open the SQLite database
            db_path = os.path.join("country_game", "database", "countries.db")
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                cur = conn.cursor()
                # Check if countries table exists
                cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='countries'")
                if cur.fetchone():
                    # Get countries with their data, including neighbors
                    cur.execute("SELECT name, capital, population, area, region, neighbors FROM countries")
                    rows = cur.fetchall()
                    conn.close()

                    # Return a list of dictionaries with country info
                    countries = []
                    for row in rows:
                        if row[0]:  # Ensure country name exists
                            neighbors = row[5].split(",") if row[5] else []
                            countries.append({
                                "name": row[0],
                                "capital": row[1] if row[1] else "Unknown",
                                "population": row[2] if row[2] else "Unknown",
                                "area": row[3] if row[3] else "Unknown",
                                "region": row[4] if row[4] else "Unknown",
                                "neighbors": [n.strip() for n in neighbors]
                            })

                    logger.info(f"Loaded {len(countries)} countries from database")
                    return countries

            # If we get here, either the database doesn't exist or the table is missing
            logger.warning("Countries table not found in database. Using fallback data.")
            return self._get_fallback_countries()

        except Exception as e:
            logger.error(f"Database error: {e}. Falling back to sample data.")
            return self._get_fallback_countries()

    def _get_fallback_countries(self) -> List[Dict]:
        """Return a comprehensive list of countries as fallback with capitals and neighbors"""
        # This is a more comprehensive list of countries with capitals and some neighbors
        return [
            {"name": "Afghanistan", "capital": "Kabul", "population": "Unknown", "area": "Unknown", "region": "Asia",
             "neighbors": ["Iran", "Pakistan", "Turkmenistan", "Uzbekistan", "Tajikistan", "China"]},
            {"name": "Albania", "capital": "Tirana", "population": "Unknown", "area": "Unknown", "region": "Europe",
             "neighbors": ["Montenegro", "Kosovo", "North_Macedonia", "Greece"]},
            {"name": "Algeria", "capital": "Algiers", "population": "Unknown", "area": "Unknown", "region": "Africa",
             "neighbors": ["Tunisia", "Libya", "Niger", "Mali", "Mauritania", "Morocco"]},
            {"name": "Andorra", "capital": "Andorra la Vella", "population": "Unknown", "area": "Unknown", "region": "Europe",
             "neighbors": ["France", "Spain"]},
            {"name": "Angola", "capital": "Luanda", "population": "Unknown", "area": "Unknown", "region": "Africa",
             "neighbors": ["Namibia", "Zambia", "Democratic_Republic_of_the_Congo", "Republic_of_the_Congo"]},
            {"name": "Argentina", "capital": "Buenos Aires", "population": "Unknown", "area": "Unknown", "region": "South America",
             "neighbors": ["Chile", "Bolivia", "Paraguay", "Brazil", "Uruguay"]},
            {"name": "Armenia", "capital": "Yerevan", "population": "Unknown", "area": "Unknown", "region": "Asia",
             "neighbors": ["Georgia", "Azerbaijan", "Iran", "Turkey"]},
            {"name": "Australia", "capital": "Canberra", "population": "Unknown", "area": "Unknown", "region": "Oceania",
             "neighbors": ["New_Zealand", "Indonesia", "Papua_New_Guinea"]},
            {"name": "Austria", "capital": "Vienna", "population": "Unknown", "area": "Unknown", "region": "Europe",
             "neighbors": ["Germany", "Czech_Republic", "Slovakia", "Hungary", "Slovenia", "Italy", "Switzerland", "Liechtenstein"]},
            {"name": "Azerbaijan", "capital": "Baku", "population": "Unknown", "area": "Unknown", "region": "Asia",
             "neighbors": ["Russia", "Georgia", "Armenia", "Iran", "Turkey"]},
            {"name": "Bahamas", "capital": "Nassau", "population": "Unknown", "area": "Unknown", "region": "North America",
             "neighbors": ["United_States", "Cuba"]},
            {"name": "Bahrain", "capital": "Manama", "population": "Unknown", "area": "Unknown", "region": "Asia",
             "neighbors": ["Saudi_Arabia", "Qatar"]},
            {"name": "Bangladesh", "capital": "Dhaka", "population": "Unknown", "area": "Unknown", "region": "Asia",
             "neighbors": ["India", "Myanmar"]},
            {"name": "Barbados", "capital": "Bridgetown", "population": "Unknown", "area": "Unknown", "region": "North America",
             "neighbors": ["Saint_Lucia", "Saint_Vincent_and_the_Grenadines"]},
            {"name": "Belarus", "capital": "Minsk", "population": "Unknown", "area": "Unknown", "region": "Europe",
             "neighbors": ["Russia", "Ukraine", "Poland", "Lithuania", "Latvia"]},
            {"name": "Belgium", "capital": "Brussels", "population": "Unknown", "area": "Unknown", "region": "Europe",
             "neighbors": ["Netherlands", "Germany", "Luxembourg", "France"]},
            {"name": "Belize", "capital": "Belmopan", "population": "Unknown", "area": "Unknown", "region": "North America",
             "neighbors": ["Mexico", "Guatemala"]},
            {"name": "Benin", "capital": "Porto-Novo", "population": "Unknown", "area": "Unknown", "region": "Africa",
             "neighbors": ["Nigeria", "Togo", "Burkina_Faso", "Niger"]},
            {"name": "Bhutan", "capital": "Thimphu", "population": "Unknown", "area": "Unknown", "region": "Asia",
             "neighbors": ["India", "China"]},
            {"name": "Bolivia", "capital": "Sucre", "population": "Unknown", "area": "Unknown", "region": "South America",
             "neighbors": ["Brazil", "Paraguay", "Argentina", "Chile", "Peru"]},
            {"name": "Bosnia_and_Herzegovina", "capital": "Sarajevo", "population": "Unknown", "area": "Unknown", "region": "Europe",
             "neighbors": ["Croatia", "Serbia", "Montenegro"]},
            {"name": "Botswana", "capital": "Gaborone", "population": "Unknown", "area": "Unknown", "region": "Africa",
             "neighbors": ["South_Africa", "Namibia", "Zimbabwe", "Zambia"]},
            {"name": "Brazil", "capital": "Brasilia", "population": "Unknown", "area": "Unknown", "region": "South America",
             "neighbors": ["Argentina", "Paraguay", "Uruguay", "Bolivia", "Peru", "Colombia", "Venezuela", "Guyana", "Suriname", "French_Guiana"]},
            {"name": "Brunei", "capital": "Bandar Seri Begawan", "population": "Unknown", "area": "Unknown", "region": "Asia",
             "neighbors": ["Malaysia"]},
            {"name": "Bulgaria", "capital": "Sofia", "population": "Unknown", "area": "Unknown", "region": "Europe",
             "neighbors": ["Romania", "Serbia", "North_Macedonia", "Greece", "Turkey"]},
            {"name": "Burkina_Faso", "capital": "Ouagadougou", "population": "Unknown", "area": "Unknown", "region": "Africa",
             "neighbors": ["Mali", "Niger", "Benin", "Togo", "Ghana", "Ivory_Coast"]},
            {"name": "Burundi", "capital": "Gitega", "population": "Unknown", "area": "Unknown", "region": "Africa",
             "neighbors": ["Rwanda", "Tanzania", "Democratic_Republic_of_the_Congo"]},
            {"name": "Cambodia", "capital": "Phnom Penh", "population": "Unknown", "area": "Unknown", "region": "Asia",
             "neighbors": ["Thailand", "Laos", "Vietnam"]},
            {"name": "Cameroon", "capital": "Yaoundé", "population": "Unknown", "area": "Unknown", "region": "Africa",
             "neighbors": ["Nigeria", "Chad", "Central_African_Republic", "Republic_of_the_Congo", "Gabon", "Equatorial_Guinea"]},
            {"name": "Canada", "capital": "Ottawa", "population": "Unknown", "area": "Unknown", "region": "North America",
             "neighbors": ["United_States"]},
            {"name": "Central_African_Republic", "capital": "Bangui", "population": "Unknown", "area": "Unknown", "region": "Africa",
             "neighbors": ["Chad", "Sudan", "South_Sudan", "Democratic_Republic_of_the_Congo", "Republic_of_the_Congo", "Cameroon"]},
            {"name": "Chad", "capital": "N'Djamena", "population": "Unknown", "area": "Unknown", "region": "Africa",
             "neighbors": ["Libya", "Sudan", "Central_African_Republic", "Cameroon", "Nigeria", "Niger"]},
            {"name": "Chile", "capital": "Santiago", "population": "Unknown", "area": "Unknown", "region": "South America",
             "neighbors": ["Peru", "Bolivia", "Argentina"]},
            {"name": "China", "capital": "Beijing", "population": "Unknown", "area": "Unknown", "region": "Asia",
             "neighbors": ["Russia", "Mongolia", "North_Korea", "Vietnam", "Laos", "Myanmar", "India", "Bhutan", "Nepal", "Pakistan", "Afghanistan", "Tajikistan", "Kyrgyzstan", "Kazakhstan"]},
            {"name": "Colombia", "capital": "Bogotá", "population": "Unknown", "area": "Unknown", "region": "South America",
             "neighbors": ["Venezuela", "Brazil", "Peru", "Ecuador", "Panama"]},
            {"name": "Comoros", "capital": "Moroni", "population": "Unknown", "area": "Unknown", "region": "Africa",
             "neighbors": ["Madagascar", "Mozambique", "Tanzania"]},
            {"name": "Congo", "capital": "Brazzaville", "population": "Unknown", "area": "Unknown", "region": "Africa",
             "neighbors": ["Democratic_Republic_of_the_Congo", "Angola", "Gabon", "Cameroon", "Central_African_Republic"]},
            {"name": "Costa_Rica", "capital": "San José", "population": "Unknown", "area": "Unknown", "region": "North America",
             "neighbors": ["Nicaragua", "Panama"]},
            {"name": "Croatia", "capital": "Zagreb", "population": "Unknown", "area": "Unknown", "region": "Europe",
             "neighbors": ["Slovenia", "Hungary", "Serbia", "Bosnia_and_Herzegovina", "Montenegro"]},
            {"name": "Cuba", "capital": "Havana", "population": "Unknown", "area": "Unknown", "region": "North America",
             "neighbors": ["United_States"]},
            {"name": "Cyprus", "capital": "Nicosia", "population": "Unknown", "area": "Unknown", "region": "Asia",
             "neighbors": ["Turkey", "Greece"]},
            {"name": "Czech_Republic", "capital": "Prague", "population": "Unknown", "area": "Unknown", "region": "Europe",
             "neighbors": ["Germany", "Poland", "Slovakia", "Austria"]},
            {"name": "Democratic_Republic_of_the_Congo", "capital": "Kinshasa", "population": "Unknown", "area": "Unknown", "region": "Africa",
             "neighbors": ["Republic_of_the_Congo", "Central_African_Republic", "South_Sudan", "Uganda", "Rwanda", "Burundi", "Tanzania", "Zambia", "Angola"]},
            {"name": "Denmark", "capital": "Copenhagen", "population": "Unknown", "area": "Unknown", "region": "Europe",
             "neighbors": ["Germany", "Sweden", "Norway"]},
            {"name": "Djibouti", "capital": "Djibouti", "population": "Unknown", "area": "Unknown", "region": "Africa",
             "neighbors": ["Eritrea", "Ethiopia", "Somalia"]},
            {"name": "Dominican_Republic", "capital": "Santo Domingo", "population": "Unknown", "area": "Unknown", "region": "North America",
             "neighbors": ["Haiti"]},
            {"name": "Ecuador", "capital": "Quito", "population": "Unknown", "area": "Unknown", "region": "South America",
             "neighbors": ["Colombia", "Peru"]},
            {"name": "Egypt", "capital": "Cairo", "population": "Unknown", "area": "Unknown", "region": "Africa",
             "neighbors": ["Libya", "Sudan", "Israel", "Palestine"]},
            {"name": "El_Salvador", "capital": "San Salvador", "population": "Unknown", "area": "Unknown", "region": "North America",
             "neighbors": ["Guatemala", "Honduras"]},
            {"name": "Equatorial_Guinea", "capital": "Malabo", "population": "Unknown", "area": "Unknown", "region": "Africa",
             "neighbors": ["Cameroon", "Gabon"]},
            {"name": "Eritrea", "capital": "Asmara", "population": "Unknown", "area": "Unknown", "region": "Africa",
             "neighbors": ["Sudan", "Ethiopia", "Djibouti"]},
            {"name": "Estonia", "capital": "Tallinn", "population": "Unknown", "area": "Unknown", "region": "Europe",
             "neighbors": ["Russia", "Latvia"]},
            {"name": "Eswatini", "capital": "Mbabane", "population": "Unknown", "area": "Unknown", "region": "Africa",
             "neighbors": ["South_Africa", "Mozambique"]},
            {"name": "Ethiopia", "capital": "Addis Ababa", "population": "Unknown", "area": "Unknown", "region": "Africa",
             "neighbors": ["Eritrea", "Djibouti", "Somalia", "Kenya", "South_Sudan", "Sudan"]},
            {"name": "Fiji", "capital": "Suva", "population": "Unknown", "area": "Unknown", "region": "Oceania",
             "neighbors": ["Vanuatu", "Tonga", "Samoa"]},
            {"name": "Finland", "capital": "Helsinki", "population": "Unknown", "area": "Unknown", "region": "Europe",
             "neighbors": ["Sweden", "Norway", "Russia"]},
            {"name": "France", "capital": "Paris", "population": "Unknown", "area": "Unknown", "region": "Europe",
             "neighbors": ["Belgium", "Luxembourg", "Germany", "Switzerland", "Italy", "Monaco", "Spain", "Andorra"]},
            {"name": "Gabon", "capital": "Libreville", "population": "Unknown", "area": "Unknown", "region": "Africa",
             "neighbors": ["Equatorial_Guinea", "Cameroon", "Republic_of_the_Congo"]},
            {"name": "Gambia", "capital": "Banjul", "population": "Unknown", "area": "Unknown", "region": "Africa",
             "neighbors": ["Senegal"]},
            {"name": "Georgia", "capital": "Tbilisi", "population": "Unknown", "area": "Unknown", "region": "Asia",
             "neighbors": ["Russia", "Azerbaijan", "Armenia", "Turkey"]},
            {"name": "Germany", "capital": "Berlin", "population": "Unknown", "area": "Unknown", "region": "Europe",
             "neighbors": ["Denmark", "Poland", "Czech_Republic", "Austria", "Switzerland", "France", "Luxembourg", "Belgium", "Netherlands"]},
            {"name": "Ghana", "capital": "Accra", "population": "Unknown", "area": "Unknown", "region": "Africa",
             "neighbors": ["Burkina_Faso", "Ivory_Coast", "Togo"]},
            {"name": "Greece", "capital": "Athens", "population": "Unknown", "area": "Unknown", "region": "Europe",
             "neighbors": ["Albania", "North_Macedonia", "Bulgaria", "Turkey"]},
            {"name": "Guatemala", "capital": "Guatemala City", "population": "Unknown", "area": "Unknown", "region": "North America",
             "neighbors": ["Mexico", "Belize", "Honduras", "El_Salvador"]},
            {"name": "Guinea", "capital": "Conakry", "population": "Unknown", "area": "Unknown", "region": "Africa",
             "neighbors": ["Guinea-Bissau", "Senegal", "Mali", "Ivory_Coast", "Liberia", "Sierra_Leone"]},
            {"name": "Guinea-Bissau", "capital": "Bissau", "population": "Unknown", "area": "Unknown", "region": "Africa",
             "neighbors": ["Senegal", "Guinea"]},
            {"name": "Guyana", "capital": "Georgetown", "population": "Unknown", "area": "Unknown", "region": "South America",
             "neighbors": ["Venezuela", "Brazil", "Suriname"]},
            {"name": "Haiti", "capital": "Port-au-Prince", "population": "Unknown", "area": "Unknown", "region": "North America",
             "neighbors": ["Dominican_Republic"]},
            {"name": "Honduras", "capital": "Tegucigalpa", "population": "Unknown", "area": "Unknown", "region": "North America",
             "neighbors": ["Guatemala", "El_Salvador", "Nicaragua"]},
            {"name": "Hungary", "capital": "Budapest", "population": "Unknown", "area": "Unknown", "region": "Europe",
             "neighbors": ["Slovakia", "Ukraine", "Romania", "Serbia", "Croatia", "Slovenia", "Austria"]},
            {"name": "Iceland", "capital": "Reykjavik", "population": "Unknown", "area": "Unknown", "region": "Europe",
             "neighbors": ["Norway", "Denmark", "United_Kingdom"]},
            {"name": "India", "capital": "New Delhi", "population": "Unknown", "area": "Unknown", "region": "Asia",
             "neighbors": ["Pakistan", "China", "Nepal", "Bhutan", "Bangladesh", "Myanmar", "Sri_Lanka"]},
            {"name": "Indonesia", "capital": "Jakarta", "population": "Unknown", "area": "Unknown", "region": "Asia",
             "neighbors": ["Papua_New_Guinea", "Malaysia", "East_Timor", "Australia"]},
            {"name": "Iran", "capital": "Tehran", "population": "Unknown", "area": "Unknown", "region": "Asia",
             "neighbors": ["Iraq", "Turkey", "Armenia", "Azerbaijan", "Turkmenistan", "Afghanistan", "Pakistan"]},
            {"name": "Iraq", "capital": "Baghdad", "population": "Unknown", "area": "Unknown", "region": "Asia",
             "neighbors": ["Iran", "Turkey", "Syria", "Jordan", "Saudi_Arabia", "Kuwait"]},
            {"name": "Ireland", "capital": "Dublin", "population": "Unknown", "area": "Unknown", "region": "Europe",
             "neighbors": ["United_Kingdom"]},
            {"name": "Israel", "capital": "Jerusalem", "population": "Unknown", "area": "Unknown", "region": "Asia",
             "neighbors": ["Lebanon", "Syria", "Jordan", "Egypt", "Palestine"]},
            {"name": "Italy", "capital": "Rome", "population": "Unknown", "area": "Unknown", "region": "Europe",
             "neighbors": ["France", "Switzerland", "Austria", "Slovenia", "San_Marino", "Vatican_City"]},
            {"name": "Ivory_Coast", "capital": "Yamoussoukro", "population": "Unknown", "area": "Unknown", "region": "Africa",
             "neighbors": ["Liberia", "Guinea", "Mali", "Burkina_Faso", "Ghana"]},
            {"name": "Jamaica", "capital": "Kingston", "population": "Unknown", "area": "Unknown", "region": "North America",
             "neighbors": ["Cuba", "Haiti"]},
            {"name": "Japan", "capital": "Tokyo", "population": "Unknown", "area": "Unknown", "region": "Asia",
             "neighbors": ["South_Korea", "China", "Russia"]},
            {"name": "Jordan", "capital": "Amman", "population": "Unknown", "area": "Unknown", "region": "Asia",
             "neighbors": ["Syria", "Iraq", "Saudi_Arabia", "Israel", "Palestine"]},
            {"name": "Kazakhstan", "capital": "Nur-Sultan", "population": "Unknown", "area": "Unknown", "region": "Asia",
             "neighbors": ["Russia", "China", "Kyrgyzstan", "Uzbekistan", "Turkmenistan"]},
            {"name": "Kenya", "capital": "Nairobi", "population": "Unknown", "area": "Unknown", "region": "Africa",
             "neighbors": ["Ethiopia", "Somalia", "South_Sudan", "Uganda", "Tanzania"]},
            {"name": "Kiribati", "capital": "Tarawa", "population": "Unknown", "area": "Unknown", "region": "Oceania",
             "neighbors": ["Marshall_Islands", "Nauru"]},
            {"name": "Kosovo", "capital": "Pristina", "population": "Unknown", "area": "Unknown", "region": "Europe",
             "neighbors": ["Serbia", "North_Macedonia", "Albania", "Montenegro"]},
            {"name": "Kuwait", "capital": "Kuwait City", "population": "Unknown", "area": "Unknown", "region": "Asia",
             "neighbors": ["Iraq", "Saudi_Arabia"]},
            {"name": "Kyrgyzstan", "capital": "Bishkek", "population": "Unknown", "area": "Unknown", "region": "Asia",
             "neighbors": ["Kazakhstan", "China", "Tajikistan", "Uzbekistan"]},
            {"name": "Laos", "capital": "Vientiane", "population": "Unknown", "area": "Unknown", "region": "Asia",
             "neighbors": ["China", "Vietnam", "Cambodia", "Thailand", "Myanmar"]},
            {"name": "Latvia", "capital": "Riga", "population": "Unknown", "area": "Unknown", "region": "Europe",
             "neighbors": ["Estonia", "Russia", "Belarus", "Lithuania"]},
            {"name": "Lebanon", "capital": "Beirut", "population": "Unknown", "area": "Unknown", "region": "Asia",
             "neighbors": ["Syria", "Israel"]},
            {"name": "Lesotho", "capital": "Maseru", "population": "Unknown", "area": "Unknown", "region": "Africa",
             "neighbors": ["South_Africa"]},
            {"name": "Liberia", "capital": "Monrovia", "population": "Unknown", "area": "Unknown", "region": "Africa",
             "neighbors": ["Sierra_Leone", "Guinea", "Ivory_Coast"]},
            {"name": "Libya", "capital": "Tripoli", "population": "Unknown", "area": "Unknown", "region": "Africa",
             "neighbors": ["Egypt", "Sudan", "Chad", "Niger", "Algeria", "Tunisia"]},
            {"name": "Liechtenstein", "capital": "Vaduz", "population": "Unknown", "area": "Unknown", "region": "Europe",
             "neighbors": ["Switzerland", "Austria"]},
            {"name": "Lithuania", "capital": "Vilnius", "population": "Unknown", "area": "Unknown", "region": "Europe",
             "neighbors": ["Latvia", "Belarus", "Poland", "Russia"]},
            {"name": "Luxembourg", "capital": "Luxembourg City", "population": "Unknown", "area": "Unknown", "region": "Europe",
             "neighbors": ["Belgium", "France", "Germany"]},
            {"name": "Madagascar", "capital": "Antananarivo", "population": "Unknown", "area": "Unknown", "region": "Africa",
             "neighbors": ["Comoros", "Mauritius", "Reunion"]},
            {"name": "Malawi", "capital": "Lilongwe", "population": "Unknown", "area": "Unknown", "region": "Africa",
             "neighbors": ["Tanzania", "Mozambique", "Zambia"]},
            {"name": "Malaysia", "capital": "Kuala Lumpur", "population": "Unknown", "area": "Unknown", "region": "Asia",
             "neighbors": ["Thailand", "Indonesia", "Brunei", "Singapore"]},
            {"name": "Maldives", "capital": "Malé", "population": "Unknown", "area": "Unknown", "region": "Asia",
             "neighbors": ["Sri_Lanka", "India"]},
            {"name": "Mali", "capital": "Bamako", "population": "Unknown", "area": "Unknown", "region": "Africa",
             "neighbors": ["Algeria", "Niger", "Burkina_Faso", "Ivory_Coast", "Guinea", "Senegal", "Mauritania"]},
            {"name": "Malta", "capital": "Valletta", "population": "Unknown", "area": "Unknown", "region": "Europe",
             "neighbors": ["Italy", "Tunisia"]},
            {"name": "Marshall_Islands", "capital": "Majuro", "population": "Unknown", "area": "Unknown", "region": "Oceania",
             "neighbors": ["Kiribati", "Micronesia"]},
            {"name": "Mauritania", "capital": "Nouakchott", "population": "Unknown", "area": "Unknown", "region": "Africa",
             "neighbors": ["Western_Sahara", "Algeria", "Mali", "Senegal"]},
            {"name": "Mauritius", "capital": "Port Louis", "population": "Unknown", "area": "Unknown", "region": "Africa",
             "neighbors": ["Madagascar", "Reunion"]},
            {"name": "Mexico", "capital": "Mexico City", "population": "Unknown", "area": "Unknown", "region": "North America",
             "neighbors": ["United_States", "Guatemala", "Belize"]},
            {"name": "Micronesia", "capital": "Palikir", "population": "Unknown", "area": "Unknown", "region": "Oceania",
             "neighbors": ["Marshall_Islands", "Palau"]},
            {"name": "Moldova", "capital": "Chișinău", "population": "Unknown", "area": "Unknown", "region": "Europe",
             "neighbors": ["Romania", "Ukraine"]},
            {"name": "Monaco", "capital": "Monaco", "population": "Unknown", "area": "Unknown", "region": "Europe",
             "neighbors": ["France"]},
            {"name": "Mongolia", "capital": "Ulaanbaatar", "population": "Unknown", "area": "Unknown", "region": "Asia",
             "neighbors": ["Russia", "China"]},
            {"name": "Montenegro", "capital": "Podgorica", "population": "Unknown", "area": "Unknown", "region": "Europe",
             "neighbors": ["Croatia", "Bosnia_and_Herzegovina", "Serbia", "Kosovo", "Albania"]},
            {"name": "Morocco", "capital": "Rabat", "population": "Unknown", "area": "Unknown", "region": "Africa",
             "neighbors": ["Algeria", "Western_Sahara", "Spain"]},
            {"name": "Mozambique", "capital": "Maputo", "population": "Unknown", "area": "Unknown", "region": "Africa",
             "neighbors": ["Tanzania", "Malawi", "Zambia", "Zimbabwe", "South_Africa", "Eswatini"]},
            {"name": "Myanmar", "capital": "Naypyidaw", "population": "Unknown", "area": "Unknown", "region": "Asia",
             "neighbors": ["Bangladesh", "India", "China", "Laos", "Thailand"]},
            {"name": "Namibia", "capital": "Windhoek", "population": "Unknown", "area": "Unknown", "region": "Africa",
             "neighbors": ["Angola", "Zambia", "Botswana", "South_Africa"]},
            {"name": "Nauru", "capital": "Yaren", "population": "Unknown", "area": "Unknown", "region": "Oceania",
             "neighbors": ["Kiribati", "Marshall_Islands"]},
            {"name": "Nepal", "capital": "Kathmandu", "population": "Unknown", "area": "Unknown", "region": "Asia",
             "neighbors": ["India", "China"]},
            {"name": "Netherlands", "capital": "Amsterdam", "population": "Unknown", "area": "Unknown", "region": "Europe",
             "neighbors": ["Germany", "Belgium"]},
            {"name": "New_Zealand", "capital": "Wellington", "population": "Unknown", "area": "Unknown", "region": "Oceania",
             "neighbors": ["Australia", "Fiji"]},
            {"name": "Nicaragua", "capital": "Managua", "population": "Unknown", "area": "Unknown", "region": "North America",
             "neighbors": ["Honduras", "Costa_Rica"]},
            {"name": "Niger", "capital": "Niamey", "population": "Unknown", "area": "Unknown", "region": "Africa",
             "neighbors": ["Algeria", "Libya", "Chad", "Nigeria", "Benin", "Burkina_Faso", "Mali"]},
            {"name": "Seychelles", "capital": "Victoria", "population": "Unknown", "area": "Unknown", "region": "Africa",
             "neighbors": ["Madagascar", "Mauritius"]},
            {"name": "Sierra_Leone", "capital": "Freetown", "population": "Unknown", "area": "Unknown", "region": "Africa",
             "neighbors": ["Guinea", "Liberia"]},
            {"name": "Singapore", "capital": "Singapore", "population": "Unknown", "area": "Unknown", "region": "Asia",
             "neighbors": ["Malaysia", "Indonesia"]},
            {"name": "Slovakia", "capital": "Bratislava", "population": "Unknown", "area": "Unknown", "region": "Europe",
             "neighbors": ["Poland", "Hungary", "Austria", "Czech_Republic", "Ukraine"]},
            {"name": "Slovenia", "capital": "Ljubljana", "population": "Unknown", "area": "Unknown", "region": "Europe",
             "neighbors": ["Italy", "Austria", "Hungary", "Croatia"]},
            {"name": "Solomon_Islands", "capital": "Honiara", "population": "Unknown", "area": "Unknown", "region": "Oceania",
             "neighbors": ["Papua_New_Guinea", "Vanuatu"]},
            {"name": "Nigeria", "capital": "Abuja", "population": "Unknown", "area": "Unknown", "region": "Africa",
             "neighbors": ["Niger", "Chad", "Cameroon", "Benin"]},
            {"name": "North_Korea", "capital": "Pyongyang", "population": "Unknown", "area": "Unknown", "region": "Asia",
             "neighbors": ["China", "South_Korea", "Russia"]},
            {"name": "North_Macedonia", "capital": "Skopje", "population": "Unknown", "area": "Unknown", "region": "Europe",
             "neighbors": ["Kosovo", "Serbia", "Bulgaria", "Greece", "Albania"]},
            {"name": "Norway", "capital": "Oslo", "population": "Unknown", "area": "Unknown", "region": "Europe",
             "neighbors": ["Sweden", "Finland", "Russia"]},
            {"name": "Oman", "capital": "Muscat", "population": "Unknown", "area": "Unknown", "region": "Asia",
             "neighbors": ["United_Arab_Emirates", "Saudi_Arabia", "Yemen"]},
            {"name": "Pakistan", "capital": "Islamabad", "population": "Unknown", "area": "Unknown", "region": "Asia",
             "neighbors": ["Iran", "Afghanistan", "China", "India"]},
            {"name": "Palau", "capital": "Ngerulmud", "population": "Unknown", "area": "Unknown", "region": "Oceania",
             "neighbors": ["Philippines", "Micronesia"]},
            {"name": "Palestine", "capital": "Ramallah", "population": "Unknown", "area": "Unknown", "region": "Asia",
             "neighbors": ["Israel", "Jordan", "Egypt"]},
            {"name": "Panama", "capital": "Panama City", "population": "Unknown", "area": "Unknown", "region": "North America",
             "neighbors": ["Costa_Rica", "Colombia"]},
            {"name": "Papua_New_Guinea", "capital": "Port Moresby", "population": "Unknown", "area": "Unknown", "region": "Oceania",
             "neighbors": ["Indonesia", "Australia"]},
            {"name": "Paraguay", "capital": "Asunción", "population": "Unknown", "area": "Unknown", "region": "South America",
             "neighbors": ["Bolivia", "Brazil", "Argentina"]},
            {"name": "Peru", "capital": "Lima", "population": "Unknown", "area": "Unknown", "region": "South America",
             "neighbors": ["Ecuador", "Colombia", "Brazil", "Bolivia", "Chile"]},
            {"name": "Philippines", "capital": "Manila", "population": "Unknown", "area": "Unknown", "region": "Asia",
             "neighbors": ["Taiwan", "Indonesia", "Malaysia"]},
            {"name": "Poland", "capital": "Warsaw", "population": "Unknown", "area": "Unknown", "region": "Europe",
             "neighbors": ["Germany", "Czech_Republic", "Slovakia", "Ukraine", "Belarus", "Lithuania", "Russia"]},
            {"name": "Portugal", "capital": "Lisbon", "population": "Unknown","area": "Unknown", "region": "Europe",
             "neighbors": ["Spain"]},
            {"name": "Qatar", "capital": "Doha", "population": "Unknown","area": "Unknown", "region": "Asia",
             "neighbors": ["Saudi_Arabia", "United_Arab_Emirates", "Bahrain"]},
            {"name": "Romania", "capital": "Bucharest", "population": "Unknown", "area": "Unknown", "region": "Europe",
             "neighbors": ["Moldova", "Ukraine", "Hungary", "Serbia", "Bulgaria"]},
            {"name": "Russia", "capital": "Moscow", "population": "Unknown", "area": "Unknown", "region": "Europe",
             "neighbors": ["Norway", "Finland", "Estonia", "Latvia", "Lithuania", "Poland", "Belarus", "Ukraine", "Georgia", "Azerbaijan", "Kazakhstan", "China", "Mongolia", "North_Korea"]},
            {"name": "Rwanda", "capital": "Kigali", "population": "Unknown", "area": "Unknown", "region": "Africa",
             "neighbors": ["Uganda", "Tanzania", "Burundi", "Democratic_Republic_of_the_Congo"]},
            {"name": "Saint_Kitts_and_Nevis", "capital": "Basseterre", "population": "Unknown", "area": "Unknown", "region": "North America",
             "neighbors": ["Antigua_and_Barbuda", "Saint_Lucia"]},
            {"name": "Saint_Lucia", "capital": "Castries", "population": "Unknown", "area": "Unknown", "region": "North America",
             "neighbors": ["Saint_Vincent_and_the_Grenadines", "Barbados"]},
            {"name": "Saint_Vincent_and_the_Grenadines", "capital": "Kingstown", "population": "Unknown", "area": "Unknown", "region": "North America",
             "neighbors": ["Saint_Lucia", "Barbados"]},
            {"name": "Samoa", "capital": "Apia", "population": "Unknown", "area": "Unknown", "region": "Oceania",
             "neighbors": ["Fiji", "Tonga"]},
            {"name": "San_Marino", "capital": "San Marino", "population": "Unknown", "area": "Unknown", "region": "Europe",
             "neighbors": ["Italy"]},
            {"name": "Saudi_Arabia", "capital": "Riyadh", "population": "Unknown", "area": "Unknown", "region": "Asia",
             "neighbors": ["Jordan", "Iraq", "Kuwait", "Bahrain", "Qatar", "United_Arab_Emirates", "Oman", "Yemen"]},
            {"name": "Senegal", "capital": "Dakar", "population": "Unknown", "area": "Unknown", "region": "Africa",
             "neighbors": ["Mauritania", "Mali", "Guinea", "Guinea-Bissau", "Gambia"]},
            {"name": "Serbia", "capital": "Belgrade", "population": "Unknown", "area": "Unknown", "region": "Europe",
             "neighbors": ["Hungary", "Romania", "Bulgaria", "North_Macedonia", "Kosovo", "Montenegro", "Bosnia_and_Herzegovina", "Croatia"]},
            {"name": "Seychelles", "capital": "Victoria", "population": "Unknown", "area": "Unknown", "region": "Africa",
             "neighbors": ["Madagascar", "Mauritius"]},
            {"name": "Sierra_Leone", "capital": "Freetown", "population": "Unknown", "area": "Unknown", "region": "Africa",
             "neighbors": ["Guinea", "Liberia"]},
            {"name": "Singapore", "capital": "Singapore", "population": "Unknown", "area": "Unknown", "region": "Asia",
             "neighbors": ["Malaysia", "Indonesia"]},
            {"name": "Slovakia", "capital": "Bratislava", "population": "Unknown", "area": "Unknown", "region": "Europe",
             "neighbors": ["Poland", "Ukraine", "Hungary", "Austria", "Czech_Republic"]},
            {"name": "Slovenia", "capital": "Ljubljana", "population": "Unknown", "area": "Unknown", "region": "Europe",
             "neighbors": ["Italy", "Austria", "Hungary", "Croatia"]},
            {"name": "Solomon_Islands", "capital": "Honiara", "population": "Unknown", "area": "Unknown", "region": "Oceania",
             "neighbors": ["Papua_New_Guinea", "Vanuatu"]},
            {"name": "Somalia", "capital": "Mogadishu", "population": "Unknown", "area": "Unknown", "region": "Africa",
             "neighbors": ["Ethiopia", "Kenya", "Djibouti"]},
            {"name": "South_Africa", "capital": "Pretoria", "population": "Unknown", "area": "Unknown", "region": "Africa",
             "neighbors": ["Namibia", "Botswana", "Zimbabwe", "Mozambique", "Eswatini", "Lesotho"]},
            {"name": "South_Korea", "capital": "Seoul", "population": "Unknown", "area": "Unknown", "region": "Asia",
             "neighbors": ["North_Korea", "Japan"]},
            {"name": "South_Sudan", "capital": "Juba", "population": "Unknown", "area": "Unknown", "region": "Africa",
             "neighbors": ["Sudan", "Ethiopia", "Kenya", "Uganda", "Democratic_Republic_of_the_Congo", "Central_African_Republic"]},
            {"name": "Spain", "capital": "Madrid", "population": "Unknown", "area": "Unknown", "region": "Europe",
             "neighbors": ["Portugal", "France", "Andorra", "Morocco"]},
            {"name": "Sri_Lanka", "capital": "Colombo", "population": "Unknown", "area": "Unknown", "region": "Asia",
             "neighbors": ["India", "Maldives"]},
            {"name": "Sudan", "capital": "Khartoum", "population": "Unknown", "area": "Unknown", "region": "Africa",
             "neighbors": ["Egypt", "Libya", "Chad", "Central_African_Republic", "South_Sudan", "Ethiopia", "Eritrea"]},
            {"name": "Suriname", "capital": "Paramaribo", "population": "Unknown", "area": "Unknown", "region": "South America",
             "neighbors": ["Guyana", "Brazil", "French_Guiana"]},
            {"name": "Sweden", "capital": "Stockholm", "population": "Unknown", "area": "Unknown", "region": "Europe",
             "neighbors": ["Norway", "Finland", "Denmark"]},
            {"name": "Switzerland", "capital": "Bern", "population": "Unknown", "area": "Unknown", "region": "Europe",
             "neighbors": ["France", "Germany", "Austria", "Liechtenstein", "Italy"]},
            {"name": "Syria", "capital": "Damascus", "population": "Unknown", "area": "Unknown", "region": "Asia",
             "neighbors": ["Turkey", "Iraq", "Jordan", "Israel", "Lebanon"]},
            {"name": "Taiwan", "capital": "Taipei", "population": "Unknown", "area": "Unknown", "region": "Asia",
             "neighbors": ["China", "Japan", "Philippines"]},
            {"name": "Tajikistan", "capital": "Dushanbe", "population": "Unknown", "area": "Unknown", "region": "Asia",
             "neighbors": ["Uzbekistan", "Kyrgyzstan", "China", "Afghanistan"]},
            {"name": "Tanzania", "capital": "Dodoma", "population": "Unknown", "area": "Unknown", "region": "Africa",
             "neighbors": ["Kenya", "Uganda", "Rwanda", "Burundi", "Democratic_Republic_of_the_Congo", "Zambia", "Malawi", "Mozambique"]},
            {"name": "Thailand", "capital": "Bangkok", "population": "Unknown", "area": "Unknown", "region": "Asia",
             "neighbors": ["Myanmar", "Laos", "Cambodia", "Malaysia"]},
            {"name": "Timor-Leste", "capital": "Dili", "population": "Unknown", "area": "Unknown", "region": "Asia",
             "neighbors": ["Indonesia"]},
            {"name": "Togo", "capital": "Lomé", "population": "Unknown", "area": "Unknown", "region": "Africa",
             "neighbors": ["Ghana", "Burkina_Faso", "Benin"]},
            {"name": "Tonga", "capital": "Nukuʻalofa", "population": "Unknown", "area": "Unknown", "region": "Oceania",
             "neighbors": ["Fiji", "Samoa"]},
            {"name": "Trinidad_and_Tobago", "capital": "Port of Spain", "population": "Unknown", "area": "Unknown", "region": "North America",
             "neighbors": ["Venezuela"]},
            {"name": "Tunisia", "capital": "Tunis", "population": "Unknown", "area": "Unknown", "region": "Africa",
             "neighbors": ["Algeria", "Libya"]},
            {"name": "Turkey", "capital": "Ankara", "population": "Unknown", "area": "Unknown", "region": "Asia",
             "neighbors": ["Greece", "Bulgaria", "Georgia", "Armenia", "Azerbaijan", "Iran", "Iraq", "Syria"]},
            {"name": "Turkmenistan", "capital": "Ashgabat", "population": "Unknown", "area": "Unknown", "region": "Asia",
             "neighbors": ["Kazakhstan", "Uzbekistan", "Afghanistan", "Iran"]},
            {"name": "Tuvalu", "capital": "Funafuti", "population": "Unknown", "area": "Unknown", "region": "Oceania",
             "neighbors": ["Fiji", "Kiribati"]},
            {"name": "Uganda", "capital": "Kampala", "population": "Unknown", "area": "Unknown", "region": "Africa",
             "neighbors": ["Kenya", "South_Sudan", "Democratic_Republic_of_the_Congo", "Rwanda", "Tanzania"]},
            {"name": "Ukraine", "capital": "Kyiv", "population": "Unknown", "area": "Unknown", "region": "Europe",
             "neighbors": ["Belarus", "Russia", "Moldova", "Romania", "Hungary", "Slovakia", "Poland"]},
            {"name": "United_Arab_Emirates", "capital": "Abu Dhabi", "population": "Unknown", "area": "Unknown", "region": "Asia",
             "neighbors": ["Saudi_Arabia", "Oman"]},
            {"name": "United_Kingdom", "capital": "London", "population": "Unknown", "area": "Unknown", "region": "Europe",
             "neighbors": ["Ireland", "France", "Iceland"]},
            {"name": "United_States", "capital": "Washington, D.C.", "population": "Unknown", "area": "Unknown", "region": "North America",
             "neighbors": ["Canada", "Mexico"]},
            {"name": "Uruguay", "capital": "Montevideo", "population": "Unknown", "area": "Unknown", "region": "South America",
             "neighbors": ["Argentina", "Brazil"]},
            {"name": "Uzbekistan", "capital": "Tashkent", "population": "Unknown", "area": "Unknown", "region": "Asia",
             "neighbors": ["Kazakhstan", "Kyrgyzstan", "Tajikistan", "Afghanistan", "Turkmenistan"]},
            {"name": "Vanuatu", "capital": "Port Vila", "population": "Unknown", "area": "Unknown", "region": "Oceania",
             "neighbors": ["Solomon_Islands", "Fiji"]},
            {"name": "Vatican_City", "capital": "Vatican City", "population": "Unknown", "area": "Unknown", "region": "Europe",
             "neighbors": ["Italy"]},
            {"name": "Venezuela", "capital": "Caracas", "population": "Unknown", "area": "Unknown", "region": "South America",
             "neighbors": ["Colombia", "Brazil", "Guyana", "Trinidad_and_Tobago"]},
            {"name": "Vietnam", "capital": "Hanoi", "population": "Unknown", "area": "Unknown", "region": "Asia",
             "neighbors": ["China", "Laos", "Cambodia"]},
            {"name": "Western_Sahara", "capital": "El Aaiún", "population": "Unknown", "area": "Unknown", "region": "Africa",
             "neighbors": ["Morocco", "Algeria", "Mauritania"]},
            {"name": "Yemen", "capital": "Sana'a", "population": "Unknown", "area": "Unknown", "region": "Asia",
             "neighbors": ["Saudi_Arabia", "Oman"]},
            {"name": "Zambia", "capital": "Lusaka", "population": "Unknown", "area": "Unknown", "region": "Africa",
             "neighbors": ["Democratic_Republic_of_the_Congo", "Tanzania", "Malawi", "Mozambique", "Zimbabwe", "Botswana", "Namibia", "Angola"]},
            {"name": "Zimbabwe", "capital": "Harare", "population": "Unknown", "area": "Unknown", "region": "Africa",
             "neighbors": ["Zambia", "Mozambique", "South_Africa", "Botswana"]}
        ]

    def get_random_country(self) -> Dict:
        """Return a random country from the loaded countries"""
        # If we're running in capital mode, any country is fine
        if hasattr(self, 'current_game_mode') and self.current_game_mode == "capital":
            return random.choice(self.countries)

        # For map and flag modes, we need to make sure the image exists
        valid_countries = []
        for country in self.countries:
            country_name = country['name']

            # Check if flag image exists for this country
            flag_path = os.path.join("country_game", "images", "wiki_flag", f"{country_name}_flag.png")

            # Check if map image exists for this country
            map_path = os.path.join("country_game", "images", "wiki_all_map_400pi", f"{country_name}_locator_map.png")

            # If we're in flag mode, we only need the flag image
            if hasattr(self, 'current_game_mode') and self.current_game_mode == "flag" and os.path.exists(flag_path):
                valid_countries.append(country)
            # If we're in map mode, we only need the map image
            elif hasattr(self, 'current_game_mode') and self.current_game_mode == "map" and os.path.exists(map_path):
                valid_countries.append(country)
            # If game mode isn't set yet, add countries that have at least one image
            elif not hasattr(self, 'current_game_mode') and (os.path.exists(flag_path) or os.path.exists(map_path)):
                valid_countries.append(country)

        # If we have valid countries with images, return one of those
        if valid_countries:
            return random.choice(valid_countries)

        # Fallback to any country if no valid ones with images are found
        return random.choice(self.countries)

    def get_answer_options(self, correct_country: Dict) -> List[Dict]:
        """Generate a list of answer options (1 correct + up to 9 others)"""
        options = []

        # Add the correct country
        options.append(correct_country)

        # Try to add neighbors first
        neighbors = correct_country.get("neighbors", [])
        neighbor_countries = []

        for neighbor_name in neighbors:
            # Clean up the name by replacing underscores
            clean_name = neighbor_name.replace("_", " ")
            # Find matching countries
            for country in self.countries:
                if country["name"].replace("_", " ").lower() == clean_name.lower():
                    neighbor_countries.append(country)
                    break

        # Add unique neighbors to options
        for country in neighbor_countries:
            if len(options) < NUM_OPTIONS and country["name"] != correct_country["name"]:
                options.append(country)

        # If we don't have enough options, add random countries
        other_countries = [c for c in self.countries if c["name"] != correct_country["name"]
                          and c not in options]
        random.shuffle(other_countries)

        for country in other_countries:
            if len(options) < NUM_OPTIONS:
                options.append(country)
            else:
                break

        # Shuffle options to randomize button positions
        random.shuffle(options)
        return options

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Display help information for the game"""
        help_text = (
            "🌍 *Country Guessing Game Options* 🌍\n\n"
            "*/g help* - Show this help message\n"
            "*/g* or */g map* - Launch game in map mode (guess from a map)\n"
            "*/g flag* - Launch game in flag mode (guess from a flag)\n"
            "*/g capital* - Launch game in capital mode (guess from a capital city)\n\n"
            "To play: simply tap on the correct country from the options provided.\n"
            "You have 15 seconds to answer each question."
        )
        await update.message.reply_text(help_text, parse_mode="Markdown")

    async def start_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE, game_mode: str = "map") -> None:
        """Start a new game with the specified mode"""
        # Get user ID
        user_id = update.effective_user.id

        # Get a random country with suitable images
        country = self._get_random_country(game_mode)
        if not country:
            await update.message.reply_text(f"Sorry, I couldn't find any suitable countries for the {game_mode} game mode.")
            return

        # Cancel any existing timer for this user
        self._cancel_timer(user_id)

        # Get answer options (including the correct one)
        options = self.get_answer_options(country)

        # Create inline keyboard for answers
        keyboard = []
        row = []
        for i, option in enumerate(options):
            display_name = option["name"].replace("_", " ")
            callback_data = f"guess_{option['name']}"
            row.append(InlineKeyboardButton(display_name, callback_data=callback_data))

            # Create a new row after every 2 buttons
            if (i + 1) % 2 == 0 or (i + 1) == len(options):
                keyboard.append(row)
                row = []

        reply_markup = InlineKeyboardMarkup(keyboard)

        # Create game state
        game_data = {
            "country": country,
            "start_time": time.time(),
            "attempts": 0,
            "mode": game_mode,  # Store the game mode
            "hints_used": 0     # Track how many hints were used
        }

        # Store the game state
        self.active_games[user_id] = game_data

        # Send game question based on mode
        if game_mode == "map":
            # Map mode - send country map
            map_path = os.path.join("country_game", "images", "wiki_all_map_400pi", f"{country['name']}_locator_map.png")
            
            if os.path.exists(map_path):
                message = await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=open(map_path, 'rb'),
                    caption="🌍 Which country is shown on this map?",
                    reply_markup=reply_markup
                )
                # Store the message ID for later updating
                game_data["message_id"] = message.message_id
            else:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"Sorry, I couldn't find a map for {country['name'].replace('_', ' ')}. Try another game!"
                )
                del self.active_games[user_id]
                await self._send_game_navigation(update, context)
                return
                
        elif game_mode == "flag":
            # Flag mode - send country flag
            flag_path = os.path.join("country_game", "images", "wiki_flag", f"{country['name']}_flag.png")
            
            if os.path.exists(flag_path):
                message = await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=open(flag_path, 'rb'),
                    caption="🏳️ Which country does this flag belong to?",
                    reply_markup=reply_markup
                )
                # Store the message ID for later updating
                game_data["message_id"] = message.message_id
            else:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"Sorry, I couldn't find a flag for {country['name'].replace('_', ' ')}. Try another game!"
                )
                del self.active_games[user_id]
                await self._send_game_navigation(update, context)
                return
                
        elif game_mode == "capital":
            # Capital mode - send capital name
            message = await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"🏙️ Which country has *{country['capital']}* as its capital?",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            # Store the message ID for later updating
            game_data["message_id"] = message.message_id
            
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Invalid game mode. Use /g help for options."
            )
            del self.active_games[user_id]
            return

        # Log the game start
        logger.info(f"Starting {game_mode} game for user {user_id} with country {country['name']}")

        # Set a timer for this game that actually waits GAME_TIMEOUT seconds
        self.timer_tasks[user_id] = asyncio.create_task(
            self._game_timeout_callback(update, context, user_id)
        )

    def _cancel_timer(self, user_id: int) -> None:
        """Cancel the timer for a specific user if it exists"""
        if user_id in self.timer_tasks:
            task = self.timer_tasks.pop(user_id)
            if not task.done():
                task.cancel()



    async def _send_map_challenge(self, update: Update, context: ContextTypes.DEFAULT_TYPE, country: Dict) -> None:
        """Send a map challenge to the user with multiple-choice options"""
        country_name = country["name"]
        image_path = os.path.join("country_game", "images", "wiki_all_map_400pi", f"{country_name}_locator_map.png")

        try:
            # Generate answer options (1 correct + 9 others)
            options = self.get_answer_options(country)

            # Create inline keyboard with answer options
            keyboard = []
            row = []
            for i, option in enumerate(options):
                display_name = option["name"].replace("_", " ")
                # Ensure consistency by using the exact country name as stored in the database
                callback_data = f"guess_{option['name']}"
                logger.info(f"Creating button for {display_name} with callback_data: {callback_data}")
                row.append(InlineKeyboardButton(display_name, callback_data=callback_data))

                # Create a new row after every 2 buttons
                if (i + 1) % 2 == 0 or (i + 1) == len(options):
                    keyboard.append(row)
                    row = []

            reply_markup = InlineKeyboardMarkup(keyboard)

            with open(image_path, "rb") as photo_file:
                caption = "🗺️ *Guess the country from this map!*\nYou have 15 seconds to answer."
                message = await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=photo_file,
                    caption=caption,
                    parse_mode="Markdown",
                    reply_markup=reply_markup
                )

                # Store the message_id for potential cleanup later
                self.active_games[update.effective_user.id]["message_id"] = message.message_id

                # Set a timer for this game that actually waits GAME_TIMEOUT seconds
                self.timer_tasks[update.effective_user.id] = asyncio.create_task(
                    self._game_timeout_callback(update, context, update.effective_user.id)
                )

        except FileNotFoundError:
            logger.error(f"Map image not found for {country_name}: {image_path}")
            await update.message.reply_text(
                f"Sorry, I couldn't find the map for this country. Try another game!"
            )
            # Clean up the game state
            if update.effective_user.id in self.active_games:
                del self.active_games[update.effective_user.id]

    async def _send_flag_challenge(self, update: Update, context: ContextTypes.DEFAULT_TYPE, country: Dict) -> None:
        """Send a flag challenge to the user with multiple-choice options"""
        country_name = country["name"]
        image_path = os.path.join("country_game", "images", "wiki_flag", f"{country_name}_flag.png")

        try:
            # Generate answer options (1 correct + 9 others)
            options = self.get_answer_options(country)

            # Create inline keyboard with answer options
            keyboard = []
            row = []
            for i, option in enumerate(options):
                display_name = option["name"].replace("_", " ")
                # Ensure consistency by using the exact country name as stored in the database
                callback_data = f"guess_{option['name']}"
                logger.info(f"Creating button for {display_name} with callback_data: {callback_data}")
                row.append(InlineKeyboardButton(display_name, callback_data=callback_data))

                # Create a new row after every 2 buttons
                if (i + 1) % 2 == 0 or (i + 1) == len(options):
                    keyboard.append(row)
                    row = []

            reply_markup = InlineKeyboardMarkup(keyboard)

            with open(image_path, "rb") as photo_file:
                caption = "🏳️ *Guess the country from this flag!*\nYou have 15 seconds to answer."
                message = await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=photo_file,
                    caption=caption,
                    parse_mode="Markdown",
                    reply_markup=reply_markup
                )

                # Store the message_id for potential cleanup later
                self.active_games[update.effective_user.id]["message_id"] = message.message_id

                # Set a timer for this game that actually waits GAME_TIMEOUT seconds
                self.timer_tasks[update.effective_user.id] = asyncio.create_task(
                    self._game_timeout_callback(update, context, update.effective_user.id)
                )

        except FileNotFoundError:
            logger.error(f"Flag image not found for {country_name}: {image_path}")
            await update.message.reply_text(
                f"Sorry, I couldn't find the flag for this country. Try another game!"
            )
            # Clean up the game state
            if update.effective_user.id in self.active_games:
                del self.active_games[update.effective_user.id]

    async def _send_capital_challenge(self, update: Update, context: ContextTypes.DEFAULT_TYPE, country: Dict) -> None:
        """Send a capital challenge to the user with multiple-choice options"""
        capital = country.get("capital", "Unknown")

        # Generate answer options (1 correct + 9 others)
        options = self.get_answer_options(country)

        # Create inline keyboard with answer options
        keyboard = []
        row = []
        for i, option in enumerate(options):
            display_name = option["name"].replace("_", " ")
            # Ensure consistency by using the exact country name as stored in the database
            callback_data = f"guess_{option['name']}"
            logger.info(f"Creating button for {display_name} with callback_data: {callback_data}")
            row.append(InlineKeyboardButton(display_name, callback_data=callback_data))

            # Create a new row after every 2 buttons
            if (i + 1) % 2 == 0 or (i + 1) == len(options):
                keyboard.append(row)
                row = []

        reply_markup = InlineKeyboardMarkup(keyboard)

        message = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"🏙️ *Guess the country whose capital is:* {capital}\nYou have 15 seconds to answer.",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )

        # Store the message_id for potential cleanup later
        self.active_games[update.effective_user.id]["message_id"] = message.message_id

        # Set a timer for this game that actually waits GAME_TIMEOUT seconds
        self.timer_tasks[update.effective_user.id] = asyncio.create_task(
            self._game_timeout_callback(update, context, update.effective_user.id)
        )

    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handles callback queries from inline keyboards."""
        query = update.callback_query
        user_id = update.effective_user.id
        
        # Add detailed logging to help debug navigation buttons
        logger.info(f"Received callback query with data: {query.data} from user {user_id}")

        # Cancel the timer for this game if it exists
        self._cancel_timer(user_id)

        await query.answer()  # Acknowledge the button press to Telegram
        
        # Check if it's a game guess
        if query.data.startswith("guess_"):
            logger.info(f"Processing guess: {query.data}")
            # Only process guesses if there's an active game
            if user_id in self.active_games:
                await self._handle_guess(update, context, query)
            else:
                logger.warning(f"Received guess but no active game for user {user_id}")
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="No active game found. Start a new game with /g"
                )
                # Send game navigation buttons
                await self._send_game_navigation(update, context)
        # Check if it's a navigation button
        elif query.data.startswith("play_"):
            game_mode = query.data.split("_")[1]
            logger.info(f"Starting new game with mode: {game_mode}")
            if game_mode == "help":
                await self.help_command(update, context)
            else:
                # Always allow starting a new game regardless of active_games state
                await self.start_game(update, context, game_mode)
        else:
            logger.warning(f"Unrecognized callback data: {query.data}")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Unrecognized button. Try /g to start a new game."
            )

    async def _handle_guess(self, update: Update, context: ContextTypes.DEFAULT_TYPE, query) -> None:
        """Handle a guess from the inline keyboard"""
        user_id = update.effective_user.id

        # Make sure this user has an active game
        if user_id not in self.active_games:
            await query.answer("No active game found. Start a new game with /g")
            return

        # Get game data
        game = self.active_games[user_id]
        correct_country = game["country"]["name"]
        guess = query.data.replace("guess_", "")
        current_mode = game.get("mode", "map")  # Default to map mode if not specified

        # Get chat ID for responding
        chat_id = update.effective_chat.id

        # Calculate elapsed time
        elapsed_time = round(time.time() - game["start_time"], 1)

        # Debug logs to help diagnose comparison issues
        logger.info(f"Comparing guess '{guess}' with correct answer '{correct_country}'")
        logger.info(f"After normalization: '{guess.lower().replace('_', '')}' vs '{correct_country.lower().replace('_', '')}'")

        # Fix: Normalize both strings for comparison to avoid false negatives
        # This makes the comparison more robust against format differences
        is_correct = guess.lower().replace("_", "") == correct_country.lower().replace("_", "")
        logger.info(f"Is correct: {is_correct}")

        # Get the message ID from the game state
        message_id = game.get("message_id")

        # Find the details of both the correct country and the guessed country
        correct_country_data = next((c for c in self.countries if c["name"] == correct_country), None)
        guessed_country_data = next((c for c in self.countries if c["name"] == guess), None)

        # Get the country population and area (mock data as this isn't in our database)
        population = self._get_mock_population(correct_country)
        area = self._get_mock_area(correct_country)
        region = self._get_mock_region(correct_country)
        subregion = self._get_mock_subregion(correct_country)

        # Get the map image path for the correct country
        map_path = f"country_game/images/wiki_all_map_400pi/{correct_country}_locator_map.png"
        flag_path = f"country_game/images/wiki_flag/{correct_country}_flag.png"

        if is_correct:
            # User got it right
            correct_msg = f"✅ Correct! The answer is indeed {correct_country.replace('_', ' ')}!\n\n"
            correct_msg += f"🎯 Impressive geography skills,  You are a Marveller!\n\n"
            correct_msg += f"👥 Population: {population:,}\n"
            correct_msg += f"🗺️ Area: {area:,.1f} km²\n"
            correct_msg += f"🏙️ Capital: {correct_country_data.get('capital', 'Unknown')}\n"
            correct_msg += f"🌎 Region: {region}"
            if subregion:
                correct_msg += f" ({subregion})"
            correct_msg += "\n"

            # Add neighbors if available
            neighbors = correct_country_data.get("neighbors", [])
            if neighbors:
                formatted_neighbors = [n.replace("_", " ") for n in neighbors]
                correct_msg += f"🏘️ Neighbors: {', '.join(formatted_neighbors)}"

            # Try to edit the message with the image
            try:
                if current_mode in ["map", "flag"]:
                    await context.bot.edit_message_caption(
                        chat_id=chat_id,
                        message_id=message_id,
                        caption=correct_msg,
                        parse_mode="Markdown"
                    )
                else:  # Capital mode
                    await context.bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=message_id,
                        text=correct_msg,
                        parse_mode="Markdown"
                    )
            except Exception as e:
                logger.error(f"Error editing message: {e}")
                # Fallback to sending a new message
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=correct_msg,
                    parse_mode="Markdown"
                )

            # Acknowledge the callback query
            await query.answer("✅ Correct!")

            # Update stats
            self._update_user_stats(user_id, True)

        else:
            # User got it wrong
            guessed_country_name = guess.replace('_', ' ')
            correct_country_name = correct_country.replace('_', ' ')

            wrong_msg = f"❌ Wrong answer! You are a VOZER. 😢\n\n"
            wrong_msg += f"You selected: {guessed_country_name}\n"
            wrong_msg += f"Correct answer: {correct_country_name}\n\n"

            # Add flag emoji and country details
            wrong_msg += f"🏳️ {correct_country_name}\n"
            wrong_msg += f"📊 Quick Facts:\n"
            wrong_msg += f"🏙️ Capital: {correct_country_data.get('capital', 'Unknown')}\n"
            wrong_msg += f"🌍 Region: {region}"
            if subregion:
                wrong_msg += f" ({subregion})"
            wrong_msg += "\n"
            wrong_msg += f"👥 Population: {self._format_population(population)}\n"
            wrong_msg += f"📏 Area: {self._format_area(area)}"

            # Try to edit the message with the image
            try:
                if current_mode in ["map", "flag"]:
                    await context.bot.edit_message_caption(
                        chat_id=chat_id,
                        message_id=message_id,
                        caption=wrong_msg,
                        parse_mode="Markdown"
                    )
                else:  # Capital mode
                    await context.bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=message_id,
                        text=wrong_msg,
                        parse_mode="Markdown"
                    )
            except Exception as e:
                logger.error(f"Error editing message: {e}")
                # Fallback to sending a new message
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=wrong_msg,
                    parse_mode="Markdown"
                )

            # Acknowledge the callback query
            await query.answer("❌ Incorrect")

            # Update stats
            self._update_user_stats(user_id, False)

        # Game is completed, let's clean up
        # Remove the active game state
        del self.active_games[user_id]

        # Cancel any existing timer
        self._cancel_timer(user_id)

        # Send game navigation buttons
        await self._send_game_navigation(update, context)



    def _format_population(self, population: int) -> str:
        """Format population number for better readability"""
        if population >= 1000000000:
            return f"{population/1000000000:.1f}B"
        elif population >= 1000000:
            return f"{population/1000000:.1f}M"
        elif population >= 1000:
            return f"{population/1000:.1f}K"
        return str(population)

    def _get_mock_population(self, country_name: str) -> int:
        """Return mock population data for a country"""
        # This is mock data for demonstration purposes
        populations = {
            "United_States": 331002651,
            "China": 1444216107,
            "India": 1393409038,
            "Brazil": 213993437,
            "Russia": 145912025,
            "Japan": 126050804,
            "Germany": 83149300,
            "United_Kingdom": 67886011,
            "France": 65426179,
            "Italy": 60367477,
            "Mexico": 130262216,
            "Canada": 38008005,
            "Australia": 25687041,
            "Nigeria": 211400708,
            "Egypt": 102334404,
            "South_Africa": 59308690,
            "Kenya": 53771296,
            "Saudi_Arabia": 34813871,
            "Argentina": 45376763,
            "Algeria": 44616624,
            "Sudan": 43849260,
            "Ukraine": 43733762,
            "Iraq": 40222493,
            "Poland": 37846611,
            "Iran": 83992949,
            "Spain": 46754778,
            "Turkey": 84339067,
            "Vietnam": 97338579,
            "Comoros": 869601,
            "Bahrain": 1701575,
        }

        # Return a population if we have it, or a random believable number if not
        return populations.get(country_name, random.randint(500000, 200000000))

    def _get_mock_area(self, country_name: str) -> float:
        """Return mock area data for a country in km²"""
        # This is mock data for demonstration purposes
        areas = {
            "United_States": 9372610.0,
            "China": 9706961.0,
            "India": 3287263.0,
            "Brazil": 8515767.0,
            "Russia": 17098246.0,
            "Japan": 377930.0,
            "Germany": 357022.0,
            "United_Kingdom": 242900.0,
            "France": 551695.0,
            "Italy": 301340.0,
            "Mexico": 1964375.0,
            "Canada": 9984670.0,
            "Australia": 7692024.0,
            "Nigeria": 923768.0,
            "Egypt": 1001450.0,
            "South_Africa": 1221037.0,
            "Kenya": 580367.0,
            "Saudi_Arabia": 2149690.0,
            "Argentina": 2780400.0,
            "Algeria": 2381741.0,
            "Sudan": 1886068.0,
            "Ukraine": 603500.0,
            "Iraq": 438317.0,
            "Poland": 312696.0,
            "Iran": 1648195.0,
            "Spain": 505990.0,
            "Turkey": 783562.0,
            "Vietnam": 331212.0,
            "Comoros": 1862.0,
            "Bahrain": 765.3,
        }

        # Return an area if we have it, or a random believable number if not
        return areas.get(country_name, random.uniform(1000.0, 1000000.0))

    def _get_mock_region(self, country_name: str) -> str:
        """Return mock region data for a country"""
        # This is mock data for demonstration purposes
        regions = {
            "United_States": "Americas",
            "China": "Asia",
            "India": "Asia",
            "Brazil": "Americas",
            "Russia": "Europe",
            "Japan": "Asia",
            "Germany": "Europe",
            "United_Kingdom": "Europe",
            "France": "Europe",
            "Italy": "Europe",
            "Mexico": "Americas",
            "Canada": "Americas",
            "Australia": "Oceania",
            "Nigeria": "Africa",
            "Egypt": "Africa",
            "South_Africa": "Africa",
            "Kenya": "Africa",
            "Saudi_Arabia": "Asia",
            "Argentina": "Americas",
            "Algeria": "Africa",
            "Sudan": "Africa",
            "Ukraine": "Europe",
            "Iraq": "Asia",
            "Poland": "Europe",
            "Iran": "Asia",
            "Spain": "Europe",
            "Turkey": "Asia",
            "Vietnam": "Asia",
            "Comoros": "Africa",
            "Bahrain": "Asia",
        }

        # Map continents to regions as a fallback
        continent_mapping = {
            "Afghanistan": "Asia", "Albania": "Europe", "Algeria": "Africa", "Andorra": "Europe",
            "Angola": "Africa", "Argentina": "Americas", "Armenia": "Asia", "Australia": "Oceania",
            "Austria": "Europe", "Azerbaijan": "Asia", "Bahamas": "Americas", "Bahrain": "Asia",
            "Bangladesh": "Asia", "Barbados": "Americas", "Belarus": "Europe", "Belgium": "Europe",
            "Belize": "Americas", "Benin": "Africa", "Bhutan": "Asia", "Bolivia": "Americas",
            "Bosnia_and_Herzegovina": "Europe", "Botswana": "Africa", "Brazil": "Americas", "Brunei": "Asia",
            "Bulgaria": "Europe", "Burkina_Faso": "Africa", "Burundi": "Africa", "Cambodia": "Asia",
            "Cameroon": "Africa", "Canada": "Americas", "Central_African_Republic": "Africa", "Chad": "Africa",
            "Chile": "Americas", "China": "Asia", "Colombia": "Americas", "Comoros": "Africa",
            "Congo": "Africa", "Costa_Rica": "Americas", "Croatia": "Europe", "Cuba": "Americas",
            "Cyprus": "Europe", "Czech_Republic": "Europe", "Democratic_Republic_of_the_Congo": "Africa",
            "Denmark": "Europe", "Djibouti": "Africa", "Dominican_Republic": "Americas", "Ecuador": "Americas",
            "Egypt": "Africa", "El_Salvador": "Americas", "Equatorial_Guinea": "Africa", "Eritrea": "Africa",
            "Estonia": "Europe", "Eswatini": "Africa", "Ethiopia": "Africa", "Fiji": "Oceania",
            "Finland": "Europe", "France": "Europe", "Gabon": "Africa", "Gambia": "Africa",
            "Georgia": "Asia", "Germany": "Europe", "Ghana": "Africa", "Greece": "Europe",
            "Guatemala": "Americas", "Guinea": "Africa", "Guinea-Bissau": "Africa", "Guyana": "Americas",
            "Haiti": "Americas", "Honduras": "Americas", "Hungary": "Europe", "Iceland": "Europe",
            "India": "Asia", "Indonesia": "Asia", "Iran": "Asia", "Iraq": "Asia",
            "Ireland": "Europe", "Israel": "Asia", "Italy": "Europe", "Ivory_Coast": "Africa",
            "Jamaica": "Americas", "Japan": "Asia", "Jordan": "Asia", "Kazakhstan": "Asia",
            "Kenya": "Africa", "Kiribati": "Oceania", "Kosovo": "Europe", "Kuwait": "Asia",
            "Kyrgyzstan": "Asia", "Laos": "Asia", "Latvia": "Europe", "Lebanon": "Asia",
            "Lesotho": "Africa", "Liberia": "Africa", "Libya": "Africa", "Liechtenstein": "Europe",
            "Lithuania": "Europe", "Luxembourg": "Europe", "Madagascar": "Africa", "Malawi": "Africa",
            "Malaysia": "Asia", "Maldives": "Asia", "Mali": "Africa", "Malta": "Europe",
            "Marshall_Islands": "Oceania", "Mauritania": "Africa", "Mauritius": "Africa", "Mexico": "Americas",
            "Micronesia": "Oceania", "Moldova": "Europe", "Monaco": "Europe", "Mongolia": "Asia",
            "Montenegro": "Europe", "Morocco": "Africa", "Mozambique": "Africa", "Myanmar": "Asia",
            "Namibia": "Africa", "Nauru": "Oceania", "Nepal": "Asia", "Netherlands": "Europe",
            "New_Zealand": "Oceania", "Nicaragua": "Americas", "Niger": "Africa", "Nigeria": "Africa",
            "North_Korea": "Asia", "North_Macedonia": "Europe", "Norway": "Europe", "Oman": "Asia",
            "Pakistan": "Asia", "Palau": "Oceania", "Palestine": "Asia", "Panama": "Americas",
            "Papua_New_Guinea": "Oceania", "Paraguay": "Americas", "Peru": "Americas", "Philippines": "Asia",
            "Poland": "Europe", "Portugal": "Europe", "Qatar": "Asia", "Romania": "Europe",
            "Russia": "Europe", "Rwanda": "Africa", "Saint_Kitts_and_Nevis": "Americas", "Saint_Lucia": "Americas",
            "Saint_Vincent_and_the_Grenadines": "Americas", "Samoa": "Oceania", "San_Marino": "Europe",
            "Saudi_Arabia": "Asia", "Senegal": "Africa", "Serbia": "Europe", "Seychelles": "Africa",
            "Sierra_Leone": "Africa", "Singapore": "Asia", "Slovakia": "Europe", "Slovenia": "Europe",
            "Solomon_Islands": "Oceania", "Somalia": "Africa", "South_Africa": "Africa", "South_Korea": "Asia",
            "South_Sudan": "Africa", "Spain": "Europe", "Sri_Lanka": "Asia", "Sudan": "Africa",
            "Suriname": "Americas", "Sweden": "Europe", "Switzerland": "Europe", "Syria": "Asia",
            "Taiwan": "Asia", "Tajikistan": "Asia", "Tanzania": "Africa", "Thailand": "Asia",
            "Timor-Leste": "Asia", "Togo": "Africa", "Tonga": "Oceania", "Trinidad_and_Tobago": "Americas",
            "Tunisia": "Africa", "Turkey": "Asia", "Turkmenistan": "Asia", "Tuvalu": "Oceania",
            "Uganda": "Africa", "Ukraine": "Europe", "United_Arab_Emirates": "Asia", "United_Kingdom": "Europe",
            "United_States": "Americas", "Uruguay": "Americas", "Uzbekistan": "Asia", "Vanuatu": "Oceania",
            "Vatican_City": "Europe", "Venezuela": "Americas", "Vietnam": "Asia", "Western_Sahara": "Africa",
            "Yemen": "Asia", "Zambia": "Africa", "Zimbabwe": "Africa"
        }

        # Return a region if we have it, or use the continent mapping, or "Unknown" as a last resort
        return regions.get(country_name, continent_mapping.get(country_name, "Unknown"))

    def _get_mock_subregion(self, country_name: str) -> str:
        """Return mock subregion data for a country"""
        # This is mock data for demonstration purposes
        subregions = {
            "United_States": "North America",
            "China": "Eastern Asia",
            "India": "Southern Asia",
            "Brazil": "South America",
            "Russia": "Eastern Europe",
            "Japan": "Eastern Asia",
            "Germany": "Western Europe",
            "United_Kingdom": "Northern Europe",
            "France": "Western Europe",
            "Italy": "Southern Europe",
            "Mexico": "North America",
            "Canada": "North America",
            "Australia": "Australia and New Zealand",
            "Nigeria": "Western Africa",
            "Egypt": "Northern Africa",
            "South_Africa": "Southern Africa",
            "Kenya": "Eastern Africa",
            "Saudi_Arabia": "Western Asia",
            "Argentina": "South America",
            "Algeria": "Northern Africa",
            "Sudan": "Northern Africa",
            "Ukraine": "Eastern Europe",
            "Iraq": "Western Asia",
            "Poland": "Eastern Europe",
            "Iran": "Southern Asia",
            "Spain": "Southern Europe",
            "Turkey": "Western Asia",
            "Vietnam": "South-Eastern Asia",
            "Comoros": "Eastern Africa",
            "Bahrain": "Western Asia",
        }

        # Return a subregion if we have it, or an empty string if not
        return subregions.get(country_name, "")

    def _format_population(self, population: int) -> str:
        """Format population to be more readable"""
        if population >= 1000000:
            return f"{population / 1000000:.1f} million"
        elif population >= 1000:
            return f"{population / 1000:.1f} thousand"
        else:
            return str(population)

    def _format_area(self, area: float) -> str:
        """Format area to be more readable"""
        if area >= 1000000:
            return f"{area / 1000000:.1f} million km²"
        elif area >= 1000:
            return f"{area:,.0f} km²"
        else:
            return f"{area:.1f} km²"

    async def _send_game_navigation(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send navigation buttons to select the next game mode"""
        logger.info("Sending game navigation buttons")
        
        keyboard = [
            [
                InlineKeyboardButton("🗺️ Play Map Game", callback_data="play_map"),
                InlineKeyboardButton("🏳️ Play Flag Game", callback_data="play_flag")
            ],
            [
                InlineKeyboardButton("🏙️ Play Capital Game", callback_data="play_capital")
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="🌍 Choose your next geography challenge:",
            reply_markup=reply_markup
        )

    async def handle_answer(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Legacy handler for text answers (we now use inline keyboards)"""
        user_id = update.effective_user.id

        # Check if user has an active game
        if user_id not in self.active_games:
            return

        # Get the active game
        game = self.active_games[user_id]
        correct_country = game["country"]["name"].replace("_", " ")
        user_answer = update.message.text.strip()

        # Cancel the timer for this game
        self._cancel_timer(user_id)

        # Increment attempts
        game["attempts"] += 1

        # Check if the answer is correct (case insensitive comparison)
        is_correct = user_answer.lower() == correct_country.lower()

        if is_correct:
            # User got it right
            await update.message.reply_text(
                f"✅ *Correct!* The country is indeed *{correct_country}*!",
                parse_mode="Markdown"
            )

            # Update stats
            self._update_user_stats(user_id, True)

            # Clean up
            del self.active_games[user_id]

            # Offer to play again with navigation buttons
            await self._send_game_navigation(update, context)

        else:
            # Wrong answer
            if game["attempts"] >= 3:
                # Too many attempts, reveal the answer
                await update.message.reply_text(
                    f"❌ Sorry, that's not correct. The country was *{correct_country}*.",
                    parse_mode="Markdown"
                )

                # Update stats
                self._update_user_stats(user_id, False)

                # Clean up
                del self.active_games[user_id]

                # Offer to play again with navigation buttons
                await self._send_game_navigation(update, context)

            else:
                # Still has attempts left
                await update.message.reply_text(
                    f"❌ That's not correct. Try again! ({game['attempts']}/3 attempts)",
                    parse_mode="Markdown"
                )

    def _update_user_stats(self, user_id: int, is_correct: bool) -> None:
        """Update game statistics for a user"""
        if str(user_id) not in self.user_stats:
            self.user_stats[str(user_id)] = {
                "games_played": 0,
                "correct": 0,
                "streak": 0,
                "max_streak": 0
            }

        stats = self.user_stats[str(user_id)]
        stats["games_played"] += 1

        if is_correct:
            stats["correct"] += 1
            stats["streak"] += 1
            stats["max_streak"] = max(stats["max_streak"], stats["streak"])
        else:
            stats["streak"] = 0
