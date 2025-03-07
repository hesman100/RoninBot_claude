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

def prepare_image_response(image_path: str, width: int = 320) -> Dict[str, Any]:
    """
    Prepare an image response for API requests
    
    Args:
        image_path (str): Path to the image file
        width (int): Width to resize the image to (default: 320px)
        
    Returns:
        Dict: Dictionary with image data and metadata
    """
    try:
        # Get file extension
        file_extension = image_path.split(".")[-1].lower()
        mime_type = f"image/{file_extension}"
        if file_extension == "jpg":
            mime_type = "image/jpeg"
        
        # Resize the image while maintaining aspect ratio
        try:
            with Image.open(image_path) as img:
                # Get original dimensions for logging
                original_width, original_height = img.size
                logger.info(f"Original image dimensions: {original_width}x{original_height}")
                
                # Calculate new height to maintain aspect ratio
                w_percent = width / float(original_width)
                height = int(float(original_height) * float(w_percent))
                
                # Resize the image
                resized_img = img.resize((width, height), Image.LANCZOS)
                
                # Log the resized dimensions
                logger.info(f"Resized image dimensions: {width}x{height}")
                
                # Save to a bytes buffer
                buffer = io.BytesIO()
                if image_path.lower().endswith('.png'):
                    resized_img.save(buffer, format='PNG')
                else:
                    resized_img.save(buffer, format='JPEG', quality=95)
                
                buffer.seek(0)
                
                # Log buffer size
                buffer_size = buffer.getbuffer().nbytes
                logger.info(f"Resized image buffer size: {buffer_size} bytes")
                
                # Encode to base64
                encoded_image = base64.b64encode(buffer.read()).decode("utf-8")
                
                return {
                    "image_data": encoded_image,
                    "mime_type": mime_type,
                    "image_path": image_path,
                    "width": width,
                    "height": height
                }
        except Exception as resize_error:
            # If resizing fails, use the original image
            logger.warning(f"Error resizing image {image_path}: {resize_error}. Using original.")
            with open(image_path, "rb") as image_file:
                image_data = image_file.read()
                encoded_image = base64.b64encode(image_data).decode("utf-8")
                
                # Try to get the original dimensions from the file
                try:
                    with Image.open(io.BytesIO(image_data)) as img:
                        orig_width, orig_height = img.size
                        return {
                            "image_data": encoded_image,
                            "mime_type": mime_type,
                            "image_path": image_path,
                            "width": orig_width,
                            "height": orig_height,
                            "note": "Using original image (resize failed)"
                        }
                except:
                    pass
                
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