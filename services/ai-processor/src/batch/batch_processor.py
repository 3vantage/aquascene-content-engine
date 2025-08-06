"""
Batch Content Processor

Handles batch processing of content generation requests with
efficient resource management, progress tracking, and error handling.
"""

import asyncio
import uuid
import time
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import structlog

from ..generators.content_orchestrator import ContentOrchestrator, ContentRequest, BatchRequest, GenerationPriority
from ..llm_clients.base_client import ContentType
from .progress_tracker import ProgressTracker

logger = structlog.get_logger()


class BatchJobStatus(Enum):
    """Status of batch processing jobs"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProcessingMode(Enum):
    """Processing modes for batch jobs"""
    SEQUENTIAL = "sequential"      # Process one at a time
    CONCURRENT = "concurrent"      # Process multiple concurrently
    ADAPTIVE = "adaptive"          # Adapt based on resource availability


@dataclass
class BatchJob:
    """Batch processing job definition"""
    id: str
    name: str
    requests: List[ContentRequest]
    processing_mode: ProcessingMode = ProcessingMode.CONCURRENT
    max_concurrent: int = 5
    priority: GenerationPriority = GenerationPriority.NORMAL
    retry_failed: bool = True
    max_retries: int = 3
    stop_on_error: bool = False
    timeout_seconds: Optional[int] = None
    
    # Callbacks
    on_progress: Optional[Callable] = None
    on_complete: Optional[Callable] = None
    on_error: Optional[Callable] = None
    
    # Status tracking
    status: BatchJobStatus = BatchJobStatus.PENDING
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    total_requests: int = 0
    completed_requests: int = 0
    failed_requests: int = 0
    current_batch_id: Optional[str] = None
    
    # Results
    results: List[ContentRequest] = field(default_factory=list)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    
    def __post_init__(self):
        if self.total_requests == 0:
            self.total_requests = len(self.requests)


@dataclass
class BatchProcessingConfig:
    """Configuration for batch processing"""
    default_max_concurrent: int = 5
    max_queue_size: int = 1000
    progress_update_interval: float = 1.0
    retry_delay_seconds: float = 2.0
    job_timeout_seconds: int = 3600  # 1 hour default
    resource_check_interval: float = 30.0
    
    # Resource limits
    max_memory_usage_percent: float = 80.0
    max_cpu_usage_percent: float = 90.0
    max_active_jobs: int = 10
    
    # Rate limiting
    requests_per_minute_limit: int = 100
    burst_limit: int = 20


class BatchProcessor:
    """Main batch processing engine"""
    
    def __init__(
        self,
        content_orchestrator: ContentOrchestrator,
        config: Optional[BatchProcessingConfig] = None
    ):
        self.orchestrator = content_orchestrator
        self.config = config or BatchProcessingConfig()
        
        # Job management
        self.active_jobs: Dict[str, BatchJob] = {}
        self.job_queue: asyncio.Queue = asyncio.Queue(maxsize=self.config.max_queue_size)
        self.completed_jobs: Dict[str, BatchJob] = {}
        
        # Progress tracking
        self.progress_tracker = ProgressTracker()
        
        # Worker management
        self.workers_running = False
        self.worker_tasks: List[asyncio.Task] = []
        self.max_workers = 3
        
        # Rate limiting
        self.request_timestamps: List[float] = []
        self.rate_limit_lock = asyncio.Lock()
        
        # Resource monitoring
        self.resource_monitor_task: Optional[asyncio.Task] = None
        self.system_resources = {"memory_percent": 0.0, "cpu_percent": 0.0}
        
        # Statistics
        self.stats = {
            "total_jobs_processed": 0,
            "total_requests_processed": 0,
            "total_failures": 0,
            "average_job_time": 0.0,
            "throughput_per_minute": 0.0
        }
    
    async def start(self) -> None:
        """Start the batch processor"""
        if self.workers_running:
            return
        
        self.workers_running = True
        
        # Start worker tasks
        for i in range(self.max_workers):
            worker_task = asyncio.create_task(self._batch_worker(f"batch-worker-{i}"))
            self.worker_tasks.append(worker_task)
        
        # Start resource monitoring
        self.resource_monitor_task = asyncio.create_task(self._resource_monitor())
        
        # Start progress tracking
        await self.progress_tracker.start()
        
        logger.info(f"Batch processor started with {self.max_workers} workers")
    
    async def stop(self) -> None:
        """Stop the batch processor"""
        self.workers_running = False
        
        # Cancel worker tasks
        for task in self.worker_tasks:
            task.cancel()
        
        if self.worker_tasks:
            await asyncio.gather(*self.worker_tasks, return_exceptions=True)
        
        # Cancel resource monitoring
        if self.resource_monitor_task:
            self.resource_monitor_task.cancel()
            try:
                await self.resource_monitor_task
            except asyncio.CancelledError:
                pass
        
        # Stop progress tracking
        await self.progress_tracker.stop()
        
        self.worker_tasks.clear()
        logger.info("Batch processor stopped")
    
    async def submit_job(self, job: BatchJob) -> str:
        """Submit a batch job for processing"""
        # Validate job
        if not job.requests:
            raise ValueError("Job must contain at least one request")
        
        if len(self.active_jobs) >= self.config.max_active_jobs:
            raise RuntimeError("Maximum number of active jobs reached")
        
        # Assign unique ID if not provided
        if not job.id:
            job.id = str(uuid.uuid4())
        
        # Initialize progress tracking
        await self.progress_tracker.create_job(job.id, len(job.requests))
        
        # Queue the job
        try:
            await self.job_queue.put(job)
            logger.info(f"Submitted batch job {job.id} with {len(job.requests)} requests")
            return job.id
        except asyncio.QueueFull:
            raise RuntimeError("Job queue is full")
    
    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a batch job"""
        if job_id in self.active_jobs:
            job = self.active_jobs[job_id]
            job.status = BatchJobStatus.CANCELLED
            
            # Cancel the current batch if running
            if job.current_batch_id:
                # This would ideally cancel the running batch in the orchestrator
                pass
            
            await self.progress_tracker.update_job_status(job_id, "cancelled")
            logger.info(f"Cancelled batch job {job_id}")
            return True
        
        return False
    
    async def pause_job(self, job_id: str) -> bool:
        """Pause a batch job"""
        if job_id in self.active_jobs:
            job = self.active_jobs[job_id]
            if job.status == BatchJobStatus.RUNNING:
                job.status = BatchJobStatus.PAUSED
                await self.progress_tracker.update_job_status(job_id, "paused")
                logger.info(f"Paused batch job {job_id}")
                return True
        
        return False
    
    async def resume_job(self, job_id: str) -> bool:
        """Resume a paused batch job"""
        if job_id in self.active_jobs:
            job = self.active_jobs[job_id]
            if job.status == BatchJobStatus.PAUSED:
                job.status = BatchJobStatus.RUNNING
                await self.progress_tracker.update_job_status(job_id, "running")
                logger.info(f"Resumed batch job {job_id}")
                return True
        
        return False
    
    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a batch job"""
        # Check active jobs
        if job_id in self.active_jobs:
            job = self.active_jobs[job_id]
            progress = await self.progress_tracker.get_job_progress(job_id)
            
            return {
                "id": job.id,
                "name": job.name,
                "status": job.status.value,
                "total_requests": job.total_requests,
                "completed_requests": job.completed_requests,
                "failed_requests": job.failed_requests,
                "progress_percent": progress.get("progress_percent", 0),
                "estimated_completion": progress.get("estimated_completion"),
                "created_at": job.created_at,
                "started_at": job.started_at,
                "processing_mode": job.processing_mode.value,
                "current_batch_id": job.current_batch_id
            }
        
        # Check completed jobs
        if job_id in self.completed_jobs:
            job = self.completed_jobs[job_id]
            return {
                "id": job.id,
                "name": job.name,
                "status": job.status.value,
                "total_requests": job.total_requests,
                "completed_requests": job.completed_requests,
                "failed_requests": job.failed_requests,
                "progress_percent": 100.0 if job.status == BatchJobStatus.COMPLETED else 0.0,
                "created_at": job.created_at,
                "started_at": job.started_at,
                "completed_at": job.completed_at,
                "processing_mode": job.processing_mode.value
            }
        
        return None
    
    async def get_job_results(self, job_id: str) -> Optional[List[ContentRequest]]:
        """Get results from a completed job"""
        job = self.completed_jobs.get(job_id) or self.active_jobs.get(job_id)
        if job:
            return job.results
        return None
    
    async def _batch_worker(self, worker_id: str) -> None:
        """Batch processing worker"""
        logger.info(f"Batch worker {worker_id} started")
        
        while self.workers_running:
            try:
                # Get job from queue
                try:
                    job = await asyncio.wait_for(self.job_queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue
                
                # Process the job
                await self._process_batch_job(job, worker_id)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Batch worker {worker_id} error", error=str(e))
                await asyncio.sleep(1)
        
        logger.info(f"Batch worker {worker_id} stopped")
    
    async def _process_batch_job(self, job: BatchJob, worker_id: str) -> None:
        """Process a single batch job"""
        job.status = BatchJobStatus.RUNNING
        job.started_at = time.time()
        self.active_jobs[job.id] = job
        
        logger.info(
            f"Worker {worker_id} processing batch job {job.id}",
            total_requests=job.total_requests,
            processing_mode=job.processing_mode.value
        )
        
        try:
            # Apply rate limiting
            await self._apply_rate_limiting(len(job.requests))
            
            # Process based on mode
            if job.processing_mode == ProcessingMode.SEQUENTIAL:
                await self._process_sequential(job)
            elif job.processing_mode == ProcessingMode.CONCURRENT:
                await self._process_concurrent(job)
            elif job.processing_mode == ProcessingMode.ADAPTIVE:
                await self._process_adaptive(job)
            
            # Mark job as completed
            job.status = BatchJobStatus.COMPLETED
            job.completed_at = time.time()
            
            # Call completion callback
            if job.on_complete:
                try:
                    await job.on_complete(job)
                except Exception as e:
                    logger.error(f"Error in completion callback for job {job.id}", error=str(e))
            
            # Update statistics
            self._update_job_statistics(job)
            
            logger.info(
                f"Batch job {job.id} completed",
                completed=job.completed_requests,
                failed=job.failed_requests,
                duration=job.completed_at - job.started_at
            )
        
        except Exception as e:
            job.status = BatchJobStatus.FAILED
            job.completed_at = time.time()
            job.errors.append({
                "error": str(e),
                "timestamp": time.time(),
                "worker_id": worker_id
            })
            
            # Call error callback
            if job.on_error:
                try:
                    await job.on_error(job, e)
                except Exception as callback_error:
                    logger.error(f"Error in error callback for job {job.id}", error=str(callback_error))
            
            logger.error(f"Batch job {job.id} failed", error=str(e))
        
        finally:
            # Move to completed jobs and clean up
            if job.id in self.active_jobs:
                del self.active_jobs[job.id]
            
            self.completed_jobs[job.id] = job
            await self.progress_tracker.complete_job(job.id)
            
            # Cleanup old completed jobs (keep last 100)
            if len(self.completed_jobs) > 100:
                oldest_jobs = sorted(
                    self.completed_jobs.items(),
                    key=lambda x: x[1].completed_at or 0
                )
                for old_job_id, _ in oldest_jobs[:-100]:
                    del self.completed_jobs[old_job_id]
    
    async def _process_sequential(self, job: BatchJob) -> None:
        """Process requests sequentially"""
        for i, request in enumerate(job.requests):
            if job.status == BatchJobStatus.CANCELLED:
                break
            
            # Wait if paused
            while job.status == BatchJobStatus.PAUSED:
                await asyncio.sleep(0.1)
            
            try:
                result = await self.orchestrator.generate_content(request)
                job.results.append(result)
                
                if result.status.value == "completed":
                    job.completed_requests += 1
                else:
                    job.failed_requests += 1
                    if job.stop_on_error:
                        raise Exception(f"Request failed: {result.error_message}")
                
                # Update progress
                await self.progress_tracker.update_progress(job.id, i + 1)
                
                # Call progress callback
                if job.on_progress:
                    try:
                        await job.on_progress(job, i + 1)
                    except Exception as e:
                        logger.error(f"Error in progress callback for job {job.id}", error=str(e))
            
            except Exception as e:
                job.failed_requests += 1
                job.errors.append({
                    "request_index": i,
                    "error": str(e),
                    "timestamp": time.time()
                })
                
                if job.stop_on_error:
                    raise
    
    async def _process_concurrent(self, job: BatchJob) -> None:
        """Process requests concurrently"""
        # Create batch request for orchestrator
        batch_request = BatchRequest(
            id=str(uuid.uuid4()),
            requests=job.requests,
            max_concurrent=job.max_concurrent,
            stop_on_error=job.stop_on_error,
            priority=job.priority
        )
        
        job.current_batch_id = batch_request.id
        
        # Process batch
        result = await self.orchestrator.generate_batch(batch_request)
        
        # Update job with results
        job.results = result.requests
        job.completed_requests = result.completed_count
        job.failed_requests = result.failed_count
        
        # Update progress
        await self.progress_tracker.update_progress(job.id, job.completed_requests)
    
    async def _process_adaptive(self, job: BatchJob) -> None:
        """Process requests adaptively based on system resources"""
        # Determine optimal concurrency based on system resources
        optimal_concurrency = await self._calculate_optimal_concurrency(job)
        
        logger.info(f"Using adaptive concurrency: {optimal_concurrency} for job {job.id}")
        
        # Update job max_concurrent and process
        job.max_concurrent = optimal_concurrency
        await self._process_concurrent(job)
    
    async def _calculate_optimal_concurrency(self, job: BatchJob) -> int:
        """Calculate optimal concurrency based on system resources"""
        base_concurrency = job.max_concurrent
        
        # Adjust based on memory usage
        memory_factor = 1.0
        if self.system_resources["memory_percent"] > 70:
            memory_factor = 0.5
        elif self.system_resources["memory_percent"] > 50:
            memory_factor = 0.7
        
        # Adjust based on CPU usage
        cpu_factor = 1.0
        if self.system_resources["cpu_percent"] > 80:
            cpu_factor = 0.6
        elif self.system_resources["cpu_percent"] > 60:
            cpu_factor = 0.8
        
        # Adjust based on active jobs
        job_factor = 1.0
        if len(self.active_jobs) > 5:
            job_factor = 0.7
        elif len(self.active_jobs) > 3:
            job_factor = 0.85
        
        # Calculate final concurrency
        optimal = int(base_concurrency * memory_factor * cpu_factor * job_factor)
        return max(1, min(optimal, base_concurrency))
    
    async def _apply_rate_limiting(self, request_count: int) -> None:
        """Apply rate limiting to prevent API overload"""
        async with self.rate_limit_lock:
            current_time = time.time()
            
            # Clean old timestamps (older than 1 minute)
            self.request_timestamps = [
                ts for ts in self.request_timestamps 
                if current_time - ts < 60
            ]
            
            # Check if we can process these requests
            if len(self.request_timestamps) + request_count > self.config.requests_per_minute_limit:
                # Calculate wait time
                oldest_request = min(self.request_timestamps) if self.request_timestamps else current_time
                wait_time = 60 - (current_time - oldest_request)
                
                if wait_time > 0:
                    logger.info(f"Rate limiting: waiting {wait_time:.1f} seconds")
                    await asyncio.sleep(wait_time)
            
            # Add current requests to tracking
            self.request_timestamps.extend([current_time] * request_count)
    
    async def _resource_monitor(self) -> None:
        """Monitor system resources"""
        try:
            import psutil
        except ImportError:
            logger.warning("psutil not available, resource monitoring disabled")
            return
        
        while self.workers_running:
            try:
                self.system_resources = {
                    "memory_percent": psutil.virtual_memory().percent,
                    "cpu_percent": psutil.cpu_percent(interval=1)
                }
                
                # Log resource usage periodically
                if time.time() % 60 < 1:  # Every minute
                    logger.info(
                        "System resources",
                        memory=f"{self.system_resources['memory_percent']:.1f}%",
                        cpu=f"{self.system_resources['cpu_percent']:.1f}%",
                        active_jobs=len(self.active_jobs)
                    )
                
                await asyncio.sleep(self.config.resource_check_interval)
                
            except Exception as e:
                logger.error("Resource monitoring error", error=str(e))
                await asyncio.sleep(30)
    
    def _update_job_statistics(self, job: BatchJob) -> None:
        """Update processing statistics"""
        self.stats["total_jobs_processed"] += 1
        self.stats["total_requests_processed"] += job.completed_requests
        self.stats["total_failures"] += job.failed_requests
        
        # Update average job time
        if job.started_at and job.completed_at:
            job_time = job.completed_at - job.started_at
            current_avg = self.stats["average_job_time"]
            total_jobs = self.stats["total_jobs_processed"]
            
            self.stats["average_job_time"] = (
                (current_avg * (total_jobs - 1) + job_time) / total_jobs
            )
        
        # Update throughput
        total_time = time.time() - (job.created_at if hasattr(job, 'created_at') else time.time())
        if total_time > 0:
            self.stats["throughput_per_minute"] = (
                self.stats["total_requests_processed"] / (total_time / 60)
            )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics"""
        return {
            **self.stats,
            "active_jobs": len(self.active_jobs),
            "queued_jobs": self.job_queue.qsize(),
            "completed_jobs": len(self.completed_jobs),
            "system_resources": self.system_resources.copy(),
            "workers_running": self.workers_running,
            "worker_count": len(self.worker_tasks)
        }
    
    async def create_content_generation_job(
        self,
        name: str,
        content_specs: List[Dict[str, Any]],
        processing_mode: ProcessingMode = ProcessingMode.CONCURRENT,
        max_concurrent: int = 5,
        priority: GenerationPriority = GenerationPriority.NORMAL
    ) -> str:
        """Convenience method to create a content generation job"""
        
        # Convert specs to ContentRequests
        requests = []
        for i, spec in enumerate(content_specs):
            request = ContentRequest(
                id=f"{name}-{i}",
                content_type=ContentType(spec["content_type"]),
                topic=spec["topic"],
                requirements=spec.get("requirements", {}),
                context=spec.get("context", {}),
                priority=priority,
                preferred_provider=spec.get("preferred_provider"),
                template_name=spec.get("template_name"),
                target_audience=spec.get("target_audience"),
                seo_keywords=spec.get("seo_keywords", []),
                brand_voice=spec.get("brand_voice"),
                max_length=spec.get("max_length"),
                additional_instructions=spec.get("additional_instructions")
            )
            requests.append(request)
        
        # Create batch job
        job = BatchJob(
            id=str(uuid.uuid4()),
            name=name,
            requests=requests,
            processing_mode=processing_mode,
            max_concurrent=max_concurrent,
            priority=priority
        )
        
        return await self.submit_job(job)