"""
Scraper API routes for the Web Scraper Service
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from pydantic import BaseModel, HttpUrl
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from ..scrapers.content_scraper import ContentScraper
from ..config.settings import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()


class ScrapeRequest(BaseModel):
    """Request model for scraping operations"""
    url: HttpUrl
    content_type: str = "article"
    tags: Optional[List[str]] = None
    priority: int = 1


class ScrapeResponse(BaseModel):
    """Response model for scraping operations"""
    job_id: str
    status: str
    url: str
    submitted_at: datetime


class ScrapeResult(BaseModel):
    """Model for scrape results"""
    job_id: str
    url: str
    status: str
    content: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    scraped_at: Optional[datetime] = None


@router.post("/scrape", response_model=ScrapeResponse)
async def submit_scrape_job(
    request: ScrapeRequest,
    background_tasks: BackgroundTasks,
    http_request: Request
) -> ScrapeResponse:
    """Submit a new scraping job"""
    try:
        scraper: ContentScraper = http_request.app.state.scraper
        
        job_id = await scraper.submit_job(
            url=str(request.url),
            content_type=request.content_type,
            tags=request.tags or [],
            priority=request.priority
        )
        
        logger.info(f"Scrape job submitted: {job_id} for URL: {request.url}")
        
        return ScrapeResponse(
            job_id=job_id,
            status="queued",
            url=str(request.url),
            submitted_at=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Failed to submit scrape job: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to submit scrape job: {str(e)}")


@router.get("/scrape/{job_id}", response_model=ScrapeResult)
async def get_scrape_result(job_id: str, request: Request) -> ScrapeResult:
    """Get the result of a scraping job"""
    try:
        scraper: ContentScraper = request.app.state.scraper
        result = await scraper.get_job_result(job_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return ScrapeResult(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get scrape result: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get scrape result: {str(e)}")


@router.get("/scrape", response_model=List[ScrapeResult])
async def list_scrape_jobs(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    request: Request = None
) -> List[ScrapeResult]:
    """List scraping jobs with optional filtering"""
    try:
        scraper: ContentScraper = request.app.state.scraper
        jobs = await scraper.list_jobs(
            status=status,
            limit=limit,
            offset=offset
        )
        
        return [ScrapeResult(**job) for job in jobs]
        
    except Exception as e:
        logger.error(f"Failed to list scrape jobs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list scrape jobs: {str(e)}")


@router.delete("/scrape/{job_id}")
async def cancel_scrape_job(job_id: str, request: Request) -> Dict[str, Any]:
    """Cancel a scraping job"""
    try:
        scraper: ContentScraper = request.app.state.scraper
        success = await scraper.cancel_job(job_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Job not found or cannot be cancelled")
        
        return {
            "job_id": job_id,
            "status": "cancelled",
            "cancelled_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel scrape job: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel scrape job: {str(e)}")


@router.get("/stats")
async def get_scraper_stats(request: Request) -> Dict[str, Any]:
    """Get scraper statistics"""
    try:
        scraper: ContentScraper = request.app.state.scraper
        stats = await scraper.get_stats()
        
        return {
            "service": "web-scraper",
            "timestamp": datetime.utcnow().isoformat(),
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Failed to get scraper stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get scraper stats: {str(e)}")