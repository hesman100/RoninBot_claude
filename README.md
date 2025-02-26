# Telegram Price Bot

## Stopping the Bot

### Local Development
To stop the bot in local development:
1. Use Ctrl+C in the terminal
2. Or send a GET request to `/shutdown` endpoint

### Autoscale Deployment
To stop a deployed bot:
1. Go to your Replit dashboard
2. Open the "price-bot" project
3. Click on "Deployments" tab
4. Find your active deployment
5. Use the "..." menu to select "Stop"
6. Wait a few minutes for the deployment to fully terminate

Note: The app URL may continue to respond briefly due to Replit's caching, but it will eventually stop completely.

## Running the Bot
To start the bot:
```bash
python3 bot.py
```

The bot will start an HTTP server on port 5000 and begin responding to Telegram commands.
