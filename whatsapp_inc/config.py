"""
WhatsApp Integration Configuration
This module contains configuration settings for the WhatsApp integration using Twilio.
"""

import os
import logging

# Twilio Credentials - These should be set as environment variables
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER")  # This should include the WhatsApp prefix, e.g. 'whatsapp:+1234567890'

# API Rate Limiting
MAX_MESSAGES_PER_SECOND = 1  # Twilio has rate limits that must be respected
MESSAGE_COOLDOWN = 1  # 1 second between messages to avoid rate limiting

# Webhook Configuration
WEBHOOK_URL = os.environ.get("WHATSAPP_WEBHOOK_URL", "")  # URL where Twilio will send incoming messages

# Flask Server Configuration
FLASK_HOST = "0.0.0.0"  # Use 0.0.0.0 to make the server publicly accessible
FLASK_PORT = 5001  # Different port than the main app to avoid conflicts

# Logging Configuration
LOG_LEVEL = logging.INFO
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_FILE = "whatsapp_bot.log"

# Command Prefixes
COMMAND_PREFIX = "/"  # Commands start with '/' like '/help', '/stock', etc.

# Default response messages
WELCOME_MESSAGE = "👋 Welcome to XBot WhatsApp! Here are available commands:\n" \
                 "/help - Show this help message\n" \
                 "/s [symbol] - Get stock price (e.g., /s AAPL)\n" \
                 "/c [symbol] - Get cryptocurrency price (e.g., /c BTC)\n" \
                 "/vn [symbol] - Get Vietnam stock price (e.g., /vn VNM)\n" \
                 "/g map - Play country guessing game with maps\n" \
                 "/g flag - Play country guessing game with flags\n" \
                 "/g cap - Play country guessing game with capitals"

HELP_MESSAGE = WELCOME_MESSAGE

ERROR_MESSAGE = "Sorry, I couldn't process your request. Please try again or type /help for assistance."

# Media handling
MEDIA_FOLDER = "whatsapp_inc/media"
MAX_MEDIA_SIZE_MB = 5  # Maximum size for media files in MB