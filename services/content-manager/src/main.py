"""
Content Manager API Service
Main FastAPI application for content management.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app
import structlog

from .config.settings import get_settings
from .database.connection import db_manager
from .api.content_routes import router as content_router
from .api.newsletter_routes import router as newsletter_router
from .api.subscriber_routes import router as subscriber_router
from .api.workflow_routes import router as workflow_router


# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    logger.info("Starting Content Manager API service")
    
    try:
        # Initialize database connections
        if settings.database_url:
            # Test database connection
            async with db_manager.async_session_factory() as session:
                logger.info("Database connection established")
        else:
            logger.warning("DATABASE_URL not configured - database features will be limited")
        
        logger.info("Content Manager API service started successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize Content Manager: {e}")
        raise
    
    yield
    
    logger.info("Shutting down Content Manager API service")
    
    # Cleanup connections
    try:
        await db_manager.close()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Create FastAPI application
app = FastAPI(
    title="AquaScene Content Manager API",
    description="Content management and orchestration service for AquaScene",
    version="1.0.0",
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Prometheus metrics
if settings.enable_metrics:
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

# Include API routes
app.include_router(content_router)
app.include_router(newsletter_router)
app.include_router(subscriber_router)
app.include_router(workflow_router)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        if settings.database_url:
            async with db_manager.async_session_factory() as session:
                # Simple query to test connection
                pass
            db_status = "connected"
        else:
            db_status = "not_configured"
        
        return {
            "status": "healthy",
            "service": "content-manager",
            "environment": settings.environment,
            "database": db_status,
            "features": {
                "content_management": True,
                "newsletter_management": True,
                "subscriber_management": True,
                "workflow_automation": True,
                "metrics": settings.enable_metrics
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "content-manager", 
            "error": str(e)
        }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AquaScene Content Manager API",
        "description": "Central hub for content lifecycle management",
        "version": "1.0.0",
        "docs": "/docs" if settings.environment != "production" else "disabled",
        "endpoints": {
            "content": "/api/v1/content",
            "newsletters": "/api/v1/newsletters", 
            "subscribers": "/api/v1/subscribers",
            "workflows": "/api/v1/workflows",
            "health": "/health"
        }
    }


@app.get("/api/v1/status")
async def service_status():
    """Get detailed service status and statistics"""
    try:
        from .services.workflow_orchestrator import workflow_orchestrator
        from .database.session import get_async_session
        
        async with get_async_session() as session:
            workflow_status = await workflow_orchestrator.get_workflow_status(session)
            
        return {
            "service": "content-manager",
            "status": "operational",
            "workflow_status": workflow_status,
            "environment": settings.environment
        }
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return {
            "service": "content-manager",
            "status": "degraded",
            "error": str(e)
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.environment == "development"
    )