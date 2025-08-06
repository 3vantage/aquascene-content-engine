"""
Content Scraper - Main scraping logic for aquascaping content
"""

import asyncio
import aioredis
import httpx
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import logging

from ..config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class ContentScraper:
    """Main content scraper class"""
    
    def __init__(self):
        self.redis = None
        self.session = None
        self._initialize()
    
    def _initialize(self):
        """Initialize the scraper"""
        self.session = httpx.AsyncClient(
            timeout=httpx.Timeout(settings.SCRAPER_TIMEOUT),
            headers={"User-Agent": settings.SCRAPER_USER_AGENT},
            follow_redirects=True
        )
        logger.info("Content scraper initialized")
    
    async def get_redis(self):
        """Get Redis connection"""
        if not self.redis:
            self.redis = aioredis.from_url(settings.REDIS_URL)
        return self.redis
    
    async def submit_job(
        self,
        url: str,
        content_type: str = "article",
        tags: List[str] = None,
        priority: int = 1
    ) -> str:
        """Submit a scraping job"""
        job_id = str(uuid.uuid4())
        job_data = {
            "job_id": job_id,
            "url": url,
            "content_type": content_type,
            "tags": tags or [],
            "priority": priority,
            "status": "queued",
            "submitted_at": datetime.utcnow().isoformat(),
            "attempts": 0
        }
        
        redis = await self.get_redis()
        await redis.hset(f"scrape_job:{job_id}", mapping={
            k: str(v) if not isinstance(v, str) else v 
            for k, v in job_data.items()
        })
        
        # Add to queue
        await redis.lpush("scrape_queue", job_id)
        
        # Start processing if not already running
        asyncio.create_task(self._process_queue())
        
        return job_id
    
    async def get_job_result(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get the result of a scraping job"""
        redis = await self.get_redis()
        job_data = await redis.hgetall(f"scrape_job:{job_id}")
        
        if not job_data:
            return None
        
        # Convert bytes to strings
        result = {k.decode(): v.decode() for k, v in job_data.items()}
        
        # Parse JSON fields
        if "content" in result and result["content"]:
            import json
            try:
                result["content"] = json.loads(result["content"])
            except json.JSONDecodeError:
                pass
        
        if "tags" in result and result["tags"]:
            import json
            try:
                result["tags"] = json.loads(result["tags"])
            except json.JSONDecodeError:
                result["tags"] = []
        
        return result
    
    async def list_jobs(
        self,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List scraping jobs with optional filtering"""
        redis = await self.get_redis()
        
        # Get all job keys
        keys = await redis.keys("scrape_job:*")
        jobs = []
        
        for key in keys:
            job_data = await redis.hgetall(key)
            if job_data:
                job = {k.decode(): v.decode() for k, v in job_data.items()}
                if not status or job.get("status") == status:
                    jobs.append(job)
        
        # Sort by submitted_at descending
        jobs.sort(key=lambda x: x.get("submitted_at", ""), reverse=True)
        
        # Apply pagination
        return jobs[offset:offset + limit]
    
    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a scraping job"""
        redis = await self.get_redis()
        job_data = await redis.hgetall(f"scrape_job:{job_id}")
        
        if not job_data:
            return False
        
        status = job_data.get(b"status", b"").decode()
        if status in ["completed", "failed", "cancelled"]:
            return False
        
        # Update status
        await redis.hset(f"scrape_job:{job_id}", "status", "cancelled")
        await redis.hset(f"scrape_job:{job_id}", "cancelled_at", datetime.utcnow().isoformat())
        
        return True
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get scraper statistics"""
        redis = await self.get_redis()
        
        # Count jobs by status
        keys = await redis.keys("scrape_job:*")
        stats = {
            "total_jobs": len(keys),
            "queued": 0,
            "processing": 0,
            "completed": 0,
            "failed": 0,
            "cancelled": 0
        }
        
        for key in keys:
            status = await redis.hget(key, "status")
            if status:
                status = status.decode()
                if status in stats:
                    stats[status] += 1
        
        # Queue length
        queue_length = await redis.llen("scrape_queue")
        stats["queue_length"] = queue_length
        
        return stats
    
    async def _process_queue(self):
        """Process the scraping queue"""
        redis = await self.get_redis()
        
        try:
            while True:
                # Get next job from queue
                job_id = await redis.brpop("scrape_queue", timeout=1)
                if not job_id:
                    break
                
                job_id = job_id[1].decode()
                await self._process_job(job_id)
                
        except Exception as e:
            logger.error(f"Error processing queue: {e}")
    
    async def _process_job(self, job_id: str):
        """Process a single scraping job"""
        redis = await self.get_redis()
        
        try:
            # Update job status
            await redis.hset(f"scrape_job:{job_id}", "status", "processing")
            await redis.hset(f"scrape_job:{job_id}", "started_at", datetime.utcnow().isoformat())
            
            # Get job data
            job_data = await redis.hgetall(f"scrape_job:{job_id}")
            if not job_data:
                return
            
            url = job_data[b"url"].decode()
            logger.info(f"Processing scrape job {job_id} for URL: {url}")
            
            # Perform scraping
            content = await self._scrape_url(url)
            
            # Store results
            import json
            await redis.hset(f"scrape_job:{job_id}", "content", json.dumps(content))
            await redis.hset(f"scrape_job:{job_id}", "status", "completed")
            await redis.hset(f"scrape_job:{job_id}", "completed_at", datetime.utcnow().isoformat())
            
            logger.info(f"Completed scrape job {job_id}")
            
        except Exception as e:
            logger.error(f"Failed to process job {job_id}: {e}")
            await redis.hset(f"scrape_job:{job_id}", "status", "failed")
            await redis.hset(f"scrape_job:{job_id}", "error", str(e))
            await redis.hset(f"scrape_job:{job_id}", "failed_at", datetime.utcnow().isoformat())
    
    async def _scrape_url(self, url: str) -> Dict[str, Any]:
        """Scrape content from a URL"""
        try:
            response = await self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract basic content
            content = {
                "url": url,
                "title": self._extract_title(soup),
                "text": self._extract_text(soup),
                "images": self._extract_images(soup, url),
                "links": self._extract_links(soup, url),
                "metadata": self._extract_metadata(soup),
                "scraped_at": datetime.utcnow().isoformat(),
                "status_code": response.status_code
            }
            
            return content
            
        except Exception as e:
            logger.error(f"Failed to scrape URL {url}: {e}")
            raise
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title"""
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text().strip()
        return ""
    
    def _extract_text(self, soup: BeautifulSoup) -> str:
        """Extract main text content"""
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text content
        text = soup.get_text()
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text[:5000]  # Limit text length
    
    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Extract image URLs and alt text"""
        images = []
        for img in soup.find_all('img', src=True):
            src = urljoin(base_url, img['src'])
            alt = img.get('alt', '')
            images.append({"src": src, "alt": alt})
        
        return images[:20]  # Limit number of images
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Extract links"""
        links = []
        for link in soup.find_all('a', href=True):
            href = urljoin(base_url, link['href'])
            text = link.get_text().strip()
            if text:
                links.append({"href": href, "text": text})
        
        return links[:50]  # Limit number of links
    
    def _extract_metadata(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract metadata from meta tags"""
        metadata = {}
        
        # Extract meta tags
        for meta in soup.find_all('meta'):
            name = meta.get('name') or meta.get('property')
            content = meta.get('content')
            if name and content:
                metadata[name] = content
        
        return metadata