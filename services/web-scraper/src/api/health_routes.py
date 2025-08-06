"""
Health check routes for the Web Scraper Service
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import asyncio
import aioredis
import asyncpg
import httpx
from datetime import datetime

from ..config.settings import get_settings

router = APIRouter()
settings = get_settings()


@router.get("")
async def health_check() -> Dict[str, Any]:
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "service": "web-scraper",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


@router.get("/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """Detailed health check with dependency status"""
    health_status = {
        "status": "healthy",
        "service": "web-scraper",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "checks": {}
    }
    
    # Check database connection
    try:
        conn = await asyncpg.connect(settings.DATABASE_URL)
        await conn.execute("SELECT 1")
        await conn.close()
        health_status["checks"]["database"] = {"status": "healthy"}
    except Exception as e:
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "unhealthy"
    
    # Check Redis connection
    try:
        redis = aioredis.from_url(settings.REDIS_URL)
        await redis.ping()
        await redis.close()
        health_status["checks"]["redis"] = {"status": "healthy"}
    except Exception as e:
        health_status["checks"]["redis"] = {
            "status": "unhealthy", 
            "error": str(e)
        }
        health_status["status"] = "unhealthy"
    
    # Check external connectivity
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("https://httpbin.org/status/200", timeout=5)
            if response.status_code == 200:
                health_status["checks"]["external_connectivity"] = {"status": "healthy"}
            else:
                health_status["checks"]["external_connectivity"] = {
                    "status": "unhealthy",
                    "error": f"HTTP {response.status_code}"
                }
                health_status["status"] = "unhealthy"
    except Exception as e:
        health_status["checks"]["external_connectivity"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "unhealthy"
    
    if health_status["status"] == "unhealthy":
        raise HTTPException(status_code=503, detail=health_status)
    
    return health_status


@router.get("/ready")
async def readiness_check() -> Dict[str, Any]:
    """Readiness check endpoint"""
    return {
        "status": "ready",
        "service": "web-scraper",
        "timestamp": datetime.utcnow().isoformat()
    }