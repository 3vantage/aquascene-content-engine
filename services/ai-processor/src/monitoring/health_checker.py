"""
Health Checker  

Performs comprehensive health checks on system components
and provides detailed health status information.
"""

import asyncio
import time
from typing import Dict, Any, Optional
import structlog

logger = structlog.get_logger()


class HealthChecker:
    """Performs health checks on system components"""
    
    def __init__(self):
        self.running = False
        self.last_check_time: Optional[float] = None
        self.cached_health_status: Optional[Dict[str, Any]] = None
        
    async def start(self) -> None:
        """Start health checker"""
        self.running = True
        logger.info("Health checker started")
    
    async def stop(self) -> None:
        """Stop health checker"""
        self.running = False
        logger.info("Health checker stopped")
    
    async def check_overall_health(
        self,
        llm_manager: Any = None,
        content_orchestrator: Any = None,
        batch_processor: Any = None
    ) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        
        current_time = time.time()
        
        # Use cached result if recent (within 30 seconds)
        if (self.cached_health_status and 
            self.last_check_time and 
            current_time - self.last_check_time < 30):
            return self.cached_health_status
        
        health_status = {
            "overall_healthy": True,
            "timestamp": current_time,
            "components": {}
        }
        
        # Check system health
        system_health = await self._check_system_health()
        health_status["components"]["system"] = system_health
        if not system_health.get("healthy", True):
            health_status["overall_healthy"] = False
        
        # Check LLM manager health
        if llm_manager:
            llm_health = await self._check_llm_manager_health(llm_manager)
            health_status["components"]["llm_manager"] = llm_health
            if not llm_health.get("healthy", True):
                health_status["overall_healthy"] = False
        
        # Check content orchestrator health
        if content_orchestrator:
            orchestrator_health = await self._check_orchestrator_health(content_orchestrator)
            health_status["components"]["content_orchestrator"] = orchestrator_health
            if not orchestrator_health.get("healthy", True):
                health_status["overall_healthy"] = False
        
        # Check batch processor health
        if batch_processor:
            batch_health = await self._check_batch_processor_health(batch_processor)
            health_status["components"]["batch_processor"] = batch_health
            if not batch_health.get("healthy", True):
                health_status["overall_healthy"] = False
        
        # Cache the result
        self.cached_health_status = health_status
        self.last_check_time = current_time
        
        return health_status
    
    async def _check_system_health(self) -> Dict[str, Any]:
        """Check basic system health"""
        try:
            import psutil
            
            # Check CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Check memory usage
            memory = psutil.virtual_memory()
            
            # Check disk usage
            disk = psutil.disk_usage('/')
            
            # Determine health based on thresholds
            healthy = True
            issues = []
            
            if cpu_percent > 90:
                healthy = False
                issues.append(f"High CPU usage: {cpu_percent:.1f}%")
            
            if memory.percent > 85:
                healthy = False
                issues.append(f"High memory usage: {memory.percent:.1f}%")
            
            if (disk.used / disk.total) * 100 > 90:
                healthy = False
                issues.append(f"High disk usage: {(disk.used / disk.total) * 100:.1f}%")
            
            return {
                "healthy": healthy,
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": (disk.used / disk.total) * 100,
                "issues": issues
            }
            
        except ImportError:
            return {
                "healthy": True,
                "note": "psutil not available, cannot check system resources"
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }
    
    async def _check_llm_manager_health(self, llm_manager: Any) -> Dict[str, Any]:
        """Check LLM manager health"""
        try:
            # Check if LLM manager has clients
            if not hasattr(llm_manager, 'clients') or not llm_manager.clients:
                return {
                    "healthy": False,
                    "error": "No LLM clients configured"
                }
            
            # Check each client
            client_health = {}
            any_healthy = False
            
            for provider, client in llm_manager.clients.items():
                try:
                    is_available = await client.is_available()
                    client_health[provider] = {
                        "healthy": is_available,
                        "available": is_available
                    }
                    if is_available:
                        any_healthy = True
                except Exception as e:
                    client_health[provider] = {
                        "healthy": False,
                        "error": str(e)
                    }
            
            return {
                "healthy": any_healthy,
                "clients": client_health,
                "total_clients": len(llm_manager.clients)
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }
    
    async def _check_orchestrator_health(self, orchestrator: Any) -> Dict[str, Any]:
        """Check content orchestrator health"""
        try:
            # Check if workers are running
            workers_running = getattr(orchestrator, 'workers_running', False)
            
            # Check active requests count
            active_requests = len(getattr(orchestrator, 'active_requests', {}))
            
            # Check queue sizes
            queued_requests = {}
            if hasattr(orchestrator, 'request_queues'):
                queued_requests = {
                    priority.name: queue.qsize()
                    for priority, queue in orchestrator.request_queues.items()
                }
            
            # Check for excessive queue buildup
            total_queued = sum(queued_requests.values())
            
            healthy = True
            issues = []
            
            if not workers_running:
                healthy = False
                issues.append("Content generation workers not running")
            
            if total_queued > 100:
                healthy = False
                issues.append(f"Excessive queue buildup: {total_queued} requests")
            
            if active_requests > 50:
                issues.append(f"High active request count: {active_requests}")
            
            return {
                "healthy": healthy,
                "workers_running": workers_running,
                "active_requests": active_requests,
                "queued_requests": queued_requests,
                "total_queued": total_queued,
                "issues": issues
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }
    
    async def _check_batch_processor_health(self, batch_processor: Any) -> Dict[str, Any]:
        """Check batch processor health"""
        try:
            # Check if workers are running
            workers_running = getattr(batch_processor, 'workers_running', False)
            
            # Check active jobs
            active_jobs = len(getattr(batch_processor, 'active_jobs', {}))
            
            # Check completed jobs
            completed_jobs = len(getattr(batch_processor, 'completed_jobs', {}))
            
            # Check queue size
            queue_size = 0
            if hasattr(batch_processor, 'job_queue'):
                queue_size = batch_processor.job_queue.qsize()
            
            healthy = True
            issues = []
            
            if not workers_running:
                healthy = False
                issues.append("Batch processing workers not running")
            
            if queue_size > 20:
                issues.append(f"High job queue size: {queue_size}")
            
            if active_jobs > 10:
                issues.append(f"High active job count: {active_jobs}")
            
            return {
                "healthy": healthy,
                "workers_running": workers_running,
                "active_jobs": active_jobs,
                "completed_jobs": completed_jobs,
                "queue_size": queue_size,
                "issues": issues
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }
    
    async def check_component_health(self, component_name: str, component: Any) -> Dict[str, Any]:
        """Check health of a specific component"""
        try:
            if hasattr(component, 'health_check'):
                return await component.health_check()
            elif hasattr(component, 'is_available'):
                is_available = await component.is_available()
                return {
                    "healthy": is_available,
                    "available": is_available
                }
            else:
                return {
                    "healthy": True,
                    "note": f"No health check method available for {component_name}"
                }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }