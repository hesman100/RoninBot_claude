# Web Interface Architecture Plan

## Overview
This document outlines the architecture and implementation plan for the web interface to the Telegram bot's country guessing game and price tracking features. The web interface will provide an alternative way to interact with the bot's functionality without requiring Telegram.

## Folder Structure
```
web_if/
│
├── docs/                    # Documentation files
│   ├── architecture_plan.md # This document
│   └── api_specs.md         # API specifications
│
├── static/                  # Static assets
│   ├── css/                 # CSS stylesheets
│   │   └── main.css         # Main stylesheet
│   ├── js/                  # JavaScript files
│   │   ├── game.js          # Game functionality
│   │   ├── wallet.js        # Wallet connection functionality 
│   │   └── api.js           # API communication
│   └── assets/              # Images, icons, etc.
│       ├── images/          # Game images (maps, flags)
│       └── icons/           # UI icons
│
├── templates/               # HTML templates
│   ├── index.html           # Main page
│   ├── game.html            # Game interface
│   ├── leaderboard.html     # Leaderboard display
│   └── help.html            # Help page
│
├── app.py                   # Flask application
├── routes.py                # Route definitions
├── models.py                # Data models
├── game_service.py          # Game service connecting to the bot's game functionality
└── wallet_service.py        # Wallet connection service (future integration)
```

## Component Design

### 1. Backend (Flask Application)
- **app.py**: Main Flask application that initializes the web server, session management, and routes.
- **routes.py**: Defines all HTTP endpoints for the web interface.
- **models.py**: Contains data models for user sessions, game state, and leaderboard.
- **game_service.py**: Connects to the bot's game functionality, reusing the existing game logic.
- **wallet_service.py**: Handles wallet connections (future implementation with Ronin wallet).

### 2. Frontend
- **Main Page (index.html)**: Simple layout with buttons for help, different game modes, and login options.
- **Game Interface (game.html)**: Interactive game UI showing maps/flags and answer options.
- **Leaderboard (leaderboard.html)**: Displays the game leaderboard.
- **Help Page (help.html)**: Shows help information about the game and features.

### 3. API Endpoints
- **/api/help**: Returns help information
- **/api/game/map**: Starts a map guessing game
- **/api/game/flag**: Starts a flag guessing game
- **/api/game/capital**: Starts a capital guessing game
- **/api/game/answer**: Submits an answer for the current game
- **/api/leaderboard**: Returns leaderboard data
- **/api/wallet/connect**: Endpoint for wallet connection (future implementation)

## User Flow

### Guest Mode Flow
1. User visits the website
2. User clicks "Play as Guest"
3. User selects a game mode (Map, Flag, Capital)
4. Game starts and user plays without results being saved
5. After game completion, user can play again or view leaderboard (but can't add their score)

### Authenticated Mode Flow (Future Implementation)
1. User visits the website
2. User clicks "Connect Wallet"
3. User connects their Ronin wallet
4. User is authenticated and can play games with results saved
5. User's scores appear on the leaderboard

## Implementation Approach

### Phase 1: Basic Web Interface
- Set up Flask application structure
- Create basic HTML templates and CSS styling
- Implement simple button functionality
- Connect to existing game logic

### Phase 2: Game Functionality
- Integrate game modes (Map, Flag, Capital)
- Implement game flow and scoring
- Create guest mode gameplay

### Phase 3: Wallet Integration
- Research Ronin wallet integration options
- Implement wallet connection functionality
- Enable authenticated gameplay and leaderboard persistence

## Integration with Existing Bot Code

### Reusing Game Logic
The web interface will reuse the existing game logic from `country_game/game_handler.py` to ensure consistent gameplay across both Telegram and web interfaces. This will be done by:

1. Creating adapter classes that translate web requests to the appropriate game handler calls
2. Modifying the game handler to be platform-agnostic (separating core game logic from Telegram-specific code)
3. Implementing a service layer that connects the web interface to the core game functionality

### Database Integration
The web interface will use the same leaderboard database as the Telegram bot, ensuring a unified leaderboard across platforms. We'll need to:

1. Create a database service that handles both Telegram and web user identities
2. Extend the leaderboard schema to include user type (Telegram or web)
3. Implement authentication and session management for web users

## Technology Stack
- **Backend**: Flask, SQLite (reusing existing database)
- **Frontend**: HTML, CSS, JavaScript
- **Authentication**: Custom integration with Ronin wallet (future implementation)

## Next Steps
1. Set up the basic Flask application structure
2. Create wireframes for the UI
3. Implement the core routes and API endpoints
4. Adapt the existing game logic for web use
5. Build the frontend interface
6. Test the guest mode gameplay
7. Research and plan Ronin wallet integration
