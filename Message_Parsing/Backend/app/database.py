from pymongo import MongoClient
import certifi
from app.utils.logging_config import logger
from app.config import MONGODB_URL

mongo_client = None

def get_mongo_client():
    global mongo_client
    try:
        if mongo_client is not None:
            # Check if it's still alive (will raise if closed)
            mongo_client.admin.command('ping')
            return mongo_client
    except Exception as e:
        logger.warning(f"Reinitializing MongoClient due to: {e}")

    try:
        if "mongodb+srv" in MONGODB_URL:
            mongo_client = MongoClient(
                MONGODB_URL,
                tls=True,
                tlsCAFile=certifi.where(),
                serverSelectionTimeoutMS=10000,
                connectTimeoutMS=10000,
                socketTimeoutMS=10000
            )
        else:
            mongo_client = MongoClient(
                MONGODB_URL,
                serverSelectionTimeoutMS=10000,
                connectTimeoutMS=10000,
                socketTimeoutMS=10000
            )

        # Test connection
        mongo_client.admin.command('ping')
        logger.info("MongoDB connection established successfully.")
        return mongo_client

    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {str(e)}")
        raise

def get_db():
    return get_mongo_client()["financial_sms_db"]
