# Deployment Configuration Guide

## The Issue
The API server is not running in the deployed environment. Currently, only the Telegram bot is running because the `.replit` file is configured to only run `bot.py` on deployment:

```
[deployment]
run = ["sh", "-c", "python3 bot.py"]
```

## The Solution: Option 1 (Recommended)
Edit the `.replit` file to run both the API server and the Telegram bot simultaneously:

1. Go to the Replit editor for your project
2. Navigate to the `.replit` file and click to edit it
3. Find this section:
   ```
   [deployment]
   run = ["sh", "-c", "python3 bot.py"]
   deploymentTarget = "cloudrun"
   ```
4. Change it to:
   ```
   [deployment]
   run = ["sh", "-c", "python3 run_all.py"]
   deploymentTarget = "cloudrun"
   ```
5. Save the file
6. Deploy the project again

## The Solution: Option 2 (Alternative)
If you can't edit the `.replit` file directly through the Replit interface, you can modify the `bot.py` file to also start the API server:

1. Edit the `bot.py` file
2. Add code at the beginning of the `main()` function to start the API server in a separate thread:

```python
def main() -> None:
    """Start the bot with error handling and health checks."""
    try:
        # Start API server in a background thread
        import threading
        from xbot_api.server import main as start_api_server
        
        api_thread = threading.Thread(target=start_api_server, daemon=True)
        api_thread.start()
        logger.info("API server thread started")
        
        # Rest of the existing code...
```

3. Save the file
4. Deploy the project again

## Verifying the Solution
After deploying with either option, you can verify that both the bot and API server are running by checking:

1. The bot should respond to Telegram commands as usual
2. The API server should be accessible at: `https://ronin-bot-hesman.replit.app/api/health`

## API Client Configuration
When connecting from other projects, make sure to use the correct URL and API key:

```javascript
// Example JavaScript client
const API_BASE_URL = "https://ronin-bot-hesman.replit.app/api";
const API_KEY = "xbot-default-api-key-9876543210";

// Example fetch request
fetch(`${API_BASE_URL}/health`, {
  headers: {
    'X-API-Key': API_KEY
  }
})
.then(response => response.json())
.then(data => console.log(data));
```

```python
# Example Python client
import requests

API_BASE_URL = "https://ronin-bot-hesman.replit.app/api"
API_KEY = "xbot-default-api-key-9876543210"

response = requests.get(
    f"{API_BASE_URL}/health",
    headers={"X-API-Key": API_KEY}
)
print(response.json())
```

## Port Configuration
The deployed environment is already configured with the correct port mappings:

- Port 5000: Used by the Telegram bot's health check server (mapped to external port 80)
- Port 5001: Used by the API server (mapped to external port 3000)

In the URL, you do not need to specify the port as Replit's routing system handles this automatically.