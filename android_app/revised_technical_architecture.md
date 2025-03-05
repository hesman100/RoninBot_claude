# Revised Technical Architecture: Direct Bot Connection Android App

## Overview

This revised architecture outlines a standalone Android application that connects directly to the bot's backend server, bypassing Telegram entirely. The app will focus exclusively on the country guessing game features, making it appropriate for children.

## System Components

```
┌─────────────────────┐       ┌────────────────────┐       ┌────────────────────┐
│                     │       │                    │       │                    │
│  Android App        │◄─────►│  Backend API       │◄─────►│  Game Database     │
│  (Country Game UI)  │       │  (Game Logic)      │       │  (Countries)       │
│                     │       │                    │       │                    │
└─────────────────────┘       └────────────────────┘       └────────────────────┘
```

### 1. Android Application
- **Target Users**: Children
- **Features**: Country guessing games only (map, flag, capital, leaderboard)
- **UI**: Kid-friendly design with visual elements and intuitive navigation
- **Technology**: Kotlin/Java, Android SDK, Retrofit for API calls

### 2. Backend API Service
- **Purpose**: Adapt existing bot's game functionality to direct REST API endpoints
- **Functions**:
  - Start new games (map/flag/capital modes)
  - Process answers and provide feedback
  - Track scores and maintain leaderboard
  - Serve country images (maps and flags)
- **Technology**: Extend current Python bot with Flask/FastAPI endpoints

### 3. Game Database
- **Content**: Countries database (already implemented)
- **Usage**: Same database used by the Telegram bot

## Communication Flow

1. **Game Initiation**:
   ```
   App → Backend API: GET /game/start?mode=map
   Backend → App: {game_id, country_image, options}
   ```

2. **Answer Submission**:
   ```
   App → Backend API: POST /game/answer
   {game_id, selected_option}
   Backend → App: {result, correct_answer, country_details}
   ```

3. **Leaderboard Request**:
   ```
   App → Backend API: GET /leaderboard
   Backend → App: {leaderboard_data}
   ```

## Authentication & Security

- Implement a lightweight API key system for authenticating app requests
- Use HTTPS for all communications
- No personal user data required (optional usernames for leaderboard)

## Data Persistence

- Game progress stored locally on the device
- Scores synchronized with server for leaderboard functionality
- No need for complex user account management

## Offline Capabilities

- Cache country images locally for offline play
- Store basic game logic to enable limited offline functionality
- Sync scores when connection is restored
