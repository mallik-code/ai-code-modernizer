"""OpenAI-specific LLM client implementation."""
from typing import List, Dict, Optional
from llm.base import BaseLLMClient
import os


class OpenAILLMClient(BaseLLMClient):
    """OpenAI-specific implementation of the LLM client."""
    
    def __init__(self, model: str = "gpt-4o"):
        super().__init__()
        from openai import OpenAI
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o")
    
    def generate(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """Generate response using OpenAI API."""
        try:
            # Add system message to messages if provided
            full_messages = []
            if system:
                full_messages.append({"role": "system", "content": system})
            full_messages.extend(messages)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=full_messages,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )
            
            # Extract usage for cost tracking
            usage = response.usage
            if usage:
                input_tokens = usage.prompt_tokens
                output_tokens = usage.completion_tokens
                self.cost_tracker.track_usage(input_tokens, output_tokens, self.model)
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            raise
    
    def get_provider_name(self) -> str:
        return "openai"
    
    def count_tokens(self, text: str) -> int:
        """Count tokens using tiktoken."""
        import tiktoken
        encoding = tiktoken.encoding_for_model(self.model)
        return len(encoding.encode(text))