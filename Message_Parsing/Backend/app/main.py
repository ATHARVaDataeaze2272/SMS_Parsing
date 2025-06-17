import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.api_routes import router as api_router
from app.routes.error_handlers import http_exception_handler, general_exception_handler
from app.utils.logging_config import logger
from app.database import get_db
from fastapi.exceptions import HTTPException


# Initialize FastAPI app
app = FastAPI(title="Financial SMS Analyzer")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router)

# Register error handlers
app.exception_handler(HTTPException)(http_exception_handler)
app.exception_handler(Exception)(general_exception_handler)


@app.on_event("shutdown")
def shutdown_mongo_client():
    from app.database import mongo_client  # import the global mongo_client
    if mongo_client:
        mongo_client.close()
        logger.info("MongoDB client closed on shutdown.")



if __name__ == "__main__":
    logger.info("Starting Financial SMS Analyzer API...")

    # Test database connection on startup
    try:
        test_db = get_db()
        test_db.command('ping')
        logger.info("Database connection test successful")
        # ✅ DO NOT CLOSE THE CLIENT HERE
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True,
        reload=True,
    )
