"""Anthropic-specific LLM client implementation."""
from typing import List, Dict, Optional
from llm.base import BaseLLMClient
import os


class AnthropicLLMClient(BaseLLMClient):
    """Anthropic-specific implementation of the LLM client."""
    
    def __init__(self, model: str = "claude-sonnet-4-20250514"):
        super().__init__()
        from anthropic import Anthropic
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = model or os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
    
    def generate(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """Generate response using Anthropic API."""
        try:
            response = self.client.messages.create(
                model=self.model,
                messages=messages,
                system=system,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )
            
            # Track costs
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            self.cost_tracker.track_usage(input_tokens, output_tokens, self.model)
            
            return response.content[0].text if response.content else ""
            
        except Exception as e:
            print(f"Error calling Anthropic API: {e}")
            raise
    
    def get_provider_name(self) -> str:
        return "anthropic"
    
    def count_tokens(self, text: str) -> int:
        """Count tokens using Anthropic's tokenizer."""
        import tiktoken
        # Anthropic uses the same encoding as GPT-4
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))