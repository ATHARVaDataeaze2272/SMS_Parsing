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
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import pathlib

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

# Path to frontend build directory
frontend_path = pathlib.Path(__file__).parent / "frontend/"

# Include API routes FIRST (before mounting static files)
app.include_router(api_router, prefix="/api")

# Check if frontend directory exists
if frontend_path.exists() and (frontend_path / "index.html").exists():
    logger.info(f"Frontend directory found at: {frontend_path}")
    
    # Mount static assets (CSS, JS, images, etc.)
    assets_path = frontend_path / "assets"
    if assets_path.exists():
        app.mount("/assets", StaticFiles(directory=assets_path), name="assets")
    
    # Serve static files (but not as catch-all)
    @app.get("/")
    async def serve_root():
        return FileResponse(frontend_path / "index.html")
    
    # Catch-all route for SPA routing (but exclude API routes)
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Don't catch API routes
        if full_path.startswith("api/"):
            return {"detail": "API endpoint not found"}
        
        # Don't catch static asset requests
        if full_path.startswith("assets/"):
            return {"detail": "Asset not found"}
        
        # Check if it's a specific file request
        file_path = frontend_path / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        
        # For all other routes, serve index.html (SPA routing)
        index_file = frontend_path / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        
        return {"detail": "Frontend build not found. Please run 'npm run build'."}
else:
    logger.warning(f"Frontend directory not found at: {frontend_path}")
    logger.warning("Please ensure your frontend build is in the correct location")

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