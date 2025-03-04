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
                    cur.execute("SELECT name, capital, neighbors FROM countries")
                    rows = cur.fetchall()
                    conn.close()

                    # Return a list of dictionaries with country info
                    countries = []
                    for row in rows:
                        if row[0]:  # Ensure country name exists
                            neighbors = row[2].split(",") if row[2] else []
                            countries.append({
                                "name": row[0],
                                "capital": row[1] if row[1] else "Unknown",
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
            {"name": "Afghanistan", "capital": "Kabul", 
             "neighbors": ["Iran", "Pakistan", "Turkmenistan", "Uzbekistan", "Tajikistan", "China"]},
            {"name": "Albania", "capital": "Tirana", 
             "neighbors": ["Montenegro", "Kosovo", "North_Macedonia", "Greece"]},
            {"name": "Algeria", "capital": "Algiers", 
             "neighbors": ["Tunisia", "Libya", "Niger", "Mali", "Mauritania", "Morocco"]},
            {"name": "Andorra", "capital": "Andorra la Vella", 
             "neighbors": ["France", "Spain"]},
            {"name": "Angola", "capital": "Luanda", 
             "neighbors": ["Namibia", "Zambia", "Democratic_Republic_of_the_Congo", "Republic_of_the_Congo"]},
            {"name": "Argentina", "capital": "Buenos Aires", 
             "neighbors": ["Chile", "Bolivia", "Paraguay", "Brazil", "Uruguay"]},
            {"name": "Armenia", "capital": "Yerevan", 
             "neighbors": ["Georgia", "Azerbaijan", "Iran", "Turkey"]},
            {"name": "Australia", "capital": "Canberra", 
             "neighbors": ["New_Zealand", "Indonesia", "Papua_New_Guinea"]},
            {"name": "Austria", "capital": "Vienna", 
             "neighbors": ["Germany", "Czech_Republic", "Slovakia", "Hungary", "Slovenia", "Italy", "Switzerland", "Liechtenstein"]},
            {"name": "Azerbaijan", "capital": "Baku", 
             "neighbors": ["Russia", "Georgia", "Armenia", "Iran", "Turkey"]},
            {"name": "Bahamas", "capital": "Nassau", 
             "neighbors": ["United_States", "Cuba"]},
            {"name": "Bahrain", "capital": "Manama", 
             "neighbors": ["Saudi_Arabia", "Qatar"]},
            {"name": "Bangladesh", "capital": "Dhaka", 
             "neighbors": ["India", "Myanmar"]},
            {"name": "Barbados", "capital": "Bridgetown", 
             "neighbors": ["Saint_Lucia", "Saint_Vincent_and_the_Grenadines"]},
            {"name": "Belarus", "capital": "Minsk", 
             "neighbors": ["Russia", "Ukraine", "Poland", "Lithuania", "Latvia"]},
            {"name": "Belgium", "capital": "Brussels", 
             "neighbors": ["Netherlands", "Germany", "Luxembourg", "France"]},
            {"name": "Belize", "capital": "Belmopan", 
             "neighbors": ["Mexico", "Guatemala"]},
            {"name": "Benin", "capital": "Porto-Novo", 
             "neighbors": ["Nigeria", "Togo", "Burkina_Faso", "Niger"]},
            {"name": "Bhutan", "capital": "Thimphu", 
             "neighbors": ["India", "China"]},
            {"name": "Bolivia", "capital": "Sucre", 
             "neighbors": ["Brazil", "Paraguay", "Argentina", "Chile", "Peru"]},
            {"name": "Bosnia_and_Herzegovina", "capital": "Sarajevo", 
             "neighbors": ["Croatia", "Serbia", "Montenegro"]},
            {"name": "Botswana", "capital": "Gaborone", 
             "neighbors": ["South_Africa", "Namibia", "Zimbabwe", "Zambia"]},
            {"name": "Brazil", "capital": "Brasilia", 
             "neighbors": ["Argentina", "Paraguay", "Uruguay", "Bolivia", "Peru", "Colombia", "Venezuela", "Guyana", "Suriname", "French_Guiana"]},
            {"name": "Brunei", "capital": "Bandar Seri Begawan", 
             "neighbors": ["Malaysia"]},
            {"name": "Bulgaria", "capital": "Sofia", 
             "neighbors": ["Romania", "Serbia", "North_Macedonia", "Greece", "Turkey"]},
            {"name": "Burkina_Faso", "capital": "Ouagadougou", 
             "neighbors": ["Mali", "Niger", "Benin", "Togo", "Ghana", "Ivory_Coast"]},
            {"name": "Burundi", "capital": "Gitega", 
             "neighbors": ["Rwanda", "Tanzania", "Democratic_Republic_of_the_Congo"]},
            {"name": "Cambodia", "capital": "Phnom Penh", 
             "neighbors": ["Thailand", "Laos", "Vietnam"]},
            {"name": "Cameroon", "capital": "Yaoundé", 
             "neighbors": ["Nigeria", "Chad", "Central_African_Republic", "Republic_of_the_Congo", "Gabon", "Equatorial_Guinea"]},
            {"name": "Canada", "capital": "Ottawa", 
             "neighbors": ["United_States"]},
            {"name": "Central_African_Republic", "capital": "Bangui", 
             "neighbors": ["Chad", "Sudan", "South_Sudan", "Democratic_Republic_of_the_Congo", "Republic_of_the_Congo", "Cameroon"]},
            {"name": "Chad", "capital": "N'Djamena", 
             "neighbors": ["Libya", "Sudan", "Central_African_Republic", "Cameroon", "Nigeria", "Niger"]},
            {"name": "Chile", "capital": "Santiago", 
             "neighbors": ["Peru", "Bolivia", "Argentina"]},
            {"name": "China", "capital": "Beijing", 
             "neighbors": ["Russia", "Mongolia", "North_Korea", "Vietnam", "Laos", "Myanmar", "India", "Bhutan", "Nepal", "Pakistan", "Afghanistan", "Tajikistan", "Kyrgyzstan", "Kazakhstan"]},
            {"name": "Colombia", "capital": "Bogotá", 
             "neighbors": ["Venezuela", "Brazil", "Peru", "Ecuador", "Panama"]},
            {"name": "Comoros", "capital": "Moroni", 
             "neighbors": ["Madagascar", "Mozambique", "Tanzania"]},
            {"name": "Congo", "capital": "Brazzaville", 
             "neighbors": ["Democratic_Republic_of_the_Congo", "Angola", "Gabon", "Cameroon", "Central_African_Republic"]},
            {"name": "Costa_Rica", "capital": "San José", 
             "neighbors": ["Nicaragua", "Panama"]},
            {"name": "Croatia", "capital": "Zagreb", 
             "neighbors": ["Slovenia", "Hungary", "Serbia", "Bosnia_and_Herzegovina", "Montenegro"]},
            {"name": "Cuba", "capital": "Havana", 
             "neighbors": ["United_States"]},
            {"name": "Cyprus", "capital": "Nicosia", 
             "neighbors": ["Turkey", "Greece"]},
            {"name": "Czech_Republic", "capital": "Prague", 
             "neighbors": ["Germany", "Poland", "Slovakia", "Austria"]},
            {"name": "Democratic_Republic_of_the_Congo", "capital": "Kinshasa", 
             "neighbors": ["Republic_of_the_Congo", "Central_African_Republic", "South_Sudan", "Uganda", "Rwanda", "Burundi", "Tanzania", "Zambia", "Angola"]},
            {"name": "Denmark", "capital": "Copenhagen", 
             "neighbors": ["Germany", "Sweden", "Norway"]},
            {"name": "Djibouti", "capital": "Djibouti", 
             "neighbors": ["Eritrea", "Ethiopia", "Somalia"]},
            {"name": "Dominican_Republic", "capital": "Santo Domingo", 
             "neighbors": ["Haiti"]},
            {"name": "Ecuador", "capital": "Quito", 
             "neighbors": ["Colombia", "Peru"]},
            {"name": "Egypt", "capital": "Cairo", 
             "neighbors": ["Libya", "Sudan", "Israel", "Palestine"]},
            {"name": "El_Salvador", "capital": "San Salvador", 
             "neighbors": ["Guatemala", "Honduras"]},
            {"name": "Equatorial_Guinea", "capital": "Malabo", 
             "neighbors": ["Cameroon", "Gabon"]},
            {"name": "Eritrea", "capital": "Asmara", 
             "neighbors": ["Sudan", "Ethiopia", "Djibouti"]},
            {"name": "Estonia", "capital": "Tallinn", 
             "neighbors": ["Russia", "Latvia"]},
            {"name": "Eswatini", "capital": "Mbabane", 
             "neighbors": ["South_Africa", "Mozambique"]},
            {"name": "Ethiopia", "capital": "Addis Ababa", 
             "neighbors": ["Eritrea", "Djibouti", "Somalia", "Kenya", "South_Sudan", "Sudan"]},
            {"name": "Fiji", "capital": "Suva", 
             "neighbors": ["Vanuatu", "Tonga", "Samoa"]},
            {"name": "Finland", "capital": "Helsinki", 
             "neighbors": ["Sweden", "Norway", "Russia"]},
            {"name": "France", "capital": "Paris", 
             "neighbors": ["Belgium", "Luxembourg", "Germany", "Switzerland", "Italy", "Monaco", "Spain", "Andorra"]},
            {"name": "Gabon", "capital": "Libreville", 
             "neighbors": ["Equatorial_Guinea", "Cameroon", "Republic_of_the_Congo"]},
            {"name": "Gambia", "capital": "Banjul", 
             "neighbors": ["Senegal"]},
            {"name": "Georgia", "capital": "Tbilisi", 
             "neighbors": ["Russia", "Azerbaijan", "Armenia", "Turkey"]},
            {"name": "Germany", "capital": "Berlin", 
             "neighbors": ["Denmark", "Poland", "Czech_Republic", "Austria", "Switzerland", "France", "Luxembourg", "Belgium", "Netherlands"]},
            {"name": "Ghana", "capital": "Accra", 
             "neighbors": ["Burkina_Faso", "Ivory_Coast", "Togo"]},
            {"name": "Greece", "capital": "Athens", 
             "neighbors": ["Albania", "North_Macedonia", "Bulgaria", "Turkey"]},
            {"name": "Guatemala", "capital": "Guatemala City", 
             "neighbors": ["Mexico", "Belize", "Honduras", "El_Salvador"]},
            {"name": "Guinea", "capital": "Conakry", 
             "neighbors": ["Guinea-Bissau", "Senegal", "Mali", "Ivory_Coast", "Liberia", "Sierra_Leone"]},
            {"name": "Guinea-Bissau", "capital": "Bissau", 
             "neighbors": ["Senegal", "Guinea"]},
            {"name": "Guyana", "capital": "Georgetown", 
             "neighbors": ["Venezuela", "Brazil", "Suriname"]},
            {"name": "Haiti", "capital": "Port-au-Prince", 
             "neighbors": ["Dominican_Republic"]},
            {"name": "Honduras", "capital": "Tegucigalpa", 
             "neighbors": ["Guatemala", "El_Salvador", "Nicaragua"]},
            {"name": "Hungary", "capital": "Budapest", 
             "neighbors": ["Slovakia", "Ukraine", "Romania", "Serbia", "Croatia", "Slovenia", "Austria"]},
            {"name": "Iceland", "capital": "Reykjavik", 
             "neighbors": ["Norway", "Denmark", "United_Kingdom"]},
            {"name": "India", "capital": "New Delhi", 
             "neighbors": ["Pakistan", "China", "Nepal", "Bhutan", "Bangladesh", "Myanmar", "Sri_Lanka"]},
            {"name": "Indonesia", "capital": "Jakarta", 
             "neighbors": ["Papua_New_Guinea", "Malaysia", "East_Timor", "Australia"]},
            {"name": "Iran", "capital": "Tehran", 
             "neighbors": ["Iraq", "Turkey", "Armenia", "Azerbaijan", "Turkmenistan", "Afghanistan", "Pakistan"]},
            {"name": "Iraq", "capital": "Baghdad", 
             "neighbors": ["Iran", "Turkey", "Syria", "Jordan", "Saudi_Arabia", "Kuwait"]},
            {"name": "Ireland", "capital": "Dublin", 
             "neighbors": ["United_Kingdom"]},
            {"name": "Israel", "capital": "Jerusalem", 
             "neighbors": ["Lebanon", "Syria", "Jordan", "Egypt", "Palestine"]},
            {"name": "Italy", "capital": "Rome", 
             "neighbors": ["France", "Switzerland", "Austria", "Slovenia", "San_Marino", "Vatican_City"]},
            {"name": "Ivory_Coast", "capital": "Yamoussoukro", 
             "neighbors": ["Liberia", "Guinea", "Mali", "Burkina_Faso", "Ghana"]},
            {"name": "Jamaica", "capital": "Kingston", 
             "neighbors": ["Cuba", "Haiti"]},
            {"name": "Japan", "capital": "Tokyo", 
             "neighbors": ["South_Korea", "China", "Russia"]},
            {"name": "Jordan", "capital": "Amman", 
             "neighbors": ["Syria", "Iraq", "Saudi_Arabia", "Israel", "Palestine"]},
            {"name": "Kazakhstan", "capital": "Nur-Sultan", 
             "neighbors": ["Russia", "China", "Kyrgyzstan", "Uzbekistan", "Turkmenistan"]},
            {"name": "Kenya", "capital": "Nairobi", 
             "neighbors": ["Ethiopia", "Somalia", "South_Sudan", "Uganda", "Tanzania"]},
            {"name": "Kiribati", "capital": "Tarawa", 
             "neighbors": ["Marshall_Islands", "Nauru"]},
            {"name": "Kosovo", "capital": "Pristina", 
             "neighbors": ["Serbia", "North_Macedonia", "Albania", "Montenegro"]},
            {"name": "Kuwait", "capital": "Kuwait City", 
             "neighbors": ["Iraq", "Saudi_Arabia"]},
            {"name": "Kyrgyzstan", "capital": "Bishkek", 
             "neighbors": ["Kazakhstan", "China", "Tajikistan", "Uzbekistan"]},
            {"name": "Laos", "capital": "Vientiane", 
             "neighbors": ["China", "Vietnam", "Cambodia", "Thailand", "Myanmar"]},
            {"name": "Latvia", "capital": "Riga", 
             "neighbors": ["Estonia", "Russia", "Belarus", "Lithuania"]},
            {"name": "Lebanon", "capital": "Beirut", 
             "neighbors": ["Syria", "Israel"]},
            {"name": "Lesotho", "capital": "Maseru", 
             "neighbors": ["South_Africa"]},
            {"name": "Liberia", "capital": "Monrovia", 
             "neighbors": ["Sierra_Leone", "Guinea", "Ivory_Coast"]},
            {"name": "Libya", "capital": "Tripoli", 
             "neighbors": ["Egypt", "Sudan", "Chad", "Niger", "Algeria", "Tunisia"]},
            {"name": "Liechtenstein", "capital": "Vaduz", 
             "neighbors": ["Switzerland", "Austria"]},
            {"name": "Lithuania", "capital": "Vilnius", 
             "neighbors": ["Latvia", "Belarus", "Poland", "Russia"]},
            {"name": "Luxembourg", "capital": "Luxembourg City", 
             "neighbors": ["Belgium", "France", "Germany"]},
            {"name": "Madagascar", "capital": "Antananarivo", 
             "neighbors": ["Comoros", "Mauritius", "Reunion"]},
            {"name": "Malawi", "capital": "Lilongwe", 
             "neighbors": ["Tanzania", "Mozambique", "Zambia"]},
            {"name": "Malaysia", "capital": "Kuala Lumpur", 
             "neighbors": ["Thailand", "Indonesia", "Brunei", "Singapore"]},
            {"name": "Maldives", "capital": "Malé", 
             "neighbors": ["Sri_Lanka", "India"]},
            {"name": "Mali", "capital": "Bamako", 
             "neighbors": ["Algeria", "Niger", "Burkina_Faso", "Ivory_Coast", "Guinea", "Senegal", "Mauritania"]},
            {"name": "Malta", "capital": "Valletta", 
             "neighbors": ["Italy", "Tunisia"]},
            {"name": "Marshall_Islands", "capital": "Majuro", 
             "neighbors": ["Kiribati", "Micronesia"]},
            {"name": "Mauritania", "capital": "Nouakchott", 
             "neighbors": ["Western_Sahara", "Algeria", "Mali", "Senegal"]},
            {"name": "Mauritius", "capital": "Port Louis", 
             "neighbors": ["Madagascar", "Reunion"]},
            {"name": "Mexico", "capital": "Mexico City", 
             "neighbors": ["United_States", "Guatemala", "Belize"]},
            {"name": "Micronesia", "capital": "Palikir", 
             "neighbors": ["Marshall_Islands", "Palau"]},
            {"name": "Moldova", "capital": "Chișinău", 
             "neighbors": ["Romania", "Ukraine"]},
            {"name": "Monaco", "capital": "Monaco", 
             "neighbors": ["France"]},
            {"name": "Mongolia", "capital": "Ulaanbaatar", 
             "neighbors": ["Russia", "China"]},
            {"name": "Montenegro", "capital": "Podgorica", 
             "neighbors": ["Croatia", "Bosnia_and_Herzegovina", "Serbia", "Kosovo", "Albania"]},
            {"name": "Morocco", "capital": "Rabat", 
             "neighbors": ["Algeria", "Western_Sahara", "Spain"]},
            {"name": "Mozambique", "capital": "Maputo", 
             "neighbors": ["Tanzania", "Malawi", "Zambia", "Zimbabwe", "South_Africa", "Eswatini"]},
            {"name": "Myanmar", "capital": "Naypyidaw", 
             "neighbors": ["Bangladesh", "India", "China", "Laos", "Thailand"]},
            {"name": "Namibia", "capital": "Windhoek", 
             "neighbors": ["Angola", "Zambia", "Botswana", "South_Africa"]},
            {"name": "Nauru", "capital": "Yaren", 
             "neighbors": ["Kiribati", "Marshall_Islands"]},
            {"name": "Nepal", "capital": "Kathmandu", 
             "neighbors": ["India", "China"]},
            {"name": "Netherlands", "capital": "Amsterdam", 
             "neighbors": ["Germany", "Belgium"]},
            {"name": "New_Zealand", "capital": "Wellington", 
             "neighbors": ["Australia", "Fiji"]},
            {"name": "Nicaragua", "capital": "Managua", 
             "neighbors": ["Honduras", "Costa_Rica"]},
            {"name": "Niger", "capital": "Niamey", 
             "neighbors": ["Algeria", "Libya", "Chad", "Nigeria", "Benin", "Burkina_Faso", "Mali"]},
            {"name": "Nigeria", "capital": "Abuja", 
             "neighbors": ["Niger", "Chad", "Cameroon", "Benin"]},
            {"name": "North_Korea", "capital": "Pyongyang", 
             "neighbors": ["China", "South_Korea", "Russia"]},
            {"name": "North_Macedonia", "capital": "Skopje", 
             "neighbors": ["Kosovo", "Serbia", "Bulgaria", "Greece", "Albania"]},
            {"name": "Norway", "capital": "Oslo", 
             "neighbors": ["Sweden", "Finland", "Russia"]},
            {"name": "Oman", "capital": "Muscat", 
             "neighbors": ["United_Arab_Emirates", "Saudi_Arabia", "Yemen"]},
            {"name": "Pakistan", "capital": "Islamabad", 
             "neighbors": ["Iran", "Afghanistan", "China", "India"]},
            {"name": "Palau", "capital": "Ngerulmud", 
             "neighbors": ["Philippines", "Micronesia"]},
            {"name": "Palestine", "capital": "Ramallah", 
             "neighbors": ["Israel", "Jordan", "Egypt"]},
            {"name": "Panama", "capital": "Panama City", 
             "neighbors": ["Costa_Rica", "Colombia"]},
            {"name": "Papua_New_Guinea", "capital": "Port Moresby", 
             "neighbors": ["Indonesia", "Australia"]},
            {"name": "Paraguay", "capital": "Asunción", 
             "neighbors": ["Bolivia", "Brazil", "Argentina"]},
            {"name": "Peru", "capital": "Lima", 
             "neighbors": ["Ecuador", "Colombia", "Brazil", "Bolivia", "Chile"]},
            {"name": "Philippines", "capital": "Manila", 
             "neighbors": ["Taiwan", "Indonesia", "Malaysia"]},
            {"name": "Poland", "capital": "Warsaw", 
             "neighbors": ["Germany", "Czech_Republic", "Slovakia", "Ukraine", "Belarus", "Lithuania", "Russia"]},
            {"name": "Portugal", "capital": "Lisbon", 
             "neighbors": ["Spain"]},
            {"name": "Qatar", "capital": "Doha", 
             "neighbors": ["Saudi_Arabia", "United_Arab_Emirates", "Bahrain"]},
            {"name": "Romania", "capital": "Bucharest", 
             "neighbors": ["Moldova", "Ukraine", "Hungary", "Serbia", "Bulgaria"]},
            {"name": "Russia", "capital": "Moscow", 
             "neighbors": ["Norway", "Finland", "Estonia", "Latvia", "Lithuania", "Poland", "Belarus", "Ukraine", "Georgia", "Azerbaijan", "Kazakhstan", "China", "Mongolia", "North_Korea"]},
            {"name": "Rwanda", "capital": "Kigali", 
             "neighbors": ["Uganda", "Tanzania", "Burundi", "Democratic_Republic_of_the_Congo"]},
            {"name": "Saint_Kitts_and_Nevis", "capital": "Basseterre", 
             "neighbors": ["Antigua_and_Barbuda", "Saint_Lucia"]},
            {"name": "Saint_Lucia", "capital": "Castries", 
             "neighbors": ["Saint_Vincent_and_the_Grenadines", "Barbados"]},
            {"name": "Saint_Vincent_and_the_Grenadines", "capital": "Kingstown", 
             "neighbors": ["Saint_Lucia", "Barbados"]},
            {"name": "Samoa", "capital": "Apia", 
             "neighbors": ["Fiji", "Tonga"]},
            {"name": "San_Marino", "capital": "San Marino", 
             "neighbors": ["Italy"]},
            {"name": "Saudi_Arabia", "capital": "Riyadh", 
             "neighbors": ["Jordan", "Iraq", "Kuwait", "Bahrain", "Qatar", "United_Arab_Emirates", "Oman", "Yemen"]},
            {"name": "Senegal", "capital": "Dakar", 
             "neighbors": ["Mauritania", "Mali", "Guinea", "Guinea-Bissau", "Gambia"]},
            {"name": "Serbia", "capital": "Belgrade", 
             "neighbors": ["Hungary", "Romania", "Bulgaria", "North_Macedonia", "Kosovo", "Montenegro", "Bosnia_and_Herzegovina", "Croatia"]},
            {"name": "Seychelles", "capital": "Victoria", 
             "neighbors": ["Madagascar", "Mauritius"]},
            {"name": "Sierra_Leone", "capital": "Freetown", 
             "neighbors": ["Guinea", "Liberia"]},
            {"name": "Singapore", "capital": "Singapore", 
             "neighbors": ["Malaysia", "Indonesia"]},
            {"name": "Slovakia", "capital": "Bratislava", 
             "neighbors": ["Poland", "Ukraine", "Hungary", "Austria", "Czech_Republic"]},
            {"name": "Slovenia", "capital": "Ljubljana", 
             "neighbors": ["Italy", "Austria", "Hungary", "Croatia"]},
            {"name": "Solomon_Islands", "capital": "Honiara", 
             "neighbors": ["Papua_New_Guinea", "Vanuatu"]},
            {"name": "Somalia", "capital": "Mogadishu", 
             "neighbors": ["Ethiopia", "Kenya", "Djibouti"]},
            {"name": "South_Africa", "capital": "Pretoria", 
             "neighbors": ["Namibia", "Botswana", "Zimbabwe", "Mozambique", "Eswatini", "Lesotho"]},
            {"name": "South_Korea", "capital": "Seoul", 
             "neighbors": ["North_Korea", "Japan"]},
            {"name": "South_Sudan", "capital": "Juba", 
             "neighbors": ["Sudan", "Ethiopia", "Kenya", "Uganda", "Democratic_Republic_of_the_Congo", "Central_African_Republic"]},
            {"name": "Spain", "capital": "Madrid", 
             "neighbors": ["Portugal", "France", "Andorra", "Morocco"]},
            {"name": "Sri_Lanka", "capital": "Colombo", 
             "neighbors": ["India", "Maldives"]},
            {"name": "Sudan", "capital": "Khartoum", 
             "neighbors": ["Egypt", "Libya", "Chad", "Central_African_Republic", "South_Sudan", "Ethiopia", "Eritrea"]},
            {"name": "Suriname", "capital": "Paramaribo", 
             "neighbors": ["Guyana", "Brazil", "French_Guiana"]},
            {"name": "Sweden", "capital": "Stockholm", 
             "neighbors": ["Norway", "Finland", "Denmark"]},
            {"name": "Switzerland", "capital": "Bern", 
             "neighbors": ["France", "Germany", "Austria", "Liechtenstein", "Italy"]},
            {"name": "Syria", "capital": "Damascus", 
             "neighbors": ["Turkey", "Iraq", "Jordan", "Israel", "Lebanon"]},
            {"name": "Taiwan", "capital": "Taipei", 
             "neighbors": ["China", "Japan", "Philippines"]},
            {"name": "Tajikistan", "capital": "Dushanbe", 
             "neighbors": ["Uzbekistan", "Kyrgyzstan", "China", "Afghanistan"]},
            {"name": "Tanzania", "capital": "Dodoma", 
             "neighbors": ["Kenya", "Uganda", "Rwanda", "Burundi", "Democratic_Republic_of_the_Congo", "Zambia", "Malawi", "Mozambique"]},
            {"name": "Thailand", "capital": "Bangkok", 
             "neighbors": ["Myanmar", "Laos", "Cambodia", "Malaysia"]},
            {"name": "Timor-Leste", "capital": "Dili", 
             "neighbors": ["Indonesia"]},
            {"name": "Togo", "capital": "Lomé", 
             "neighbors": ["Ghana", "Burkina_Faso", "Benin"]},
            {"name": "Tonga", "capital": "Nukuʻalofa", 
             "neighbors": ["Fiji", "Samoa"]},
            {"name": "Trinidad_and_Tobago", "capital": "Port of Spain", 
             "neighbors": ["Venezuela"]},
            {"name": "Tunisia", "capital": "Tunis", 
             "neighbors": ["Algeria", "Libya"]},
            {"name": "Turkey", "capital": "Ankara", 
             "neighbors": ["Greece", "Bulgaria", "Georgia", "Armenia", "Azerbaijan", "Iran", "Iraq", "Syria"]},
            {"name": "Turkmenistan", "capital": "Ashgabat", 
             "neighbors": ["Kazakhstan", "Uzbekistan", "Afghanistan", "Iran"]},
            {"name": "Tuvalu", "capital": "Funafuti", 
             "neighbors": ["Fiji", "Kiribati"]},
            {"name": "Uganda", "capital": "Kampala", 
             "neighbors": ["Kenya", "South_Sudan", "Democratic_Republic_of_the_Congo", "Rwanda", "Tanzania"]},
            {"name": "Ukraine", "capital": "Kyiv", 
             "neighbors": ["Belarus", "Russia", "Moldova", "Romania", "Hungary", "Slovakia", "Poland"]},
            {"name": "United_Arab_Emirates", "capital": "Abu Dhabi", 
             "neighbors": ["Saudi_Arabia", "Oman"]},
            {"name": "United_Kingdom", "capital": "London", 
             "neighbors": ["Ireland", "France", "Iceland"]},
            {"name": "United_States", "capital": "Washington, D.C.", 
             "neighbors": ["Canada", "Mexico"]},
            {"name": "Uruguay", "capital": "Montevideo", 
             "neighbors": ["Argentina", "Brazil"]},
            {"name": "Uzbekistan", "capital": "Tashkent", 
             "neighbors": ["Kazakhstan", "Kyrgyzstan", "Tajikistan", "Afghanistan", "Turkmenistan"]},
            {"name": "Vanuatu", "capital": "Port Vila", 
             "neighbors": ["Solomon_Islands", "Fiji"]},
            {"name": "Vatican_City", "capital": "Vatican City", 
             "neighbors": ["Italy"]},
            {"name": "Venezuela", "capital": "Caracas", 
             "neighbors": ["Colombia", "Brazil", "Guyana", "Trinidad_and_Tobago"]},
            {"name": "Vietnam", "capital": "Hanoi", 
             "neighbors": ["China", "Laos", "Cambodia"]},
            {"name": "Western_Sahara", "capital": "El Aaiún", 
             "neighbors": ["Morocco", "Algeria", "Mauritania"]},
            {"name": "Yemen", "capital": "Sana'a", 
             "neighbors": ["Saudi_Arabia", "Oman"]},
            {"name": "Zambia", "capital": "Lusaka", 
             "neighbors": ["Democratic_Republic_of_the_Congo", "Tanzania", "Malawi", "Mozambique", "Zimbabwe", "Botswana", "Namibia", "Angola"]},
            {"name": "Zimbabwe", "capital": "Harare", 
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
            elif hasattr(self, 'current_game_mode') and self.current_game_mode == "map" and os.path.path.exists(map_path):
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

    async def start_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE, game_mode: str) -> None:
        """Start a new game in the specified mode"""
        user_id = update.effective_user.id

        # Store the current game mode so get_random_country can use it
        self.current_game_mode = game_mode

        # Get a random country that has appropriate images for this game mode
        country = self.get_random_country()

        # Cancel any existing timer for this user
        self._cancel_timer(user_id)

        # Store game state
        self.active_games[user_id] = {
            "country": country,
            "mode": game_mode,
            "attempts": 0,
            "start_time": time.time()
        }

        # Log the game start
        logger.info(f"Starting {game_mode} game for user {user_id} with country {country['name']}")

        if game_mode == "map":
            await self._send_map_challenge(update, context, country)
        elif game_mode == "flag":
            await self._send_flag_challenge(update, context, country)
        elif game_mode == "capital":
            await self._send_capital_challenge(update, context, country)
        else:
            await update.message.reply_text("Invalid game mode. Use /g help for options.")

    def _cancel_timer(self, user_id: int) -> None:
        """Cancel the timer for a specific user if it exists"""
        if user_id in self.timer_tasks:
            task = self.timer_tasks.pop(user_id)
            if not task.done():
                task.cancel()

    async def _game_timeout_callback(self, update: Update, context: CallbackContext, user_id: int) -> None:
        """Handle game timeout after waiting for the timeout period"""
        try:
            # Capture chat_id before sleep to avoid any issues with update object becoming stale
            chat_id = update.effective_chat.id
            logger.info(f"Starting timeout timer for user {user_id} in chat {chat_id} - waiting {GAME_TIMEOUT} seconds")

            # Wait for GAME_TIMEOUT seconds
            await asyncio.sleep(GAME_TIMEOUT)

            logger.info(f"Timeout period completed for user {user_id} - checking if game is still active")

            # Check if the game is still active (user hasn't answered yet)
            if user_id in self.active_games:
                game = self.active_games[user_id]
                correct_country = game["country"]["name"].replace("_", " ")
                logger.info(f"Game for user {user_id} is still active - sending timeout message")

                try:
                    # Get the original message ID
                    message_id = game.get("message_id")
                    if message_id and game["mode"] in ["map", "flag"]:
                        # For map and flag modes, edit the caption
                        try:
                            await context.bot.edit_message_caption(
                                chat_id=chat_id,
                                message_id=message_id,
                                caption=f"⏱️ Time's up! The correct answer was *{correct_country}*.",
                                parse_mode="Markdown"
                            )
                            logger.info(f"Successfully edited caption for timeout in {game['mode']} mode")
                        except Exception as e:
                            logger.error(f"Error editing caption: {e}")
                            # Fall back to sending a new message
                            await context.bot.send_message(
                                chat_id=chat_id,
                                text=f"⏱️ Time's up! The correct answer was *{correct_country}*.",
                                parse_mode="Markdown"
                            )
                    elif message_id and game["mode"] == "capital":
                        # For capital mode, edit the text
                        try:
                            await context.bot.edit_message_text(
                                chat_id=chat_id,
                                message_id=message_id,
                                text=f"⏱️ Time's up! The correct answer was *{correct_country}*.",
                                parse_mode="Markdown"
                            )
                            logger.info(f"Successfully edited text for timeout in capital mode")
                        except Exception as e:
                            logger.error(f"Error editing text: {e}")
                            # Fall back to sending a new message
                            await context.bot.send_message(
                                chat_id=chat_id,
                                text=f"⏱️ Time's up! The correct answer was *{correct_country}*.",
                                parse_mode="Markdown"
                            )
                    else:
                        # If we don't have a message_id, send a new message
                        await context.bot.send_message(
                            chat_id=chat_id,
                            text=f"⏱️ Time's up! The correct answer was *{correct_country}*.",
                            parse_mode="Markdown"
                        )
                        logger.info("Sent new timeout message (no message_id available for editing)")

                    # Update stats
                    self._update_user_stats(user_id, False)

                    # Offer to play again with navigation buttons
                    await self._send_game_navigation(update, context)

                    # Remove game state
                    del self.active_games[user_id]
                    logger.info(f"Timeout handled successfully for user {user_id}")
                except Exception as e:
                    logger.error(f"Error handling game timeout: {e}")
            else:
                logger.info(f"Game for user {user_id} is no longer active - user already answered")
        except asyncio.CancelledError:
            # Timer was cancelled, no need to do anything
            logger.info(f"Timer for user {user_id} was cancelled - user answered before timeout")
        except Exception as e:
            logger.error(f"Error in game timeout callback: {e}")

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
        """Handle callback queries from inline keyboard buttons"""
        query = update.callback_query
        user_id = update.effective_user.id

        # Add detailed logging to help debug navigation buttons
        logger.info(f"Received callback query with data: {query.data} from user {user_id}")

        # Cancel the timer for this game
        self._cancel_timer(user_id)

        await query.answer()  # Acknowledge the button press to Telegram

        # Check if it's a game guess
        if query.data.startswith("guess_"):
            logger.info(f"Processing guess: {query.data}")
            await self._handle_guess(update, context, query)
        # Check if it's a navigation button
        elif query.data.startswith("play_"):
            game_mode = query.data.split("_")[1]
            logger.info(f"Starting new game with mode: {game_mode}")
            await self.start_game(update, context, game_mode)
        else:
            logger.warning(f"Unrecognized callback data: {query.data}")

    async def _handle_guess(self, update: Update, context: ContextTypes.DEFAULT_TYPE, query) -> None:
        """Handle a guess from the inline keyboard"""
        user_id = update.effective_user.id

        # Check if user has an active game
        if user_id not in self.active_games:
            await query.edit_message_text("No active game found. Please start a new game.")
            return

        # Get the active game
        game = self.active_games[user_id]
        correct_country = game["country"]["name"]
        guess = query.data.split("_")[1]  # Format is "guess_CountryName"

        # Calculate elapsed time
        elapsed_time = round(time.time() - game["start_time"], 1)

        # Debug logs to help diagnose comparison issues
        logger.info(f"Comparing guess '{guess}' with correct answer '{correct_country}'")
        logger.info(f"After normalization: '{guess.lower().replace('_', '')}' vs '{correct_country.lower().replace('_', '')}'")

        # Fix: Normalize both strings for comparison to avoid false negatives
        # This makes the comparison more robust against format differences
        is_correct = guess.lower().replace("_", "") == correct_country.lower().replace("_", "")
        logger.info(f"Is correct: {is_correct}")

        if is_correct:
            # User got it right
            await query.edit_message_caption(
                caption=f"✅ *Correct!* The country is indeed *{correct_country.replace('_', ' ')}*!\n"\
                       f"You answered in {elapsed_time} seconds.",
                parse_mode="Markdown"
            )

            # Update stats
            self._update_user_stats(user_id, True)

        else:
            # Wrong answer
            await query.edit_message_caption(
                caption=f"❌ Sorry, that's not correct. The country was *{correct_country.replace('_', ' ')}*.",
                parse_mode="Markdown"
            )

            # Update stats
            self._update_user_stats(user_id, False)

        # Clean up
        del self.active_games[user_id]

        # Offer to play again with navigation buttons
        await self._send_game_navigation(update, context)

    async def _send_game_navigation(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send navigation buttons to select the next game"""
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
            text="Choose your next game:",
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