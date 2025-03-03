import os

# Bot configuration
# For a real bot, you need to get a token from @BotFather on Telegram
# Set it as an environment variable named TELEGRAM_TOKEN
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "1234567890:ABCdefGhIJKlmnOPQRstUVwxYZ")
# The default dummy token is for development purposes only and won't work with the Telegram API

# Game settings
ANSWER_TIMEOUT = 15  # seconds

# API URLs
COUNTRIES_API_URL = "https://restcountries.com/v3.1/all"

# We need APIs that support country border highlighting
# For this, we need more specialized services

# Primary Map Provider: MapTiler (supports highlighting with their API)
MAPTILER_API_URL = "https://api.maptiler.com/maps/basic/static"

# Backup Map Providers
YANDEX_API_URL = "https://static-maps.yandex.ru/1.x/"
GEOAPIFY_API_URL = "https://maps.geoapify.com/v1/staticmap"
GEOAPIFY_API_KEY = os.getenv("GEOAPIFY_API_KEY", "YOUR_GEOAPIFY_API_KEY")

# Country boundary API for reference (We won't use this directly, but it's helpful to know)
COUNTRY_BOUNDARY_API = "https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson"

# Alternative map URLs for different countries
# These are pre-rendered maps with highlighted borders from Wikimedia Commons
HIGHLIGHTED_MAPS = {
    # Major countries
    "United States": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/13/Map_of_USA_with_state_names.svg/1024px-Map_of_USA_with_state_names.svg.png",
    "Russia": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3f/Russia_on_the_globe_%28Russia_centered%29.svg/1024px-Russia_on_the_globe_%28Russia_centered%29.svg.png",
    "Brazil": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/bc/Brazil_%28orthographic_projection%29.svg/1024px-Brazil_%28orthographic_projection%29.svg.png",
    "China": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/78/People%27s_Republic_of_China_%28orthographic_projection%29.svg/1024px-People%27s_Republic_of_China_%28orthographic_projection%29.svg.png",
    "India": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/bb/India_%28orthographic_projection%29.svg/1024px-India_%28orthographic_projection%29.svg.png",
    "Canada": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/67/Canada_%28orthographic_projection%29.svg/1024px-Canada_%28orthographic_projection%29.svg.png",
    "Australia": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7d/Australia_%28orthographic_projection%29.svg/1024px-Australia_%28orthographic_projection%29.svg.png",
    
    # Europe
    "France": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e1/France_%28orthographic_projection%29.svg/1024px-France_%28orthographic_projection%29.svg.png",
    "Germany": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/95/Germany_%28orthographic_projection%29.svg/1024px-Germany_%28orthographic_projection%29.svg.png",
    "United Kingdom": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/13/United_Kingdom_%28orthographic_projection%29.svg/1024px-United_Kingdom_%28orthographic_projection%29.svg.png",
    "Spain": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/86/Spain_%28orthographic_projection%29.svg/1024px-Spain_%28orthographic_projection%29.svg.png",
    "Italy": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e2/Italy_%28orthographic_projection%29.svg/1024px-Italy_%28orthographic_projection%29.svg.png",
    "Netherlands": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9f/Netherlands_%28orthographic_projection%29.svg/1024px-Netherlands_%28orthographic_projection%29.svg.png",
    "Sweden": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/16/EU-Sweden_%28orthographic_projection%29.svg/1024px-EU-Sweden_%28orthographic_projection%29.svg.png",
    "Poland": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a1/EU-Poland_%28orthographic_projection%29.svg/1024px-EU-Poland_%28orthographic_projection%29.svg.png",
    
    # Asia
    "Japan": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0a/Japan_%28orthographic_projection%29.svg/1024px-Japan_%28orthographic_projection%29.svg.png",
    "South Korea": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/95/South_Korea_%28orthographic_projection%29.svg/1024px-South_Korea_%28orthographic_projection%29.svg.png",
    "Indonesia": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/Indonesia_%28orthographic_projection%29.svg/1024px-Indonesia_%28orthographic_projection%29.svg.png",
    "Malaysia": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9b/Malaysia_%28orthographic_projection%29.svg/1024px-Malaysia_%28orthographic_projection%29.svg.png",
    "Philippines": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a0/Philippines_%28orthographic_projection%29.svg/1024px-Philippines_%28orthographic_projection%29.svg.png",
    "Singapore": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c7/Singapore_%28orthographic_projection%29.svg/1024px-Singapore_%28orthographic_projection%29.svg.png",
    "Myanmar": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/88/Myanmar_%28orthographic_projection%29.svg/1024px-Myanmar_%28orthographic_projection%29.svg.png",
    "Cambodia": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9e/Cambodia_%28orthographic_projection%29.svg/1024px-Cambodia_%28orthographic_projection%29.svg.png",
    "Mongolia": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/Mongolia_%28orthographic_projection%29.svg/1024px-Mongolia_%28orthographic_projection%29.svg.png",
    "Nepal": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5d/Nepal_%28orthographic_projection%29.svg/1024px-Nepal_%28orthographic_projection%29.svg.png",
    "Bangladesh": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/39/Bangladesh_%28orthographic_projection%29.svg/1024px-Bangladesh_%28orthographic_projection%29.svg.png",
    "Sri Lanka": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/27/Sri_Lanka_%28orthographic_projection%29.svg/1024px-Sri_Lanka_%28orthographic_projection%29.svg.png",
    
    # Middle East
    "Saudi Arabia": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c0/Saudi_Arabia_%28orthographic_projection%29.svg/1024px-Saudi_Arabia_%28orthographic_projection%29.svg.png",
    "United Arab Emirates": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/cd/United_Arab_Emirates_%28orthographic_projection%29.svg/1024px-United_Arab_Emirates_%28orthographic_projection%29.svg.png",
    "Qatar": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/59/Qatar_%28orthographic_projection%29.svg/1024px-Qatar_%28orthographic_projection%29.svg.png",
    "Israel": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5a/Israel_%28orthographic_projection%29.svg/1024px-Israel_%28orthographic_projection%29.svg.png",
    "Turkey": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1c/Turkey_%28orthographic_projection%29.svg/1024px-Turkey_%28orthographic_projection%29.svg.png",
    "Iran": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/21/Iran_%28orthographic_projection%29.svg/1024px-Iran_%28orthographic_projection%29.svg.png",
    "Iraq": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a8/Iraq_%28orthographic_projection%29.svg/1024px-Iraq_%28orthographic_projection%29.svg.png",
    "Jordan": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/bc/Jordan_%28orthographic_projection%29.svg/1024px-Jordan_%28orthographic_projection%29.svg.png",
    
    # Southeast Asia
    "Thailand": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/cc/Thailand_%28orthographic_projection%29.svg/1024px-Thailand_%28orthographic_projection%29.svg.png",
    "Vietnam": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/59/Vietnam_%28orthographic_projection%29.svg/1024px-Vietnam_%28orthographic_projection%29.svg.png",
    
    # Africa
    "South Africa": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6e/South_Africa_%28orthographic_projection%29.svg/1024px-South_Africa_%28orthographic_projection%29.svg.png",
    "Egypt": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a1/Egypt_%28orthographic_projection%29.svg/1024px-Egypt_%28orthographic_projection%29.svg.png",
    "Nigeria": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4b/Nigeria_%28orthographic_projection%29.svg/1024px-Nigeria_%28orthographic_projection%29.svg.png",
    "Kenya": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a5/Kenya_%28orthographic_projection%29.svg/1024px-Kenya_%28orthographic_projection%29.svg.png",
    "Morocco": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/26/Morocco_%28orthographic_projection%29.svg/1024px-Morocco_%28orthographic_projection%29.svg.png",
    "Algeria": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/25/Algeria_%28orthographic_projection%29.svg/1024px-Algeria_%28orthographic_projection%29.svg.png",
    "Tunisia": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/08/Tunisia_%28orthographic_projection%29.svg/1024px-Tunisia_%28orthographic_projection%29.svg.png",
    "Libya": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a9/Libya_%28orthographic_projection%29.svg/1024px-Libya_%28orthographic_projection%29.svg.png",
    "Ghana": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/30/Ghana_%28orthographic_projection%29.svg/1024px-Ghana_%28orthographic_projection%29.svg.png",
    "Ethiopia": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/85/Ethiopia_%28orthographic_projection%29.svg/1024px-Ethiopia_%28orthographic_projection%29.svg.png",
    "Uganda": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3e/Uganda_%28orthographic_projection%29.svg/1024px-Uganda_%28orthographic_projection%29.svg.png",
    "Tanzania": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/Tanzania_%28orthographic_projection%29.svg/1024px-Tanzania_%28orthographic_projection%29.svg.png",
    "Madagascar": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/99/Madagascar_%28orthographic_projection%29.svg/1024px-Madagascar_%28orthographic_projection%29.svg.png",
    "Senegal": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5c/Senegal_%28orthographic_projection%29.svg/1024px-Senegal_%28orthographic_projection%29.svg.png",
    "Cameroon": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b4/Cameroon_%28orthographic_projection%29.svg/1024px-Cameroon_%28orthographic_projection%29.svg.png",
    "Ivory Coast": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/45/Côte_d%27Ivoire_%28orthographic_projection%29.svg/1024px-Côte_d%27Ivoire_%28orthographic_projection%29.svg.png",
    "Angola": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/Angola_%28orthographic_projection%29.svg/1024px-Angola_%28orthographic_projection%29.svg.png",
    "Democratic Republic of the Congo": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d6/Democratic_Republic_of_the_Congo_%28orthographic_projection%29.svg/1024px-Democratic_Republic_of_the_Congo_%28orthographic_projection%29.svg.png",
    "Zambia": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/26/Zambia_%28orthographic_projection%29.svg/1024px-Zambia_%28orthographic_projection%29.svg.png",
    "Zimbabwe": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/50/Zimbabwe_%28orthographic_projection%29.svg/1024px-Zimbabwe_%28orthographic_projection%29.svg.png",
    "Mozambique": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/84/Mozambique_%28orthographic_projection%29.svg/1024px-Mozambique_%28orthographic_projection%29.svg.png",
    "Namibia": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d8/Namibia_%28orthographic_projection%29.svg/1024px-Namibia_%28orthographic_projection%29.svg.png",
    "Botswana": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8f/Botswana_%28orthographic_projection%29.svg/1024px-Botswana_%28orthographic_projection%29.svg.png",
    "Malawi": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/13/Malawi_%28orthographic_projection%29.svg/1024px-Malawi_%28orthographic_projection%29.svg.png",
    "Mali": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8b/Mali_%28orthographic_projection%29.svg/1024px-Mali_%28orthographic_projection%29.svg.png",
    "Burkina Faso": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4d/Burkina_Faso_%28orthographic_projection%29.svg/1024px-Burkina_Faso_%28orthographic_projection%29.svg.png",
    "Niger": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/88/Niger_%28orthographic_projection%29.svg/1024px-Niger_%28orthographic_projection%29.svg.png",
    "Chad": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/46/Chad_%28orthographic_projection%29.svg/1024px-Chad_%28orthographic_projection%29.svg.png",
    "Sudan": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/77/Sudan_%28orthographic_projection%29.svg/1024px-Sudan_%28orthographic_projection%29.svg.png",
    "South Sudan": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/65/South_Sudan_%28orthographic_projection%29.svg/1024px-South_Sudan_%28orthographic_projection%29.svg.png",
    "Somalia": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4c/Somalia_%28orthographic_projection%29.svg/1024px-Somalia_%28orthographic_projection%29.svg.png",
    "Eritrea": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/43/Eritrea_%28Africa_orthographic_projection%29.svg/1024px-Eritrea_%28Africa_orthographic_projection%29.svg.png",
    "Djibouti": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b7/Djibouti_%28orthographic_projection%29.svg/1024px-Djibouti_%28orthographic_projection%29.svg.png",
    "Guinea": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e3/Guinea_%28orthographic_projection%29.svg/1024px-Guinea_%28orthographic_projection%29.svg.png",
    "Sierra Leone": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/38/Sierra_Leone_%28orthographic_projection%29.svg/1024px-Sierra_Leone_%28orthographic_projection%29.svg.png",
    "Liberia": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/91/Liberia_%28orthographic_projection%29.svg/1024px-Liberia_%28orthographic_projection%29.svg.png",
    "Togo": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b1/Togo_%28orthographic_projection%29.svg/1024px-Togo_%28orthographic_projection%29.svg.png",
    "Benin": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9a/Benin_%28orthographic_projection%29.svg/1024px-Benin_%28orthographic_projection%29.svg.png",
    "Gabon": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/bf/Gabon_%28orthographic_projection%29.svg/1024px-Gabon_%28orthographic_projection%29.svg.png",
    "Republic of the Congo": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/Republic_of_the_Congo_%28orthographic_projection%29.svg/1024px-Republic_of_the_Congo_%28orthographic_projection%29.svg.png",
    "Central African Republic": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0c/Central_African_Republic_%28orthographic_projection%29.svg/1024px-Central_African_Republic_%28orthographic_projection%29.svg.png",
    "Rwanda": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/76/Rwanda_%28orthographic_projection%29.svg/1024px-Rwanda_%28orthographic_projection%29.svg.png",
    "Burundi": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/27/Burundi_%28orthographic_projection%29.svg/1024px-Burundi_%28orthographic_projection%29.svg.png",
    
    # South America
    "Argentina": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/bd/Argentina_%28orthographic_projection%29.svg/1024px-Argentina_%28orthographic_projection%29.svg.png",
    "Colombia": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/ca/Colombia_%28orthographic_projection%29.svg/1024px-Colombia_%28orthographic_projection%29.svg.png",
    "Chile": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/33/Chile_%28orthographic_projection%29.svg/1024px-Chile_%28orthographic_projection%29.svg.png",
    "Peru": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Peru_%28orthographic_projection%29.svg/1024px-Peru_%28orthographic_projection%29.svg.png",
    "Venezuela": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0d/Venezuela_%28orthographic_projection%29.svg/1024px-Venezuela_%28orthographic_projection%29.svg.png",
    "Ecuador": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e3/Ecuador_%28orthographic_projection%29.svg/1024px-Ecuador_%28orthographic_projection%29.svg.png",
    "Bolivia": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Bolivia_%28orthographic_projection%29.svg/1024px-Bolivia_%28orthographic_projection%29.svg.png",
    "Paraguay": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9c/Paraguay_%28orthographic_projection%29.svg/1024px-Paraguay_%28orthographic_projection%29.svg.png",
    "Uruguay": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5c/Uruguay_%28orthographic_projection%29.svg/1024px-Uruguay_%28orthographic_projection%29.svg.png",
    "Suriname": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/89/Suriname_%28orthographic_projection%29.svg/1024px-Suriname_%28orthographic_projection%29.svg.png",
    "Guyana": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/20/Guyana_%28orthographic_projection%29.svg/1024px-Guyana_%28orthographic_projection%29.svg.png",
    
    # North America
    "Mexico": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/Mexico_%28orthographic_projection%29.svg/1024px-Mexico_%28orthographic_projection%29.svg.png",
    "Cuba": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/bd/Cuba_%28orthographic_projection%29.svg/1024px-Cuba_%28orthographic_projection%29.svg.png",
    "Jamaica": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1d/Jamaica_%28orthographic_projection%29.svg/1024px-Jamaica_%28orthographic_projection%29.svg.png",
    "Panama": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5c/Panama_%28orthographic_projection%29.svg/1024px-Panama_%28orthographic_projection%29.svg.png",
    "Costa Rica": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/Costa_Rica_%28orthographic_projection%29.svg/1024px-Costa_Rica_%28orthographic_projection%29.svg.png",
    "Haiti": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/fe/Haiti_%28orthographic_projection%29.svg/1024px-Haiti_%28orthographic_projection%29.svg.png",
    "Dominican Republic": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/95/Dominican_Republic_%28orthographic_projection%29.svg/1024px-Dominican_Republic_%28orthographic_projection%29.svg.png",
    "Bahamas": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9b/The_Bahamas_%28orthographic_projection%29.svg/1024px-The_Bahamas_%28orthographic_projection%29.svg.png",
    "Trinidad and Tobago": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d4/Trinidad_and_Tobago_%28orthographic_projection%29.svg/1024px-Trinidad_and_Tobago_%28orthographic_projection%29.svg.png",
    "Barbados": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8a/Barbados_on_the_globe_%28small_islands_magnified%29.svg/1024px-Barbados_on_the_globe_%28small_islands_magnified%29.svg.png",
    "Saint Lucia": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8a/Saint_Lucia_on_the_globe_%28small_islands_magnified%29.svg/1024px-Saint_Lucia_on_the_globe_%28small_islands_magnified%29.svg.png",
    "Grenada": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8a/Grenada_on_the_globe_%28small_islands_magnified%29.svg/1024px-Grenada_on_the_globe_%28small_islands_magnified%29.svg.png",
    "El Salvador": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d2/El_Salvador_%28orthographic_projection%29.svg/1024px-El_Salvador_%28orthographic_projection%29.svg.png",
    "Honduras": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0c/Honduras_%28orthographic_projection%29.svg/1024px-Honduras_%28orthographic_projection%29.svg.png",
    "Nicaragua": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0c/Nicaragua_%28orthographic_projection%29.svg/1024px-Nicaragua_%28orthographic_projection%29.svg.png",
    "Guatemala": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d5/Guatemala_%28orthographic_projection%29.svg/1024px-Guatemala_%28orthographic_projection%29.svg.png",
    "Belize": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9d/BLZ_orthographic.svg/1024px-BLZ_orthographic.svg.png",
    
    # Oceania
    "New Zealand": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d8/New_Zealand_%28orthographic_projection%29.svg/1024px-New_Zealand_%28orthographic_projection%29.svg.png",
    "Fiji": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5e/Fiji_%28orthographic_projection%29.svg/1024px-Fiji_%28orthographic_projection%29.svg.png",
    "Papua New Guinea": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/Papua_New_Guinea_%28orthographic_projection%29.svg/1024px-Papua_New_Guinea_%28orthographic_projection%29.svg.png",
    "Solomon Islands": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8a/Solomon_Islands_on_the_globe_%28small_islands_magnified%29.svg/1024px-Solomon_Islands_on_the_globe_%28small_islands_magnified%29.svg.png",
    "Vanuatu": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7a/Vanuatu_on_the_globe_%28Polynesia_centered%29.svg/1024px-Vanuatu_on_the_globe_%28Polynesia_centered%29.svg.png",
    "Samoa": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7a/Samoa_on_the_globe_%28Polynesia_centered%29.svg/1024px-Samoa_on_the_globe_%28Polynesia_centered%29.svg.png",
    "Kiribati": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7a/Kiribati_on_the_globe_%28Polynesia_centered%29.svg/1024px-Kiribati_on_the_globe_%28Polynesia_centered%29.svg.png",
    "Tonga": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7a/Tonga_on_the_globe_%28Polynesia_centered%29.svg/1024px-Tonga_on_the_globe_%28Polynesia_centered%29.svg.png",
    "Marshall Islands": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7a/Marshall_Islands_on_the_globe_%28small_islands_magnified%29_%28Polynesia_centered%29.svg/1024px-Marshall_Islands_on_the_globe_%28small_islands_magnified%29_%28Polynesia_centered%29.svg.png",
    "Micronesia": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7a/Federated_States_of_Micronesia_on_the_globe_%28small_islands_magnified%29_%28Polynesia_centered%29.svg/1024px-Federated_States_of_Micronesia_on_the_globe_%28small_islands_magnified%29_%28Polynesia_centered%29.svg.png",
    "Palau": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7a/Palau_on_the_globe_%28small_islands_magnified%29_%28Polynesia_centered%29.svg/1024px-Palau_on_the_globe_%28small_islands_magnified%29_%28Polynesia_centered%29.svg.png",
    "Nauru": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7a/Nauru_on_the_globe_%28small_islands_magnified%29_%28Polynesia_centered%29.svg/1024px-Nauru_on_the_globe_%28small_islands_magnified%29_%28Polynesia_centered%29.svg.png",
    "Tuvalu": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7a/Tuvalu_on_the_globe_%28small_islands_magnified%29_%28Polynesia_centered%29.svg/1024px-Tuvalu_on_the_globe_%28small_islands_magnified%29_%28Polynesia_centered%29.svg.png",
    
    # Additional European countries
    "Ireland": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/14/EU-Ireland_%28orthographic_projection%29.svg/1024px-EU-Ireland_%28orthographic_projection%29.svg.png",
    "Greece": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6d/EU-Greece_%28orthographic_projection%29.svg/1024px-EU-Greece_%28orthographic_projection%29.svg.png",
    "Portugal": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/49/EU-Portugal_%28orthographic_projection%29.svg/1024px-EU-Portugal_%28orthographic_projection%29.svg.png",
    "Switzerland": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f2/Switzerland_%28orthographic_projection%29.svg/1024px-Switzerland_%28orthographic_projection%29.svg.png",
    "Denmark": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9f/Denmark_%28orthographic_projection%29.svg/1024px-Denmark_%28orthographic_projection%29.svg.png",
    "Iceland": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/93/Iceland_%28orthographic_projection%29.svg/1024px-Iceland_%28orthographic_projection%29.svg.png",
    "Finland": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f7/EU-Finland_%28orthographic_projection%29.svg/1024px-EU-Finland_%28orthographic_projection%29.svg.png",
    "Estonia": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8c/EU-Estonia_%28orthographic_projection%29.svg/1024px-EU-Estonia_%28orthographic_projection%29.svg.png",
    "Latvia": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e2/EU-Latvia_%28orthographic_projection%29.svg/1024px-EU-Latvia_%28orthographic_projection%29.svg.png",
    "Lithuania": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9a/EU-Lithuania_%28orthographic_projection%29.svg/1024px-EU-Lithuania_%28orthographic_projection%29.svg.png",
    "Austria": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a5/EU-Austria_%28orthographic_projection%29.svg/1024px-EU-Austria_%28orthographic_projection%29.svg.png",
    "Romania": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/Romania_%28orthographic_projection%29.svg/1024px-Romania_%28orthographic_projection%29.svg.png",
    "Belgium": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/eb/EU-Belgium_%28orthographic_projection%29.svg/1024px-EU-Belgium_%28orthographic_projection%29.svg.png",
    "Czechia": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/96/EU-Czechia_%28orthographic_projection%29.svg/1024px-EU-Czechia_%28orthographic_projection%29.svg.png",
    "Slovakia": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/EU-Slovakia_%28orthographic_projection%29.svg/1024px-EU-Slovakia_%28orthographic_projection%29.svg.png",
    "Hungary": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/41/EU-Hungary_%28orthographic_projection%29.svg/1024px-EU-Hungary_%28orthographic_projection%29.svg.png",
    "Croatia": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/69/EU-Croatia_%28orthographic_projection%29.svg/1024px-EU-Croatia_%28orthographic_projection%29.svg.png",
    "Serbia": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e8/Serbia_%28orthographic_projection%29.svg/1024px-Serbia_%28orthographic_projection%29.svg.png",
    "Bulgaria": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/EU-Bulgaria_%28orthographic_projection%29.svg/1024px-EU-Bulgaria_%28orthographic_projection%29.svg.png",
    "Ukraine": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0c/Ukraine_%28orthographic_projection%29.svg/1024px-Ukraine_%28orthographic_projection%29.svg.png",
    "Belarus": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6f/Belarus_%28orthographic_projection%29.svg/1024px-Belarus_%28orthographic_projection%29.svg.png",
    "Moldova": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e5/Moldova_%28orthographic_projection%29.svg/1024px-Moldova_%28orthographic_projection%29.svg.png",
    "Cyprus": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/70/EU-Cyprus_%28orthographic_projection%29.svg/1024px-EU-Cyprus_%28orthographic_projection%29.svg.png",
    "Malta": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8c/EU-Malta_%28orthographic_projection%29.svg/1024px-EU-Malta_%28orthographic_projection%29.svg.png"
}

# Cache settings (to reduce API calls)
# Cache duration in seconds (1 day)
CACHE_DURATION = 24 * 60 * 60

# Game messages
START_MESSAGE = "👋 Welcome to Country Guess! Use /game or /g to start a new game. Try /g help to see all commands and game modes."
HELP_MESSAGE = """
🌍 *Country Guess Bot* 🌍

Commands:
/start - Start the bot
/game or /g - Start a new game (map mode)
/game map or /g map - Start a map guessing game
/game flag or /g flag - Start a flag guessing game
/game cap or /g cap - Start a capital city guessing game
/game me or /g me - View your personal statistics
/game lb or /g lb - View the global leaderboard
/game help or /g help - Show this help message

Game Modes:
- 🗺️ *Map Mode*: See a country map, guess the country name
- 🚩 *Flag Mode*: See a country flag, guess the country name
- 🏙️ *Capital Mode*: See a country map, guess the capital city

How to play:
1. Use /g to start a new game in map mode
2. You have 15 seconds to guess the answer
3. If correct, you're a marveller! 🏆
4. If wrong or too slow, you're a vozer! 😢

Track your progress with /g me and compete with others on the /g lb leaderboard!

Good luck!
"""

GAME_START_MESSAGE = "🗺️ Guess the country shown in the map! You have 15 seconds ⏱️"
CORRECT_ANSWER_MESSAGE = "🎉 Correct! You are a marveller! 🏆"
WRONG_ANSWER_MESSAGE = "❌ Wrong answer! You are a VOZER. 😢"
TIMEOUT_MESSAGE = "⏱️ Time's up! You are a VOZER. 😢"
ERROR_MESSAGE = "Sorry, there was an error. Please try again."
