"""
Ollama Local LLM Client Implementation

Handles integration with local Ollama models for aquascaping content generation.
Provides fallback capabilities when cloud services are unavailable.
"""

import asyncio
from typing import Dict, Optional, Any
import aiohttp
import json
import structlog

from .base_client import BaseLLMClient, LLMResponse, LLMConfig, ContentType, ModelType

logger = structlog.get_logger()


class OllamaClient(BaseLLMClient):
    """Ollama local LLM client for content generation"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        
    def _initialize_client(self) -> None:
        """Initialize Ollama client"""
        # Default to local Ollama instance
        self.base_url = self.config.base_url or "http://localhost:11434"
        
        # Model-specific configurations (estimates for local models)
        self.model_configs = {
            ModelType.OLLAMA_LLAMA3: {
                "max_tokens": 2000,
                "context_window": 8192,
                "cost_per_1k_input": 0.0,  # Local models are free
                "cost_per_1k_output": 0.0
            },
            ModelType.OLLAMA_MISTRAL: {
                "max_tokens": 2000,
                "context_window": 8192,
                "cost_per_1k_input": 0.0,
                "cost_per_1k_output": 0.0
            },
            ModelType.OLLAMA_CODELLAMA: {
                "max_tokens": 2000,
                "context_window": 4096,
                "cost_per_1k_input": 0.0,
                "cost_per_1k_output": 0.0
            }
        }
        
        # Create HTTP session
        self.session = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout_seconds)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    async def generate_content(
        self,
        prompt: str,
        content_type: ContentType,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate content using Ollama local models"""
        logger.info(
            "Generating content with Ollama",
            model=self.config.model.value,
            content_type=content_type.value
        )
        
        # Prepare full prompt with system context
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"System: {system_prompt}\n\nUser: {prompt}"
        
        # Prepare request data
        request_data = {
            "model": self.config.model.value,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", self.config.temperature),
                "num_predict": kwargs.get("max_tokens", self.config.max_tokens),
                **self.config.additional_params
            }
        }
        
        session = await self._get_session()
        
        try:
            async with session.post(
                f"{self.base_url}/api/generate",
                json=request_data
            ) as response:
                
                if response.status != 200:
                    raise Exception(f"Ollama API error: {response.status}")
                
                result = await response.json()
                
                content = result.get("response", "")
                
                # Ollama doesn't provide exact token counts, estimate them
                estimated_tokens = self.estimate_tokens(full_prompt + content)
                
                return LLMResponse(
                    content=content,
                    model_used=self.config.model.value,
                    provider="ollama",
                    tokens_used=estimated_tokens,
                    cost_estimate=0.0,  # Local models are free
                    metadata={
                        "content_type": content_type.value,
                        "total_duration": result.get("total_duration"),
                        "load_duration": result.get("load_duration"),
                        "prompt_eval_count": result.get("prompt_eval_count"),
                        "eval_count": result.get("eval_count"),
                        "eval_duration": result.get("eval_duration")
                    }
                )
                
        except aiohttp.ClientError as e:
            logger.error("Ollama connection error", error=str(e))
            raise
        except json.JSONDecodeError as e:
            logger.error("Ollama response parsing error", error=str(e))
            raise
        except Exception as e:
            logger.error("Ollama API error", error=str(e))
            raise
    
    async def is_available(self) -> bool:
        """Check if Ollama service is available"""
        try:
            session = await self._get_session()
            async with session.get(f"{self.base_url}/api/version") as response:
                return response.status == 200
        except Exception as e:
            logger.error("Ollama availability check failed", error=str(e))
            return False
    
    def get_cost_per_token(self) -> Dict[str, float]:
        """Get cost per token (always 0 for local models)"""
        return {"input": 0.0, "output": 0.0}
    
    def get_model_limits(self) -> Dict[str, int]:
        """Get Ollama model-specific limits"""
        model_config = self.model_configs.get(self.config.model, {})
        return {
            "max_context_tokens": model_config.get("context_window", 4096),
            "max_output_tokens": model_config.get("max_tokens", 2000),
            "requests_per_minute": 1000  # Local models have no API limits
        }
    
    async def list_available_models(self) -> list[str]:
        """List models available in local Ollama instance"""
        try:
            session = await self._get_session()
            async with session.get(f"{self.base_url}/api/tags") as response:
                if response.status == 200:
                    result = await response.json()
                    return [model["name"] for model in result.get("models", [])]
                return []
        except Exception as e:
            logger.error("Error listing Ollama models", error=str(e))
            return []
    
    async def pull_model(self, model_name: str) -> bool:
        """Pull/download a model to local Ollama instance"""
        logger.info("Pulling Ollama model", model=model_name)
        
        try:
            session = await self._get_session()
            request_data = {"name": model_name}
            
            async with session.post(
                f"{self.base_url}/api/pull",
                json=request_data
            ) as response:
                if response.status != 200:
                    return False
                
                # Stream the pull progress
                async for line in response.content:
                    if line:
                        try:
                            progress = json.loads(line.decode())
                            logger.info(
                                "Model pull progress",
                                status=progress.get("status"),
                                completed=progress.get("completed"),
                                total=progress.get("total")
                            )
                        except json.JSONDecodeError:
                            continue
                
                return True
                
        except Exception as e:
            logger.error("Error pulling Ollama model", model=model_name, error=str(e))
            return False
    
    async def generate_streaming(
        self,
        prompt: str,
        content_type: ContentType,
        system_prompt: Optional[str] = None,
        **kwargs
    ):
        """Generate content with streaming response"""
        logger.info(
            "Streaming content generation with Ollama",
            model=self.config.model.value,
            content_type=content_type.value
        )
        
        # Prepare full prompt with system context
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"System: {system_prompt}\n\nUser: {prompt}"
        
        request_data = {
            "model": self.config.model.value,
            "prompt": full_prompt,
            "stream": True,
            "options": {
                "temperature": kwargs.get("temperature", self.config.temperature),
                "num_predict": kwargs.get("max_tokens", self.config.max_tokens),
                **self.config.additional_params
            }
        }
        
        session = await self._get_session()
        
        try:
            async with session.post(
                f"{self.base_url}/api/generate",
                json=request_data
            ) as response:
                
                if response.status != 200:
                    raise Exception(f"Ollama API error: {response.status}")
                
                full_content = ""
                
                async for line in response.content:
                    if line:
                        try:
                            chunk = json.loads(line.decode())
                            
                            if "response" in chunk:
                                token = chunk["response"]
                                full_content += token
                                
                                yield {
                                    "token": token,
                                    "full_content": full_content,
                                    "done": chunk.get("done", False)
                                }
                                
                            if chunk.get("done", False):
                                # Final response with metadata
                                yield {
                                    "token": "",
                                    "full_content": full_content,
                                    "done": True,
                                    "metadata": {
                                        "total_duration": chunk.get("total_duration"),
                                        "load_duration": chunk.get("load_duration"),
                                        "prompt_eval_count": chunk.get("prompt_eval_count"),
                                        "eval_count": chunk.get("eval_count")
                                    }
                                }
                                break
                                
                        except json.JSONDecodeError:
                            continue
                            
        except Exception as e:
            logger.error("Ollama streaming error", error=str(e))
            raise
    
    async def close(self):
        """Close the HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    def __del__(self):
        """Ensure session is closed on deletion"""
        if hasattr(self, 'session') and self.session and not self.session.closed:
            # Create a new event loop if none exists
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self.session.close())
                else:
                    loop.run_until_complete(self.session.close())
            except:
                pass  # Best effort cleanup