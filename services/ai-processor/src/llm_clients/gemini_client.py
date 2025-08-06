"""
Google Gemini Client Implementation

Handles integration with Google's Gemini models for aquascaping content generation.
Supports Gemini Pro and other available models.
"""

import asyncio
from typing import Dict, Optional, Any
import google.generativeai as genai
import structlog

from .base_client import BaseLLMClient, LLMResponse, LLMConfig, ContentType, ModelType

logger = structlog.get_logger()


class GeminiClient(BaseLLMClient):
    """Google Gemini client for content generation"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        
    def _initialize_client(self) -> None:
        """Initialize Google Gemini client"""
        if not self.config.api_key:
            raise ValueError("Google Gemini API key is required")
            
        genai.configure(api_key=self.config.api_key)
        
        # Model-specific configurations
        self.model_configs = {
            ModelType.GEMINI_PRO: {
                "max_tokens": 4000,
                "context_window": 32768,
                "cost_per_1k_input": 0.0005,
                "cost_per_1k_output": 0.0015
            },
            ModelType.GEMINI_PRO_VISION: {
                "max_tokens": 4000,
                "context_window": 16384,
                "cost_per_1k_input": 0.0005,
                "cost_per_1k_output": 0.0015
            }
        }
        
        # Initialize the model
        model_name = self._get_model_name()
        self.model = genai.GenerativeModel(
            model_name=model_name,
            generation_config=genai.types.GenerationConfig(
                temperature=self.config.temperature,
                max_output_tokens=self.config.max_tokens,
            )
        )
        
        logger.info(f"Initialized Gemini client with model: {model_name}")
    
    def _get_model_name(self) -> str:
        """Get the actual model name for Gemini API"""
        model_mapping = {
            ModelType.GEMINI_PRO: "gemini-pro",
            ModelType.GEMINI_PRO_VISION: "gemini-pro-vision"
        }
        return model_mapping.get(self.config.model, "gemini-pro")
    
    async def generate_content(
        self,
        prompt: str,
        content_type: ContentType,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate content using Google Gemini"""
        logger.info(
            "Generating content with Gemini",
            model=self.config.model.value,
            content_type=content_type.value
        )
        
        # Prepare the full prompt
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        # Update generation config if needed
        generation_config = genai.types.GenerationConfig(
            temperature=kwargs.get("temperature", self.config.temperature),
            max_output_tokens=kwargs.get("max_tokens", self.config.max_tokens),
        )
        
        try:
            # Generate content - Gemini API is synchronous, so we run in executor
            loop = asyncio.get_event_loop()
            
            def _generate():
                return self.model.generate_content(
                    full_prompt,
                    generation_config=generation_config
                )
            
            response = await loop.run_in_executor(None, _generate)
            
            # Extract content
            content = response.text if response.text else ""
            
            # Estimate token usage (Gemini doesn't provide exact counts yet)
            estimated_input_tokens = self.estimate_tokens(full_prompt)
            estimated_output_tokens = self.estimate_tokens(content)
            total_tokens = estimated_input_tokens + estimated_output_tokens
            
            # Calculate cost estimate
            cost_estimate = self.calculate_cost(estimated_input_tokens, estimated_output_tokens)
            
            return LLMResponse(
                content=content,
                model_used=self._get_model_name(),
                provider="gemini",
                tokens_used=total_tokens,
                cost_estimate=cost_estimate,
                metadata={
                    "content_type": content_type.value,
                    "finish_reason": "stop",  # Gemini doesn't provide detailed finish reasons
                    "estimated_input_tokens": estimated_input_tokens,
                    "estimated_output_tokens": estimated_output_tokens,
                    "safety_ratings": self._extract_safety_ratings(response) if hasattr(response, 'candidates') else None
                }
            )
            
        except Exception as e:
            logger.error("Gemini API error", error=str(e))
            # Check for specific Gemini errors
            if "SAFETY" in str(e):
                logger.warning("Content blocked by Gemini safety filters", error=str(e))
            raise
    
    def _extract_safety_ratings(self, response) -> Dict[str, str]:
        """Extract safety ratings from Gemini response"""
        safety_ratings = {}
        try:
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'safety_ratings'):
                    for rating in candidate.safety_ratings:
                        safety_ratings[rating.category.name] = rating.probability.name
        except Exception as e:
            logger.debug("Error extracting safety ratings", error=str(e))
        
        return safety_ratings
    
    async def is_available(self) -> bool:
        """Check if Gemini service is available"""
        try:
            # Simple test request
            loop = asyncio.get_event_loop()
            
            def _test():
                test_model = genai.GenerativeModel(model_name="gemini-pro")
                return test_model.generate_content(
                    "Hello",
                    generation_config=genai.types.GenerationConfig(max_output_tokens=1)
                )
            
            response = await loop.run_in_executor(None, _test)
            return bool(response and response.text)
            
        except Exception as e:
            logger.error("Gemini availability check failed", error=str(e))
            return False
    
    def get_cost_per_token(self) -> Dict[str, float]:
        """Get cost per token for the current model"""
        model_config = self.model_configs.get(self.config.model, {})
        return {
            "input": model_config.get("cost_per_1k_input", 0) / 1000,
            "output": model_config.get("cost_per_1k_output", 0) / 1000
        }
    
    def get_model_limits(self) -> Dict[str, int]:
        """Get Gemini model-specific limits"""
        model_config = self.model_configs.get(self.config.model, {})
        return {
            "max_context_tokens": model_config.get("context_window", 32768),
            "max_output_tokens": model_config.get("max_tokens", 4000),
            "requests_per_minute": 60  # Conservative estimate
        }
    
    async def generate_with_images(
        self,
        prompt: str,
        image_data: list[str],
        content_type: ContentType,
        system_prompt: Optional[str] = None
    ) -> LLMResponse:
        """Generate content with image understanding (Gemini Pro Vision)"""
        if self.config.model != ModelType.GEMINI_PRO_VISION:
            raise ValueError("Image understanding only supported for Gemini Pro Vision")
        
        logger.info(
            "Generating content with images",
            model=self.config.model.value,
            image_count=len(image_data)
        )
        
        # Prepare the full prompt
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        try:
            loop = asyncio.get_event_loop()
            
            def _generate_with_images():
                # For now, we'll just use text (image handling would require PIL/image processing)
                # This could be extended to handle actual image data
                return self.model.generate_content([full_prompt])
            
            response = await loop.run_in_executor(None, _generate_with_images)
            
            content = response.text if response.text else ""
            
            # Estimate token usage
            estimated_input_tokens = self.estimate_tokens(full_prompt) + (len(image_data) * 200)  # Rough image token estimate
            estimated_output_tokens = self.estimate_tokens(content)
            total_tokens = estimated_input_tokens + estimated_output_tokens
            
            cost_estimate = self.calculate_cost(estimated_input_tokens, estimated_output_tokens)
            
            return LLMResponse(
                content=content,
                model_used=self._get_model_name(),
                provider="gemini",
                tokens_used=total_tokens,
                cost_estimate=cost_estimate,
                metadata={
                    "content_type": content_type.value,
                    "image_count": len(image_data),
                    "estimated_input_tokens": estimated_input_tokens,
                    "estimated_output_tokens": estimated_output_tokens,
                    "safety_ratings": self._extract_safety_ratings(response) if hasattr(response, 'candidates') else None
                }
            )
            
        except Exception as e:
            logger.error("Gemini image generation error", error=str(e))
            raise
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for Gemini models"""
        # Gemini uses similar tokenization to other models
        # Rough approximation: ~4 characters per token for English text
        return max(1, len(text) // 4)
    
    async def close(self) -> None:
        """Close Gemini client connections (no persistent connections in Gemini)"""
        pass