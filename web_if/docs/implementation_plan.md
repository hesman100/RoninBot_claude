# Web Interface Implementation Plan

This document outlines the technical implementation plan for creating a web interface for the country guessing game. It provides a step-by-step approach to building the web application while reusing existing game functionality.

## Phase 1: Setup and Basic Structure (1-2 weeks)

### 1. Flask Application Setup
- Create the main Flask application (`app.py`)
- Configure session management and security settings
- Set up error handling and logging
- Create basic route structure

### 2. Database Integration
- Analyze the existing SQLite database schema for leaderboard
- Create adapter classes to access the database from Flask
- Design database extensions to handle web users vs. Telegram users
- Implement session management for guest users

### 3. Static Files Organization
- Set up CSS styling framework (custom or Bootstrap)
- Create basic JavaScript structure
- Organize assets folder for images and icons
- Implement responsive design templates

### 4. Basic UI Implementation
- Create the main page layout with navigation
- Implement help page with game instructions
- Set up basic leaderboard view
- Create placeholders for game screens

## Phase 2: Game Logic Integration (2-3 weeks)

### 1. Game Service Layer
- Create adapter classes to interface with existing game logic
- Refactor `game_handler.py` to separate core game logic from Telegram-specific code
- Implement web-specific game session management
- Create API endpoints for game operations

### 2. Game UI Implementation
- Build interactive game screens for map, flag, and capital modes
- Implement timer functionality for game sessions
- Create answer submission and validation logic
- Design and implement game result displays

### 3. Guest Mode Gameplay
- Implement guest user session tracking
- Create temporary game state storage for guest sessions
- Build game flow for guests without leaderboard integration
- Implement play again functionality

### 4. Image Asset Management
- Create a system to serve country maps and flags
- Optimize images for web delivery
- Implement lazy loading for better performance
- Ensure mobile compatibility of image display

## Phase 3: API and Integration (2-3 weeks)

### 1. RESTful API Development
- Design comprehensive API for all game functions
- Implement authentication logic for API endpoints
- Create documentation for API usage
- Add rate limiting and security measures

### 2. Leaderboard Integration
- Connect web interface to existing leaderboard database
- Implement leaderboard display with filtering options
- Create user profile display for authenticated users
- Implement leaderboard statistics and visualizations

### 3. Testing and Optimization
- Develop unit tests for core functionality
- Implement integration tests for game flow
- Optimize performance for mobile devices
- Address cross-browser compatibility issues

## Phase 4: Wallet Integration (Future Implementation, 3-4 weeks)

### 1. Ronin Wallet Research
- Research Ronin wallet API and integration options
- Design authentication flow using wallet signatures
- Plan secure session management for wallet users
- Design user identity management system

### 2. Wallet Connection Implementation
- Create wallet connection interface
- Implement authentication using wallet signatures
- Develop session management for authenticated users
- Build user profile system tied to wallet addresses

### 3. Authenticated Gameplay
- Connect authenticated users to leaderboard persistence
- Implement profile-based game statistics
- Create achievements and progression system
- Design personalized dashboards for users

### 4. Security and Compliance
- Implement secure wallet integration practices
- Ensure data privacy compliance
- Create backup and recovery options
- Develop anti-cheating measures

## Technical Architecture Details

### Backend Components

#### 1. Core Flask Application (`app.py`)
```python
from flask import Flask, session, render_template
from flask_login import LoginManager
from game_service import GameService

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Use environment variable in production
login_manager = LoginManager(app)

# Initialize services
game_service = GameService()

@app.route('/')
def index():
    return render_template('index.html', version="1.3")

# Additional routes will be defined in routes.py
```

#### 2. Game Service Adapter (`game_service.py`)
```python
import random
import time
from country_game.game_handler import GameHandler  # Reuse existing game logic

class GameService:
    """Service that adapts the existing game handler for web use"""
    
    def __init__(self):
        self.game_handler = GameHandler(bot_version="1.3")
        self.active_games = {}  # Web sessions to active games mapping
        
    def start_game(self, session_id, game_mode):
        """Start a new game for a web session"""
        # Implementation will adapt GameHandler functionality for web
        
    def submit_answer(self, session_id, answer):
        """Process an answer from a web user"""
        # Implementation will adapt GameHandler functionality for web
```

#### 3. Database Integration (`models.py`)
```python
import sqlite3
import time
from flask_login import UserMixin

class User(UserMixin):
    """User model for Flask-Login"""
    
    def __init__(self, id, name, auth_type="guest"):
        self.id = id
        self.name = name
        self.auth_type = auth_type  # "guest" or "wallet"

class LeaderboardService:
    """Service to interact with the leaderboard database"""
    
    def __init__(self, db_path="country_game/database/leaderboard.db"):
        self.db_path = db_path
        
    def get_leaderboard(self, limit=10):
        """Get top scores from the leaderboard"""
        # Implementation will access the existing leaderboard
```

### Frontend Components

#### 1. Main JavaScript Module (`static/js/game.js`)
```javascript
// Game management module
const GameManager = {
    currentGame: null,
    timeRemaining: 0,
    timerInterval: null,
    
    // Start a new game
    startGame: function(mode) {
        fetch(`/api/game/${mode}`)
            .then(response => response.json())
            .then(data => {
                this.setupGameUI(data);
                this.startTimer();
            });
    },
    
    // Submit an answer
    submitAnswer: function(answer) {
        fetch('/api/game/answer', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ answer: answer })
        })
        .then(response => response.json())
        .then(data => {
            this.showResult(data);
        });
    },
    
    // Additional game UI functions will be implemented
};
```

#### 2. API Communication (`static/js/api.js`)
```javascript
// API communication module
const ApiClient = {
    baseUrl: '/api',
    
    // Fetch leaderboard data
    getLeaderboard: async function() {
        const response = await fetch(`${this.baseUrl}/leaderboard`);
        return await response.json();
    },
    
    // Fetch help information
    getHelp: async function() {
        const response = await fetch(`${this.baseUrl}/help`);
        return await response.json();
    },
    
    // Connect wallet (future implementation)
    connectWallet: async function() {
        // Placeholder for future wallet connection logic
    }
};
```

## API Endpoints Specification

### Game API
- `GET /api/game/map` - Start a new map guessing game
- `GET /api/game/flag` - Start a new flag guessing game
- `GET /api/game/capital` - Start a new capital guessing game
- `POST /api/game/answer` - Submit an answer for the current game
  - Request body: `{ "answer": "CountryName" }`
  - Response: Game result with correct answer and details

### Leaderboard API
- `GET /api/leaderboard` - Get leaderboard data
  - Query parameters: `limit` (number of entries), `mode` (game mode filter)
  - Response: List of top players with scores and stats

### User API
- `GET /api/user/profile` - Get current user profile (if authenticated)
- `POST /api/user/guest` - Create a new guest session
- `POST /api/wallet/connect` - Connect wallet (future implementation)
  - Request body: `{ "signature": "WalletSignature", "address": "WalletAddress" }`
  - Response: Authentication token and user profile

## Deployment Considerations

### Hosting Options
- Deploy on Replit with continuous integration
- Ensure proper environment variable management for secrets
- Configure proper caching for static assets
- Implement rate limiting for API endpoints

### Performance Optimization
- Minify and bundle JavaScript and CSS
- Optimize image delivery for different device sizes
- Implement lazy loading for game assets
- Use caching strategies for game data

### Security Considerations
- Implement CSRF protection for all forms
- Secure session management
- Input validation for all user-provided data
- Rate limiting to prevent abuse
- Secure wallet integration with proper signature validation

## Testing Strategy

### Unit Testing
- Test core game logic functions
- Test API endpoints
- Test database integrations

### Integration Testing
- Test complete game flows
- Test user session management
- Test leaderboard functionality

### User Acceptance Testing
- Test on multiple devices and browsers
- Verify responsive design
- Validate game experience against Telegram version

## Future Expansion Options

### Additional Features
- Achievement system for players
- Social sharing functionality
- Daily challenges and streaks
- Custom game modes
- Multiplayer/competitive mode

### Advanced Wallet Integration
- NFT rewards for achievements
- Token-gated special game modes
- On-chain leaderboard for certain competitions

## Conclusion

This implementation plan provides a roadmap for developing the web interface for the country guessing game. By following this phased approach, we can create a modular, maintainable web application that leverages the existing game logic while providing a new way for users to interact with the game.

The plan emphasizes code reuse, proper separation of concerns, and a flexible architecture that will allow for future expansions like wallet integration.
