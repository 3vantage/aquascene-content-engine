"""
LLM Client Manager

Orchestrates multiple LLM clients with intelligent routing, fallback handling,
load balancing, and cost optimization for aquascaping content generation.
"""

import asyncio
from typing import Dict, List, Optional, Any, Union
from enum import Enum
import random
import time
import structlog

from .base_client import BaseLLMClient, LLMResponse, LLMConfig, ContentType, ModelType
from .openai_client import OpenAIClient
from .anthropic_client import AnthropicClient
from .gemini_client import GeminiClient
from .ollama_client import OllamaClient

logger = structlog.get_logger()


class RoutingStrategy(Enum):
    """Strategies for routing requests to different LLM providers"""
    COST_OPTIMIZED = "cost_optimized"
    QUALITY_FIRST = "quality_first"
    SPEED_FIRST = "speed_first"
    BALANCED = "balanced"
    ROUND_ROBIN = "round_robin"


class LLMClientManager:
    """Manages multiple LLM clients with intelligent routing and fallback"""
    
    def __init__(self, configs: Dict[str, LLMConfig]):
        self.clients: Dict[str, BaseLLMClient] = {}
        self.client_health: Dict[str, Dict[str, Any]] = {}
        self.routing_strategy = RoutingStrategy.BALANCED
        self.fallback_order = ["openai", "anthropic", "gemini", "ollama"]
        self.round_robin_index = 0
        
        # Performance tracking
        self.performance_stats = {}
        
        # Initialize clients
        self._initialize_clients(configs)
        
        # Content type preferences (which models work best for what)
        self.content_preferences = {
            ContentType.NEWSLETTER_ARTICLE: ["openai", "anthropic", "gemini", "ollama"],
            ContentType.INSTAGRAM_CAPTION: ["anthropic", "gemini", "openai", "ollama"],
            ContentType.HOW_TO_GUIDE: ["openai", "anthropic", "gemini", "ollama"],
            ContentType.PRODUCT_REVIEW: ["anthropic", "openai", "gemini", "ollama"],
            ContentType.COMMUNITY_POST: ["gemini", "ollama", "anthropic", "openai"],
            ContentType.SEO_BLOG_POST: ["openai", "gemini", "anthropic", "ollama"],
            ContentType.WEEKLY_DIGEST: ["anthropic", "gemini", "openai", "ollama"],
            ContentType.EXPERT_INTERVIEW: ["anthropic", "openai", "gemini", "ollama"]
        }
    
    def _initialize_clients(self, configs: Dict[str, LLMConfig]) -> None:
        """Initialize all LLM clients"""
        for provider, config in configs.items():
            try:
                if provider == "openai":
                    self.clients[provider] = OpenAIClient(config)
                elif provider == "anthropic":
                    self.clients[provider] = AnthropicClient(config)
                elif provider == "gemini":
                    self.clients[provider] = GeminiClient(config)
                elif provider == "ollama":
                    self.clients[provider] = OllamaClient(config)
                else:
                    logger.warning(f"Unknown provider: {provider}")
                    continue
                
                logger.info(f"Initialized {provider} client", model=config.model.value)
                
            except Exception as e:
                logger.error(f"Failed to initialize {provider} client", error=str(e))
    
    async def generate_content(
        self,
        prompt: str,
        content_type: ContentType,
        system_prompt: Optional[str] = None,
        preferred_provider: Optional[str] = None,
        routing_strategy: Optional[RoutingStrategy] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate content with intelligent routing and fallback"""
        strategy = routing_strategy or self.routing_strategy
        
        # Update client health status
        await self._update_health_status()
        
        # Determine the best client to use
        if preferred_provider and preferred_provider in self.clients:
            primary_client = self.clients[preferred_provider]
            fallback_clients = [
                self.clients[name] for name in self.fallback_order 
                if name != preferred_provider and name in self.clients
            ]
        else:
            primary_client, fallback_clients = self._select_clients(content_type, strategy)
        
        start_time = time.time()
        
        try:
            response = await primary_client.generate_with_fallback(
                prompt, content_type, fallback_clients, system_prompt, **kwargs
            )
            
            # Track performance
            self._track_performance(primary_client.provider_name, time.time() - start_time, True)
            
            return response
            
        except Exception as e:
            # Track failure
            self._track_performance(primary_client.provider_name, time.time() - start_time, False)
            logger.error(
                "All LLM clients failed",
                primary=primary_client.provider_name,
                error=str(e)
            )
            raise
    
    def _select_clients(
        self, 
        content_type: ContentType, 
        strategy: RoutingStrategy
    ) -> tuple[BaseLLMClient, List[BaseLLMClient]]:
        """Select primary and fallback clients based on strategy"""
        
        available_clients = [
            (name, client) for name, client in self.clients.items()
            if self.client_health.get(name, {}).get("available", False)
        ]
        
        if not available_clients:
            # If no health data, assume all are available
            available_clients = list(self.clients.items())
        
        if strategy == RoutingStrategy.COST_OPTIMIZED:
            # Sort by cost (ascending)
            available_clients.sort(key=lambda x: self._get_client_cost(x[1]))
            
        elif strategy == RoutingStrategy.QUALITY_FIRST:
            # Use content type preferences
            preferred_order = self.content_preferences.get(content_type, self.fallback_order)
            available_clients.sort(key=lambda x: preferred_order.index(x[0]) if x[0] in preferred_order else 999)
            
        elif strategy == RoutingStrategy.SPEED_FIRST:
            # Sort by average response time
            available_clients.sort(key=lambda x: self._get_average_response_time(x[0]))
            
        elif strategy == RoutingStrategy.ROUND_ROBIN:
            # Simple round-robin
            self.round_robin_index = (self.round_robin_index + 1) % len(available_clients)
            selected = available_clients[self.round_robin_index]
            others = available_clients[:self.round_robin_index] + available_clients[self.round_robin_index + 1:]
            available_clients = [selected] + others
            
        elif strategy == RoutingStrategy.BALANCED:
            # Weighted selection based on performance and cost
            available_clients.sort(key=lambda x: self._get_balanced_score(x[0], x[1]))
        
        if not available_clients:
            raise Exception("No LLM clients available")
        
        primary_client = available_clients[0][1]
        fallback_clients = [client for _, client in available_clients[1:]]
        
        return primary_client, fallback_clients
    
    def _get_client_cost(self, client: BaseLLMClient) -> float:
        """Get estimated cost per request for a client"""
        costs = client.get_cost_per_token()
        # Estimate based on average tokens (input: 500, output: 300)
        return (500 * costs["input"]) + (300 * costs["output"])
    
    def _get_average_response_time(self, provider: str) -> float:
        """Get average response time for a provider"""
        stats = self.performance_stats.get(provider, {})
        times = stats.get("response_times", [])
        return sum(times) / len(times) if times else 999.0
    
    def _get_balanced_score(self, provider: str, client: BaseLLMClient) -> float:
        """Calculate balanced score considering cost, speed, and reliability"""
        cost = self._get_client_cost(client)
        speed = self._get_average_response_time(provider)
        
        stats = self.performance_stats.get(provider, {})
        reliability = stats.get("success_rate", 0.5)
        
        # Lower is better (cost and speed should be minimized, reliability maximized)
        return (cost * 0.3) + (speed * 0.4) + ((1 - reliability) * 0.3)
    
    def _track_performance(self, provider: str, response_time: float, success: bool) -> None:
        """Track performance metrics for providers"""
        if provider not in self.performance_stats:
            self.performance_stats[provider] = {
                "response_times": [],
                "successes": 0,
                "failures": 0,
                "total_requests": 0
            }
        
        stats = self.performance_stats[provider]
        stats["response_times"].append(response_time)
        stats["total_requests"] += 1
        
        if success:
            stats["successes"] += 1
        else:
            stats["failures"] += 1
        
        # Keep only last 100 response times
        if len(stats["response_times"]) > 100:
            stats["response_times"] = stats["response_times"][-100:]
        
        # Calculate success rate
        stats["success_rate"] = stats["successes"] / stats["total_requests"]
    
    async def _update_health_status(self) -> None:
        """Update health status for all clients"""
        health_tasks = []
        
        for name, client in self.clients.items():
            health_tasks.append(self._check_client_health(name, client))
        
        if health_tasks:
            await asyncio.gather(*health_tasks, return_exceptions=True)
    
    async def _check_client_health(self, name: str, client: BaseLLMClient) -> None:
        """Check health of a specific client"""
        try:
            health = await client.health_check()
            self.client_health[name] = health
        except Exception as e:
            self.client_health[name] = {
                "provider": name,
                "available": False,
                "error": str(e)
            }
    
    async def batch_generate(
        self,
        requests: List[Dict[str, Any]],
        max_concurrent: int = 5
    ) -> List[LLMResponse]:
        """Generate multiple pieces of content concurrently"""
        logger.info(f"Starting batch generation of {len(requests)} requests")
        
        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def generate_single(request_data: Dict[str, Any]) -> LLMResponse:
            async with semaphore:
                return await self.generate_content(**request_data)
        
        # Execute all requests concurrently
        tasks = [generate_single(request) for request in requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        successful_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Batch request {i} failed", error=str(result))
            else:
                successful_results.append(result)
        
        logger.info(
            f"Batch generation completed",
            total=len(requests),
            successful=len(successful_results),
            failed=len(requests) - len(successful_results)
        )
        
        return successful_results
    
    def set_routing_strategy(self, strategy: RoutingStrategy) -> None:
        """Set the default routing strategy"""
        self.routing_strategy = strategy
        logger.info(f"Routing strategy set to {strategy.value}")
    
    def set_fallback_order(self, order: List[str]) -> None:
        """Set the fallback order for providers"""
        valid_providers = [name for name in order if name in self.clients]
        self.fallback_order = valid_providers
        logger.info(f"Fallback order set to {valid_providers}")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for all providers"""
        return {
            "stats": self.performance_stats.copy(),
            "health": self.client_health.copy(),
            "routing_strategy": self.routing_strategy.value,
            "fallback_order": self.fallback_order
        }
    
    async def optimize_for_content_type(self, content_type: ContentType) -> None:
        """Optimize routing for a specific content type"""
        logger.info(f"Optimizing routing for {content_type.value}")
        
        # Test each provider with sample content
        test_prompt = f"Generate a short sample {content_type.value} about aquascaping."
        test_results = {}
        
        for name, client in self.clients.items():
            try:
                start_time = time.time()
                response = await client.generate_content(test_prompt, content_type)
                response_time = time.time() - start_time
                
                test_results[name] = {
                    "response_time": response_time,
                    "cost": response.cost_estimate or 0,
                    "quality": len(response.content),  # Simple quality metric
                    "success": True
                }
            except Exception as e:
                test_results[name] = {
                    "response_time": 999,
                    "cost": 999,
                    "quality": 0,
                    "success": False
                }
        
        # Update content preferences based on test results
        sorted_providers = sorted(
            test_results.items(),
            key=lambda x: (
                not x[1]["success"],  # Failed providers last
                x[1]["response_time"] * 0.4 + x[1]["cost"] * 0.3 - x[1]["quality"] * 0.3
            )
        )
        
        self.content_preferences[content_type] = [name for name, _ in sorted_providers]
        
        logger.info(
            f"Optimized preferences for {content_type.value}",
            preferences=self.content_preferences[content_type]
        )
    
    async def close_all(self) -> None:
        """Close all client connections"""
        for name, client in self.clients.items():
            try:
                if hasattr(client, 'close'):
                    await client.close()
            except Exception as e:
                logger.error(f"Error closing {name} client", error=str(e))