"""
Pytest configuration for E2E testing
"""
import pytest
import asyncio
from typing import Dict, Any

from fixtures.test_data import (
    sample_content_request,
    sample_scrape_request, 
    sample_subscriber_data,
    service_endpoints,
    database_urls,
    expected_health_response,
    test_urls
)

from utils.test_helpers import ServiceHealthChecker


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def health_checker(service_endpoints):
    """Create a service health checker"""
    return ServiceHealthChecker(service_endpoints)


@pytest.fixture(scope="session", autouse=True)
async def wait_for_services(health_checker):
    """Wait for all services to be ready before running tests"""
    # Wait for services to be healthy (with timeout)
    await health_checker.wait_for_all_services(timeout=120)
    yield
    # Cleanup after tests if needed


@pytest.fixture
def test_timeout():
    """Default timeout for tests"""
    return 60


@pytest.fixture
def retry_config():
    """Retry configuration for flaky operations"""
    return {
        "max_retries": 3,
        "retry_delay": 2,
        "backoff_factor": 2
    }


# Make fixtures available to all test modules
__all__ = [
    'sample_content_request',
    'sample_scrape_request', 
    'sample_subscriber_data',
    'service_endpoints',
    'database_urls',
    'expected_health_response',
    'test_urls',
    'health_checker',
    'wait_for_services',
    'test_timeout',
    'retry_config'
]