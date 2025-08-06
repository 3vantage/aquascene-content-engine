"""
Test helper utilities for E2E testing
"""
import asyncio
import httpx
import time
import logging
from typing import Dict, Any, Optional, Callable

logger = logging.getLogger(__name__)


async def wait_for_service(
    url: str,
    timeout: int = 60,
    interval: int = 5
) -> bool:
    """
    Wait for a service to become available
    
    Args:
        url: Service URL to check
        timeout: Maximum time to wait in seconds
        interval: Check interval in seconds
        
    Returns:
        True if service becomes available, False if timeout
    """
    start_time = time.time()
    
    async with httpx.AsyncClient() as client:
        while time.time() - start_time < timeout:
            try:
                response = await client.get(url, timeout=10)
                if response.status_code == 200:
                    logger.info(f"Service {url} is available")
                    return True
            except (httpx.RequestError, httpx.TimeoutException):
                pass
            
            await asyncio.sleep(interval)
    
    logger.warning(f"Service {url} did not become available within {timeout} seconds")
    return False


async def poll_for_completion(
    check_url: str,
    condition: Callable[[Dict[str, Any]], bool],
    timeout: int = 120,
    interval: int = 5
) -> Optional[Dict[str, Any]]:
    """
    Poll an endpoint until a condition is met
    
    Args:
        check_url: URL to poll
        condition: Function that returns True when condition is met
        timeout: Maximum time to wait in seconds
        interval: Poll interval in seconds
        
    Returns:
        The response data when condition is met, None if timeout
    """
    start_time = time.time()
    
    async with httpx.AsyncClient() as client:
        while time.time() - start_time < timeout:
            try:
                response = await client.get(check_url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if condition(data):
                        return data
            except (httpx.RequestError, httpx.TimeoutException, ValueError):
                pass
            
            await asyncio.sleep(interval)
    
    logger.warning(f"Condition not met for {check_url} within {timeout} seconds")
    return None


def is_job_completed(data: Dict[str, Any]) -> bool:
    """Check if a job is completed"""
    status = data.get("status", "").lower()
    return status in ["completed", "success", "done"]


def is_job_failed(data: Dict[str, Any]) -> bool:
    """Check if a job has failed"""
    status = data.get("status", "").lower()
    return status in ["failed", "error", "cancelled"]


async def cleanup_test_data(
    service_url: str,
    resource_id: str,
    endpoint: str = "cleanup"
) -> bool:
    """
    Clean up test data after tests
    
    Args:
        service_url: Base service URL
        resource_id: ID of resource to clean up
        endpoint: Cleanup endpoint
        
    Returns:
        True if cleanup successful, False otherwise
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{service_url}/{endpoint}/{resource_id}",
                timeout=30
            )
            return response.status_code in [200, 204, 404]
    except Exception as e:
        logger.warning(f"Cleanup failed for {resource_id}: {e}")
        return False


class ServiceHealthChecker:
    """Helper class for checking service health"""
    
    def __init__(self, services: Dict[str, str]):
        self.services = services
    
    async def check_all_services(self) -> Dict[str, bool]:
        """Check health of all services"""
        results = {}
        
        async with httpx.AsyncClient(timeout=30) as client:
            tasks = []
            for name, url in self.services.items():
                health_url = f"{url}/health"
                task = asyncio.create_task(
                    self._check_service_health(client, name, health_url)
                )
                tasks.append(task)
            
            results_list = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(results_list):
                service_name = list(self.services.keys())[i]
                if isinstance(result, Exception):
                    results[service_name] = False
                else:
                    results[service_name] = result
        
        return results
    
    async def _check_service_health(
        self,
        client: httpx.AsyncClient,
        name: str,
        url: str
    ) -> bool:
        """Check individual service health"""
        try:
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                return data.get("status") == "healthy"
        except Exception:
            pass
        return False
    
    async def wait_for_all_services(self, timeout: int = 180) -> bool:
        """Wait for all services to become healthy"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            health_status = await self.check_all_services()
            
            if all(health_status.values()):
                logger.info("All services are healthy")
                return True
            
            unhealthy = [name for name, status in health_status.items() if not status]
            logger.info(f"Waiting for services to become healthy: {unhealthy}")
            
            await asyncio.sleep(10)
        
        logger.error(f"Not all services became healthy within {timeout} seconds")
        return False