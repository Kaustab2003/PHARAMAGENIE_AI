# utils/api_client.py
"""
Unified API client with fallback support
Supports OpenAI, DeepSeek, and Groq APIs with automatic fallback
"""

import os
import logging
from typing import Optional, List, Dict, Any
from openai import OpenAI

logger = logging.getLogger(__name__)

class UnifiedAPIClient:
    """
    Unified API client that supports multiple LLM providers with automatic fallback.
    Priority order: DeepSeek -> Groq -> OpenAI
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize with automatic provider detection and fallback setup.
        
        Args:
            api_key: Optional API key (will auto-detect from environment if not provided)
        """
        self.providers = self._setup_providers(api_key)
        self.current_provider = None
        self._select_provider()
    
    def _setup_providers(self, api_key: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """Setup available API providers with their configurations."""
        providers = {}
        
        # DeepSeek (Priority 1)
        deepseek_key = os.getenv("DEEPSEEK_API_KEY")
        if deepseek_key:
            providers["deepseek"] = {
                "client": OpenAI(
                    api_key=deepseek_key,
                    base_url="https://api.deepseek.com"
                ),
                "model": "deepseek-chat",
                "name": "DeepSeek"
            }
            logger.info("✅ DeepSeek API configured")
        
        # Groq (Priority 2)
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key:
            providers["groq"] = {
                "client": OpenAI(
                    api_key=groq_key,
                    base_url="https://api.groq.com/openai/v1"
                ),
                "model": "llama-3.3-70b-versatile",
                "name": "Groq"
            }
            logger.info("✅ Groq API configured")
        
        # OpenAI (Priority 3 - Fallback)
        openai_key = api_key or os.getenv("OPENAI_API_KEY")
        if openai_key:
            providers["openai"] = {
                "client": OpenAI(api_key=openai_key),
                "model": "gpt-4",
                "name": "OpenAI"
            }
            logger.info("✅ OpenAI API configured")
        
        return providers
    
    def _select_provider(self):
        """Select the best available provider."""
        priority_order = ["deepseek", "groq", "openai"]
        
        for provider_name in priority_order:
            if provider_name in self.providers:
                self.current_provider = provider_name
                logger.info(f"🎯 Using {self.providers[provider_name]['name']} as primary provider")
                return
        
        raise ValueError(
            "No API keys configured. Please set DEEPSEEK_API_KEY, GROQ_API_KEY, or OPENAI_API_KEY"
        )
    
    def get_client(self) -> OpenAI:
        """Get the current OpenAI-compatible client."""
        if not self.current_provider:
            raise ValueError("No API provider available")
        return self.providers[self.current_provider]["client"]
    
    def get_model(self) -> str:
        """Get the model name for the current provider."""
        if not self.current_provider:
            raise ValueError("No API provider available")
        return self.providers[self.current_provider]["model"]
    
    def get_provider_name(self) -> str:
        """Get the name of the current provider."""
        if not self.current_provider:
            return "None"
        return self.providers[self.current_provider]["name"]
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Any:
        """
        Create a chat completion with automatic fallback.
        
        Args:
            messages: List of message dictionaries
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters
            
        Returns:
            Chat completion response
        """
        client = self.get_client()
        model = self.get_model()
        
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            return response
        except Exception as e:
            logger.error(f"Error with {self.get_provider_name()}: {e}")
            
            # Try fallback providers
            priority_order = ["deepseek", "groq", "openai"]
            for provider_name in priority_order:
                if provider_name != self.current_provider and provider_name in self.providers:
                    logger.info(f"🔄 Falling back to {self.providers[provider_name]['name']}")
                    try:
                        fallback_client = self.providers[provider_name]["client"]
                        fallback_model = self.providers[provider_name]["model"]
                        
                        response = fallback_client.chat.completions.create(
                            model=fallback_model,
                            messages=messages,
                            temperature=temperature,
                            max_tokens=max_tokens,
                            **kwargs
                        )
                        
                        # Update current provider on successful fallback
                        self.current_provider = provider_name
                        logger.info(f"✅ Successfully switched to {self.providers[provider_name]['name']}")
                        return response
                    except Exception as fallback_error:
                        logger.error(f"Fallback to {provider_name} also failed: {fallback_error}")
                        continue
            
            # All providers failed
            raise Exception(f"All API providers failed. Last error: {e}")

# Global instance for easy access
_global_client = None

def get_api_client(api_key: Optional[str] = None) -> UnifiedAPIClient:
    """
    Get or create the global API client instance.
    
    Args:
        api_key: Optional API key (only used on first initialization)
        
    Returns:
        UnifiedAPIClient instance
    """
    global _global_client
    if _global_client is None:
        _global_client = UnifiedAPIClient(api_key)
    return _global_client

def reset_api_client():
    """Reset the global API client (useful for testing)."""
    global _global_client
    _global_client = None
