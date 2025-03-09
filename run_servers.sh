#!/bin/bash

# Start the API server in the background
echo "Starting API server..."
python run_api_server.py &
API_PID=$!

# Give it a moment to start
sleep 2
echo "API server started with PID: $API_PID"

# Start the Telegram bot in the foreground
echo "Starting Telegram bot..."
python bot.py

# If the bot exits, also kill the API server
kill $API_PID