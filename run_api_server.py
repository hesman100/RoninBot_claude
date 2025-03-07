"""
Run the XBot API server
"""

import os
import logging
from xbot_api.utils import get_api_key
from xbot_api.api import app

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger('xbot_api')
    
    # Get API key
    api_key = get_api_key()
    os.environ["XBOT_API_KEY"] = api_key
    
    logger.info(f"Starting XBot API server with API key: {api_key}")
    
    # Get port from environment or use default
    port = int(os.environ.get("API_PORT", 5001))
    
    # Start the server
    logger.info(f"Server running on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True)