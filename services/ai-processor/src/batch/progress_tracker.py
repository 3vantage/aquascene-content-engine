"""
Progress Tracker

Tracks progress of batch jobs and provides real-time updates
on job completion status and estimated completion times.
"""

import time
import asyncio
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
import structlog

logger = structlog.get_logger()


@dataclass
class JobProgress:
    """Progress information for a job"""
    job_id: str
    total_items: int
    completed_items: int = 0
    failed_items: int = 0
    started_at: Optional[float] = None
    estimated_completion: Optional[float] = None
    status: str = "pending"
    
    @property
    def progress_percent(self) -> float:
        """Calculate progress percentage"""
        if self.total_items == 0:
            return 0.0
        return (self.completed_items / self.total_items) * 100
    
    @property
    def remaining_items(self) -> int:
        """Calculate remaining items"""
        return self.total_items - self.completed_items - self.failed_items


class ProgressTracker:
    """Tracks progress of batch operations"""
    
    def __init__(self):
        self.jobs: Dict[str, JobProgress] = {}
        self.running = False
        self.update_task: Optional[asyncio.Task] = None
        
    async def start(self) -> None:
        """Start progress tracking"""
        if self.running:
            return
        
        self.running = True
        self.update_task = asyncio.create_task(self._progress_update_loop())
        logger.info("Progress tracker started")
    
    async def stop(self) -> None:
        """Stop progress tracking"""
        self.running = False
        
        if self.update_task:
            self.update_task.cancel()
            try:
                await self.update_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Progress tracker stopped")
    
    async def create_job(self, job_id: str, total_items: int) -> None:
        """Create a new job for tracking"""
        self.jobs[job_id] = JobProgress(
            job_id=job_id,
            total_items=total_items,
            started_at=time.time()
        )
        logger.info(f"Created progress tracking for job {job_id}", total_items=total_items)
    
    async def update_progress(self, job_id: str, completed_items: int, failed_items: int = 0) -> None:
        """Update progress for a job"""
        if job_id not in self.jobs:
            logger.warning(f"Job {job_id} not found for progress update")
            return
        
        job = self.jobs[job_id]
        job.completed_items = completed_items
        job.failed_items = failed_items
        
        # Update estimated completion time
        if job.started_at and completed_items > 0:
            elapsed_time = time.time() - job.started_at
            items_per_second = completed_items / elapsed_time
            
            if items_per_second > 0:
                remaining_items = job.remaining_items
                estimated_seconds = remaining_items / items_per_second
                job.estimated_completion = time.time() + estimated_seconds
    
    async def update_job_status(self, job_id: str, status: str) -> None:
        """Update job status"""
        if job_id in self.jobs:
            self.jobs[job_id].status = status
    
    async def complete_job(self, job_id: str) -> None:
        """Mark job as completed and clean up"""
        if job_id in self.jobs:
            self.jobs[job_id].status = "completed"
            # Keep completed jobs for a while for status queries
            # They will be cleaned up by the cleanup loop
    
    async def get_job_progress(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get progress information for a specific job"""
        if job_id not in self.jobs:
            return None
        
        job = self.jobs[job_id]
        
        return {
            "job_id": job.job_id,
            "total_items": job.total_items,
            "completed_items": job.completed_items,
            "failed_items": job.failed_items,
            "progress_percent": job.progress_percent,
            "remaining_items": job.remaining_items,
            "status": job.status,
            "started_at": job.started_at,
            "estimated_completion": job.estimated_completion,
            "estimated_time_remaining": (
                job.estimated_completion - time.time() 
                if job.estimated_completion and job.estimated_completion > time.time() 
                else None
            )
        }
    
    async def get_all_jobs_progress(self) -> Dict[str, Dict[str, Any]]:
        """Get progress information for all jobs"""
        return {
            job_id: await self.get_job_progress(job_id)
            for job_id in self.jobs.keys()
        }
    
    async def _progress_update_loop(self) -> None:
        """Progress update and cleanup loop"""
        while self.running:
            try:
                await self._cleanup_old_jobs()
                await asyncio.sleep(60)  # Run cleanup every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Progress tracker update error", error=str(e))
                await asyncio.sleep(60)
    
    async def _cleanup_old_jobs(self) -> None:
        """Clean up old completed jobs"""
        current_time = time.time()
        cleanup_threshold = 3600  # 1 hour
        
        jobs_to_remove = []
        
        for job_id, job in self.jobs.items():
            if (job.status in ["completed", "failed"] and 
                job.started_at and 
                current_time - job.started_at > cleanup_threshold):
                jobs_to_remove.append(job_id)
        
        for job_id in jobs_to_remove:
            del self.jobs[job_id]
            logger.debug(f"Cleaned up old job {job_id}")
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics for all jobs"""
        active_jobs = sum(1 for job in self.jobs.values() if job.status not in ["completed", "failed"])
        completed_jobs = sum(1 for job in self.jobs.values() if job.status == "completed")
        failed_jobs = sum(1 for job in self.jobs.values() if job.status == "failed")
        
        total_items = sum(job.total_items for job in self.jobs.values())
        completed_items = sum(job.completed_items for job in self.jobs.values())
        failed_items = sum(job.failed_items for job in self.jobs.values())
        
        return {
            "total_jobs": len(self.jobs),
            "active_jobs": active_jobs,
            "completed_jobs": completed_jobs,
            "failed_jobs": failed_jobs,
            "total_items": total_items,
            "completed_items": completed_items,
            "failed_items": failed_items,
            "overall_progress_percent": (
                (completed_items / total_items * 100) if total_items > 0 else 0
            )
        }