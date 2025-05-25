# WhatsApp Integration for XBot

This module provides WhatsApp messaging capabilities for the XBot, allowing users to interact with the bot through WhatsApp.

## Setup Instructions

### Prerequisites

1. A Twilio account (sign up at [twilio.com](https://www.twilio.com))
2. A Twilio phone number with WhatsApp capabilities
3. The following environment variables:
   - `TWILIO_ACCOUNT_SID`: Your Twilio Account SID
   - `TWILIO_AUTH_TOKEN`: Your Twilio Auth Token
   - `TWILIO_PHONE_NUMBER`: Your Twilio WhatsApp-enabled phone number (format: `whatsapp:+1234567890`)

### Configuration Steps

1. **Create a Twilio Account**:
   - Sign up at [twilio.com](https://www.twilio.com) and verify your email
   - Navigate to the Twilio Console to find your Account SID and Auth Token

2. **Set Up a WhatsApp Sandbox**:
   - In the Twilio Console, navigate to "Messaging" → "Try it out" → "Send a WhatsApp message"
   - Follow the instructions to connect your WhatsApp account to the Twilio Sandbox

3. **Configure Webhook URL**:
   - Set up a publicly accessible URL for your webhook (using a service like ngrok for development)
   - In the Twilio Console, go to "Messaging" → "Settings" → "WhatsApp Sandbox Settings"
   - Set the "When a message comes in" webhook URL to your public URL + `/webhook` (e.g., `https://your-domain.com/webhook`)

4. **Set Environment Variables**:
   ```bash
   export TWILIO_ACCOUNT_SID=your_account_sid
   export TWILIO_AUTH_TOKEN=your_auth_token
   export TWILIO_PHONE_NUMBER=whatsapp:+1234567890
   ```

## Running the WhatsApp Server

Run the WhatsApp webhook server with:

```bash
python run_whatsapp_server.py
```

The server will start on port 5001 by default and will be ready to receive incoming WhatsApp messages.

## Available Commands

Users can interact with the bot through the following commands:

- `/help` - Show help message with available commands
- `/s [symbol]` - Get stock price (e.g., `/s AAPL`)
- `/c [symbol]` - Get cryptocurrency price (e.g., `/c BTC`)
- `/vn [symbol]` - Get Vietnam stock price (e.g., `/vn VNM`)
- `/g map` - Play country guessing game with maps
- `/g flag` - Play country guessing game with flags
- `/g cap` - Play country guessing game with capitals

## Development Notes

### Media Handling

For the country guessing game, the bot needs to send map and flag images. In a production environment, these images need to be hosted somewhere with public URLs that Twilio can access.

### WhatsApp API Limitations

- WhatsApp messages through Twilio have rate limits
- Media messages have size restrictions (maximum 5MB)
- During development with the sandbox, only pre-registered numbers can receive messages

### Production Deployment

For production use:
1. Move beyond the WhatsApp Sandbox by completing the Twilio WhatsApp Business Profile application
2. Host the server on a reliable platform with HTTPS
3. Set up proper media hosting for game images
4. Implement additional security measures like request validation