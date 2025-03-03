# Country Guessing Game Bot - Files for Transfer

This folder contains all the core files needed to transfer the Country Guessing Game bot functionality to your other Telegram bot project.

## Core Files
- `bot.py` - Main bot implementation with command handlers
- `game_handler.py` - Game logic, user state management, and conversation handling
- `country_database.py` - Database interface for country data
- `country_data.py` - Legacy file for country data (can be used as a fallback)
- `config.py` - Configuration settings and message templates

## Test Files
- `comprehensive_test.py` - Complete testing suite for all bot components
- `test_bot.py` - Testing specific bot functionality
- `test_database.py` - Testing database functionality
- `test_game_functionality.py` - Testing game-specific features

## Database Files
- `sql/` - Contains SQL scripts for database setup

## Implementation Instructions

### Setup in Your Project
1. Copy these files to your CryptoPriceBot project
2. Install necessary dependencies:
   ```
   pip install python-telegram-bot psycopg2-binary
   ```
3. Ensure you have the TELEGRAM_TOKEN environment variable set

### Database Setup
1. You'll need PostgreSQL database access
2. The database structure is in the SQL files
3. The bot expects environment variables like DATABASE_URL to be set

### Code Modification for CryptoPriceBot
In your CryptoPriceBot project:

1. Integrate the command handlers from `bot.py` into your existing bot
2. Adapt the game functionality for cryptocurrency prices if needed
3. Update the config.py messages for your bot's specific needs

### Example Integration
```python
# In your CryptoPriceBot's main file
from country_game.game_handler import GameHandler  # Import the game functionality

# Initialize your existing bot...

# Add the country game functionality
game_handler = GameHandler()
dispatcher.add_handler(game_handler.get_conversation_handler())
dispatcher.add_handler(CommandHandler("game", game_command, pass_args=True))
dispatcher.add_handler(CommandHandler("g", game_command, pass_args=True))
```

## Image Transfer
The main project uses local map and flag images. You'll need to:

1. Copy the wiki_all_map_400pi and wiki_flag folders to your project
2. These folders are available as zip files in the main project

## Important Notes
- The game handler includes a statistics system for tracking user performance
- Adapt the messages in config.py to match your bot's style
- You may need to customize the hint generation logic for your specific use case

## Testing
The comprehensive_test.py script can be run to verify all components are working properly:

```
python comprehensive_test.py
```