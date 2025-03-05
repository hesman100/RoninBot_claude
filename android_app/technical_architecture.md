# Technical Architecture

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Android Application                         │
│                                                                     │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────────┐     │
│  │    View     │      │  ViewModel  │      │   Repository    │     │
│  │             │      │             │      │                 │     │
│  │ - Activities│<────>│ - Commands  │<────>│ - API Interface │     │
│  │ - Fragments │      │ - UI State  │      │ - Data Caching  │     │
│  │ - Compose UI│      │ - Validation│      │ - Error Handling│     │
│  └─────────────┘      └─────────────┘      └────────┬────────┘     │
│                                                     │              │
└─────────────────────────────────────────────────────┼──────────────┘
                                                      │
                                                      │ HTTPS
                                                      │ (Retrofit)
                                                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        Backend Mediator (Replit)                    │
│                                                                     │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────────┐     │
│  │   Flask     │      │  Command    │      │   Telegram      │     │
│  │   Server    │      │  Processor  │      │   Bot Client    │     │
│  │             │<────>│             │<────>│                 │     │
│  │ - Endpoints │      │ - Parsing   │      │ - API Interface │     │
│  │ - Auth      │      │ - Validation│      │ - Response      │     │
│  │ - Routing   │      │ - Formatting│      │   Handling      │     │
│  └─────────────┘      └─────────────┘      └────────┬────────┘     │
│                                                     │              │
└─────────────────────────────────────────────────────┼──────────────┘
                                                      │
                                                      │ HTTPS
                                                      │
                                                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       Telegram Infrastructure                        │
│                                                                     │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────────┐     │
│  │  Telegram   │      │ Your Ronin  │      │  Market Data    │     │
│  │  Bot API    │      │    Bot      │      │     APIs        │     │
│  │             │<────>│             │<────>│                 │     │
│  │ - sendMessage│      │ - Command   │      │ - CoinGecko     │     │
│  │ - getUpdates │      │   Handlers  │      │ - AlphaVantage  │     │
│  │ - callbackQuery│     │ - Game Logic│      │ - Finnhub       │     │
│  └─────────────┘      └─────────────┘      └─────────────────┘     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Android Application

#### View Layer
- **Activities**: Main activity and settings
- **Fragments**: Command-specific screens
- **Jetpack Compose UI**: Modern UI components
- **Responsible for**: User interaction, display formatting, input validation

#### ViewModel Layer
- **Command Processing**: Formats and validates user inputs
- **UI State Management**: Tracks loading, success, error states
- **User Preferences**: Manages app settings
- **Responsible for**: Business logic, state management, UI event handling

#### Repository Layer
- **API Interface**: Communicates with backend mediator
- **Local Caching**: Stores recent responses
- **Error Handling**: Manages network failures
- **Responsible for**: Data operations, network communication

### 2. Backend Mediator (Replit)

#### Flask Server
- **API Endpoints**: Receives requests from Android app
- **Authentication**: Validates API keys
- **Request Routing**: Directs to appropriate handlers
- **Responsible for**: HTTP handling, security, routing

#### Command Processor
- **Command Parsing**: Extracts command parameters
- **Validation**: Ensures valid commands
- **Formatting**: Prepares commands for Telegram
- **Responsible for**: Command processing logic

#### Telegram Bot Client
- **API Integration**: Interfaces with Telegram Bot API
- **Response Handling**: Processes bot responses
- **Webhook Management**: Handles incoming updates
- **Responsible for**: Telegram API communication

### 3. Telegram Infrastructure

#### Telegram Bot API
- **Message Sending**: Delivers commands to users
- **Update Receiving**: Gets user responses
- **Callback Handling**: Processes inline buttons
- **Responsible for**: Core Telegram functionality

#### Your Ronin Bot
- **Command Handlers**: Processes user commands
- **Game Logic**: Manages country guessing games
- **Data Formatting**: Prepares responses
- **Responsible for**: Bot-specific functionality

#### Market Data APIs
- **Price Retrieval**: Gets cryptocurrency and stock prices
- **Data Formatting**: Standardizes response format
- **Caching**: Reduces API calls
- **Responsible for**: External data gathering

## Data Flow

### Command Flow (Android to Telegram)
1. User taps a command button in the Android app
2. App formats the command and sends HTTPS request to backend
3. Backend validates the request and processes the command
4. Backend sends the command to Telegram Bot API
5. Telegram delivers the command to the bot
6. Bot processes the command and generates a response
7. Response is displayed to the user in Telegram

### Response Flow (Optional Enhancement)
1. Bot sends response to the user in Telegram
2. Backend periodically polls for new messages (or via webhook)
3. When a new response is detected, backend notifies the app
4. App displays the response in the UI

## Security Layers

1. **API Key Authentication**: Android app includes API key in requests
2. **HTTPS Encryption**: All communication uses TLS
3. **Token Security**: Telegram Bot token only exists on backend
4. **Request Validation**: Backend validates all incoming requests
5. **Parameter Sanitization**: Prevents injection attacks

## Scalability Considerations

1. **Command Queuing**: Handles high volume periods
2. **Response Caching**: Reduces duplicate API calls
3. **Rate Limiting**: Prevents API abuse
4. **Stateless Design**: Allows for horizontal scaling
5. **Modular Architecture**: Enables independent component updates

This architecture provides a secure, reliable, and scalable foundation for your Android app to interact with your Telegram bot. The separation of concerns between components allows for easier maintenance and future enhancements.
