"""
Utility functions for the XBot API
"""

import os
import logging
from typing import Dict, List, Optional, Any, Union

logger = logging.getLogger('xbot_api.utils')

def get_api_key() -> str:
    """Get the API key from environment variable or generate one"""
    api_key = os.environ.get("XBOT_API_KEY")
    if not api_key:
        # Generate a random key for development
        import uuid
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
    if not os.path.exists(image_path):
        return {"error": f"Image not found: {image_path}"}
    
    import base64
    
    # Get image file extension
    _, ext = os.path.splitext(image_path)
    mime_type = {
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.svg': 'image/svg+xml'
    }.get(ext.lower(), 'application/octet-stream')
    
    # Read and encode the image
    try:
        with open(image_path, 'rb') as img_file:
            encoded_img = base64.b64encode(img_file.read()).decode('utf-8')
            
        return {
            "image_data": encoded_img,
            "mime_type": mime_type,
            "filename": os.path.basename(image_path)
        }
    except Exception as e:
        logger.error(f"Error preparing image response: {e}")
        return {"error": f"Error processing image: {str(e)}"}

def format_country_data(country: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format country data for API responses
    
    Args:
        country (Dict): Country data from the database
        
    Returns:
        Dict: Formatted country data
    """
    # Format population
    population = country.get("population", 0)
    if population >= 1000000000:
        formatted_population = f"{population/1000000000:.2f} billion"
    elif population >= 1000000:
        formatted_population = f"{population/1000000:.2f} million"
    elif population >= 1000:
        formatted_population = f"{population/1000:.1f} thousand"
    else:
        formatted_population = str(population)
    
    # Format area
    area = country.get("area", 0)
    formatted_area = f"{area:,.0f} km²" if area else "Unknown"
    
    return {
        "id": country.get("id"),
        "name": country.get("name", "Unknown"),
        "capital": country.get("capital", "Unknown"),
        "region": country.get("region", "Unknown"),
        "population": population,
        "area": area,
        "formatted_population": formatted_population,
        "formatted_area": formatted_area,
        "neighbors": country.get("neighbors", []),
        "neighbor_capitals": country.get("neighbor_capitals", [])
    }