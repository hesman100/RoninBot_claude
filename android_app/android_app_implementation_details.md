# Android App for Telegram Bot - Technical Implementation Details

## 1. API Design for Mediator Server

### Endpoints

```
POST /api/send-command
Request:
{
  "command": "/c BTC",
  "chat_id": "user_telegram_id",
  "api_key": "your_secret_api_key"
}

Response:
{
  "success": true,
  "message_sent": true,
  "response_preview": "BTC price: $50,000 (+2.5%)"
}
```

### Flask Server Implementation

```python
from flask import Flask, request, jsonify
import requests
import os
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
API_KEY = os.environ.get('API_KEY')  # For authenticating app requests
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

@app.route('/api/send-command', methods=['POST'])
def send_command():
    # Validate API key
    if request.json.get('api_key') != API_KEY:
        return jsonify({"success": False, "error": "Invalid API key"}), 401
    
    # Extract command and chat ID
    command = request.json.get('command')
    chat_id = request.json.get('chat_id')
    
    if not command or not chat_id:
        return jsonify({"success": False, "error": "Missing command or chat_id"}), 400
    
    try:
        # Send command to Telegram Bot API
        response = requests.post(
            TELEGRAM_API_URL,
            json={
                "chat_id": chat_id,
                "text": command
            }
        )
        
        response.raise_for_status()
        result = response.json()
        
        return jsonify({
            "success": True,
            "message_sent": result.get("ok", False),
            "response_preview": f"Command {command} sent to Telegram"
        })
        
    except Exception as e:
        logger.error(f"Error sending command to Telegram: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
```

## 2. Android App Implementation

### API Interface (Retrofit)

```kotlin
interface BotCommandService {
    @POST("/api/send-command")
    suspend fun sendCommand(@Body commandRequest: CommandRequest): Response<CommandResponse>
}

data class CommandRequest(
    val command: String,
    val chat_id: String,
    val api_key: String
)

data class CommandResponse(
    val success: Boolean,
    val message_sent: Boolean,
    val response_preview: String?,
    val error: String?
)
```

### ViewModel

```kotlin
class MainViewModel(private val repository: BotRepository) : ViewModel() {
    private val _uiState = MutableStateFlow<UiState>(UiState.Idle)
    val uiState: StateFlow<UiState> = _uiState

    fun sendCommand(command: String) {
        viewModelScope.launch {
            _uiState.value = UiState.Loading
            
            try {
                val result = repository.sendCommand(command)
                if (result.success && result.message_sent) {
                    _uiState.value = UiState.Success(result.response_preview ?: "Command sent successfully")
                } else {
                    _uiState.value = UiState.Error(result.error ?: "Unknown error")
                }
            } catch (e: Exception) {
                _uiState.value = UiState.Error(e.message ?: "Network error")
            }
        }
    }
}

sealed class UiState {
    object Idle : UiState()
    object Loading : UiState()
    data class Success(val message: String) : UiState()
    data class Error(val message: String) : UiState()
}
```

### Repository

```kotlin
class BotRepository(private val apiService: BotCommandService) {
    private val apiKey = BuildConfig.API_KEY
    private val chatId = UserPreferences.getTelegramChatId()
    
    suspend fun sendCommand(commandText: String): CommandResponse {
        val request = CommandRequest(commandText, chatId, apiKey)
        val response = apiService.sendCommand(request)
        
        if (response.isSuccessful) {
            return response.body() ?: CommandResponse(false, false, null, "Empty response")
        } else {
            throw IOException("API call failed with code: ${response.code()}")
        }
    }
}
```

### Main Activity UI (Jetpack Compose)

```kotlin
@Composable
fun MainScreen(viewModel: MainViewModel) {
    val uiState by viewModel.uiState.collectAsState()
    
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp)
    ) {
        Text(
            text = "Ronin Bot Commander",
            style = MaterialTheme.typography.h5,
            modifier = Modifier.padding(bottom = 16.dp)
        )
        
        // Command buttons grid
        CommandButtonsGrid(onCommandClick = { command ->
            viewModel.sendCommand(command)
        })
        
        Spacer(modifier = Modifier.height(16.dp))
        
        // Response area
        ResponseArea(uiState = uiState)
    }
}

@Composable
fun CommandButtonsGrid(onCommandClick: (String) -> Unit) {
    val commands = listOf(
        CommandButton("/c", "Crypto", Icons.Filled.AttachMoney),
        CommandButton("/s", "Stocks", Icons.Filled.TrendingUp),
        CommandButton("/vn", "VN Stocks", Icons.Filled.Public),
        CommandButton("/g map", "Map Game", Icons.Filled.Map),
        CommandButton("/g cap", "Capital Game", Icons.Filled.LocationCity),
        CommandButton("/g flag", "Flag Game", Icons.Filled.Flag),
        CommandButton("/g lb", "Leaderboard", Icons.Filled.EmojiEvents)
    )
    
    LazyVerticalGrid(
        columns = GridCells.Fixed(3),
        contentPadding = PaddingValues(4.dp)
    ) {
        items(commands) { command ->
            CommandButton(
                command = command,
                onClick = { onCommandClick(command.command) }
            )
        }
    }
}

@Composable
fun CommandButton(
    command: CommandButton,
    onClick: () -> Unit
) {
    Button(
        onClick = onClick,
        modifier = Modifier
            .padding(4.dp)
            .fillMaxWidth()
            .aspectRatio(1f)
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Icon(
                imageVector = command.icon,
                contentDescription = command.label,
                modifier = Modifier.size(24.dp)
            )
            Spacer(modifier = Modifier.height(4.dp))
            Text(text = command.label)
        }
    }
}

@Composable
fun ResponseArea(uiState: UiState) {
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .height(120.dp)
            .border(1.dp, Color.LightGray, RoundedCornerShape(8.dp))
            .padding(8.dp)
    ) {
        when (uiState) {
            is UiState.Idle -> Text("Ready to send commands")
            is UiState.Loading -> CircularProgressIndicator(
                modifier = Modifier.align(Alignment.Center)
            )
            is UiState.Success -> Text(uiState.message)
            is UiState.Error -> Text(
                text = "Error: ${uiState.message}",
                color = Color.Red
            )
        }
    }
}

data class CommandButton(
    val command: String,
    val label: String,
    val icon: ImageVector
)
```

## 3. Sequence Diagram for Command Flow

```
┌─────────┐          ┌──────────┐          ┌──────────┐          ┌─────────────┐
│ Android │          │ Backend  │          │ Telegram │          │  Telegram   │
│   App   │          │ Mediator │          │ Bot API  │          │  Bot Logic  │
└────┬────┘          └────┬─────┘          └────┬─────┘          └──────┬──────┘
     │                     │                     │                       │
     │  Send Command       │                     │                       │
     │  (/c BTC)           │                     │                       │
     │─────────────────────>                     │                       │
     │                     │                     │                       │
     │                     │  Forward Command    │                       │
     │                     │  to Telegram API    │                       │
     │                     │────────────────────>│                       │
     │                     │                     │                       │
     │                     │                     │  Process Command      │
     │                     │                     │─────────────────────>│
     │                     │                     │                       │
     │                     │                     │  Command Response     │
     │                     │                     │<─────────────────────│
     │                     │                     │                       │
     │                     │  HTTP Response      │                       │
     │                     │  (Message Sent)     │                       │
     │                     │<────────────────────│                       │
     │                     │                     │                       │
     │  Response           │                     │                       │
     │  (Success)          │                     │                       │
     │<─────────────────────                     │                       │
     │                     │                     │                       │
     │                     │                     │                       │
```

## 4. User Authentication Flow

One important aspect is how users will authenticate their Telegram account with the Android app:

1. **Option 1: Manual Chat ID Entry**
   - User finds their Telegram chat ID (by messaging @userinfobot)
   - User enters this ID in the app settings
   - Simple but requires manual effort from users

2. **Option 2: Deep Linking with Bot**
   - App generates a unique token
   - User clicks a button in app that opens Telegram and sends a special command to your bot
   - Bot receives command with token and returns the chat ID
   - App polls backend to retrieve the linked chat ID
   - More seamless but requires additional backend logic

3. **Option 3: Telegram Login Widget**
   - Implement Telegram Login for Android
   - User authenticates with Telegram account directly
   - Most user-friendly, but more complex to implement

For initial implementation, Option 1 provides the quickest path to a functional app, with the other options as potential enhancements.

## 5. Testing Strategy

1. **Unit Testing**
   - Test repository and ViewModel logic
   - Mock API responses for different scenarios

2. **Integration Testing**
   - Test communication between app and backend
   - Ensure proper error handling

3. **End-to-End Testing**
   - Test full command flow from app to Telegram and back
   - Verify all features work as expected

## 6. Security Implementation

1. **API Key Storage**
   - Store API key in BuildConfig (not in source code)
   - For production, use Android Keystore for secure storage

2. **Secure Communication**
   - Implement certificate pinning for HTTPS connections
   - Add request signing for additional security

3. **User Data Protection**
   - Minimize data collection
   - Store user preferences using EncryptedSharedPreferences

## 7. Deployment Process

1. **Backend Deployment**
   - Deploy Flask app on Replit
   - Set up environment variables for API keys and tokens
   - Configure automatic restarts and monitoring

2. **App Distribution**
   - Generate signed APK/Bundle
   - Distribute via Google Play Store or alternative methods
   - Set up crash reporting and analytics
