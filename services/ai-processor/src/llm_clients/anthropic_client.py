"""
Anthropic Claude Client Implementation

Handles integration with Anthropic's Claude models for aquascaping content generation.
Includes support for Claude Sonnet, Haiku, and Opus models.
"""

import asyncio
from typing import Dict, Optional, Any, List
import anthropic
from anthropic import AsyncAnthropic
import structlog

from .base_client import BaseLLMClient, LLMResponse, LLMConfig, ContentType, ModelType

logger = structlog.get_logger()


class AnthropicClient(BaseLLMClient):
    """Anthropic Claude client for content generation"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        
    def _initialize_client(self) -> None:
        """Initialize Anthropic Claude client"""
        if not self.config.api_key:
            raise ValueError("Anthropic API key is required")
            
        self.client = AsyncAnthropic(
            api_key=self.config.api_key,
            base_url=self.config.base_url
        )
        
        # Model-specific configurations
        self.model_configs = {
            ModelType.CLAUDE_SONNET: {
                "max_tokens": 4000,
                "context_window": 200000,
                "cost_per_1k_input": 0.003,
                "cost_per_1k_output": 0.015
            },
            ModelType.CLAUDE_HAIKU: {
                "max_tokens": 2000,
                "context_window": 200000,
                "cost_per_1k_input": 0.00025,
                "cost_per_1k_output": 0.00125
            },
            ModelType.CLAUDE_OPUS: {
                "max_tokens": 4000,
                "context_window": 200000,
                "cost_per_1k_input": 0.015,
                "cost_per_1k_output": 0.075
            }
        }
    
    async def generate_content(
        self,
        prompt: str,
        content_type: ContentType,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate content using Anthropic Claude models"""
        logger.info(
            "Generating content with Anthropic Claude",
            model=self.config.model.value,
            content_type=content_type.value
        )
        
        # Prepare request parameters
        request_params = {
            "model": self.config.model.value,
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "temperature": kwargs.get("temperature", self.config.temperature),
            "messages": [{"role": "user", "content": prompt}],
            **self.config.additional_params
        }
        
        # Add system prompt if provided
        if system_prompt:
            request_params["system"] = system_prompt
        
        try:
            response = await self.client.messages.create(**request_params)
            
            content = ""
            if response.content:
                content = response.content[0].text if response.content[0].type == "text" else ""
            
            # Claude returns input/output tokens separately
            input_tokens = response.usage.input_tokens if response.usage else 0
            output_tokens = response.usage.output_tokens if response.usage else 0
            total_tokens = input_tokens + output_tokens
            
            cost_estimate = self.calculate_cost(input_tokens, output_tokens)
            
            return LLMResponse(
                content=content,
                model_used=self.config.model.value,
                provider="anthropic",
                tokens_used=total_tokens,
                cost_estimate=cost_estimate,
                metadata={
                    "stop_reason": response.stop_reason,
                    "content_type": content_type.value,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "usage": response.usage.model_dump() if response.usage else None
                }
            )
            
        except anthropic.RateLimitError as e:
            logger.error("Anthropic rate limit exceeded", error=str(e))
            raise
        except anthropic.APITimeoutError as e:
            logger.error("Anthropic API timeout", error=str(e))
            raise
        except Exception as e:
            logger.error("Anthropic API error", error=str(e))
            raise
    
    async def is_available(self) -> bool:
        """Check if Anthropic service is available"""
        try:
            # Simple test request
            response = await self.client.messages.create(
                model=self.config.model.value,
                max_tokens=1,
                messages=[{"role": "user", "content": "Test"}]
            )
            return bool(response)
        except Exception as e:
            logger.error("Anthropic availability check failed", error=str(e))
            return False
    
    def get_cost_per_token(self) -> Dict[str, float]:
        """Get cost per token for the current model"""
        model_config = self.model_configs.get(self.config.model, {})
        return {
            "input": model_config.get("cost_per_1k_input", 0) / 1000,
            "output": model_config.get("cost_per_1k_output", 0) / 1000
        }
    
    def get_model_limits(self) -> Dict[str, int]:
        """Get Claude model-specific limits"""
        model_config = self.model_configs.get(self.config.model, {})
        return {
            "max_context_tokens": model_config.get("context_window", 200000),
            "max_output_tokens": model_config.get("max_tokens", 4000),
            "requests_per_minute": 50  # Conservative estimate
        }
    
    async def generate_with_tools(
        self,
        prompt: str,
        tools: List[Dict[str, Any]],
        content_type: ContentType,
        system_prompt: Optional[str] = None
    ) -> LLMResponse:
        """Generate content with tool use (Claude 3 feature)"""
        logger.info(
            "Generating content with tools",
            model=self.config.model.value,
            tool_count=len(tools)
        )
        
        request_params = {
            "model": self.config.model.value,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "messages": [{"role": "user", "content": prompt}],
            "tools": tools
        }
        
        if system_prompt:
            request_params["system"] = system_prompt
        
        try:
            response = await self.client.messages.create(**request_params)
            
            content = ""
            tool_calls = []
            
            for content_block in response.content:
                if content_block.type == "text":
                    content += content_block.text
                elif content_block.type == "tool_use":
                    tool_calls.append({
                        "id": content_block.id,
                        "name": content_block.name,
                        "input": content_block.input
                    })
            
            input_tokens = response.usage.input_tokens if response.usage else 0
            output_tokens = response.usage.output_tokens if response.usage else 0
            total_tokens = input_tokens + output_tokens
            
            cost_estimate = self.calculate_cost(input_tokens, output_tokens)
            
            return LLMResponse(
                content=content,
                model_used=self.config.model.value,
                provider="anthropic",
                tokens_used=total_tokens,
                cost_estimate=cost_estimate,
                metadata={
                    "stop_reason": response.stop_reason,
                    "content_type": content_type.value,
                    "tool_calls": tool_calls,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens
                }
            )
            
        except Exception as e:
            logger.error("Anthropic tool generation error", error=str(e))
            raise
    
    async def generate_with_images(
        self,
        prompt: str,
        image_data: List[Dict[str, Any]],
        content_type: ContentType,
        system_prompt: Optional[str] = None
    ) -> LLMResponse:
        """Generate content with image understanding"""
        logger.info(
            "Generating content with images",
            model=self.config.model.value,
            image_count=len(image_data)
        )
        
        # Construct message content with images
        message_content = []
        
        # Add text prompt
        message_content.append({
            "type": "text",
            "text": prompt
        })
        
        # Add images
        for image in image_data:
            message_content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": image.get("media_type", "image/jpeg"),
                    "data": image["data"]
                }
            })
        
        request_params = {
            "model": self.config.model.value,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "messages": [{"role": "user", "content": message_content}]
        }
        
        if system_prompt:
            request_params["system"] = system_prompt
        
        try:
            response = await self.client.messages.create(**request_params)
            
            content = ""
            if response.content:
                content = response.content[0].text if response.content[0].type == "text" else ""
            
            input_tokens = response.usage.input_tokens if response.usage else 0
            output_tokens = response.usage.output_tokens if response.usage else 0
            total_tokens = input_tokens + output_tokens
            
            cost_estimate = self.calculate_cost(input_tokens, output_tokens)
            
            return LLMResponse(
                content=content,
                model_used=self.config.model.value,
                provider="anthropic",
                tokens_used=total_tokens,
                cost_estimate=cost_estimate,
                metadata={
                    "stop_reason": response.stop_reason,
                    "content_type": content_type.value,
                    "image_count": len(image_data),
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens
                }
            )
            
        except Exception as e:
            logger.error("Anthropic image generation error", error=str(e))
            raise
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for Claude models"""
        # Claude uses a different tokenization than OpenAI
        # Rough approximation: ~3.5 characters per token
        return len(text) // 3