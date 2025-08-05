"""
OpenAI GPT Client Implementation

Handles integration with OpenAI's GPT models including GPT-4 and GPT-3.5-turbo
for aquascaping content generation.
"""

import asyncio
from typing import Dict, Optional, Any
import openai
from openai import AsyncOpenAI
import structlog

from .base_client import BaseLLMClient, LLMResponse, LLMConfig, ContentType, ModelType

logger = structlog.get_logger()


class OpenAIClient(BaseLLMClient):
    """OpenAI GPT client for content generation"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        
    def _initialize_client(self) -> None:
        """Initialize OpenAI client"""
        if not self.config.api_key:
            raise ValueError("OpenAI API key is required")
            
        self.client = AsyncOpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url
        )
        
        # Model-specific configurations
        self.model_configs = {
            ModelType.OPENAI_GPT4: {
                "max_tokens": 4000,
                "context_window": 128000,
                "cost_per_1k_input": 0.01,
                "cost_per_1k_output": 0.03
            },
            ModelType.OPENAI_GPT4_MINI: {
                "max_tokens": 2000,
                "context_window": 128000,
                "cost_per_1k_input": 0.00015,
                "cost_per_1k_output": 0.0006
            },
            ModelType.OPENAI_GPT35: {
                "max_tokens": 2000,
                "context_window": 16000,
                "cost_per_1k_input": 0.0015,
                "cost_per_1k_output": 0.002
            }
        }
    
    async def generate_content(
        self,
        prompt: str,
        content_type: ContentType,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate content using OpenAI GPT models"""
        logger.info(
            "Generating content with OpenAI",
            model=self.config.model.value,
            content_type=content_type.value
        )
        
        # Prepare messages
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        # Prepare request parameters
        request_params = {
            "model": self.config.model.value,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.config.temperature),
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            **self.config.additional_params
        }
        
        try:
            response = await self.client.chat.completions.create(**request_params)
            
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else None
            
            # Calculate cost if tokens are available
            cost_estimate = None
            if response.usage:
                input_tokens = response.usage.prompt_tokens
                output_tokens = response.usage.completion_tokens
                cost_estimate = self.calculate_cost(input_tokens, output_tokens)
            
            return LLMResponse(
                content=content,
                model_used=self.config.model.value,
                provider="openai",
                tokens_used=tokens_used,
                cost_estimate=cost_estimate,
                metadata={
                    "finish_reason": response.choices[0].finish_reason,
                    "content_type": content_type.value,
                    "usage": response.usage.model_dump() if response.usage else None
                }
            )
            
        except openai.RateLimitError as e:
            logger.error("OpenAI rate limit exceeded", error=str(e))
            raise
        except openai.APITimeoutError as e:
            logger.error("OpenAI API timeout", error=str(e))
            raise
        except Exception as e:
            logger.error("OpenAI API error", error=str(e))
            raise
    
    async def is_available(self) -> bool:
        """Check if OpenAI service is available"""
        try:
            # Simple test request
            response = await self.client.chat.completions.create(
                model=self.config.model.value,
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=1
            )
            return bool(response)
        except Exception as e:
            logger.error("OpenAI availability check failed", error=str(e))
            return False
    
    def get_cost_per_token(self) -> Dict[str, float]:
        """Get cost per token for the current model"""
        model_config = self.model_configs.get(self.config.model, {})
        return {
            "input": model_config.get("cost_per_1k_input", 0) / 1000,
            "output": model_config.get("cost_per_1k_output", 0) / 1000
        }
    
    def get_model_limits(self) -> Dict[str, int]:
        """Get OpenAI model-specific limits"""
        model_config = self.model_configs.get(self.config.model, {})
        return {
            "max_context_tokens": model_config.get("context_window", 4000),
            "max_output_tokens": model_config.get("max_tokens", 2000),
            "requests_per_minute": 60 if self.config.model == ModelType.OPENAI_GPT4 else 3500
        }
    
    async def generate_structured_content(
        self,
        prompt: str,
        response_format: Dict[str, Any],
        content_type: ContentType,
        system_prompt: Optional[str] = None
    ) -> LLMResponse:
        """Generate structured content using JSON mode (GPT-4 only)"""
        if self.config.model not in [ModelType.OPENAI_GPT4, ModelType.OPENAI_GPT4_MINI]:
            raise ValueError("Structured output only supported for GPT-4 models")
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # Add JSON format instruction to prompt
        structured_prompt = f"""{prompt}

Please respond with valid JSON matching this format:
{response_format}"""
        
        messages.append({"role": "user", "content": structured_prompt})
        
        try:
            response = await self.client.chat.completions.create(
                model=self.config.model.value,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else None
            
            cost_estimate = None
            if response.usage:
                input_tokens = response.usage.prompt_tokens
                output_tokens = response.usage.completion_tokens
                cost_estimate = self.calculate_cost(input_tokens, output_tokens)
            
            return LLMResponse(
                content=content,
                model_used=self.config.model.value,
                provider="openai",
                tokens_used=tokens_used,
                cost_estimate=cost_estimate,
                metadata={
                    "finish_reason": response.choices[0].finish_reason,
                    "content_type": content_type.value,
                    "structured": True,
                    "usage": response.usage.model_dump() if response.usage else None
                }
            )
            
        except Exception as e:
            logger.error("OpenAI structured generation error", error=str(e))
            raise
    
    async def generate_with_images(
        self,
        prompt: str,
        image_urls: list[str],
        content_type: ContentType,
        system_prompt: Optional[str] = None
    ) -> LLMResponse:
        """Generate content with image understanding (GPT-4V)"""
        if self.config.model != ModelType.OPENAI_GPT4:
            raise ValueError("Image understanding only supported for GPT-4")
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # Construct message with images
        content_parts = [{"type": "text", "text": prompt}]
        
        for image_url in image_urls:
            content_parts.append({
                "type": "image_url",
                "image_url": {"url": image_url}
            })
        
        messages.append({
            "role": "user",
            "content": content_parts
        })
        
        try:
            response = await self.client.chat.completions.create(
                model=self.config.model.value,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )
            
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else None
            
            cost_estimate = None
            if response.usage:
                input_tokens = response.usage.prompt_tokens
                output_tokens = response.usage.completion_tokens
                cost_estimate = self.calculate_cost(input_tokens, output_tokens)
            
            return LLMResponse(
                content=content,
                model_used=self.config.model.value,
                provider="openai",
                tokens_used=tokens_used,
                cost_estimate=cost_estimate,
                metadata={
                    "finish_reason": response.choices[0].finish_reason,
                    "content_type": content_type.value,
                    "image_count": len(image_urls),
                    "usage": response.usage.model_dump() if response.usage else None
                }
            )
            
        except Exception as e:
            logger.error("OpenAI image generation error", error=str(e))
            raise