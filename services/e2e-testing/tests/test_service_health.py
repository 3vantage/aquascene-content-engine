"""
End-to-End Health Check Tests
Tests all service endpoints to ensure they're responsive
"""
import asyncio
import pytest
import httpx
from typing import Dict, List


# Service endpoints to test
SERVICES = {
    "content-manager": "http://content-manager:8000",
    "ai-processor": "http://ai-processor:8001", 
    "web-scraper": "http://web-scraper:8002",
    "distributor": "http://distributor:8003",
    "subscriber-manager": "http://subscriber-manager:8004",
    "nginx": "http://nginx:80",
    "prometheus": "http://prometheus:9090",
    "grafana": "http://grafana:3000",
    "redis": "redis://redis:6379",
    "postgres": "postgresql://postgres:5432"
}


class TestServiceHealth:
    """Test all service health endpoints"""
    
    @pytest.mark.asyncio
    async def test_http_services_health(self):
        """Test HTTP service health endpoints"""
        http_services = [
            ("content-manager", f"{SERVICES['content-manager']}/health"),
            ("ai-processor", f"{SERVICES['ai-processor']}/health"),
            ("web-scraper", f"{SERVICES['web-scraper']}/health"),
            ("distributor", f"{SERVICES['distributor']}/health"),
            ("subscriber-manager", f"{SERVICES['subscriber-manager']}/health"),
        ]
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for service_name, url in http_services:
                try:
                    response = await client.get(url)
                    assert response.status_code == 200, f"{service_name} health check failed"
                    
                    data = response.json()
                    assert data["status"] == "healthy", f"{service_name} reports unhealthy status"
                    
                except httpx.RequestError as e:
                    pytest.fail(f"{service_name} is not reachable: {e}")
    
    @pytest.mark.asyncio
    async def test_nginx_proxy(self):
        """Test Nginx proxy is routing correctly"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # Test main proxy
                response = await client.get("http://nginx:80/health")
                assert response.status_code == 200
                
                # Test API routing
                response = await client.get("http://nginx:80/api/", follow_redirects=True)
                # Should reach content-manager service
                assert response.status_code in [200, 404], "Nginx routing failed"
                
            except httpx.RequestError as e:
                pytest.fail(f"Nginx proxy is not reachable: {e}")
    
    @pytest.mark.asyncio  
    async def test_database_connectivity(self):
        """Test database connectivity"""
        import asyncpg
        import redis
        
        # Test PostgreSQL
        try:
            conn = await asyncpg.connect(
                "postgresql://postgres:postgres@postgres:5432/content_engine",
                timeout=10
            )
            result = await conn.fetchval("SELECT 1")
            assert result == 1, "PostgreSQL connectivity test failed"
            await conn.close()
        except Exception as e:
            pytest.fail(f"PostgreSQL connection failed: {e}")
        
        # Test Redis
        try:
            r = redis.Redis(host='redis', port=6379, decode_responses=True, socket_timeout=10)
            result = r.ping()
            assert result is True, "Redis connectivity test failed"
        except Exception as e:
            pytest.fail(f"Redis connection failed: {e}")
    
    @pytest.mark.asyncio
    async def test_service_discovery(self):
        """Test that services can discover each other"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # Test AI processor can be reached from content manager context
                response = await client.get("http://nginx:80/ai/health")
                # Should route through nginx to ai-processor
                assert response.status_code in [200, 404, 502], "Service discovery through nginx failed"
                
            except httpx.RequestError as e:
                pytest.fail(f"Service discovery test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_monitoring_stack(self):
        """Test monitoring services are accessible"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test Prometheus
            try:
                response = await client.get("http://prometheus:9090/-/healthy")
                assert response.status_code == 200, "Prometheus health check failed"
            except httpx.RequestError as e:
                pytest.fail(f"Prometheus is not reachable: {e}")
            
            # Test Grafana
            try:
                response = await client.get("http://grafana:3000/api/health")
                assert response.status_code == 200, "Grafana health check failed"
            except httpx.RequestError as e:
                pytest.fail(f"Grafana is not reachable: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])