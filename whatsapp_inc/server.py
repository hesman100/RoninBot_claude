"""
WhatsApp Webhook Server
This module handles incoming webhook requests from Twilio for WhatsApp messages.
"""

import os
import logging
import threading
from flask import Flask, request, jsonify
from twilio.twiml.messaging_response import MessagingResponse

from whatsapp_inc.handler import WhatsAppMessageHandler
from whatsapp_inc.config import FLASK_HOST, FLASK_PORT

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Initialize Flask app
app = Flask(__name__)

# Initialize the message handler
message_handler = WhatsAppMessageHandler()

@app.route('/', methods=['GET'])
def home():
    """Home endpoint to verify the server is running"""
    return jsonify({
        "status": "ok",
        "message": "WhatsApp webhook server is running"
    })

@app.route('/webhook', methods=['POST'])
def webhook():
    """Webhook endpoint to receive WhatsApp messages from Twilio"""
    try:
        # Get the incoming message details from Twilio's request
        from_number = request.values.get('From', '')
        body = request.values.get('Body', '')
        media_url = request.values.get('MediaUrl0', None)
        
        logger.info(f"Received message from {from_number}: {body[:50]}...")
        
        # Create a TwiML response
        resp = MessagingResponse()
        
        # Process the message in a separate thread to avoid blocking
        threading.Thread(
            target=process_message_async,
            args=(from_number, body, media_url)
        ).start()
        
        # Return an empty response - we'll send messages asynchronously
        return str(resp)
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        # Return a simple response to acknowledge receipt
        resp = MessagingResponse()
        return str(resp)

def process_message_async(from_number, body, media_url=None):
    """Process a message asynchronously
    
    Args:
        from_number (str): Sender's phone number
        body (str): Message text
        media_url (str, optional): URL of attached media
    """
    try:
        # Process the message using the message handler
        message_handler.process_message(from_number, body, media_url)
        logger.info(f"Message from {from_number} processed successfully")
    except Exception as e:
        logger.error(f"Error in async message processing: {str(e)}")

def run_server():
    """Run the Flask server"""
    logger.info(f"Starting WhatsApp webhook server on {FLASK_HOST}:{FLASK_PORT}")
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=False, threaded=True)

if __name__ == '__main__':
    run_server()