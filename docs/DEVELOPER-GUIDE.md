# AquaScene Content Engine - Developer Guide

**Version:** 1.0  
**Last Updated:** August 6, 2025  
**Target Audience:** Developers, DevOps Engineers, AI Agents

## Overview

This guide provides comprehensive instructions for developers working with the AquaScene Content Engine. Whether you're a human developer or an AI agent, this document will help you understand the system architecture, development workflows, and best practices.

## Table of Contents

1. [Development Environment Setup](#development-environment-setup)
2. [Architecture Deep Dive](#architecture-deep-dive)
3. [Service Development](#service-development)
4. [AI Integration](#ai-integration)
5. [Database Operations](#database-operations)
6. [Testing Framework](#testing-framework)
7. [Deployment and Operations](#deployment-and-operations)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best-practices)
10. [Contributing Guidelines](#contributing-guidelines)

## Development Environment Setup

### Prerequisites

```bash
# Required software
- Docker 20.10+
- Docker Compose 2.0+
- Python 3.11+
- Node.js 18+ (for admin dashboard)
- Git 2.30+

# Optional but recommended
- VS Code with Python extension
- Postman/Insomnia for API testing
- pgAdmin for database management
```

### Quick Start

1. **Clone and Setup**
   ```bash
   git clone <repository-url>
   cd aquascene-content-engine
   
   # Fix any dependency issues
   ./fix-dependencies.sh
   
   # Configure environment
   cp .env.example .env
   # Edit .env with your API keys and secrets
   ```

2. **Start Development Environment**
   ```bash
   # Start all services
   ./start-services.sh
   
   # Or start individually
   docker-compose up -d postgres redis minio
   docker-compose up -d content-manager ai-processor
   docker-compose up -d admin-dashboard
   ```

3. **Verify Setup**
   ```bash
   # Run health checks
   curl http://localhost:8000/health  # Content Manager
   curl http://localhost:8001/health  # AI Processor
   
   # Run full test suite
   ./run-full-test-suite.sh
   ```

### Development Tools Setup

#### IDE Configuration (VS Code)

Create `.vscode/settings.json`:
```json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests/"],
    "files.associations": {
        "*.yml": "yaml",
        "Dockerfile*": "dockerfile"
    }
}
```

#### Debug Configuration

Create `.vscode/launch.json`:
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "AI Processor",
            "type": "python",
            "request": "launch",
            "program": "services/ai-processor/src/main.py",
            "console": "integratedTerminal",
            "env": {
                "PYTHONPATH": "services/ai-processor/src"
            }
        },
        {
            "name": "Content Manager",
            "type": "python", 
            "request": "launch",
            "program": "services/content-manager/src/main.py",
            "console": "integratedTerminal"
        }
    ]
}
```

### Environment Variables

#### Required Configuration (.env)

```bash
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=content_engine
DB_USER=postgres
DB_PASSWORD=your_secure_password

# Redis Configuration  
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password

# AI Service APIs
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
OLLAMA_BASE_URL=http://localhost:11434

# Security
JWT_SECRET=your-jwt-secret-key
ENCRYPTION_KEY=your-32-byte-encryption-key

# Email Service
SENDGRID_API_KEY=SG.your-sendgrid-key

# Instagram Integration
INSTAGRAM_ACCESS_TOKEN=your-instagram-token
INSTAGRAM_PAGE_ID=your-page-id

# Monitoring
ENABLE_METRICS=true
LOG_LEVEL=INFO
```

#### Development vs Production

```bash
# Development overrides
DEBUG=true
LOG_LEVEL=DEBUG
ENABLE_DEBUG_ENDPOINTS=true
CORS_ALLOW_ALL=true

# Production settings
DEBUG=false
LOG_LEVEL=INFO
ENABLE_DEBUG_ENDPOINTS=false
CORS_ALLOW_ALL=false
```

## Architecture Deep Dive

### Service Architecture Pattern

Each service follows a consistent architecture pattern:

```
service/
├── src/
│   ├── api/                 # FastAPI route definitions
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── config/              # Configuration management
│   │   ├── __init__.py
│   │   └── settings.py
│   ├── database/            # Database models and connections
│   │   ├── __init__.py
│   │   └── connection.py
│   ├── models/              # Pydantic models
│   │   └── __init__.py
│   ├── services/            # Business logic
│   │   └── __init__.py
│   ├── utils/               # Utility functions
│   │   └── __init__.py
│   └── main.py             # Application entry point
├── tests/                   # Unit and integration tests
├── Dockerfile              # Container configuration
├── requirements.txt        # Python dependencies
└── README.md              # Service-specific documentation
```

### Inter-Service Communication

Services communicate via:
1. **REST APIs:** Primary communication method
2. **Database:** Shared data layer
3. **Redis:** Caching and real-time data
4. **Message Queue:** Async processing (planned)

```python
# Example service communication
import aiohttp

class ServiceClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
    
    async def call_service(self, endpoint: str, data: dict):
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}{endpoint}"
            async with session.post(url, json=data) as response:
                return await response.json()

# Usage
ai_client = ServiceClient("http://ai-processor:8001")
result = await ai_client.call_service("/generate", content_request)
```

## Service Development

### Creating a New Service

1. **Generate Service Structure**
   ```bash
   # Use service template
   cp -r services/template services/new-service
   cd services/new-service
   
   # Update service-specific files
   # - Update Dockerfile
   # - Update requirements.txt
   # - Update main.py
   ```

2. **Configure Service**
   ```python
   # src/config/settings.py
   from pydantic_settings import BaseSettings
   from pydantic import Field
   
   class Settings(BaseSettings):
       service_name: str = "new-service"
       host: str = Field(default="0.0.0.0", env="HOST")
       port: int = Field(default=8005, env="PORT")
       
       # Database
       database_url: str = Field(env="DATABASE_URL")
       redis_url: str = Field(env="REDIS_URL")
       
       class Config:
           env_file = ".env"
   
   settings = Settings()
   ```

3. **Create FastAPI Application**
   ```python
   # src/main.py
   from fastapi import FastAPI
   from .api import health_routes, service_routes
   from .config.settings import settings
   
   app = FastAPI(
       title=f"{settings.service_name} API",
       version="1.0.0"
   )
   
   # Include routers
   app.include_router(health_routes.router, prefix="/health")
   app.include_router(service_routes.router, prefix="/api/v1")
   
   if __name__ == "__main__":
       import uvicorn
       uvicorn.run(app, host=settings.host, port=settings.port)
   ```

4. **Add to Docker Compose**
   ```yaml
   # docker-compose.yml
   new-service:
     build: ./services/new-service
     ports:
       - "8005:8005"
     environment:
       - DATABASE_URL=${DATABASE_URL}
       - REDIS_URL=${REDIS_URL}
     depends_on:
       - postgres
       - redis
     networks:
       - content-engine
   ```

### AI Processor Service Development

The AI Processor is the core content generation service. Here's how to work with it:

#### Service Structure
```
ai-processor/
├── src/
│   ├── llm_clients/         # LLM integrations
│   │   ├── base_client.py   # Abstract base class
│   │   ├── openai_client.py # OpenAI integration
│   │   ├── anthropic_client.py # Anthropic integration
│   │   ├── ollama_client.py # Local Ollama integration
│   │   └── client_manager.py # LLM routing logic
│   ├── generators/          # Content generation
│   │   └── content_orchestrator.py
│   ├── validators/          # Quality assurance
│   │   ├── quality_validator.py
│   │   ├── fact_checker.py
│   │   └── brand_validator.py
│   ├── optimizers/          # Content optimization
│   │   ├── content_optimizer.py
│   │   ├── seo_optimizer.py
│   │   └── engagement_optimizer.py
│   └── knowledge/           # Aquascaping knowledge base
│       └── aquascaping_kb.py
```

#### Adding a New LLM Provider

1. **Create Provider Client**
   ```python
   # src/llm_clients/new_provider_client.py
   from .base_client import BaseLLMClient, LLMResponse
   import aiohttp
   
   class NewProviderClient(BaseLLMClient):
       def __init__(self, api_key: str, model: str = "default"):
           super().__init__("new_provider", model)
           self.api_key = api_key
           self.base_url = "https://api.newprovider.com"
       
       async def generate_content(self, prompt: str, **kwargs) -> LLMResponse:
           headers = {"Authorization": f"Bearer {self.api_key}"}
           data = {
               "model": self.model,
               "messages": [{"role": "user", "content": prompt}],
               **kwargs
           }
           
           async with aiohttp.ClientSession() as session:
               async with session.post(
                   f"{self.base_url}/completions",
                   headers=headers,
                   json=data
               ) as response:
                   result = await response.json()
                   
                   return LLMResponse(
                       content=result["choices"][0]["message"]["content"],
                       model=self.model,
                       provider=self.provider_name,
                       cost=self.calculate_cost(result),
                       metadata=result.get("metadata", {})
                   )
   ```

2. **Register in Client Manager**
   ```python
   # src/llm_clients/client_manager.py
   from .new_provider_client import NewProviderClient
   
   class LLMClientManager:
       def __init__(self):
           self.clients = {}
           self._register_clients()
       
       def _register_clients(self):
           # Existing clients...
           
           # New provider
           if settings.NEW_PROVIDER_API_KEY:
               self.clients["new_provider"] = NewProviderClient(
                   settings.NEW_PROVIDER_API_KEY
               )
   ```

#### Content Type Development

1. **Define Content Type**
   ```python
   # src/llm_clients/base_client.py
   from enum import Enum
   
   class ContentType(Enum):
       NEWSLETTER_ARTICLE = "newsletter_article"
       INSTAGRAM_CAPTION = "instagram_caption"
       # Add new type
       PRODUCT_COMPARISON = "product_comparison"
   ```

2. **Create Content Template**
   ```python
   # src/templates/product_comparison.py
   PRODUCT_COMPARISON_TEMPLATE = """
   Create a detailed comparison between {product_a} and {product_b} for aquascaping.
   
   Structure:
   1. Introduction
   2. Feature Comparison
   3. Pros and Cons
   4. Recommendation
   
   Target audience: {target_audience}
   Brand voice: {brand_voice}
   """
   ```

3. **Add Validation Rules**
   ```python
   # src/validators/quality_validator.py
   def _validate_product_comparison(self, content: str) -> ValidationScore:
       score = 0.0
       issues = []
       
       # Check for required sections
       required_sections = ["Introduction", "Feature Comparison", 
                          "Pros and Cons", "Recommendation"]
       for section in required_sections:
           if section.lower() in content.lower():
               score += 0.25
           else:
               issues.append(f"Missing section: {section}")
       
       # Check for balanced comparison
       if "both products" in content.lower() or "comparison" in content.lower():
           score += 0.2
       
       return ValidationScore(score, issues)
   ```

### Database Development

#### Database Schema Management

1. **Create Migration**
   ```sql
   -- infrastructure/database/migrations/001_create_tables.sql
   CREATE TABLE content_pieces (
       id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
       title VARCHAR(255) NOT NULL,
       content TEXT NOT NULL,
       content_type VARCHAR(50) NOT NULL,
       status VARCHAR(20) DEFAULT 'draft',
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
       updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );
   
   CREATE INDEX idx_content_pieces_type ON content_pieces(content_type);
   CREATE INDEX idx_content_pieces_status ON content_pieces(status);
   ```

2. **Create Models**
   ```python
   # services/content-manager/src/models/content.py
   from pydantic import BaseModel, Field
   from datetime import datetime
   from uuid import UUID
   from enum import Enum
   
   class ContentStatus(str, Enum):
       DRAFT = "draft"
       PUBLISHED = "published"
       ARCHIVED = "archived"
   
   class ContentPiece(BaseModel):
       id: UUID = Field(default_factory=lambda: uuid4())
       title: str = Field(..., max_length=255)
       content: str
       content_type: str
       status: ContentStatus = ContentStatus.DRAFT
       created_at: datetime = Field(default_factory=datetime.utcnow)
       updated_at: datetime = Field(default_factory=datetime.utcnow)
   ```

3. **Database Connection**
   ```python
   # src/database/connection.py
   import asyncpg
   from typing import Optional
   
   class DatabaseConnection:
       def __init__(self, connection_string: str):
           self.connection_string = connection_string
           self.pool: Optional[asyncpg.Pool] = None
       
       async def connect(self):
           self.pool = await asyncpg.create_pool(
               self.connection_string,
               min_size=5,
               max_size=20,
               command_timeout=60
           )
       
       async def execute(self, query: str, *args):
           async with self.pool.acquire() as connection:
               return await connection.execute(query, *args)
       
       async def fetch(self, query: str, *args):
           async with self.pool.acquire() as connection:
               return await connection.fetch(query, *args)
   ```

## AI Integration

### LLM Client Development

#### Base Client Pattern
```python
# src/llm_clients/base_client.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class LLMResponse:
    content: str
    model: str
    provider: str
    cost: float
    metadata: Dict[str, Any]

class BaseLLMClient(ABC):
    def __init__(self, provider_name: str, model: str):
        self.provider_name = provider_name
        self.model = model
    
    @abstractmethod
    async def generate_content(
        self, 
        prompt: str, 
        **kwargs
    ) -> LLMResponse:
        pass
    
    def calculate_cost(self, response_data: Dict) -> float:
        """Calculate the cost of the API call"""
        # Provider-specific cost calculation
        pass
    
    def format_prompt(self, content_type: str, **kwargs) -> str:
        """Format prompt based on content type"""
        # Template loading and formatting
        pass
```

#### Intelligent Routing
```python
# src/llm_clients/client_manager.py
class LLMClientManager:
    def __init__(self):
        self.clients = {}
        self.routing_strategy = "balanced"  # cost_optimized, quality_first, balanced
    
    async def generate_content(
        self, 
        content_type: str, 
        **kwargs
    ) -> LLMResponse:
        # Select best client based on strategy
        client = self._select_client(content_type, **kwargs)
        
        try:
            return await client.generate_content(**kwargs)
        except Exception as e:
            # Failover to backup client
            backup_client = self._get_backup_client(client)
            if backup_client:
                return await backup_client.generate_content(**kwargs)
            raise e
    
    def _select_client(self, content_type: str, **kwargs) -> BaseLLMClient:
        if self.routing_strategy == "cost_optimized":
            return self._get_cheapest_client()
        elif self.routing_strategy == "quality_first":
            return self._get_highest_quality_client(content_type)
        else:
            return self._get_balanced_client(content_type)
```

### Content Generation Pipeline

#### Content Orchestrator
```python
# src/generators/content_orchestrator.py
class ContentOrchestrator:
    def __init__(self):
        self.client_manager = LLMClientManager()
        self.quality_validator = QualityValidator()
        self.content_optimizer = ContentOptimizer()
        self.template_manager = TemplateManager()
    
    async def generate_content(
        self, 
        request: ContentRequest
    ) -> ContentResponse:
        # 1. Load and format template
        template = self.template_manager.get_template(request.content_type)
        prompt = template.format(**request.dict())
        
        # 2. Generate content
        llm_response = await self.client_manager.generate_content(
            content_type=request.content_type,
            prompt=prompt,
            **request.generation_params
        )
        
        # 3. Validate quality
        validation_result = await self.quality_validator.validate(
            content=llm_response.content,
            content_type=request.content_type
        )
        
        if not validation_result.is_valid:
            # Retry with improvements
            improved_prompt = self._improve_prompt(prompt, validation_result)
            llm_response = await self.client_manager.generate_content(
                prompt=improved_prompt,
                **request.generation_params
            )
        
        # 4. Optimize content
        optimized_content = await self.content_optimizer.optimize(
            content=llm_response.content,
            content_type=request.content_type,
            optimization_strategy=request.optimization_strategy
        )
        
        return ContentResponse(
            content=optimized_content,
            metadata=llm_response.metadata,
            quality_score=validation_result.score,
            cost=llm_response.cost
        )
```

### Batch Processing

#### Batch Processor Implementation
```python
# src/batch/batch_processor.py
import asyncio
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor

class BatchProcessor:
    def __init__(self, max_concurrent: int = 5):
        self.max_concurrent = max_concurrent
        self.orchestrator = ContentOrchestrator()
    
    async def process_batch(
        self, 
        requests: List[ContentRequest]
    ) -> BatchResponse:
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        # Process requests concurrently
        tasks = [
            self._process_with_semaphore(semaphore, request) 
            for request in requests
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Aggregate results
        successful = [r for r in results if not isinstance(r, Exception)]
        failed = [r for r in results if isinstance(r, Exception)]
        
        return BatchResponse(
            successful_count=len(successful),
            failed_count=len(failed),
            results=successful,
            errors=failed,
            total_cost=sum(r.cost for r in successful if hasattr(r, 'cost'))
        )
    
    async def _process_with_semaphore(
        self, 
        semaphore: asyncio.Semaphore, 
        request: ContentRequest
    ) -> ContentResponse:
        async with semaphore:
            return await self.orchestrator.generate_content(request)
```

## Testing Framework

### Unit Testing

#### Test Structure
```python
# tests/test_ai_processor.py
import pytest
from unittest.mock import AsyncMock, patch
from src.generators.content_orchestrator import ContentOrchestrator
from src.models.requests import ContentRequest

class TestContentOrchestrator:
    @pytest.fixture
    def orchestrator(self):
        return ContentOrchestrator()
    
    @pytest.fixture
    def sample_request(self):
        return ContentRequest(
            content_type="newsletter_article",
            topic="Aquarium lighting basics",
            target_audience="beginners",
            max_length=1500
        )
    
    @pytest.mark.asyncio
    async def test_generate_content_success(self, orchestrator, sample_request):
        # Mock dependencies
        with patch.object(orchestrator.client_manager, 'generate_content') as mock_generate:
            mock_generate.return_value = Mock(
                content="Generated content",
                cost=0.05,
                metadata={}
            )
            
            result = await orchestrator.generate_content(sample_request)
            
            assert result.content == "Generated content"
            assert result.cost == 0.05
            mock_generate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_content_validation_failure(self, orchestrator, sample_request):
        with patch.object(orchestrator.quality_validator, 'validate') as mock_validate:
            mock_validate.return_value = ValidationResult(
                is_valid=False,
                score=0.3,
                issues=["Content too short"]
            )
            
            # Should retry with improved prompt
            result = await orchestrator.generate_content(sample_request)
            assert mock_validate.call_count == 2  # Initial + retry
```

### Integration Testing

#### API Testing
```python
# tests/test_integration.py
import pytest
from httpx import AsyncClient
from src.main import app

@pytest.mark.asyncio
async def test_generate_content_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/generate", json={
            "content_type": "newsletter_article",
            "topic": "Beginner aquascaping",
            "target_audience": "beginners",
            "max_length": 1000
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "quality_score" in data
        assert "cost" in data

@pytest.mark.asyncio  
async def test_batch_processing_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/batch/generate", json={
            "requests": [
                {
                    "content_type": "newsletter_article",
                    "topic": "Plant care basics"
                },
                {
                    "content_type": "instagram_caption",
                    "topic": "Beautiful aquascape"
                }
            ],
            "processing_mode": "concurrent",
            "max_concurrent": 2
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["successful_count"] == 2
        assert len(data["results"]) == 2
```

### E2E Testing

#### System Testing
```python
# services/e2e-testing/tests/test_content_workflow.py
import pytest
import asyncio
from tests.utils.test_helpers import APIClient, DatabaseHelper

class TestContentWorkflow:
    @pytest.mark.asyncio
    async def test_complete_content_generation_workflow(self):
        # 1. Generate content via AI processor
        ai_client = APIClient("http://localhost:8001")
        generation_response = await ai_client.post("/generate", {
            "content_type": "newsletter_article",
            "topic": "CO2 systems for planted tanks",
            "target_audience": "intermediate"
        })
        
        assert generation_response.status_code == 200
        content_data = generation_response.json()
        
        # 2. Save content via content manager
        cm_client = APIClient("http://localhost:8000")
        save_response = await cm_client.post("/content", {
            "title": "CO2 Systems Guide",
            "content": content_data["content"],
            "content_type": "newsletter_article"
        })
        
        assert save_response.status_code == 201
        content_id = save_response.json()["id"]
        
        # 3. Verify in database
        db = DatabaseHelper()
        saved_content = await db.fetch_content(content_id)
        assert saved_content is not None
        assert saved_content["status"] == "draft"
        
        # 4. Publish content
        publish_response = await cm_client.patch(f"/content/{content_id}", {
            "status": "published"
        })
        
        assert publish_response.status_code == 200
        
        # 5. Verify published status
        updated_content = await db.fetch_content(content_id)
        assert updated_content["status"] == "published"
```

### Performance Testing

#### Load Testing
```python
# tests/performance/test_load.py
import asyncio
import time
import statistics
from typing import List

class LoadTester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = APIClient(base_url)
    
    async def test_concurrent_requests(
        self, 
        endpoint: str, 
        payload: dict, 
        concurrent_users: int = 10,
        requests_per_user: int = 5
    ) -> dict:
        results = []
        
        async def user_simulation():
            user_results = []
            for _ in range(requests_per_user):
                start_time = time.time()
                try:
                    response = await self.client.post(endpoint, payload)
                    end_time = time.time()
                    user_results.append({
                        "status_code": response.status_code,
                        "response_time": end_time - start_time,
                        "success": 200 <= response.status_code < 300
                    })
                except Exception as e:
                    end_time = time.time()
                    user_results.append({
                        "status_code": 0,
                        "response_time": end_time - start_time,
                        "success": False,
                        "error": str(e)
                    })
            return user_results
        
        # Run concurrent user simulations
        tasks = [user_simulation() for _ in range(concurrent_users)]
        user_results = await asyncio.gather(*tasks)
        
        # Flatten results
        for user_result in user_results:
            results.extend(user_result)
        
        # Calculate statistics
        response_times = [r["response_time"] for r in results]
        success_count = sum(1 for r in results if r["success"])
        
        return {
            "total_requests": len(results),
            "successful_requests": success_count,
            "success_rate": success_count / len(results) * 100,
            "avg_response_time": statistics.mean(response_times),
            "p95_response_time": statistics.quantiles(response_times, n=20)[18],
            "p99_response_time": statistics.quantiles(response_times, n=100)[98],
            "max_response_time": max(response_times),
            "min_response_time": min(response_times)
        }

# Usage in tests
@pytest.mark.performance
@pytest.mark.asyncio
async def test_ai_processor_load():
    load_tester = LoadTester("http://localhost:8001")
    
    results = await load_tester.test_concurrent_requests(
        endpoint="/generate",
        payload={
            "content_type": "newsletter_article",
            "topic": "Aquascaping basics",
            "max_length": 1000
        },
        concurrent_users=20,
        requests_per_user=3
    )
    
    # Performance assertions
    assert results["success_rate"] >= 95.0
    assert results["p95_response_time"] <= 10.0  # 10 seconds
    assert results["avg_response_time"] <= 5.0   # 5 seconds average
```

## Deployment and Operations

### Docker Development

#### Service Dockerfile Template
```dockerfile
# services/template/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY tests/ ./tests/

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start application
CMD ["python", "-m", "src.main"]
```

#### Docker Compose Override for Development
```yaml
# docker-compose.override.yml (for development)
version: '3.8'

services:
  ai-processor:
    build:
      context: ./services/ai-processor
      dockerfile: Dockerfile.dev
    volumes:
      - ./services/ai-processor/src:/app/src:ro
      - ./services/ai-processor/tests:/app/tests:ro
    environment:
      - DEBUG=true
      - LOG_LEVEL=DEBUG
      - RELOAD=true
    command: python -m uvicorn src.main:app --host 0.0.0.0 --port 8001 --reload
  
  content-manager:
    volumes:
      - ./services/content-manager/src:/app/src:ro
    environment:
      - DEBUG=true
      - LOG_LEVEL=DEBUG
```

### Monitoring Integration

#### Prometheus Metrics
```python
# src/monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import time
from functools import wraps

# Metrics definitions
REQUEST_COUNT = Counter(
    'http_requests_total', 
    'Total HTTP requests', 
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

CONTENT_GENERATION_COUNT = Counter(
    'content_generation_total',
    'Total content pieces generated',
    ['content_type', 'provider']
)

CONTENT_QUALITY_SCORE = Gauge(
    'content_quality_score',
    'Average content quality score',
    ['content_type']
)

def track_requests(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            REQUEST_COUNT.labels(
                method='POST', 
                endpoint='/generate', 
                status='200'
            ).inc()
            return result
        except Exception as e:
            REQUEST_COUNT.labels(
                method='POST', 
                endpoint='/generate', 
                status='500'
            ).inc()
            raise
        finally:
            REQUEST_DURATION.labels(
                method='POST', 
                endpoint='/generate'
            ).observe(time.time() - start_time)
    return wrapper

# Usage in FastAPI
@app.post("/generate")
@track_requests
async def generate_content(request: ContentRequest):
    result = await orchestrator.generate_content(request)
    
    # Track business metrics
    CONTENT_GENERATION_COUNT.labels(
        content_type=request.content_type,
        provider=result.provider
    ).inc()
    
    CONTENT_QUALITY_SCORE.labels(
        content_type=request.content_type
    ).set(result.quality_score)
    
    return result
```

#### Health Checks
```python
# src/api/health_routes.py
from fastapi import APIRouter, Depends
from src.database.connection import get_db_health
from src.monitoring.health_checker import HealthChecker

router = APIRouter()

@router.get("/health")
async def health_check():
    checker = HealthChecker()
    
    checks = await asyncio.gather(
        checker.check_database(),
        checker.check_redis(),
        checker.check_external_apis(),
        return_exceptions=True
    )
    
    database_healthy = not isinstance(checks[0], Exception)
    redis_healthy = not isinstance(checks[1], Exception)
    apis_healthy = not isinstance(checks[2], Exception)
    
    overall_healthy = all([database_healthy, redis_healthy, apis_healthy])
    
    return {
        "status": "healthy" if overall_healthy else "unhealthy",
        "checks": {
            "database": "healthy" if database_healthy else "unhealthy",
            "redis": "healthy" if redis_healthy else "unhealthy",
            "external_apis": "healthy" if apis_healthy else "unhealthy"
        },
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/ready")
async def readiness_check():
    # More strict check for readiness
    return {"status": "ready"}

@router.get("/live")  
async def liveness_check():
    # Basic liveness check
    return {"status": "alive"}
```

### CI/CD Pipeline

#### GitHub Actions Workflow
```yaml
# .github/workflows/ci-cd.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r services/ai-processor/requirements.txt
        pip install pytest pytest-cov pytest-asyncio
    
    - name: Run tests
      run: |
        pytest services/ai-processor/tests/ -v --cov=src --cov-report=xml
      env:
        DATABASE_URL: postgresql://postgres:test@localhost:5432/test_db
        REDIS_URL: redis://localhost:6379
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml

  build:
    needs: test
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3
    
    - name: Log in to Container Registry
      uses: docker/login-action@v3
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Build and push AI Processor
      uses: docker/build-push-action@v5
      with:
        context: ./services/ai-processor
        push: true
        tags: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}/ai-processor:${{ github.sha }}
        cache-from: type=gha
        cache-to: type=gha,mode=max

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - name: Deploy to staging
      run: |
        echo "Deploying to staging environment"
        # Add deployment commands here
```

## Best Practices

### Code Quality

#### Python Code Standards
```python
# Use type hints everywhere
from typing import List, Dict, Optional, Union
from pydantic import BaseModel

async def generate_content(
    request: ContentRequest,
    options: Optional[Dict[str, Any]] = None
) -> ContentResponse:
    """Generate content based on request parameters.
    
    Args:
        request: Content generation request
        options: Optional generation parameters
    
    Returns:
        Generated content response
    
    Raises:
        ValidationError: If request validation fails
        GenerationError: If content generation fails
    """
    pass

# Use dataclasses/Pydantic for structured data
class ContentRequest(BaseModel):
    content_type: str = Field(..., description="Type of content to generate")
    topic: str = Field(..., min_length=5, max_length=200)
    target_audience: str = Field(default="general")
    
    class Config:
        schema_extra = {
            "example": {
                "content_type": "newsletter_article",
                "topic": "Beginner aquascaping tips",
                "target_audience": "beginners"
            }
        }
```

#### Error Handling
```python
# Custom exceptions
class ContentEngineError(Exception):
    """Base exception for content engine errors"""
    pass

class ValidationError(ContentEngineError):
    """Raised when content validation fails"""
    pass

class GenerationError(ContentEngineError):
    """Raised when content generation fails"""
    pass

# Comprehensive error handling
async def generate_content(request: ContentRequest) -> ContentResponse:
    try:
        # Validate request
        if not request.topic.strip():
            raise ValidationError("Topic cannot be empty")
        
        # Generate content
        result = await llm_client.generate(request)
        
        # Validate result
        if not result.content:
            raise GenerationError("No content generated")
        
        return result
    
    except ValidationError:
        logger.warning(f"Validation error for request: {request}")
        raise
    
    except GenerationError as e:
        logger.error(f"Generation failed: {e}")
        # Implement retry logic or fallback
        raise
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise GenerationError(f"Content generation failed: {str(e)}")
```

#### Async Best Practices
```python
# Use async context managers
class AsyncLLMClient:
    async def __aenter__(self):
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()

# Usage
async with AsyncLLMClient() as client:
    result = await client.generate_content(request)

# Proper resource management
async def batch_process(requests: List[ContentRequest]) -> List[ContentResponse]:
    semaphore = asyncio.Semaphore(5)  # Limit concurrency
    
    async def process_single(request):
        async with semaphore:
            return await generate_content(request)
    
    return await asyncio.gather(*[process_single(req) for req in requests])
```

### API Design

#### RESTful Endpoints
```python
# Consistent URL patterns
/api/v1/content              # GET, POST
/api/v1/content/{id}         # GET, PUT, DELETE
/api/v1/content/{id}/publish # POST
/api/v1/generate             # POST
/api/v1/batch/generate       # POST

# Standard HTTP status codes
200 OK - Successful GET, PUT
201 Created - Successful POST
204 No Content - Successful DELETE
400 Bad Request - Validation error
401 Unauthorized - Authentication required
403 Forbidden - Authorization failed
404 Not Found - Resource not found
429 Too Many Requests - Rate limit exceeded
500 Internal Server Error - Server error
```

#### Response Format Consistency
```python
# Standard response wrapper
class APIResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    meta: Dict[str, Any] = Field(default_factory=dict)

# Success response
{
    "success": true,
    "data": {...},
    "error": null,
    "meta": {
        "version": "1.0",
        "timestamp": "2025-08-06T12:00:00Z",
        "request_id": "req-123"
    }
}

# Error response
{
    "success": false,
    "data": null,
    "error": "Validation failed: topic is required",
    "meta": {
        "error_code": "VALIDATION_ERROR",
        "timestamp": "2025-08-06T12:00:00Z"
    }
}
```

### Performance Optimization

#### Caching Strategy
```python
# Redis caching decorator
import functools
import json
from typing import Any

def cache_result(expiry_seconds: int = 3600):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Create cache key
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            cached = await redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Store in cache
            await redis_client.setex(
                cache_key, 
                expiry_seconds, 
                json.dumps(result, default=str)
            )
            
            return result
        return wrapper
    return decorator

# Usage
@cache_result(expiry_seconds=1800)  # 30 minutes
async def generate_content(request: ContentRequest) -> ContentResponse:
    # Expensive content generation
    pass
```

#### Database Optimization
```python
# Connection pooling
class DatabaseManager:
    def __init__(self, connection_string: str, pool_size: int = 20):
        self.connection_string = connection_string
        self.pool_size = pool_size
        self.pool = None
    
    async def initialize(self):
        self.pool = await asyncpg.create_pool(
            self.connection_string,
            min_size=5,
            max_size=self.pool_size,
            command_timeout=60
        )
    
    async def execute_query(self, query: str, *args):
        async with self.pool.acquire() as connection:
            return await connection.fetch(query, *args)

# Batch operations
async def batch_insert_content(content_pieces: List[ContentPiece]):
    values = [
        (piece.title, piece.content, piece.content_type)
        for piece in content_pieces
    ]
    
    query = """
        INSERT INTO content_pieces (title, content, content_type)
        VALUES ($1, $2, $3)
    """
    
    async with db.pool.acquire() as connection:
        await connection.executemany(query, values)
```

## Troubleshooting

### Common Development Issues

#### Service Startup Problems
```bash
# Check port conflicts
lsof -ti :8001
netstat -tulpn | grep :8001

# Check Docker status
docker ps -a
docker logs ai-processor

# Check environment variables
printenv | grep -E "(DATABASE_URL|REDIS_URL|.*_API_KEY)"
```

#### Database Connection Issues
```bash
# Test PostgreSQL connection
docker exec -it postgres psql -U postgres -d content_engine -c "SELECT 1;"

# Test Redis connection
docker exec -it redis redis-cli ping

# Check connection strings
echo $DATABASE_URL
echo $REDIS_URL
```

#### AI Service Issues
```python
# Test LLM clients individually
from src.llm_clients.openai_client import OpenAIClient

async def test_openai():
    client = OpenAIClient(api_key="your-key")
    response = await client.generate_content("Test prompt")
    print(response)

# Check API key validity
import openai
openai.api_key = "your-key"
try:
    models = openai.Model.list()
    print("OpenAI API key is valid")
except:
    print("OpenAI API key is invalid")
```

### Debugging Tools

#### Logging Configuration
```python
# src/utils/logging.py
import logging
import sys
from pythonjsonlogger import jsonlogger

def setup_logging(level: str = "INFO"):
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level))
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(name)s %(levelname)s %(message)s"
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

# Usage in services
logger = setup_logging(os.getenv("LOG_LEVEL", "INFO"))
```

#### Development Debugging
```python
# Add debug endpoints (development only)
if settings.DEBUG:
    @app.get("/debug/status")
    async def debug_status():
        return {
            "service": "ai-processor",
            "version": "1.0.0",
            "environment": settings.ENVIRONMENT,
            "database_connected": await db.health_check(),
            "redis_connected": await redis.ping(),
            "llm_clients": list(client_manager.clients.keys())
        }
    
    @app.get("/debug/config")
    async def debug_config():
        return {
            key: value for key, value in settings.dict().items()
            if not key.endswith("_KEY") and not key.endswith("_SECRET")
        }
```

## Contributing Guidelines

### Development Workflow

1. **Fork and Clone**
   ```bash
   git clone https://github.com/your-username/aquascene-content-engine.git
   cd aquascene-content-engine
   ```

2. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make Changes**
   - Follow code style guidelines
   - Add tests for new functionality
   - Update documentation

4. **Test Changes**
   ```bash
   # Run unit tests
   pytest services/ai-processor/tests/
   
   # Run integration tests
   ./run-full-test-suite.sh
   
   # Check code quality
   black services/ai-processor/src/
   flake8 services/ai-processor/src/
   ```

5. **Submit Pull Request**
   - Clear description of changes
   - Link to related issues
   - Include test results

### Code Review Checklist

- [ ] Code follows project style guidelines
- [ ] Tests added for new functionality  
- [ ] Documentation updated
- [ ] No security vulnerabilities introduced
- [ ] Performance impact considered
- [ ] Error handling implemented
- [ ] Logging added for debugging

### Release Process

1. **Version Bumping**
   ```bash
   # Update version in relevant files
   # services/*/src/__init__.py
   # docker-compose.yml tags
   ```

2. **Testing**
   ```bash
   # Full test suite
   ./run-full-test-suite.sh
   
   # Performance testing
   pytest tests/performance/
   ```

3. **Documentation**
   - Update CHANGELOG.md
   - Update README.md
   - Update API documentation

4. **Deployment**
   ```bash
   # Tag release
   git tag -a v1.1.0 -m "Release v1.1.0"
   git push origin v1.1.0
   
   # Deploy to staging
   docker-compose -f docker-compose.staging.yml up -d
   
   # Deploy to production (after validation)
   docker-compose -f docker-compose.production.yml up -d
   ```

---

This guide provides comprehensive instructions for developers working with the AquaScene Content Engine. For specific service documentation, refer to the individual README files in each service directory.

**Next Steps:**
1. Set up your development environment
2. Run the test suite to verify setup
3. Start with small changes to familiarize yourself with the codebase
4. Join our development discussions for questions and guidance

**Document Status:** Complete ✅  
**Last Updated:** August 6, 2025  
**Maintainer:** AquaScene Development Team