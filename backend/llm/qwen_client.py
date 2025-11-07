"""Qwen-specific LLM client implementation."""
from typing import List, Dict, Optional
from llm.base import BaseLLMClient
import os


class QwenLLMClient(BaseLLMClient):
    """Qwen-specific implementation of the LLM client."""
    
    def __init__(self, model: str = "qwen-turbo"):
        super().__init__()
        # Import dashscope (Alibaba's SDK for Qwen)
        import dashscope
        api_key = os.getenv("QWEN_API_KEY") or os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            raise ValueError("QWEN_API_KEY or DASHSCOPE_API_KEY environment variable must be set for Qwen provider")
        
        self.api_key = api_key
        self.model = model or os.getenv("QWEN_MODEL", "qwen-turbo")
        dashscope.api_key = api_key
    
    def generate(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """Generate response using Qwen API via DashScope."""
        try:
            import dashscope
            from http import HTTPStatus
            
            # Prepare messages with optional system prompt
            full_messages = []
            if system:
                full_messages.append({"role": "system", "content": system})
            full_messages.extend(messages)
            
            # Generate response using dashscope
            response = dashscope.Generation.call(
                model=self.model,
                messages=full_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            # Check response status
            if response.status_code == HTTPStatus.OK:
                # Extract usage for cost tracking
                usage = response.usage
                if usage:
                    input_tokens = usage.input_tokens or 0
                    output_tokens = usage.output_tokens or 0
                    self.cost_tracker.track_usage(input_tokens, output_tokens, self.model)
                
                return response.output.text
            else:
                raise Exception(f"Qwen API error: {response.code} - {response.message}")
                
        except Exception as e:
            print(f"Error calling Qwen API: {e}")
            raise
    
    def get_provider_name(self) -> str:
        return "qwen"
    
    def count_tokens(self, text: str) -> int:
        """Count tokens using a simple approximation."""
        # For lack of a specific Qwen tokenizer, use a common one
        import tiktoken
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))