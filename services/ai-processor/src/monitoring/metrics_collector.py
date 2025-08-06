"""
Metrics Collector

Collects system and application metrics for monitoring and analysis.
"""

import asyncio
import time
from typing import Dict, Any, List
import structlog

logger = structlog.get_logger()


class MetricsCollector:
    """Collects various system and application metrics"""
    
    def __init__(self):
        self.running = False
        self.collection_task: Optional[asyncio.Task] = None
        self.metrics_history: List[Dict[str, Any]] = []
        self.max_history_size = 1000
        
    async def start(self) -> None:
        """Start metrics collection"""
        if self.running:
            return
        
        self.running = True
        self.collection_task = asyncio.create_task(self._collection_loop())
        logger.info("Metrics collector started")
    
    async def stop(self) -> None:
        """Stop metrics collection"""
        self.running = False
        
        if self.collection_task:
            self.collection_task.cancel()
            try:
                await self.collection_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Metrics collector stopped")
    
    async def _collection_loop(self) -> None:
        """Main metrics collection loop"""
        while self.running:
            try:
                metrics = await self._collect_metrics()
                self.metrics_history.append(metrics)
                
                # Keep history size manageable
                if len(self.metrics_history) > self.max_history_size:
                    self.metrics_history = self.metrics_history[-self.max_history_size:]
                
                await asyncio.sleep(30)  # Collect every 30 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Metrics collection error", error=str(e))
                await asyncio.sleep(30)
    
    async def _collect_metrics(self) -> Dict[str, Any]:
        """Collect current system metrics"""
        timestamp = time.time()
        
        # System metrics
        system_metrics = await self.get_system_metrics()
        
        return {
            "timestamp": timestamp,
            "system": system_metrics,
            "application": {
                "metrics_history_size": len(self.metrics_history),
                "collector_running": self.running
            }
        }
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get system resource metrics"""
        try:
            import psutil
            
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            
            return {
                "cpu_percent": cpu_percent,
                "cpu_count": cpu_count,
                "memory_percent": memory.percent,
                "memory_total": memory.total,
                "memory_available": memory.available,
                "memory_used": memory.used,
                "disk_percent": (disk.used / disk.total) * 100,
                "disk_total": disk.total,
                "disk_used": disk.used,
                "disk_free": disk.free
            }
            
        except ImportError:
            # psutil not available, return basic metrics
            return {
                "cpu_percent": 0.0,
                "cpu_count": 1,
                "memory_percent": 0.0,
                "memory_total": 0,
                "memory_available": 0,
                "memory_used": 0,
                "disk_percent": 0.0,
                "disk_total": 0,
                "disk_used": 0,
                "disk_free": 0
            }
        except Exception as e:
            logger.error("Error collecting system metrics", error=str(e))
            return {"error": str(e)}
    
    def get_latest_metrics(self) -> Optional[Dict[str, Any]]:
        """Get the most recent metrics"""
        return self.metrics_history[-1] if self.metrics_history else None
    
    def get_metrics_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get metrics history"""
        return self.metrics_history[-limit:]