"""
Test data fixtures for E2E testing
"""
import pytest
from typing import Dict, Any, List


@pytest.fixture
def sample_content_request() -> Dict[str, Any]:
    """Sample content generation request"""
    return {
        "topic": "Aquarium Plant Care for Beginners",
        "content_type": "blog_post",
        "target_audience": "beginners",
        "word_count": 500,
        "keywords": ["aquarium plants", "plant care", "aquascaping"],
        "tone": "friendly",
        "format": "markdown"
    }


@pytest.fixture
def sample_scrape_request() -> Dict[str, Any]:
    """Sample scraping request"""
    return {
        "url": "https://httpbin.org/json",
        "content_type": "reference",
        "tags": ["test", "reference"],
        "priority": 1
    }


@pytest.fixture
def sample_subscriber_data() -> Dict[str, Any]:
    """Sample subscriber data"""
    return {
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "interests": ["aquascaping", "freshwater", "plants"]
    }


@pytest.fixture
def service_endpoints() -> Dict[str, str]:
    """Service endpoint URLs"""
    return {
        "content_manager": "http://content-manager:8000",
        "ai_processor": "http://ai-processor:8001",
        "web_scraper": "http://web-scraper:8002",
        "distributor": "http://distributor:8003",
        "subscriber_manager": "http://subscriber-manager:8004",
        "admin_dashboard": "http://admin-dashboard:3000",
        "nginx": "http://nginx:80",
        "prometheus": "http://prometheus:9090",
        "grafana": "http://grafana:3000"
    }


@pytest.fixture
def database_urls() -> Dict[str, str]:
    """Database connection URLs"""
    return {
        "postgres": "postgresql://postgres:postgres@postgres:5432/content_engine",
        "redis": "redis://redis:6379"
    }


@pytest.fixture
def expected_health_response() -> Dict[str, Any]:
    """Expected health check response structure"""
    return {
        "status": "healthy",
        "service": str,
        "timestamp": str,
        "version": str
    }


@pytest.fixture
def test_urls() -> List[str]:
    """URLs safe for testing scraping"""
    return [
        "https://httpbin.org/json",
        "https://httpbin.org/html",
        "https://jsonplaceholder.typicode.com/posts/1"
    ]