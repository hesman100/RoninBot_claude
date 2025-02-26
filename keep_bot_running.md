# How to Keep Your Telegram Bot Running (Free Method)

## Using UptimeRobot (Free Service)

1. First, create a free account at [UptimeRobot](https://uptimerobot.com/)

2. After logging in:
   - Click "Add New Monitor"
   - Select "HTTP(s)" as the monitor type
   - Enter a name for your monitor (e.g., "Telegram Bot")
   - Enter your Replit URL: `https://[your-repl-name].[your-username].repl.co`
   - Set monitoring interval to 5 minutes
   - Click "Create Monitor"

3. UptimeRobot will now ping your bot every 5 minutes, keeping it active

## How It Works:
- The bot runs an HTTP server on port 5000
- UptimeRobot regularly pings your bot
- These regular pings prevent Replit from putting your bot to sleep
- The health check endpoint (`/health`) confirms the bot is running properly

## Tips:
- Keep your Replit tab open when coding/testing
- Check UptimeRobot dashboard to monitor uptime
- The bot will automatically restart if it crashes

Need help setting this up? Just ask!
