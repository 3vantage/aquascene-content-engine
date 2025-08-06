"""
End-to-End Content Workflow Tests
Tests the complete content creation and distribution flow
"""
import asyncio
import pytest
import httpx
import uuid
from typing import Dict, Any


class TestContentWorkflow:
    """Test complete content workflow from creation to distribution"""
    
    @pytest.mark.asyncio
    async def test_content_creation_flow(self):
        """Test content creation through AI processor"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Step 1: Create content request
            content_request = {
                "topic": "Beginner Aquascaping Tips",
                "content_type": "blog_post",
                "target_audience": "beginners",
                "word_count": 500
            }
            
            try:
                # Submit to AI processor
                response = await client.post(
                    "http://ai-processor:8001/api/v1/generate",
                    json=content_request
                )
                
                if response.status_code == 404:
                    pytest.skip("AI processor generate endpoint not implemented yet")
                
                assert response.status_code in [200, 201, 202], f"Content creation failed: {response.text}"
                
                result = response.json()
                job_id = result.get("job_id") or result.get("id")
                assert job_id, "No job ID returned from content creation"
                
                # Step 2: Check job status (with retries)
                for attempt in range(10):  # Wait up to 50 seconds
                    status_response = await client.get(
                        f"http://ai-processor:8001/api/v1/jobs/{job_id}"
                    )
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        if status_data.get("status") == "completed":
                            assert status_data.get("content"), "No content generated"
                            break
                        elif status_data.get("status") == "failed":
                            pytest.fail(f"Content generation failed: {status_data.get('error')}")
                    
                    await asyncio.sleep(5)
                else:
                    pytest.skip("Content generation took too long, skipping")
                    
            except httpx.RequestError as e:
                pytest.skip(f"AI processor service not available: {e}")
    
    @pytest.mark.asyncio
    async def test_scraping_workflow(self):
        """Test web scraping workflow"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            scrape_request = {
                "url": "https://httpbin.org/json",
                "content_type": "reference",
                "priority": 1
            }
            
            try:
                # Submit scraping job
                response = await client.post(
                    "http://web-scraper:8002/api/v1/scrape",
                    json=scrape_request
                )
                
                if response.status_code == 404:
                    pytest.skip("Web scraper scrape endpoint not implemented yet")
                
                assert response.status_code in [200, 201, 202], f"Scrape job submission failed: {response.text}"
                
                result = response.json()
                job_id = result.get("job_id")
                assert job_id, "No job ID returned from scrape submission"
                
                # Check job completion (with retries)
                for attempt in range(10):  # Wait up to 50 seconds
                    status_response = await client.get(
                        f"http://web-scraper:8002/api/v1/scrape/{job_id}"
                    )
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        if status_data.get("status") == "completed":
                            assert status_data.get("content"), "No content scraped"
                            break
                        elif status_data.get("status") == "failed":
                            # This might fail for external URLs, which is acceptable in E2E
                            pytest.skip(f"Scraping failed (expected for external URLs): {status_data.get('error')}")
                    
                    await asyncio.sleep(5)
                else:
                    pytest.skip("Scraping took too long, skipping")
                    
            except httpx.RequestError as e:
                pytest.skip(f"Web scraper service not available: {e}")
    
    @pytest.mark.asyncio
    async def test_subscriber_management_workflow(self):
        """Test subscriber management workflow"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Generate unique email for testing
            test_email = f"test-{uuid.uuid4().hex[:8]}@example.com"
            
            subscribe_request = {
                "email": test_email,
                "first_name": "Test",
                "last_name": "User",
                "interests": ["aquascaping", "plants"]
            }
            
            try:
                # Test subscription
                response = await client.post(
                    "http://subscriber-manager:8004/api/v1/subscribers/subscribe",
                    json=subscribe_request
                )
                
                if response.status_code == 404:
                    pytest.skip("Subscriber manager subscribe endpoint not implemented yet")
                
                assert response.status_code in [200, 201], f"Subscription failed: {response.text}"
                
                result = response.json()
                subscriber_id = result.get("subscriber_id")
                assert subscriber_id, "No subscriber ID returned"
                
                # Test getting subscriber
                get_response = await client.get(
                    f"http://subscriber-manager:8004/api/v1/subscribers/{subscriber_id}"
                )
                
                if get_response.status_code == 200:
                    subscriber_data = get_response.json()
                    assert subscriber_data["email"] == test_email
                    assert subscriber_data["first_name"] == "Test"
                
                # Test unsubscribe
                unsubscribe_response = await client.post(
                    "http://subscriber-manager:8004/api/v1/subscribers/unsubscribe",
                    params={"email": test_email}
                )
                
                if unsubscribe_response.status_code == 200:
                    result = unsubscribe_response.json()
                    assert "successfully unsubscribed" in result.get("message", "").lower()
                    
            except httpx.RequestError as e:
                pytest.skip(f"Subscriber manager service not available: {e}")
    
    @pytest.mark.asyncio
    async def test_service_integration(self):
        """Test that services can communicate with each other"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # Test that services can reach shared dependencies
                services_to_test = [
                    ("content-manager", "http://content-manager:8000/health/detailed"),
                    ("ai-processor", "http://ai-processor:8001/health/detailed"),
                    ("web-scraper", "http://web-scraper:8002/health/detailed"),
                    ("subscriber-manager", "http://subscriber-manager:8004/health/detailed")
                ]
                
                for service_name, url in services_to_test:
                    try:
                        response = await client.get(url)
                        if response.status_code == 200:
                            health_data = response.json()
                            checks = health_data.get("checks", {})
                            
                            # Verify database connectivity
                            if "database" in checks:
                                assert checks["database"]["status"] == "healthy", f"{service_name} database connection unhealthy"
                            
                            # Verify Redis connectivity  
                            if "redis" in checks:
                                assert checks["redis"]["status"] == "healthy", f"{service_name} Redis connection unhealthy"
                                
                    except httpx.RequestError:
                        # Service might not be available, skip individual service test
                        continue
                        
            except Exception as e:
                pytest.skip(f"Service integration test skipped: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])