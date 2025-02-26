# Telegram Price Bot

## Completely Stopping the Bot

### 1. Stop Local Development
To stop the bot in local development:
1. Use Ctrl+C in the terminal
2. Or send a GET request to `/shutdown` endpoint

### 2. Stop Autoscale Deployment
To stop a deployed bot:
1. Go to your Replit dashboard
2. Open the "price-bot" project
3. Click on "Deployments" tab
4. Find your active deployment
5. Use the "..." menu to select "Stop"
6. Wait a few minutes for the deployment to fully terminate

### 3. Remove Telegram Webhook (Important!)
If the bot is still responding after stopping deployments:
1. Open your browser
2. Visit this URL (replace with your bot token):
   ```
   https://api.telegram.org/bot<YOUR_BOT_TOKEN>/deleteWebhook
   ```
3. You should see: `{"ok":true,"result":true,"description":"Webhook was deleted"}`

### 4. Last Resort: Revoke Bot Token
If the bot still responds after all above steps:
1. Go to @BotFather in Telegram
2. Send `/revoke` command
3. Select your bot
4. Confirm revocation
5. Get a new token using `/token` when ready to restart

Note: The app URL may continue to respond briefly due to Replit's caching, but it will eventually stop completely.

## Running the Bot
To start the bot:
```bash
python3 bot.py
```

The bot will start an HTTP server on port 5000 and begin responding to Telegram commands.