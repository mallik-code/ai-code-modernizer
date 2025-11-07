"""Factory for creating LLM clients based on configuration."""
from typing import Optional
from llm.anthropic_client import AnthropicLLMClient
from llm.openai_client import OpenAILLMClient
from llm.huggingface_client import HuggingFaceLLMClient
from llm.gemini_client import GeminiLLMClient
from llm.qwen_client import QwenLLMClient
from llm.base import BaseLLMClient
import os
from dotenv import load_dotenv

# Load environment variables from .env file when this module is imported
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path, override=True)


def create_llm_client(provider: Optional[str] = None, model: Optional[str] = None) -> BaseLLMClient:
    """Factory function to create appropriate LLM client based on configuration.
    
    Args:
        provider: LLM provider ('anthropic', 'openai', 'huggingface', 'gemini', 'qwen', etc.)
        model: Specific model name (optional, will use default for provider)
    
    Returns:
        Instance of the appropriate LLM client
    """
    # Determine provider from parameter or environment
    provider = provider or os.getenv("LLM_PROVIDER", "anthropic").lower()
    
    if provider == "anthropic":
        return AnthropicLLMClient(model)
    elif provider == "openai":
        return OpenAILLMClient(model)
    elif provider == "huggingface":
        return HuggingFaceLLMClient(model)
    elif provider == "gemini":
        return GeminiLLMClient(model)
    elif provider == "qwen":
        return QwenLLMClient(model)
    else:
        # Default to Anthropic if provider is unknown
        print(f"Unknown provider '{provider}', defaulting to Anthropic")
        return AnthropicLLMClient(model)