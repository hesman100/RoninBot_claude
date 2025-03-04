import os
import sqlite3
import time
import logging
from typing import Dict, List, Optional, Tuple

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
COUNTRY_LIST_PATH = "country_game/country_name.list"
DB_PATH = "country_game/database/countries.db"
MAP_IMAGES_DIR = "country_game/images/wiki_all_map_400pi"
FLAG_IMAGES_DIR = "country_game/images/wiki_flag"

# Custom flag paths for countries with missing flags
CUSTOM_FLAG_PATHS = {
    "Guinea-Bissau": "country_game/images/wiki_flag/GuineaBissau_flag.png",
    "São Tomé and Príncipe": "country_game/images/wiki_flag/So_Tom_and_Prncipe_flag.png"
}

# Hardcoded data for some major countries' capitals
CAPITAL_DATA = {
    "United_States": "Washington D.C.",
    "United_Kingdom": "London",
    "France": "Paris",
    "Germany": "Berlin",
    "Japan": "Tokyo",
    "Australia": "Canberra",
    "Brazil": "Brasília",
    "Canada": "Ottawa",
    "China": "Beijing",
    "Russia": "Moscow",
    "India": "New Delhi",
    "Italy": "Rome",
    "Spain": "Madrid",
    "Mexico": "Mexico City",
    "South_Korea": "Seoul",
    "Argentina": "Buenos Aires",
    "South_Africa": "Pretoria",
    "Egypt": "Cairo",
    "Turkey": "Ankara",
    "Indonesia": "Jakarta",
    "Nigeria": "Abuja",
    "Vietnam": "Hanoi",
    "Thailand": "Bangkok",
    "Philippines": "Manila",
    "Sweden": "Stockholm",
    "Switzerland": "Bern",
    "Netherlands": "Amsterdam",
    "Belgium": "Brussels",
    "Greece": "Athens",
    "Ukraine": "Kyiv",
    "Poland": "Warsaw",
    "Portugal": "Lisbon",
    "Ireland": "Dublin",
    "Norway": "Oslo",
    "Finland": "Helsinki",
    "Denmark": "Copenhagen",
    "New_Zealand": "Wellington",
    "Singapore": "Singapore",
    "Malaysia": "Kuala Lumpur",
    "Afghanistan": "Kabul",
    "Saudi_Arabia": "Riyadh",
    "Iran": "Tehran",
    "Iraq": "Baghdad",
    "Pakistan": "Islamabad",
    "Bangladesh": "Dhaka",
    "Colombia": "Bogotá",
    "Peru": "Lima",
    "Chile": "Santiago",
    "Venezuela": "Caracas",
    "Morocco": "Rabat",
    "Algeria": "Algiers",
    "Kenya": "Nairobi",
    "Ethiopia": "Addis Ababa",
    "Ghana": "Accra",
    "Angola": "Luanda",
    "Tanzania": "Dodoma",
    "Sudan": "Khartoum",
    "Uganda": "Kampala",
    "Zimbabwe": "Harare",
    "Cuba": "Havana",
    "Dominican_Republic": "Santo Domingo",
    "Guatemala": "Guatemala City",
    "Hungary": "Budapest",
    "Romania": "Bucharest",
    "Bulgaria": "Sofia",
    "Serbia": "Belgrade",
    "Austria": "Vienna",
    "Czech_Republic": "Prague",
    "Slovakia": "Bratislava",
    "Croatia": "Zagreb",
    "Israel": "Jerusalem",
    "United_Arab_Emirates": "Abu Dhabi",
    "Qatar": "Doha",
    "Kuwait": "Kuwait City",
    "Jordan": "Amman",
    "Lebanon": "Beirut",
    "Nepal": "Kathmandu",
    "Sri_Lanka": "Colombo",
    "Myanmar": "Naypyidaw",
    "Kazakhstan": "Nur-Sultan",
    "Uzbekistan": "Tashkent",
    "Azerbaijan": "Baku",
    "Georgia": "Tbilisi",
    "Armenia": "Yerevan",
    "Belarus": "Minsk",
    "Latvia": "Riga",
    "Lithuania": "Vilnius",
    "Estonia": "Tallinn",
    "Slovenia": "Ljubljana",
    "Albania": "Tirana",
    "North_Macedonia": "Skopje",
    "Bosnia_and_Herzegovina": "Sarajevo",
    "Montenegro": "Podgorica",
    "Iceland": "Reykjavik",
    "Luxembourg": "Luxembourg City",
    "Malta": "Valletta",
    "Cyprus": "Nicosia",
    "Bahrain": "Manama",
    "Oman": "Muscat",
    "Moldova": "Chișinău",
    "Mongolia": "Ulaanbaatar",
    "Laos": "Vientiane",
    "Cambodia": "Phnom Penh",
    "Tunisia": "Tunis",
    "Libya": "Tripoli",
    "Zambia": "Lusaka",
    "Mozambique": "Maputo",
    "Botswana": "Gaborone",
    "Namibia": "Windhoek",
    "Senegal": "Dakar",
    "Mali": "Bamako",
    "Niger": "Niamey",
    "Chad": "N'Djamena",
    "Somalia": "Mogadishu",
    "Eritrea": "Asmara",
    "Mauritania": "Nouakchott",
    "Malawi": "Lilongwe",
    "Benin": "Porto-Novo",
    "Togo": "Lomé",
    "Liberia": "Monrovia",
    "Sierra_Leone": "Freetown",
    "Guinea": "Conakry",
    "Guinea-Bissau": "Bissau",
    "Gambia": "Banjul",
    "Equatorial_Guinea": "Malabo",
    "Republic_of_the_Congo": "Brazzaville",
    "Gabon": "Libreville",
    "Cameroon": "Yaoundé",
    "Burkina_Faso": "Ouagadougou",
    "Madagascar": "Antananarivo",
    "Eswatini": "Mbabane",
    "Lesotho": "Maseru",
    "Rwanda": "Kigali",
    "Burundi": "Gitega",
    "Djibouti": "Djibouti",
    "Mauritius": "Port Louis",
    "Comoros": "Moroni",
    "São_Tomé_and_Príncipe": "São Tomé",
    "Seychelles": "Victoria",
    "Cape_Verde": "Praia",
    "Jamaica": "Kingston",
    "Trinidad_and_Tobago": "Port of Spain",
    "Bahamas": "Nassau",
    "Barbados": "Bridgetown",
    "Haiti": "Port-au-Prince",
    "Suriname": "Paramaribo",
    "Guyana": "Georgetown",
    "Ecuador": "Quito",
    "Bolivia": "La Paz",
    "Paraguay": "Asunción",
    "Uruguay": "Montevideo",
    "Panama": "Panama City",
    "Costa_Rica": "San José",
    "Honduras": "Tegucigalpa",
    "El_Salvador": "San Salvador",
    "Nicaragua": "Managua",
    "Belize": "Belmopan",
    "Fiji": "Suva",
    "Papua_New_Guinea": "Port Moresby",
    "Solomon_Islands": "Honiara",
    "Vanuatu": "Port Vila",
    "Kiribati": "South Tarawa"
}

# Region data for continents
REGION_DATA = {
    "Afghanistan": "Asia",
    "Albania": "Europe",
    "Algeria": "Africa",
    "Andorra": "Europe",
    "Angola": "Africa",
    "Antigua_and_Barbuda": "North America",
    "Argentina": "South America",
    "Armenia": "Asia",
    "Australia": "Oceania",
    "Austria": "Europe",
    "Azerbaijan": "Asia",
    "Bahamas": "North America",
    "Bahrain": "Asia",
    "Bangladesh": "Asia",
    "Barbados": "North America",
    "Belarus": "Europe",
    "Belgium": "Europe",
    "Belize": "North America",
    "Benin": "Africa",
    "Bhutan": "Asia",
    "Bolivia": "South America",
    "Bosnia_and_Herzegovina": "Europe",
    "Botswana": "Africa",
    "Brazil": "South America",
    "Brunei": "Asia",
    "Bulgaria": "Europe",
    "Burkina_Faso": "Africa",
    "Burundi": "Africa",
    "Cabo_Verde": "Africa",
    "Cambodia": "Asia",
    "Cameroon": "Africa",
    "Canada": "North America",
    "Cape_Verde": "Africa",
    "Central_African_Republic": "Africa",
    "Chad": "Africa",
    "Chile": "South America",
    "China": "Asia",
    "Colombia": "South America",
    "Comoros": "Africa",
    "Costa_Rica": "North America",
    "Croatia": "Europe",
    "Cuba": "North America",
    "Cyprus": "Europe",
    "Czech_Republic": "Europe", 
    "Democratic_Republic_of_the_Congo": "Africa",
    "Denmark": "Europe",
    "Djibouti": "Africa",
    "Dominica": "North America",
    "Dominican_Republic": "North America",
    "East_Timor": "Asia",
    "Ecuador": "South America",
    "Egypt": "Africa",
    "El_Salvador": "North America",
    "Equatorial_Guinea": "Africa",
    "Eritrea": "Africa",
    "Estonia": "Europe",
    "Eswatini": "Africa",
    "Ethiopia": "Africa",
    "Fiji": "Oceania",
    "Finland": "Europe",
    "France": "Europe",
    "Gabon": "Africa",
    "Gambia": "Africa",
    "Georgia": "Asia",
    "Germany": "Europe",
    "Ghana": "Africa",
    "Greece": "Europe",
    "Grenada": "North America",
    "Guatemala": "North America",
    "Guinea": "Africa",
    "Guinea-Bissau": "Africa",
    "Guyana": "South America",
    "Haiti": "North America",
    "Honduras": "North America",
    "Hungary": "Europe",
    "Iceland": "Europe",
    "India": "Asia",
    "Indonesia": "Asia",
    "Iran": "Asia",
    "Iraq": "Asia",
    "Ireland": "Europe",
    "Israel": "Asia",
    "Italy": "Europe",
    "Jamaica": "North America",
    "Japan": "Asia",
    "Jordan": "Asia",
    "Kazakhstan": "Asia",
    "Kenya": "Africa",
    "Kiribati": "Oceania",
    "Kuwait": "Asia",
    "Kyrgyzstan": "Asia",
    "Laos": "Asia",
    "Latvia": "Europe",
    "Lebanon": "Asia",
    "Lesotho": "Africa",
    "Liberia": "Africa",
    "Libya": "Africa",
    "Liechtenstein": "Europe",
    "Lithuania": "Europe",
    "Luxembourg": "Europe",
    "Madagascar": "Africa",
    "Malawi": "Africa",
    "Malaysia": "Asia",
    "Maldives": "Asia",
    "Mali": "Africa",
    "Malta": "Europe",
    "Marshall_Islands": "Oceania",
    "Mauritania": "Africa",
    "Mauritius": "Africa",
    "Mexico": "North America",
    "Micronesia": "Oceania",
    "Moldova": "Europe",
    "Monaco": "Europe",
    "Mongolia": "Asia",
    "Montenegro": "Europe",
    "Morocco": "Africa",
    "Mozambique": "Africa",
    "Myanmar": "Asia",
    "Namibia": "Africa",
    "Nauru": "Oceania",
    "Nepal": "Asia",
    "Netherlands": "Europe",
    "New_Zealand": "Oceania",
    "Nicaragua": "North America",
    "Niger": "Africa",
    "Nigeria": "Africa",
    "North_Korea": "Asia",
    "North_Macedonia": "Europe",
    "Norway": "Europe",
    "Oman": "Asia",
    "Pakistan": "Asia",
    "Palau": "Oceania",
    "Palestine": "Asia",
    "Panama": "North America",
    "Papua_New_Guinea": "Oceania",
    "Paraguay": "South America",
    "Peru": "South America",
    "Philippines": "Asia",
    "Poland": "Europe",
    "Portugal": "Europe",
    "Qatar": "Asia",
    "Republic_of_the_Congo": "Africa",
    "Romania": "Europe",
    "Russia": "Europe/Asia",
    "Rwanda": "Africa",
    "Saint_Kitts_and_Nevis": "North America",
    "Saint_Lucia": "North America",
    "Saint_Vincent_and_the_Grenadines": "North America",
    "Samoa": "Oceania",
    "San_Marino": "Europe",
    "São_Tomé_and_Príncipe": "Africa",
    "Saudi_Arabia": "Asia",
    "Senegal": "Africa",
    "Serbia": "Europe",
    "Seychelles": "Africa",
    "Sierra_Leone": "Africa",
    "Singapore": "Asia",
    "Slovakia": "Europe",
    "Slovenia": "Europe",
    "Solomon_Islands": "Oceania",
    "Somalia": "Africa",
    "South_Africa": "Africa",
    "South_Korea": "Asia",
    "South_Sudan": "Africa",
    "Spain": "Europe",
    "Sri_Lanka": "Asia",
    "Sudan": "Africa",
    "Suriname": "South America",
    "Sweden": "Europe",
    "Switzerland": "Europe",
    "Syria": "Asia",
    "Taiwan": "Asia",
    "Tajikistan": "Asia",
    "Tanzania": "Africa",
    "Thailand": "Asia",
    "Togo": "Africa",
    "Tonga": "Oceania",
    "Trinidad_and_Tobago": "North America",
    "Tunisia": "Africa",
    "Turkey": "Europe/Asia",
    "Turkmenistan": "Asia",
    "Tuvalu": "Oceania",
    "Uganda": "Africa",
    "Ukraine": "Europe",
    "United_Arab_Emirates": "Asia",
    "United_Kingdom": "Europe",
    "United_States": "North America",
    "Uruguay": "South America",
    "Uzbekistan": "Asia",
    "Vanuatu": "Oceania",
    "Vatican_City": "Europe",
    "Venezuela": "South America",
    "Vietnam": "Asia",
    "Yemen": "Asia",
    "Zambia": "Africa",
    "Zimbabwe": "Africa"
}

# Population data (in millions)
POPULATION_DATA = {
    "China": 1410,
    "India": 1380,
    "United_States": 331,
    "Indonesia": 273,
    "Pakistan": 220,
    "Brazil": 212,
    "Nigeria": 206,
    "Bangladesh": 164,
    "Russia": 144,
    "Mexico": 128,
    "Japan": 126,
    "Ethiopia": 114,
    "Philippines": 109,
    "Egypt": 102,
    "Vietnam": 97,
    "Turkey": 84,
    "Iran": 83,
    "Germany": 83,
    "Thailand": 70,
    "United_Kingdom": 67,
    "France": 65,
    "Italy": 60,
    "South_Africa": 59,
    "Tanzania": 59,
    "Myanmar": 54,
    "South_Korea": 51,
    "Colombia": 50,
    "Kenya": 53,
    "Spain": 47,
    "Argentina": 45,
    "Ukraine": 44,
    "Algeria": 43,
    "Sudan": 43,
    "Iraq": 40,
    "Poland": 38,
    "Canada": 38,
    "Morocco": 36,
    "Uzbekistan": 33,
    "Saudi_Arabia": 34,
    "Afghanistan": 38,
    "Malaysia": 32,
    "Peru": 32,
    "Angola": 32,
    "Ghana": 31,
    "Mozambique": 31,
    "Yemen": 29,
    "Nepal": 29,
    "Venezuela": 28,
    "Madagascar": 27,
    "Australia": 25,
    "North_Korea": 25,
    "Taiwan": 23,
    "Cameroon": 26
}

# Area data (in square kilometers)
AREA_DATA = {
    "Russia": 17098242,
    "Canada": 9984670,
    "United_States": 9833517,
    "China": 9596960,
    "Brazil": 8515767,
    "Australia": 7692024,
    "India": 3287263,
    "Argentina": 2780400,
    "Kazakhstan": 2724900,
    "Algeria": 2381741,
    "Democratic_Republic_of_the_Congo": 2344858,
    "Saudi_Arabia": 2149690,
    "Mexico": 1964375,
    "Indonesia": 1910931,
    "Sudan": 1886068,
    "Libya": 1759540,
    "Iran": 1648195,
    "Mongolia": 1564110,
    "Peru": 1285216,
    "Chad": 1284000,
    "Niger": 1267000,
    "Angola": 1246700,
    "Mali": 1240192,
    "South_Africa": 1221037,
    "Colombia": 1141748,
    "Ethiopia": 1104300,
    "Bolivia": 1098581,
    "Mauritania": 1030700,
    "Egypt": 1002000,
    "Tanzania": 945087,
    "Nigeria": 923768,
    "Venezuela": 916445,
    "Pakistan": 881912,
    "Namibia": 825615,
    "Mozambique": 801590,
    "Turkey": 783562,
    "Chile": 756102,
    "Zambia": 752612,
    "Myanmar": 676578,
    "Afghanistan": 652230,
    "South_Sudan": 644329,
    "France": 640679,
    "Somalia": 637657,
    "Central_African_Republic": 622984,
    "Ukraine": 603500,
    "Madagascar": 587041,
    "Botswana": 581730,
    "Kenya": 580367,
    "Yemen": 527968,
    "Thailand": 513120,
    "Spain": 505992,
    "Turkmenistan": 488100,
    "Cameroon": 475442,
    "Papua_New_Guinea": 462840,
    "Sweden": 450295,
    "Uzbekistan": 447400,
    "Morocco": 446550,
    "Iraq": 438317,
    "Paraguay": 406752,
    "Zimbabwe": 390757,
    "Japan": 377975,
    "Germany": 357114,
    "Finland": 338424,
    "Vietnam": 331212,
    "Malaysia": 330803,
    "Norway": 323802,
    "Poland": 312696,
    "Oman": 309500,
    "Italy": 301339,
    "Philippines": 300000,
    "Ecuador": 276841,
    "Burkina_Faso": 274200,
    "New_Zealand": 270467,
    "Gabon": 267668,
    "Guinea": 245857,
    "United_Kingdom": 242495,
    "Uganda": 241550,
    "Ghana": 238533,
    "Romania": 238397,
    "Laos": 236800,
    "Guyana": 214969,
    "Belarus": 207600,
    "Kyrgyzstan": 199951,
    "Senegal": 196722,
    "Syria": 185180,
    "Cambodia": 181035,
    "Uruguay": 181034,
    "Tunisia": 163610,
    "Suriname": 163820,
    "Bangladesh": 147570,
    "Nepal": 147181,
    "Tajikistan": 143100,
    "Greece": 131957,
    "Nicaragua": 130373,
    "North_Korea": 120538,
    "Malawi": 118484,
    "Eritrea": 117600,
    "Benin": 112622,
    "Honduras": 112492,
    "Liberia": 111369,
    "Bulgaria": 110879,
    "Cuba": 109884,
    "Guatemala": 108889,
    "Iceland": 103000,
    "South_Korea": 100210,
    "Hungary": 93028,
    "Portugal": 92090,
    "Jordan": 89342,
    "Azerbaijan": 86600,
    "Austria": 83871,
    "United_Arab_Emirates": 83600,
    "Czech_Republic": 78865,
    "Serbia": 77474,
    "Panama": 75417,
    "Sierra_Leone": 71740,
    "Ireland": 70273,
    "Georgia": 69700,
    "Sri_Lanka": 65610,
    "Lithuania": 65300,
    "Latvia": 64589,
    "Togo": 56785,
    "Croatia": 56594,
    "Bosnia_and_Herzegovina": 51209,
    "Costa_Rica": 51100,
    "Slovakia": 49037
}

class SimpleDatabaseBuilder:
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.countries = []
        self.missing_info = []
        self.map_images_found = 0
        self.flag_images_found = 0

    def connect_to_database(self):
        """Connect to SQLite database, creating the directory if needed"""
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
        logger.info(f"Connected to database at {DB_PATH}")

    def delete_existing_data(self):
        """Delete all existing data from the database"""
        try:
            if self.cursor is None:
                raise ValueError("Database connection not established. Call connect_to_database() first.")

            self.cursor.execute("DROP TABLE IF EXISTS countries")
            self.cursor.execute("DROP TABLE IF EXISTS maps")
            self.cursor.execute("DROP TABLE IF EXISTS hints")
            self.conn.commit()
            logger.info("Deleted existing tables")
        except Exception as e:
            logger.error(f"Error deleting existing data: {e}")
            raise

    def create_schema(self):
        """Create the new database schema"""
        try:
            if self.cursor is None:
                raise ValueError("Database connection not established. Call connect_to_database() first.")

            # Create the countries table with all required columns
            self.cursor.execute('''
            CREATE TABLE countries (
                number INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                neighbor_country TEXT,
                map_image_link TEXT,
                flag_image_link TEXT,
                capital TEXT,
                neighbor_capital TEXT,
                region TEXT,
                area REAL,
                population INTEGER,
                last_updated INTEGER
            )
            ''')
            self.conn.commit()
            logger.info("Created new database schema")
        except Exception as e:
            logger.error(f"Error creating schema: {e}")
            raise

    def load_country_list(self):
        """Load the list of countries from file"""
        try:
            with open(COUNTRY_LIST_PATH, 'r') as file:
                self.countries = [line.strip() for line in file if line.strip()]
            logger.info(f"Loaded {len(self.countries)} countries from {COUNTRY_LIST_PATH}")
        except Exception as e:
            logger.error(f"Error loading country list: {e}")
            raise

    def check_image_exists(self, country_name: str) -> Tuple[bool, bool]:
        """Check if map and flag images exist for the country"""
        formatted_name = country_name.replace(' ', '_')
        map_path = os.path.join(MAP_IMAGES_DIR, f"{formatted_name}_locator_map.png")
        flag_path = os.path.join(FLAG_IMAGES_DIR, f"{formatted_name}_flag.png")

        # Check for custom flag path
        if country_name in CUSTOM_FLAG_PATHS:
            flag_path = CUSTOM_FLAG_PATHS[country_name]
        elif formatted_name in CUSTOM_FLAG_PATHS:
            flag_path = CUSTOM_FLAG_PATHS[formatted_name]

        map_exists = os.path.exists(map_path)
        flag_exists = os.path.exists(flag_path)

        return map_exists, flag_exists

    def get_capital(self, country_name: str) -> str:
        """Get capital city for the country from hardcoded data"""
        formatted_name = country_name.replace(' ', '_')
        return CAPITAL_DATA.get(formatted_name, "Unknown")

    def get_region(self, country_name: str) -> str:
        """Get region (continent) for the country from hardcoded data"""
        formatted_name = country_name.replace(' ', '_')
        return REGION_DATA.get(formatted_name, "Unknown")

    def get_population(self, country_name: str) -> Optional[int]:
        """Get population for the country from hardcoded data (in millions)"""
        formatted_name = country_name.replace(' ', '_')
        # Return population in actual numbers (not millions)
        pop_in_millions = POPULATION_DATA.get(formatted_name)
        if pop_in_millions is not None:
            return pop_in_millions * 1000000
        return None

    def get_area(self, country_name: str) -> Optional[float]:
        """Get area for the country from hardcoded data (in square kilometers)"""
        formatted_name = country_name.replace(' ', '_')
        return AREA_DATA.get(formatted_name)

    def populate_database(self):
        """Populate the database with country data"""
        for index, country_name in enumerate(self.countries, 1):
            try:
                # Format country name for image paths
                formatted_name = country_name.replace(' ', '_')

                # Define image links
                map_image_link = f"country_game/images/wiki_all_map_400pi/{formatted_name}_locator_map.png"

                # Use custom flag path if available
                if country_name in CUSTOM_FLAG_PATHS:
                    flag_image_link = CUSTOM_FLAG_PATHS[country_name]
                elif formatted_name in CUSTOM_FLAG_PATHS:
                    flag_image_link = CUSTOM_FLAG_PATHS[formatted_name]
                else:
                    flag_image_link = f"country_game/images/wiki_flag/{formatted_name}_flag.png"

                # Check if images exist
                map_exists, flag_exists = self.check_image_exists(country_name)

                if map_exists:
                    self.map_images_found += 1
                else:
                    logger.warning(f"Map image not found for {country_name}")
                    self.missing_info.append(f"{country_name} - Missing map image")
                    map_image_link = None

                if flag_exists:
                    self.flag_images_found += 1
                else:
                    # Try with custom flag paths
                    custom_path = None
                    if country_name in CUSTOM_FLAG_PATHS:
                        custom_path = CUSTOM_FLAG_PATHS[country_name]
                    elif formatted_name in CUSTOM_FLAG_PATHS:
                        custom_path = CUSTOM_FLAG_PATHS[formatted_name]

                    if custom_path and os.path.exists(custom_path):
                        flag_exists = True
                        self.flag_images_found += 1
                        flag_image_link = custom_path
                    else:
                        if custom_path:
                            logger.warning(f"Custom flag image not found for {country_name} at {custom_path}")
                            self.missing_info.append(f"{country_name} - Missing custom flag image")
                        else:
                            logger.warning(f"Flag image not found for {country_name}")
                            self.missing_info.append(f"{country_name} - Missing flag image")
                        flag_image_link = None

                # Get data from hardcoded collections
                capital = self.get_capital(country_name)
                region = self.get_region(country_name)
                population = self.get_population(country_name)
                area = self.get_area(country_name)

                # Insert data into database
                if self.cursor is None:
                    raise ValueError("Database connection not established. Call connect_to_database() first.")

                self.cursor.execute('''
                INSERT INTO countries (
                    number, name, neighbor_country, map_image_link, flag_image_link, 
                    capital, neighbor_capital, region, area, population, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    index, 
                    formatted_name, 
                    None,  # neighbor_country
                    map_image_link,
                    flag_image_link,
                    capital,
                    None,  # neighbor_capital
                    region,
                    area,  # area
                    population,  # population
                    int(time.time())
                ))

                # Commit every 20 countries to avoid losing all data if there's an error
                if index % 20 == 0:
                    self.conn.commit()
                    logger.info(f"Progress: {index}/{len(self.countries)} countries processed")

            except Exception as e:
                logger.error(f"Error processing country {country_name}: {e}")
                self.missing_info.append(f"{country_name} - Error: {str(e)}")
                continue

        # Final commit
        self.conn.commit()
        logger.info(f"Database population completed. Found {self.map_images_found} maps and {self.flag_images_found} flags.")

    def close_connection(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

    def report_missing_info(self):
        """Report any missinginformation"""
        if self.missing_info:
            logger.warning(f"Missing information for {len(self.missing_info)} countries:")
            for info in self.missing_info[:20]:  # Show just the first 20 to avoid overwhelming
                logger.warning(f"  - {info}")
            if len(self.missing_info) > 20:
                logger.warning(f"  - ... and {len(self.missing_info) - 20} more")
        else:
            logger.info("All country information successfully added to database")

    def run(self):
        """Run the full database rebuild process"""
        try:
            self.connect_to_database()
            self.delete_existing_data()
            self.create_schema()
            self.load_country_list()
            self.populate_database()
            self.report_missing_info()
        finally:
            self.close_connection()

if __name__ == "__main__":
    logger.info("Starting country database rebuild process (enhanced version)")
    builder = SimpleDatabaseBuilder()
    builder.run()
    logger.info("Country database rebuild completed")