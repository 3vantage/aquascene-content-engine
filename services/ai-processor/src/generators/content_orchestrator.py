"""
Content Generation Orchestrator

Coordinates content generation across different types and formats,
manages workflow, and ensures quality and consistency.
"""

import asyncio
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import structlog

from ..llm_clients.client_manager import LLMClientManager
from ..llm_clients.base_client import ContentType, LLMResponse
from ..knowledge.aquascaping_kb import AquascapingKnowledgeBase
from ..validators.quality_validator import QualityValidator
from ..templates.template_manager import TemplateManager
from ..optimizers.content_optimizer import ContentOptimizer

logger = structlog.get_logger()


class GenerationPriority(Enum):
    """Priority levels for content generation requests"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


class GenerationStatus(Enum):
    """Status of content generation requests"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    GENERATED = "generated"
    VALIDATED = "validated"
    OPTIMIZED = "optimized"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ContentRequest:
    """Content generation request"""
    id: str
    content_type: ContentType
    topic: str
    requirements: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    priority: GenerationPriority = GenerationPriority.NORMAL
    preferred_provider: Optional[str] = None
    template_name: Optional[str] = None
    target_audience: Optional[str] = None
    seo_keywords: List[str] = field(default_factory=list)
    brand_voice: Optional[str] = None
    max_length: Optional[int] = None
    additional_instructions: Optional[str] = None
    
    # Generated fields
    status: GenerationStatus = GenerationStatus.PENDING
    generated_content: Optional[str] = None
    llm_response: Optional[LLMResponse] = None
    quality_score: Optional[float] = None
    optimization_results: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[float] = None
    completed_at: Optional[float] = None
    error_message: Optional[str] = None


@dataclass
class BatchRequest:
    """Batch content generation request"""
    id: str
    requests: List[ContentRequest]
    max_concurrent: int = 5
    stop_on_error: bool = False
    priority: GenerationPriority = GenerationPriority.NORMAL
    
    # Status tracking
    completed_count: int = 0
    failed_count: int = 0
    total_count: int = 0
    
    def __post_init__(self):
        self.total_count = len(self.requests)


class ContentOrchestrator:
    """Orchestrates content generation workflow"""
    
    def __init__(
        self,
        llm_manager: LLMClientManager,
        knowledge_base: AquascapingKnowledgeBase,
        quality_validator: QualityValidator,
        template_manager: TemplateManager,
        content_optimizer: ContentOptimizer
    ):
        self.llm_manager = llm_manager
        self.knowledge_base = knowledge_base
        self.quality_validator = quality_validator
        self.template_manager = template_manager
        self.content_optimizer = content_optimizer
        
        # Request queues by priority
        self.request_queues = {
            GenerationPriority.URGENT: asyncio.Queue(),
            GenerationPriority.HIGH: asyncio.Queue(),
            GenerationPriority.NORMAL: asyncio.Queue(),
            GenerationPriority.LOW: asyncio.Queue()
        }
        
        # Active requests tracking
        self.active_requests: Dict[str, ContentRequest] = {}
        self.batch_requests: Dict[str, BatchRequest] = {}
        
        # Worker management
        self.workers_running = False
        self.worker_tasks: List[asyncio.Task] = []
        self.max_concurrent_workers = 3
        
        # Performance tracking
        self.generation_stats = {
            "total_requests": 0,
            "successful_generations": 0,
            "failed_generations": 0,
            "average_generation_time": 0.0,
            "content_type_stats": {}
        }
    
    async def start_workers(self) -> None:
        """Start content generation workers"""
        if self.workers_running:
            return
            
        self.workers_running = True
        
        for i in range(self.max_concurrent_workers):
            worker_task = asyncio.create_task(self._content_worker(f"worker-{i}"))
            self.worker_tasks.append(worker_task)
        
        logger.info(f"Started {self.max_concurrent_workers} content generation workers")
    
    async def stop_workers(self) -> None:
        """Stop all content generation workers"""
        self.workers_running = False
        
        # Cancel all worker tasks
        for task in self.worker_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self.worker_tasks:
            await asyncio.gather(*self.worker_tasks, return_exceptions=True)
        
        self.worker_tasks.clear()
        logger.info("Stopped all content generation workers")
    
    async def generate_content(self, request: ContentRequest) -> ContentRequest:
        """Generate a single piece of content"""
        import time
        
        request.created_at = time.time()
        request.status = GenerationStatus.IN_PROGRESS
        self.active_requests[request.id] = request
        
        logger.info(
            "Starting content generation",
            request_id=request.id,
            content_type=request.content_type.value,
            topic=request.topic
        )
        
        try:
            # Step 1: Prepare context and prompts
            context = await self._prepare_generation_context(request)
            
            # Step 2: Generate content using LLM
            llm_response = await self._generate_with_llm(request, context)
            request.llm_response = llm_response
            request.generated_content = llm_response.content
            request.status = GenerationStatus.GENERATED
            
            # Step 3: Validate quality
            quality_score = await self._validate_content(request)
            request.quality_score = quality_score
            request.status = GenerationStatus.VALIDATED
            
            # Step 4: Optimize content
            optimization_results = await self._optimize_content(request)
            request.optimization_results = optimization_results
            request.status = GenerationStatus.OPTIMIZED
            
            # Step 5: Final processing
            await self._finalize_content(request)
            request.status = GenerationStatus.COMPLETED
            request.completed_at = time.time()
            
            # Update statistics
            self._update_generation_stats(request, success=True)
            
            logger.info(
                "Content generation completed",
                request_id=request.id,
                quality_score=quality_score,
                generation_time=request.completed_at - request.created_at
            )
            
            return request
            
        except Exception as e:
            request.status = GenerationStatus.FAILED
            request.error_message = str(e)
            request.completed_at = time.time()
            
            self._update_generation_stats(request, success=False)
            
            logger.error(
                "Content generation failed",
                request_id=request.id,
                error=str(e)
            )
            
            return request
        
        finally:
            # Clean up
            if request.id in self.active_requests:
                del self.active_requests[request.id]
    
    async def queue_request(self, request: ContentRequest) -> None:
        """Queue a content generation request"""
        await self.request_queues[request.priority].put(request)
        logger.info(
            "Queued content request",
            request_id=request.id,
            priority=request.priority.name
        )
    
    async def generate_batch(self, batch_request: BatchRequest) -> BatchRequest:
        """Generate multiple pieces of content in batch"""
        logger.info(
            "Starting batch generation",
            batch_id=batch_request.id,
            total_requests=batch_request.total_count,
            max_concurrent=batch_request.max_concurrent
        )
        
        self.batch_requests[batch_request.id] = batch_request
        
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(batch_request.max_concurrent)
        
        async def generate_single(request: ContentRequest) -> ContentRequest:
            async with semaphore:
                try:
                    result = await self.generate_content(request)
                    if result.status == GenerationStatus.COMPLETED:
                        batch_request.completed_count += 1
                    else:
                        batch_request.failed_count += 1
                        if batch_request.stop_on_error:
                            raise Exception(f"Request {request.id} failed: {request.error_message}")
                    return result
                except Exception as e:
                    batch_request.failed_count += 1
                    if batch_request.stop_on_error:
                        raise
                    return request
        
        # Execute all requests
        tasks = [generate_single(request) for request in batch_request.requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Update batch request with results
        batch_request.requests = [
            result for result in results 
            if isinstance(result, ContentRequest)
        ]
        
        logger.info(
            "Batch generation completed",
            batch_id=batch_request.id,
            completed=batch_request.completed_count,
            failed=batch_request.failed_count,
            total=batch_request.total_count
        )
        
        return batch_request
    
    async def _content_worker(self, worker_id: str) -> None:
        """Content generation worker"""
        logger.info(f"Content worker {worker_id} started")
        
        while self.workers_running:
            try:
                # Check queues in priority order
                request = None
                for priority in [GenerationPriority.URGENT, GenerationPriority.HIGH, 
                               GenerationPriority.NORMAL, GenerationPriority.LOW]:
                    try:
                        request = await asyncio.wait_for(
                            self.request_queues[priority].get(), 
                            timeout=1.0
                        )
                        break
                    except asyncio.TimeoutError:
                        continue
                
                if request:
                    await self.generate_content(request)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} error", error=str(e))
                await asyncio.sleep(1)  # Prevent tight error loops
        
        logger.info(f"Content worker {worker_id} stopped")
    
    async def _prepare_generation_context(self, request: ContentRequest) -> Dict[str, Any]:
        """Prepare context for content generation"""
        context = {
            "knowledge_base": await self.knowledge_base.get_context_for_topic(request.topic),
            "content_type": request.content_type,
            "requirements": request.requirements,
            "brand_voice": request.brand_voice or "professional and educational",
            "target_audience": request.target_audience or "aquascaping enthusiasts",
            "seo_keywords": request.seo_keywords
        }
        
        # Add template context if specified
        if request.template_name:
            template_context = await self.template_manager.get_template_context(
                request.template_name, request.content_type
            )
            context.update(template_context)
        
        # Merge with request context
        context.update(request.context)
        
        return context
    
    async def _generate_with_llm(self, request: ContentRequest, context: Dict[str, Any]) -> LLMResponse:
        """Generate content using LLM"""
        # Build system prompt
        system_prompt = await self._build_system_prompt(request, context)
        
        # Build user prompt
        user_prompt = await self._build_user_prompt(request, context)
        
        # Generate content
        response = await self.llm_manager.generate_content(
            prompt=user_prompt,
            content_type=request.content_type,
            system_prompt=system_prompt,
            preferred_provider=request.preferred_provider,
            max_tokens=request.max_length
        )
        
        return response
    
    async def _build_system_prompt(self, request: ContentRequest, context: Dict[str, Any]) -> str:
        """Build system prompt for content generation using aquascaping-specific templates"""
        # Get aquascaping-specific system prompt from template manager
        aquascaping_system_prompt = self.template_manager.get_aquascaping_prompt(
            request.content_type, "system_prompt"
        )
        
        # Use aquascaping prompt if available, fallback to generic
        if aquascaping_system_prompt:
            base_prompt = aquascaping_system_prompt
        else:
            base_prompt = f"""You are an expert aquascaping content creator for AquaScene, specializing in creating high-quality, educational content about planted aquariums, aquascaping techniques, and aquatic plant care.

BRAND VOICE: {context['brand_voice']}
TARGET AUDIENCE: {context['target_audience']}
CONTENT TYPE: {request.content_type.value}

AQUASCAPING EXPERTISE:
- Deep knowledge of aquatic plants, substrates, fertilizers, and equipment
- Understanding of aquascaping styles (Nature, Dutch, Iwagumi, etc.)
- Familiarity with major brands (Green Aqua, ADA, Tropica, etc.)
- Expertise in plant care, water parameters, and troubleshooting

CONTENT GUIDELINES:
- Always provide accurate, science-based information
- Include practical tips and actionable advice
- Reference specific products and techniques when relevant
- Maintain professional yet approachable tone
- Focus on education and community building"""

        # Add contextual information
        if context.get('brand_voice'):
            base_prompt += f"\n\nBRAND VOICE: {context['brand_voice']}"
        
        if context.get('target_audience'):
            base_prompt += f"\nTARGET AUDIENCE: {context['target_audience']}"

        if context.get("knowledge_base"):
            base_prompt += f"\n\nRELEVANT KNOWLEDGE:\n{context['knowledge_base']}"
        
        if request.seo_keywords:
            base_prompt += f"\n\nSEO KEYWORDS TO INCLUDE: {', '.join(request.seo_keywords)}"
        
        return base_prompt
    
    async def _build_user_prompt(self, request: ContentRequest, context: Dict[str, Any]) -> str:
        """Build user prompt for content generation using enhanced template prompts"""
        base_prompt = f"Create a {request.content_type.value} about: {request.topic}"
        
        # Use template manager to build enhanced prompt with aquascaping context
        enhanced_prompt = self.template_manager.build_enhanced_prompt(
            base_prompt=base_prompt,
            content_type=request.content_type,
            context={
                "target_audience": request.target_audience,
                "seo_keywords": request.seo_keywords,
                "brand_voice": request.brand_voice,
                "additional_instructions": request.additional_instructions
            }
        )
        
        if request.requirements:
            enhanced_prompt += f"\n\nREQUIREMENTS:\n"
            for key, value in request.requirements.items():
                enhanced_prompt += f"- {key}: {value}\n"
        
        if request.max_length:
            enhanced_prompt += f"\n\nMAX LENGTH: {request.max_length} characters"
        
        # Note: additional_instructions is already handled by build_enhanced_prompt
        
        # Add template-specific instructions
        if request.template_name and context.get("template_instructions"):
            enhanced_prompt += f"\n\nTEMPLATE INSTRUCTIONS:\n{context['template_instructions']}"
        
        return enhanced_prompt
    
    async def _validate_content(self, request: ContentRequest) -> float:
        """Validate content quality"""
        if not request.generated_content:
            return 0.0
        
        quality_score = await self.quality_validator.validate_content(
            content=request.generated_content,
            content_type=request.content_type,
            topic=request.topic,
            requirements=request.requirements
        )
        
        return quality_score
    
    async def _optimize_content(self, request: ContentRequest) -> Dict[str, Any]:
        """Optimize content for engagement and SEO"""
        if not request.generated_content:
            return {}
        
        optimization_results = await self.content_optimizer.optimize_content(
            content=request.generated_content,
            content_type=request.content_type,
            seo_keywords=request.seo_keywords,
            target_audience=request.target_audience
        )
        
        # Apply optimizations to content if available
        if optimization_results.get("optimized_content"):
            request.generated_content = optimization_results["optimized_content"]
        
        return optimization_results
    
    async def _finalize_content(self, request: ContentRequest) -> None:
        """Final processing and cleanup of generated content"""
        if not request.generated_content:
            return
        
        # Apply template formatting if needed
        if request.template_name:
            formatted_content = await self.template_manager.apply_template(
                template_name=request.template_name,
                content=request.generated_content,
                content_type=request.content_type,
                context=request.context
            )
            request.generated_content = formatted_content
        
        # Final cleanup and validation
        request.generated_content = request.generated_content.strip()
    
    def _update_generation_stats(self, request: ContentRequest, success: bool) -> None:
        """Update generation statistics"""
        self.generation_stats["total_requests"] += 1
        
        if success:
            self.generation_stats["successful_generations"] += 1
        else:
            self.generation_stats["failed_generations"] += 1
        
        # Update content type stats
        content_type = request.content_type.value
        if content_type not in self.generation_stats["content_type_stats"]:
            self.generation_stats["content_type_stats"][content_type] = {
                "total": 0, "successful": 0, "failed": 0
            }
        
        stats = self.generation_stats["content_type_stats"][content_type]
        stats["total"] += 1
        if success:
            stats["successful"] += 1
        else:
            stats["failed"] += 1
        
        # Update average generation time
        if request.created_at and request.completed_at:
            generation_time = request.completed_at - request.created_at
            current_avg = self.generation_stats["average_generation_time"]
            total_requests = self.generation_stats["total_requests"]
            
            # Running average calculation
            self.generation_stats["average_generation_time"] = (
                (current_avg * (total_requests - 1) + generation_time) / total_requests
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get generation statistics"""
        return {
            **self.generation_stats,
            "active_requests": len(self.active_requests),
            "queued_requests": {
                priority.name: self.request_queues[priority].qsize()
                for priority in GenerationPriority
            },
            "workers_running": self.workers_running,
            "active_workers": len(self.worker_tasks)
        }
    
    def get_request_status(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific request"""
        if request_id in self.active_requests:
            request = self.active_requests[request_id]
            return {
                "id": request.id,
                "status": request.status.value,
                "content_type": request.content_type.value,
                "topic": request.topic,
                "quality_score": request.quality_score,
                "created_at": request.created_at,
                "completed_at": request.completed_at,
                "error_message": request.error_message
            }
        return None