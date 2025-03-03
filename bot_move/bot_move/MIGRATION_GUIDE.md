# Migration Guide: Country Bot to CryptoPriceBot

This guide will help you transfer the country guessing game functionality to your CryptoPriceBot project while maintaining the same command structure.

## Step 1: Copy Files

First, copy all the files from this `bot_move` folder to your CryptoPriceBot project. You can organize them in one of two ways:

### Option A: Separate Module
Create a subdirectory in your CryptoPriceBot project:
```
mkdir -p CryptoPriceBot/country_game/
cp -r * CryptoPriceBot/country_game/
```

### Option B: Direct Integration
Copy the files directly to your project's root:
```
cp -r * CryptoPriceBot/
```

## Step 2: Install Dependencies

Install the required dependencies:
```
pip install -r requirements.txt
```

## Step 3: Database Setup

The country game requires a PostgreSQL database. You have two options:

### Option A: Use the Existing Database
If your CryptoPriceBot already has a PostgreSQL database, you can create the necessary tables in that database:
```python
from country_database import CountryDatabase
db = CountryDatabase()
db.create_tables()
```

### Option B: Create a New Database
Create a new PostgreSQL database specifically for the country game functionality.

## Step 4: Integrate Bot Commands

You need to integrate the game commands into your existing CryptoPriceBot. Here's how:

### Identify Main Command Entry Points
The key commands to integrate are:
- `/game` or `/g` - Starts the country guessing game
- Subcommands like `/game map`, `/game flag`, `/game capital`
- Conversation handlers for managing game state

### Integration Example
In your main bot file:

```python
# Import the necessary components
from country_game.game_handler import GameHandler
from country_game.country_database import get_database

# Your existing bot setup code...

# Initialize the country database
country_database = get_database()

# Create the game handler
game_handler = GameHandler()

# Store in bot_data for access
dispatcher.bot_data['game_handler'] = game_handler
dispatcher.bot_data['country_database'] = country_database

# Add the game conversation handler
dispatcher.add_handler(game_handler.get_conversation_handler())

# Add command handlers
def game_command(update, context):
    # This function is from bot.py
    # Copy the implementation from bot.py or import it
    ...

dispatcher.add_handler(CommandHandler("game", game_command, pass_args=True))
dispatcher.add_handler(CommandHandler("g", game_command, pass_args=True))
```

## Step 5: Adapt Messages and Theme

Update the messages in `config.py` to match your CryptoPriceBot's theme and style.

## Step 6: Test the Integration

Run the tests to make sure everything works:
```
python comprehensive_test.py
```

## Troubleshooting

### Database Connection Issues
- Ensure the DATABASE_URL environment variable is set
- Check permissions on the PostgreSQL user

### Missing Images
- Make sure you've copied the `wiki_all_map_400pi` and `wiki_flag` folders
- Update file paths in the code if you've stored them in a different location

### Command Conflicts
- If both bots have commands with the same name, you might need to rename them
- You can modify the conversation handlers to use different entry points

## Optional Customization

If you want to completely rebrand the country game functionality:

1. Edit `config.py` to change all message texts
2. Update command names in the bot.py file if needed
3. Modify the game handler to use different state names