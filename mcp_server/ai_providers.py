"""
Multi-Provider AI Integration System

Supports multiple LLM providers with fallback mechanisms,
rate limiting, and response validation.
"""

import os
import time
import json
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum

import openai
import anthropic
import requests
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential


class AIProvider(Enum):
    """Supported AI providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE_OPENAI = "azure_openai"
    LOCAL_OLLAMA = "local_ollama"
    HUGGINGFACE = "huggingface"


@dataclass
class AIResponse:
    """Standardized AI response format."""
    content: str
    provider: AIProvider
    model: str
    tokens_used: int
    cost_estimate: float
    confidence_score: float
    metadata: Dict[str, Any]


class BaseAIProvider(ABC):
    """Base class for AI providers."""
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        self.api_key = api_key
        self.config = kwargs
        self.rate_limit_delay = 1.0
        self.last_request_time = 0
    
    @abstractmethod
    def generate_response(self, prompt: str, **kwargs) -> AIResponse:
        """Generate response from the AI provider."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available."""
        pass
    
    def _rate_limit(self):
        """Implement basic rate limiting."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)
        self.last_request_time = time.time()


class OpenAIProvider(BaseAIProvider):
    """OpenAI GPT provider."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4", **kwargs):
        super().__init__(api_key, **kwargs)
        self.model = model
        self.client = openai.OpenAI(api_key=api_key) if api_key else None
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def generate_response(self, prompt: str, **kwargs) -> AIResponse:
        """Generate response using OpenAI."""
        if not self.client:
            raise ValueError("OpenAI client not initialized")
        
        self._rate_limit()
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=kwargs.get("temperature", 0.1),
                max_tokens=kwargs.get("max_tokens", 4000)
            )
            
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            
            return AIResponse(
                content=content,
                provider=AIProvider.OPENAI,
                model=self.model,
                tokens_used=tokens_used,
                cost_estimate=self._calculate_cost(tokens_used),
                confidence_score=0.9,
                metadata={"finish_reason": response.choices[0].finish_reason}
            )
            
        except Exception as e:
            logger.error(f"OpenAI request failed: {e}")
            raise
    
    def is_available(self) -> bool:
        """Check OpenAI availability."""
        if not self.client:
            return False
        try:
            # Simple test request
            self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1
            )
            return True
        except Exception:
            return False
    
    def _calculate_cost(self, tokens: int) -> float:
        """Calculate estimated cost for OpenAI."""
        # Rough cost estimates (as of 2024)
        cost_per_1k_tokens = {
            "gpt-4": 0.03,
            "gpt-4-turbo": 0.01,
            "gpt-3.5-turbo": 0.002
        }
        rate = cost_per_1k_tokens.get(self.model, 0.01)
        return (tokens / 1000) * rate


class AnthropicProvider(BaseAIProvider):
    """Anthropic Claude provider."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-sonnet-20240229", **kwargs):
        super().__init__(api_key, **kwargs)
        self.model = model
        self.client = anthropic.Anthropic(api_key=api_key) if api_key else None
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def generate_response(self, prompt: str, **kwargs) -> AIResponse:
        """Generate response using Anthropic Claude."""
        if not self.client:
            raise ValueError("Anthropic client not initialized")
        
        self._rate_limit()
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=kwargs.get("max_tokens", 4000),
                temperature=kwargs.get("temperature", 0.1),
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text
            tokens_used = response.usage.input_tokens + response.usage.output_tokens
            
            return AIResponse(
                content=content,
                provider=AIProvider.ANTHROPIC,
                model=self.model,
                tokens_used=tokens_used,
                cost_estimate=self._calculate_cost(tokens_used),
                confidence_score=0.9,
                metadata={"stop_reason": response.stop_reason}
            )
            
        except Exception as e:
            logger.error(f"Anthropic request failed: {e}")
            raise
    
    def is_available(self) -> bool:
        """Check Anthropic availability."""
        if not self.client:
            return False
        try:
            # Simple test request
            self.client.messages.create(
                model=self.model,
                max_tokens=1,
                messages=[{"role": "user", "content": "test"}]
            )
            return True
        except Exception:
            return False
    
    def _calculate_cost(self, tokens: int) -> float:
        """Calculate estimated cost for Anthropic."""
        # Rough cost estimates (as of 2024)
        cost_per_1k_tokens = {
            "claude-3-opus-20240229": 0.015,
            "claude-3-sonnet-20240229": 0.003,
            "claude-3-haiku-20240307": 0.00025
        }
        rate = cost_per_1k_tokens.get(self.model, 0.003)
        return (tokens / 1000) * rate


class LocalOllamaProvider(BaseAIProvider):
    """Local Ollama provider for self-hosted models."""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama2", **kwargs):
        super().__init__(**kwargs)
        self.base_url = base_url
        self.model = model
    
    def generate_response(self, prompt: str, **kwargs) -> AIResponse:
        """Generate response using local Ollama."""
        self._rate_limit()
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": kwargs.get("temperature", 0.1),
                        "num_predict": kwargs.get("max_tokens", 4000)
                    }
                },
                timeout=120
            )
            response.raise_for_status()
            
            result = response.json()
            content = result.get("response", "")
            
            return AIResponse(
                content=content,
                provider=AIProvider.LOCAL_OLLAMA,
                model=self.model,
                tokens_used=len(content.split()),  # Rough estimate
                cost_estimate=0.0,  # Local model, no cost
                confidence_score=0.7,  # Lower confidence for local models
                metadata={"done": result.get("done", False)}
            )
            
        except Exception as e:
            logger.error(f"Ollama request failed: {e}")
            raise
    
    def is_available(self) -> bool:
        """Check Ollama availability."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False


class AIProviderManager:
    """Manages multiple AI providers with fallback logic."""
    
    def __init__(self):
        self.providers: Dict[AIProvider, BaseAIProvider] = {}
        self.provider_priority = [
            AIProvider.OPENAI,
            AIProvider.ANTHROPIC,
            AIProvider.LOCAL_OLLAMA
        ]
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize available providers."""
        # OpenAI
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            self.providers[AIProvider.OPENAI] = OpenAIProvider(openai_key)
        
        # Anthropic
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            self.providers[AIProvider.ANTHROPIC] = AnthropicProvider(anthropic_key)
        
        # Local Ollama
        self.providers[AIProvider.LOCAL_OLLAMA] = LocalOllamaProvider()
    
    def get_available_providers(self) -> List[AIProvider]:
        """Get list of available providers."""
        available = []
        for provider_type in self.provider_priority:
            if provider_type in self.providers:
                provider = self.providers[provider_type]
                if provider.is_available():
                    available.append(provider_type)
        return available
    
    def generate_with_fallback(self, prompt: str, preferred_provider: Optional[AIProvider] = None, 
                             **kwargs) -> AIResponse:
        """Generate response with automatic fallback."""
        providers_to_try = []
        
        # Try preferred provider first
        if preferred_provider and preferred_provider in self.providers:
            providers_to_try.append(preferred_provider)
        
        # Add other providers in priority order
        for provider_type in self.provider_priority:
            if provider_type not in providers_to_try and provider_type in self.providers:
                providers_to_try.append(provider_type)
        
        last_error = None
        for provider_type in providers_to_try:
            provider = self.providers[provider_type]
            try:
                logger.info(f"Attempting to use {provider_type.value} provider")
                response = provider.generate_response(prompt, **kwargs)
                logger.info(f"Successfully generated response using {provider_type.value}")
                return response
            except Exception as e:
                logger.warning(f"Provider {provider_type.value} failed: {e}")
                last_error = e
                continue
        
        # If all providers failed
        raise Exception(f"All AI providers failed. Last error: {last_error}")
    
    def validate_response(self, response: AIResponse, expected_format: str = "json") -> bool:
        """Validate AI response format."""
        if expected_format == "json":
            try:
                json.loads(response.content)
                return True
            except json.JSONDecodeError:
                return False
        
        # Add other validation logic as needed
        return True
