"""
Service Monitor

Monitors the health and performance of the AI content processor service,
collecting metrics and providing alerts for operational issues.
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import structlog

from .metrics_collector import MetricsCollector
from .health_checker import HealthChecker

logger = structlog.get_logger()


class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Alert:
    """System alert"""
    id: str
    level: AlertLevel
    title: str
    message: str
    component: str
    timestamp: float = field(default_factory=time.time)
    resolved: bool = False
    resolved_at: Optional[float] = None


@dataclass
class PerformanceMetrics:
    """Performance metrics snapshot"""
    timestamp: float
    requests_per_minute: float
    average_response_time: float
    error_rate: float
    active_connections: int
    memory_usage_percent: float
    cpu_usage_percent: float
    queue_size: int
    
    # LLM specific metrics
    llm_requests_total: int
    llm_errors_total: int
    llm_cost_total: float
    
    # Content generation metrics
    content_generated_total: int
    content_generation_errors: int
    average_quality_score: float


class ServiceMonitor:
    """Main service monitoring coordinator"""
    
    def __init__(
        self,
        llm_manager: Any,
        content_orchestrator: Any,
        batch_processor: Any,
        check_interval: float = 30.0
    ):
        self.llm_manager = llm_manager
        self.content_orchestrator = content_orchestrator
        self.batch_processor = batch_processor
        self.check_interval = check_interval
        
        # Monitoring components
        self.metrics_collector = MetricsCollector()
        self.health_checker = HealthChecker()
        
        # Alert management
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.alert_callbacks: List[Callable] = []
        
        # Performance tracking
        self.performance_history: List[PerformanceMetrics] = []
        self.max_history_size = 1000
        
        # Monitoring task
        self.monitoring_task: Optional[asyncio.Task] = None
        self.running = False
        
        # Thresholds for alerts
        self.thresholds = {
            "memory_usage_critical": 90.0,
            "memory_usage_warning": 80.0,
            "cpu_usage_critical": 95.0,
            "cpu_usage_warning": 85.0,
            "error_rate_critical": 10.0,
            "error_rate_warning": 5.0,
            "response_time_critical": 30.0,
            "response_time_warning": 15.0,
            "queue_size_critical": 1000,
            "queue_size_warning": 500
        }
        
        # Health status cache
        self.last_health_check: Optional[Dict[str, Any]] = None
        self.health_check_cache_duration = 60.0  # 1 minute
    
    async def start(self) -> None:
        """Start the service monitor"""
        if self.running:
            return
        
        self.running = True
        
        # Start metrics collection
        await self.metrics_collector.start()
        
        # Start health checker
        await self.health_checker.start()
        
        # Start monitoring task
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        logger.info("Service monitor started")
    
    async def stop(self) -> None:
        """Stop the service monitor"""
        self.running = False
        
        # Cancel monitoring task
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        # Stop components
        await self.health_checker.stop()
        await self.metrics_collector.stop()
        
        logger.info("Service monitor stopped")
    
    async def _monitoring_loop(self) -> None:
        """Main monitoring loop"""
        logger.info("Starting monitoring loop")
        
        while self.running:
            try:
                # Collect current metrics
                metrics = await self._collect_current_metrics()
                
                # Add to history
                self.performance_history.append(metrics)
                if len(self.performance_history) > self.max_history_size:
                    self.performance_history = self.performance_history[-self.max_history_size:]
                
                # Check for alerts
                await self._check_alerts(metrics)
                
                # Update health status
                await self._update_health_status()
                
                # Log periodic summary
                if len(self.performance_history) % 10 == 0:  # Every 10 checks
                    await self._log_performance_summary(metrics)
                
                await asyncio.sleep(self.check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Monitoring loop error", error=str(e))
                await asyncio.sleep(self.check_interval)
        
        logger.info("Monitoring loop stopped")
    
    async def _collect_current_metrics(self) -> PerformanceMetrics:
        """Collect current performance metrics"""
        # Get basic system metrics
        system_metrics = await self.metrics_collector.get_system_metrics()
        
        # Get service-specific metrics
        orchestrator_stats = self.content_orchestrator.get_stats()
        batch_stats = self.batch_processor.get_statistics()
        llm_stats = self.llm_manager.get_performance_stats()
        
        # Calculate derived metrics
        requests_per_minute = orchestrator_stats.get("total_requests", 0) / (time.time() - (getattr(self, 'start_time', time.time()) or time.time())) * 60
        error_rate = (orchestrator_stats.get("failed_generations", 0) / max(orchestrator_stats.get("total_requests", 1), 1)) * 100
        
        # Calculate average quality score
        content_stats = orchestrator_stats.get("content_type_stats", {})
        total_content = sum(stats.get("successful", 0) for stats in content_stats.values())
        avg_quality = 0.75  # Default estimate, would be calculated from actual data
        
        return PerformanceMetrics(
            timestamp=time.time(),
            requests_per_minute=requests_per_minute,
            average_response_time=orchestrator_stats.get("average_generation_time", 0),
            error_rate=error_rate,
            active_connections=orchestrator_stats.get("active_requests", 0),
            memory_usage_percent=system_metrics.get("memory_percent", 0),
            cpu_usage_percent=system_metrics.get("cpu_percent", 0),
            queue_size=sum(orchestrator_stats.get("queued_requests", {}).values()),
            llm_requests_total=sum(stats.get("stats", {}).get("total_requests", 0) for stats in llm_stats.get("stats", {}).values()),
            llm_errors_total=sum(stats.get("stats", {}).get("failures", 0) for stats in llm_stats.get("stats", {}).values()),
            llm_cost_total=0.0,  # Would calculate from actual cost tracking
            content_generated_total=orchestrator_stats.get("successful_generations", 0),
            content_generation_errors=orchestrator_stats.get("failed_generations", 0),
            average_quality_score=avg_quality
        )
    
    async def _check_alerts(self, metrics: PerformanceMetrics) -> None:
        """Check for alert conditions"""
        alerts_to_create = []
        alerts_to_resolve = []
        
        # Memory usage alerts
        if metrics.memory_usage_percent >= self.thresholds["memory_usage_critical"]:
            alerts_to_create.append({
                "id": "memory_critical",
                "level": AlertLevel.CRITICAL,
                "title": "Critical Memory Usage",
                "message": f"Memory usage at {metrics.memory_usage_percent:.1f}%",
                "component": "system"
            })
        elif metrics.memory_usage_percent >= self.thresholds["memory_usage_warning"]:
            alerts_to_create.append({
                "id": "memory_warning",
                "level": AlertLevel.WARNING,
                "title": "High Memory Usage",
                "message": f"Memory usage at {metrics.memory_usage_percent:.1f}%",
                "component": "system"
            })
        else:
            alerts_to_resolve.extend(["memory_critical", "memory_warning"])
        
        # CPU usage alerts
        if metrics.cpu_usage_percent >= self.thresholds["cpu_usage_critical"]:
            alerts_to_create.append({
                "id": "cpu_critical",
                "level": AlertLevel.CRITICAL,
                "title": "Critical CPU Usage",
                "message": f"CPU usage at {metrics.cpu_usage_percent:.1f}%",
                "component": "system"
            })
        elif metrics.cpu_usage_percent >= self.thresholds["cpu_usage_warning"]:
            alerts_to_create.append({
                "id": "cpu_warning",
                "level": AlertLevel.WARNING,
                "title": "High CPU Usage",
                "message": f"CPU usage at {metrics.cpu_usage_percent:.1f}%",
                "component": "system"
            })
        else:
            alerts_to_resolve.extend(["cpu_critical", "cpu_warning"])
        
        # Error rate alerts
        if metrics.error_rate >= self.thresholds["error_rate_critical"]:
            alerts_to_create.append({
                "id": "error_rate_critical",
                "level": AlertLevel.CRITICAL,
                "title": "Critical Error Rate",
                "message": f"Error rate at {metrics.error_rate:.1f}%",
                "component": "content_generation"
            })
        elif metrics.error_rate >= self.thresholds["error_rate_warning"]:
            alerts_to_create.append({
                "id": "error_rate_warning",
                "level": AlertLevel.WARNING,
                "title": "High Error Rate",
                "message": f"Error rate at {metrics.error_rate:.1f}%",
                "component": "content_generation"
            })
        else:
            alerts_to_resolve.extend(["error_rate_critical", "error_rate_warning"])
        
        # Response time alerts
        if metrics.average_response_time >= self.thresholds["response_time_critical"]:
            alerts_to_create.append({
                "id": "response_time_critical",
                "level": AlertLevel.CRITICAL,
                "title": "Critical Response Time",
                "message": f"Average response time at {metrics.average_response_time:.1f}s",
                "component": "content_generation"
            })
        elif metrics.average_response_time >= self.thresholds["response_time_warning"]:
            alerts_to_create.append({
                "id": "response_time_warning",
                "level": AlertLevel.WARNING,
                "title": "High Response Time",
                "message": f"Average response time at {metrics.average_response_time:.1f}s",
                "component": "content_generation"
            })
        else:
            alerts_to_resolve.extend(["response_time_critical", "response_time_warning"])
        
        # Queue size alerts
        if metrics.queue_size >= self.thresholds["queue_size_critical"]:
            alerts_to_create.append({
                "id": "queue_size_critical",
                "level": AlertLevel.CRITICAL,
                "title": "Critical Queue Size",
                "message": f"Queue size at {metrics.queue_size}",
                "component": "content_generation"
            })
        elif metrics.queue_size >= self.thresholds["queue_size_warning"]:
            alerts_to_create.append({
                "id": "queue_size_warning",
                "level": AlertLevel.WARNING,
                "title": "High Queue Size",
                "message": f"Queue size at {metrics.queue_size}",
                "component": "content_generation"
            })
        else:
            alerts_to_resolve.extend(["queue_size_critical", "queue_size_warning"])
        
        # Create new alerts
        for alert_data in alerts_to_create:
            await self._create_alert(**alert_data)
        
        # Resolve alerts
        for alert_id in alerts_to_resolve:
            await self._resolve_alert(alert_id)
    
    async def _create_alert(
        self,
        id: str,
        level: AlertLevel,
        title: str,
        message: str,
        component: str
    ) -> None:
        """Create a new alert"""
        # Don't create duplicate alerts
        if id in self.active_alerts:
            return
        
        alert = Alert(
            id=id,
            level=level,
            title=title,
            message=message,
            component=component
        )
        
        self.active_alerts[id] = alert
        self.alert_history.append(alert)
        
        # Keep alert history limited
        if len(self.alert_history) > 1000:
            self.alert_history = self.alert_history[-1000:]
        
        # Log alert
        log_method = {
            AlertLevel.INFO: logger.info,
            AlertLevel.WARNING: logger.warning,
            AlertLevel.ERROR: logger.error,
            AlertLevel.CRITICAL: logger.critical
        }.get(level, logger.info)
        
        log_method(
            f"Alert created: {title}",
            alert_id=id,
            level=level.value,
            component=component,
            message=message
        )
        
        # Call alert callbacks
        for callback in self.alert_callbacks:
            try:
                await callback(alert, "created")
            except Exception as e:
                logger.error("Alert callback error", error=str(e))
    
    async def _resolve_alert(self, alert_id: str) -> None:
        """Resolve an active alert"""
        if alert_id not in self.active_alerts:
            return
        
        alert = self.active_alerts[alert_id]
        alert.resolved = True
        alert.resolved_at = time.time()
        
        del self.active_alerts[alert_id]
        
        logger.info(
            f"Alert resolved: {alert.title}",
            alert_id=alert_id,
            duration=alert.resolved_at - alert.timestamp
        )
        
        # Call alert callbacks
        for callback in self.alert_callbacks:
            try:
                await callback(alert, "resolved")
            except Exception as e:
                logger.error("Alert callback error", error=str(e))
    
    async def _update_health_status(self) -> None:
        """Update overall health status"""
        try:
            # Check if we should update health status (cache for performance)
            current_time = time.time()
            if (self.last_health_check and 
                current_time - self.last_health_check.get("timestamp", 0) < self.health_check_cache_duration):
                return
            
            health_status = await self.health_checker.check_overall_health(
                llm_manager=self.llm_manager,
                content_orchestrator=self.content_orchestrator,
                batch_processor=self.batch_processor
            )
            
            health_status["timestamp"] = current_time
            self.last_health_check = health_status
            
            # Create alerts for unhealthy components
            for component, status in health_status.get("components", {}).items():
                if not status.get("healthy", True):
                    await self._create_alert(
                        id=f"health_{component}",
                        level=AlertLevel.ERROR,
                        title=f"Component Health Issue: {component}",
                        message=status.get("error", "Component is unhealthy"),
                        component=component
                    )
                else:
                    await self._resolve_alert(f"health_{component}")
        
        except Exception as e:
            logger.error("Health status update error", error=str(e))
    
    async def _log_performance_summary(self, metrics: PerformanceMetrics) -> None:
        """Log periodic performance summary"""
        logger.info(
            "Performance summary",
            requests_per_minute=f"{metrics.requests_per_minute:.1f}",
            avg_response_time=f"{metrics.average_response_time:.2f}s",
            error_rate=f"{metrics.error_rate:.1f}%",
            memory_usage=f"{metrics.memory_usage_percent:.1f}%",
            cpu_usage=f"{metrics.cpu_usage_percent:.1f}%",
            active_requests=metrics.active_connections,
            queue_size=metrics.queue_size,
            active_alerts=len(self.active_alerts)
        )
    
    def add_alert_callback(self, callback: Callable[[Alert, str], None]) -> None:
        """Add alert callback function"""
        self.alert_callbacks.append(callback)
    
    def get_current_metrics(self) -> Optional[PerformanceMetrics]:
        """Get the most recent performance metrics"""
        return self.performance_history[-1] if self.performance_history else None
    
    def get_metrics_history(self, limit: int = 100) -> List[PerformanceMetrics]:
        """Get performance metrics history"""
        return self.performance_history[-limit:]
    
    def get_active_alerts(self) -> List[Alert]:
        """Get currently active alerts"""
        return list(self.active_alerts.values())
    
    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """Get alert history"""
        return self.alert_history[-limit:]
    
    def get_health_status(self) -> Optional[Dict[str, Any]]:
        """Get cached health status"""
        return self.last_health_check
    
    def update_thresholds(self, new_thresholds: Dict[str, float]) -> None:
        """Update alert thresholds"""
        self.thresholds.update(new_thresholds)
        logger.info("Alert thresholds updated", thresholds=new_thresholds)
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for monitoring dashboard"""
        current_metrics = self.get_current_metrics()
        
        return {
            "current_metrics": current_metrics.__dict__ if current_metrics else None,
            "active_alerts": [alert.__dict__ for alert in self.get_active_alerts()],
            "health_status": self.get_health_status(),
            "recent_performance": [
                metrics.__dict__ for metrics in self.get_metrics_history(24)  # Last 24 data points
            ],
            "system_info": {
                "running": self.running,
                "check_interval": self.check_interval,
                "thresholds": self.thresholds
            }
        }