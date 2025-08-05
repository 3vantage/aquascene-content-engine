"""
LLM Client Management Package

Provides unified interface for multiple LLM providers:
- OpenAI GPT-4/GPT-3.5
- Anthropic Claude
- Local Ollama models
"""

from .base_client import BaseLLMClient, LLMResponse, LLMConfig
from .openai_client import OpenAIClient
from .anthropic_client import AnthropicClient
from .ollama_client import OllamaClient
from .client_manager import LLMClientManager

__all__ = [
    "BaseLLMClient",
    "LLMResponse", 
    "LLMConfig",
    "OpenAIClient",
    "AnthropicClient", 
    "OllamaClient",
    "LLMClientManager"
]