"""
Utility functions for the XBot API
"""

import os
import uuid
import base64
import logging
import io
from typing import Dict, Any, Optional
from PIL import Image

logger = logging.getLogger(__name__)

def get_api_key() -> str:
    """
    Get the API key from environment variable or generate one
    
    Returns:
        str: The API key to use for authentication
    """
    api_key = os.environ.get("XBOT_API_KEY")
    if not api_key:
        # Generate a random API key if not set
        api_key = str(uuid.uuid4())
        logger.warning(f"Generated random API key: {api_key}")
        logger.warning("Set XBOT_API_KEY environment variable for production use")
    
    return api_key

def prepare_image_response(image_path: str) -> Dict[str, Any]:
    """
    Prepare an image response for API requests
    
    Args:
        image_path (str): Path to the image file
        
    Returns:
        Dict: Dictionary with image data and metadata
    """
    try:
        with open(image_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode("utf-8")
            
            # Get file extension
            file_extension = image_path.split(".")[-1].lower()
            mime_type = f"image/{file_extension}"
            if file_extension == "jpg":
                mime_type = "image/jpeg"
                
            return {
                "image_data": encoded_image,
                "mime_type": mime_type,
                "image_path": image_path
            }
    except Exception as e:
        logger.error(f"Error preparing image response: {e}")
        return {
            "error": f"Failed to load image: {str(e)}",
            "image_path": image_path
        }

def format_country_data(country: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format country data for API responses
    
    Args:
        country (Dict): Country data from the database
        
    Returns:
        Dict: Formatted country data
    """
    return {
        "id": country.get("id"),
        "name": country.get("name"),
        "capital": country.get("capital"),
        "region": country.get("region"),
        "population": country.get("population"),
        "area": country.get("area"),
    }