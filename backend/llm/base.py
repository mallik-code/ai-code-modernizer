"""Base interface for LLM clients supporting multiple providers."""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from utils.cost_tracker import CostTracker


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""
    
    def __init__(self):
        self.cost_tracker = CostTracker()
    
    @abstractmethod
    def generate(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """Generate response from the LLM.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            system: Optional system prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional provider-specific arguments
            
        Returns:
            Generated text response
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Return the name of the LLM provider."""
        pass
    
    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Count tokens in the given text."""
        pass