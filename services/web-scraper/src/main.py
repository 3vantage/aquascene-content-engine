"""
Web Scraper Service - Main FastAPI Application
Handles web scraping for aquascaping content and research
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import sys
from typing import Dict, Any

from .config.settings import get_settings
from .api import scraper_routes, health_routes
from .database.connection import init_database
from .scrapers.content_scraper import ContentScraper


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting Web Scraper Service...")
    
    # Initialize database
    try:
        await init_database()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    # Initialize scraper
    app.state.scraper = ContentScraper()
    logger.info("Content scraper initialized")
    
    yield
    
    # Cleanup
    logger.info("Shutting down Web Scraper Service...")


# Create FastAPI application
app = FastAPI(
    title="AquaScene Web Scraper Service",
    description="Web scraping service for aquascaping content and research",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_routes.router, prefix="/health", tags=["health"])
app.include_router(scraper_routes.router, prefix="/api/v1", tags=["scraper"])


@app.get("/")
async def root() -> Dict[str, Any]:
    """Root endpoint"""
    return {
        "service": "AquaScene Web Scraper Service",
        "version": "1.0.0",
        "status": "running",
        "environment": settings.ENVIRONMENT
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8002,
        reload=settings.ENVIRONMENT == "development"
    )