import os
from dotenv import load_dotenv
from app.utils.logging_config import logger

# Load environment variables
load_dotenv()
# logger.debug(f"Loaded MONGODB_URL: {os.getenv('MONGODB_URL')}")

# Environment variables
MONGODB_URL = os.getenv("MONGODB_URL")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("API_KEY")

# Validate environment variables
if not MONGODB_URL:
    logger.error("MONGODB_URL environment variable not set")
    raise ValueError("MONGODB_URL environment variable not set")

if not GOOGLE_API_KEY:
    logger.error("GOOGLE_API_KEY environment variable not set")
    raise ValueError("GOOGLE_API_KEY environment variable not set")