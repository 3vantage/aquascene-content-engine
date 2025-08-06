"""
AI Content Processor Service

Main entry point for the AI content generation service.
Provides FastAPI web interface and coordinates all AI processing components.
"""

import asyncio
import os
from contextlib import asynccontextmanager
from typing import Dict, List, Optional, Any

import structlog
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .config.settings import Settings, get_settings
from .llm_clients.client_manager import LLMClientManager, RoutingStrategy
from .llm_clients.base_client import LLMConfig, ModelType, ContentType
from .generators.content_orchestrator import ContentOrchestrator, ContentRequest, GenerationPriority
from .knowledge.aquascaping_kb import AquascapingKnowledgeBase
from .validators.quality_validator import QualityValidator
from .validators.brand_validator import BrandValidator
from .validators.fact_checker import FactChecker
from .validators.readability_checker import ReadabilityChecker
from .templates.template_manager import TemplateManager
from .optimizers.content_optimizer import ContentOptimizer, OptimizationStrategy
from .batch.batch_processor import BatchProcessor, BatchJob, ProcessingMode
from .monitoring.service_monitor import ServiceMonitor

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


# Service components (initialized in lifespan)
llm_manager: Optional[LLMClientManager] = None
content_orchestrator: Optional[ContentOrchestrator] = None
batch_processor: Optional[BatchProcessor] = None
service_monitor: Optional[ServiceMonitor] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global llm_manager, content_orchestrator, batch_processor, service_monitor
    
    settings = get_settings()
    
    try:
        # Initialize components
        logger.info("Initializing AI Content Processor Service")
        
        # Initialize LLM clients
        llm_configs = {}
        
        if settings.openai_api_key:
            llm_configs["openai"] = LLMConfig(
                model=ModelType.OPENAI_GPT4_MINI,
                api_key=settings.openai_api_key,
                temperature=0.7,
                max_tokens=2000
            )
        
        if settings.anthropic_api_key:
            llm_configs["anthropic"] = LLMConfig(
                model=ModelType.CLAUDE_SONNET,
                api_key=settings.anthropic_api_key,
                temperature=0.7,
                max_tokens=2000
            )
        
        if settings.google_api_key:
            llm_configs["gemini"] = LLMConfig(
                model=ModelType.GEMINI_PRO,
                api_key=settings.google_api_key,
                temperature=0.7,
                max_tokens=2000
            )
        
        if settings.ollama_base_url:
            llm_configs["ollama"] = LLMConfig(
                model=ModelType.OLLAMA_LLAMA3,
                base_url=settings.ollama_base_url,
                temperature=0.7,
                max_tokens=2000
            )
        
        if not llm_configs:
            raise RuntimeError("No LLM providers configured")
        
        llm_manager = LLMClientManager(llm_configs)
        
        # Initialize knowledge base
        knowledge_base = AquascapingKnowledgeBase()
        
        # Initialize validators
        brand_validator = BrandValidator()
        fact_checker = FactChecker(knowledge_base)
        readability_checker = ReadabilityChecker()
        quality_validator = QualityValidator(
            knowledge_base, brand_validator, fact_checker, readability_checker
        )
        
        # Initialize template manager
        template_manager = TemplateManager()
        
        # Initialize content optimizer
        content_optimizer = ContentOptimizer()
        
        # Initialize content orchestrator
        content_orchestrator = ContentOrchestrator(
            llm_manager=llm_manager,
            knowledge_base=knowledge_base,
            quality_validator=quality_validator,
            template_manager=template_manager,
            content_optimizer=content_optimizer
        )
        
        # Initialize batch processor
        batch_processor = BatchProcessor(content_orchestrator)
        
        # Initialize service monitor
        service_monitor = ServiceMonitor(
            llm_manager=llm_manager,
            content_orchestrator=content_orchestrator,
            batch_processor=batch_processor
        )
        
        # Start services
        await content_orchestrator.start_workers()
        await batch_processor.start()
        await service_monitor.start()
        
        logger.info("AI Content Processor Service initialized successfully")
        
        yield
        
    except Exception as e:
        logger.error("Failed to initialize service", error=str(e))
        raise
    
    finally:
        # Cleanup
        logger.info("Shutting down AI Content Processor Service")
        
        if service_monitor:
            await service_monitor.stop()
        
        if batch_processor:
            await batch_processor.stop()
        
        if content_orchestrator:
            await content_orchestrator.stop_workers()
        
        if llm_manager:
            await llm_manager.close_all()
        
        logger.info("AI Content Processor Service shutdown complete")


# FastAPI app
app = FastAPI(
    title="AI Content Processor",
    description="AI-powered content generation service for aquascaping content",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class ContentGenerationRequest(BaseModel):
    content_type: str = Field(..., description="Type of content to generate")
    topic: str = Field(..., description="Topic or subject for the content")
    requirements: Dict[str, Any] = Field(default_factory=dict, description="Content requirements")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")
    preferred_provider: Optional[str] = Field(None, description="Preferred LLM provider")
    template_name: Optional[str] = Field(None, description="Template to use")
    target_audience: Optional[str] = Field(None, description="Target audience")
    seo_keywords: List[str] = Field(default_factory=list, description="SEO keywords")
    brand_voice: Optional[str] = Field(None, description="Brand voice to use")
    max_length: Optional[int] = Field(None, description="Maximum content length")
    additional_instructions: Optional[str] = Field(None, description="Additional instructions")
    priority: str = Field("normal", description="Generation priority")
    optimize_content: bool = Field(True, description="Apply content optimization")
    optimization_strategy: str = Field("balanced", description="Optimization strategy")


class BatchGenerationRequest(BaseModel):
    name: str = Field(..., description="Batch job name")
    requests: List[ContentGenerationRequest] = Field(..., description="Content requests")
    processing_mode: str = Field("concurrent", description="Processing mode")
    max_concurrent: int = Field(5, description="Maximum concurrent requests")
    priority: str = Field("normal", description="Batch priority")


class ContentResponse(BaseModel):
    id: str
    content: str
    content_type: str
    quality_score: Optional[float]
    optimization_results: Dict[str, Any]
    llm_response: Dict[str, Any]
    status: str
    created_at: float
    completed_at: Optional[float]


class BatchJobResponse(BaseModel):
    id: str
    name: str
    status: str
    total_requests: int
    completed_requests: int
    failed_requests: int
    progress_percent: float
    created_at: float
    started_at: Optional[float]
    completed_at: Optional[float]


# API endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    if not llm_manager or not content_orchestrator:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    # Check LLM availability
    health_status = {}
    for provider, client in llm_manager.clients.items():
        try:
            is_available = await client.is_available()
            health_status[provider] = "healthy" if is_available else "unavailable"
        except Exception as e:
            health_status[provider] = f"error: {str(e)}"
    
    return {
        "status": "healthy",
        "llm_providers": health_status,
        "workers_running": content_orchestrator.workers_running,
        "active_requests": len(content_orchestrator.active_requests)
    }


@app.get("/stats")
async def get_statistics():
    """Get service statistics"""
    if not content_orchestrator or not batch_processor or not llm_manager:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    return {
        "content_generation": content_orchestrator.get_stats(),
        "batch_processing": batch_processor.get_statistics(),
        "llm_performance": llm_manager.get_performance_stats()
    }


@app.post("/generate", response_model=ContentResponse)
async def generate_content(request: ContentGenerationRequest, background_tasks: BackgroundTasks):
    """Generate a single piece of content"""
    if not content_orchestrator:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    try:
        # Convert request to ContentRequest
        content_request = ContentRequest(
            id=f"single-{asyncio.get_event_loop().time()}",
            content_type=ContentType(request.content_type),
            topic=request.topic,
            requirements=request.requirements,
            context=request.context,
            priority=GenerationPriority(request.priority.upper()),
            preferred_provider=request.preferred_provider,
            template_name=request.template_name,
            target_audience=request.target_audience,
            seo_keywords=request.seo_keywords,
            brand_voice=request.brand_voice,
            max_length=request.max_length,
            additional_instructions=request.additional_instructions
        )
        
        # Generate content
        result = await content_orchestrator.generate_content(content_request)
        
        # Apply optimization if requested
        optimization_results = {}
        if request.optimize_content and result.generated_content:
            optimizer = ContentOptimizer()
            opt_result = await optimizer.optimize_content(
                content=result.generated_content,
                content_type=result.content_type,
                seo_keywords=request.seo_keywords,
                target_audience=request.target_audience,
                optimization_strategy=OptimizationStrategy(request.optimization_strategy.upper())
            )
            optimization_results = {
                "optimizations_applied": opt_result.optimizations_applied,
                "scores": opt_result.scores,
                "suggestions": opt_result.suggestions
            }
            
            # Use optimized content if available
            if opt_result.optimized_content:
                result.generated_content = opt_result.optimized_content
        
        return ContentResponse(
            id=result.id,
            content=result.generated_content or "",
            content_type=result.content_type.value,
            quality_score=result.quality_score,
            optimization_results=optimization_results,
            llm_response={
                "model_used": result.llm_response.model_used if result.llm_response else "",
                "provider": result.llm_response.provider if result.llm_response else "",
                "tokens_used": result.llm_response.tokens_used if result.llm_response else 0,
                "cost_estimate": result.llm_response.cost_estimate if result.llm_response else 0.0
            },
            status=result.status.value,
            created_at=result.created_at or 0,
            completed_at=result.completed_at
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Content generation error", error=str(e))
        raise HTTPException(status_code=500, detail="Content generation failed")


@app.post("/batch/generate", response_model=BatchJobResponse)
async def generate_batch_content(request: BatchGenerationRequest):
    """Generate multiple pieces of content in batch"""
    if not batch_processor:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    try:
        # Convert requests to content specs
        content_specs = []
        for req in request.requests:
            spec = {
                "content_type": req.content_type,
                "topic": req.topic,
                "requirements": req.requirements,
                "context": req.context,
                "preferred_provider": req.preferred_provider,
                "template_name": req.template_name,
                "target_audience": req.target_audience,
                "seo_keywords": req.seo_keywords,
                "brand_voice": req.brand_voice,
                "max_length": req.max_length,
                "additional_instructions": req.additional_instructions
            }
            content_specs.append(spec)
        
        # Create batch job
        job_id = await batch_processor.create_content_generation_job(
            name=request.name,
            content_specs=content_specs,
            processing_mode=ProcessingMode(request.processing_mode.upper()),
            max_concurrent=request.max_concurrent,
            priority=GenerationPriority(request.priority.upper())
        )
        
        # Get job status
        job_status = await batch_processor.get_job_status(job_id)
        if not job_status:
            raise HTTPException(status_code=500, detail="Failed to create batch job")
        
        return BatchJobResponse(**job_status)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Batch generation error", error=str(e))
        raise HTTPException(status_code=500, detail="Batch generation failed")


@app.get("/batch/{job_id}", response_model=BatchJobResponse)
async def get_batch_job_status(job_id: str):
    """Get batch job status"""
    if not batch_processor:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    job_status = await batch_processor.get_job_status(job_id)
    if not job_status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return BatchJobResponse(**job_status)


@app.get("/batch/{job_id}/results")
async def get_batch_job_results(job_id: str):
    """Get batch job results"""
    if not batch_processor:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    results = await batch_processor.get_job_results(job_id)
    if results is None:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Convert results to response format
    response_results = []
    for result in results:
        response_results.append({
            "id": result.id,
            "content": result.generated_content or "",
            "content_type": result.content_type.value,
            "quality_score": result.quality_score,
            "status": result.status.value,
            "error_message": result.error_message
        })
    
    return {"job_id": job_id, "results": response_results}


@app.post("/batch/{job_id}/cancel")
async def cancel_batch_job(job_id: str):
    """Cancel a batch job"""
    if not batch_processor:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    success = await batch_processor.cancel_job(job_id)
    if not success:
        raise HTTPException(status_code=404, detail="Job not found or cannot be cancelled")
    
    return {"message": "Job cancelled successfully"}


@app.get("/templates")
async def get_available_templates():
    """Get available content templates"""
    if not content_orchestrator:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    templates = content_orchestrator.template_manager.get_available_templates()
    return {"templates": templates}


@app.get("/knowledge/stats")
async def get_knowledge_base_stats():
    """Get knowledge base statistics"""
    if not content_orchestrator:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    stats = content_orchestrator.knowledge_base.get_stats()
    return {"knowledge_base": stats}


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )