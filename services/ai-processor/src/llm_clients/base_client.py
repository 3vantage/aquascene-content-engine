"""
Base LLM Client Interface

Defines the common interface that all LLM clients must implement
for consistent usage across the content generation pipeline.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import time


class ModelType(Enum):
    """Supported model types across providers"""
    OPENAI_GPT4 = "gpt-4-turbo-preview"
    OPENAI_GPT4_MINI = "gpt-4o-mini"
    OPENAI_GPT35 = "gpt-3.5-turbo"
    CLAUDE_SONNET = "claude-3-5-sonnet-20241022"
    CLAUDE_HAIKU = "claude-3-haiku-20240307"
    CLAUDE_OPUS = "claude-3-opus-20240229"
    OLLAMA_LLAMA3 = "llama3.1:8b"
    OLLAMA_MISTRAL = "mistral:7b"
    OLLAMA_CODELLAMA = "codellama:7b"


class ContentType(Enum):
    """Types of content that can be generated"""
    NEWSLETTER_ARTICLE = "newsletter_article"
    INSTAGRAM_CAPTION = "instagram_caption"
    HOW_TO_GUIDE = "how_to_guide"
    PRODUCT_REVIEW = "product_review"
    COMMUNITY_POST = "community_post"
    SEO_BLOG_POST = "seo_blog_post"
    WEEKLY_DIGEST = "weekly_digest"
    EXPERT_INTERVIEW = "expert_interview"


@dataclass
class LLMConfig:
    """Configuration for LLM client"""
    model: ModelType
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout_seconds: int = 30
    retry_attempts: int = 3
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    additional_params: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.additional_params is None:
            self.additional_params = {}


@dataclass 
class LLMResponse:
    """Standardized response from LLM clients"""
    content: str
    model_used: str
    provider: str
    tokens_used: Optional[int] = None
    cost_estimate: Optional[float] = None
    response_time: Optional[float] = None
    quality_score: Optional[float] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseLLMClient(ABC):
    """Base class for all LLM clients"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.provider_name = self.__class__.__name__.replace("Client", "").lower()
        self._initialize_client()
    
    @abstractmethod
    def _initialize_client(self) -> None:
        """Initialize the specific LLM client"""
        pass
    
    @abstractmethod
    async def generate_content(
        self,
        prompt: str,
        content_type: ContentType,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate content using the LLM"""
        pass
    
    @abstractmethod
    async def is_available(self) -> bool:
        """Check if the LLM service is available"""
        pass
    
    @abstractmethod
    def get_cost_per_token(self) -> Dict[str, float]:
        """Get cost per token for input/output"""
        pass
    
    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost based on token usage"""
        costs = self.get_cost_per_token()
        return (input_tokens * costs.get("input", 0) + 
                output_tokens * costs.get("output", 0))
    
    async def generate_with_fallback(
        self,
        prompt: str,  
        content_type: ContentType,
        fallback_clients: List["BaseLLMClient"] = None,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate content with fallback to other clients if this one fails"""
        start_time = time.time()
        
        try:
            response = await self.generate_content(
                prompt, content_type, system_prompt, **kwargs
            )
            response.response_time = time.time() - start_time
            return response
        except Exception as e:
            if fallback_clients:
                for fallback_client in fallback_clients:
                    try:
                        response = await fallback_client.generate_content(
                            prompt, content_type, system_prompt, **kwargs
                        )
                        response.response_time = time.time() - start_time
                        response.metadata["fallback_used"] = True
                        response.metadata["original_error"] = str(e)
                        return response
                    except Exception:
                        continue
            raise e
    
    def get_model_limits(self) -> Dict[str, int]:
        """Get model-specific limits (context window, max output, etc.)"""
        return {
            "max_context_tokens": 4000,
            "max_output_tokens": 2000,
            "requests_per_minute": 60
        }
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text (rough approximation)"""
        # Simple estimation: ~4 characters per token for English text
        return len(text) // 4
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the LLM service"""
        try:
            is_available = await self.is_available()
            return {
                "provider": self.provider_name,
                "model": self.config.model.value,
                "available": is_available,
                "limits": self.get_model_limits(),
                "cost_per_token": self.get_cost_per_token()
            }
        except Exception as e:
            return {
                "provider": self.provider_name,
                "available": False,
                "error": str(e)
            }