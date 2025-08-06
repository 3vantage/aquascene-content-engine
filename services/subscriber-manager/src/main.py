"""
Subscriber Manager Service - Main FastAPI Application
Handles subscriber management, authentication, and email services
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import sys
from typing import Dict, Any

from .config.settings import get_settings
from .api import subscriber_routes, auth_routes, health_routes
from .database.connection import init_database
from .services.email_service import EmailService


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
    logger.info("Starting Subscriber Manager Service...")
    
    # Initialize database
    try:
        await init_database()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    # Initialize email service
    app.state.email_service = EmailService()
    logger.info("Email service initialized")
    
    yield
    
    # Cleanup
    logger.info("Shutting down Subscriber Manager Service...")


# Create FastAPI application
app = FastAPI(
    title="AquaScene Subscriber Manager Service",
    description="Subscriber management, authentication, and email services",
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
app.include_router(auth_routes.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(subscriber_routes.router, prefix="/api/v1/subscribers", tags=["subscribers"])


@app.get("/")
async def root() -> Dict[str, Any]:
    """Root endpoint"""
    return {
        "service": "AquaScene Subscriber Manager Service",
        "version": "1.0.0",
        "status": "running",
        "environment": settings.ENVIRONMENT
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8004,
        reload=settings.ENVIRONMENT == "development"
    )