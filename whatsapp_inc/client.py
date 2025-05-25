"""
WhatsApp Client Module
This module handles sending messages through the Twilio WhatsApp API.
"""

import time
import logging
import os
from typing import Dict, List, Optional, Union
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

from whatsapp_inc.config import (
    TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN,
    TWILIO_PHONE_NUMBER,
    MESSAGE_COOLDOWN,
    MEDIA_FOLDER
)

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class WhatsAppClient:
    """Client for sending WhatsApp messages through Twilio"""
    
    def __init__(self):
        """Initialize the WhatsApp client with Twilio credentials"""
        self.account_sid = TWILIO_ACCOUNT_SID
        self.auth_token = TWILIO_AUTH_TOKEN
        self.phone_number = TWILIO_PHONE_NUMBER
        self.client = None
        self.last_message_time = 0
        
        # Create media folder if it doesn't exist
        os.makedirs(MEDIA_FOLDER, exist_ok=True)
        
        # Try to initialize the Twilio client
        self._initialize_client()
    
    def _initialize_client(self) -> bool:
        """Initialize the Twilio client with the provided credentials
        
        Returns:
            bool: True if initialization was successful, False otherwise
        """
        if not self.account_sid or not self.auth_token or not self.phone_number:
            logger.error("Missing Twilio credentials. Cannot initialize WhatsApp client.")
            return False
        
        try:
            self.client = Client(self.account_sid, self.auth_token)
            logger.info("WhatsApp client initialized successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize WhatsApp client: {str(e)}")
            return False
    
    def _respect_rate_limit(self):
        """Ensure we don't exceed Twilio's rate limits by adding a delay if needed"""
        current_time = time.time()
        time_since_last_message = current_time - self.last_message_time
        
        if time_since_last_message < MESSAGE_COOLDOWN:
            # Wait to respect rate limit
            sleep_time = MESSAGE_COOLDOWN - time_since_last_message
            logger.debug(f"Rate limit sleep: {sleep_time} seconds")
            time.sleep(sleep_time)
        
        self.last_message_time = time.time()
    
    def send_message(self, to_number: str, message: str) -> Dict:
        """Send a text message via WhatsApp
        
        Args:
            to_number (str): The recipient's phone number with country code, e.g., '+1234567890'
            message (str): The message text to send
            
        Returns:
            Dict: Response from the Twilio API or error information
        """
        # Check if client is initialized
        if not self.client:
            if not self._initialize_client():
                return {"error": "WhatsApp client not initialized. Check your Twilio credentials."}
        
        # Ensure to_number has WhatsApp prefix
        if not to_number.startswith('whatsapp:'):
            to_number = f'whatsapp:{to_number}'
        
        # Respect rate limits
        self._respect_rate_limit()
        
        try:
            # Send the message
            if self.client:
                response = self.client.messages.create(
                    from_=self.phone_number,
                    body=message,
                    to=to_number
                )
            else:
                return {"error": "WhatsApp client not initialized"}
            
            logger.info(f"Message sent to {to_number}, SID: {response.sid}")
            return {
                "success": True,
                "sid": response.sid,
                "status": response.status
            }
            
        except TwilioRestException as e:
            logger.error(f"Twilio API error: {str(e)}")
            return {
                "error": str(e),
                "code": e.code,
                "status": e.status
            }
        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {str(e)}")
            return {"error": str(e)}
    
    def send_media(self, to_number: str, media_url: str, caption: Optional[str] = None) -> Dict:
        """Send a media message via WhatsApp
        
        Args:
            to_number (str): The recipient's phone number with country code
            media_url (str): URL of the media to send
            caption (str, optional): Caption for the media
            
        Returns:
            Dict: Response from the Twilio API or error information
        """
        # Check if client is initialized
        if not self.client:
            if not self._initialize_client():
                return {"error": "WhatsApp client not initialized. Check your Twilio credentials."}
        
        # Ensure to_number has WhatsApp prefix
        if not to_number.startswith('whatsapp:'):
            to_number = f'whatsapp:{to_number}'
        
        # Respect rate limits
        self._respect_rate_limit()
        
        try:
            # Send the media message
            if self.client:
                response = self.client.messages.create(
                    from_=self.phone_number,
                    media_url=[media_url],
                    body=caption,
                    to=to_number
                )
            else:
                return {"error": "WhatsApp client not initialized"}
            
            logger.info(f"Media message sent to {to_number}, SID: {response.sid}")
            return {
                "success": True,
                "sid": response.sid,
                "status": response.status
            }
            
        except TwilioRestException as e:
            logger.error(f"Twilio API error: {str(e)}")
            return {
                "error": str(e),
                "code": e.code,
                "status": e.status
            }
        except Exception as e:
            logger.error(f"Error sending WhatsApp media: {str(e)}")
            return {"error": str(e)}