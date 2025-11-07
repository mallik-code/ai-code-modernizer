"""HuggingFace-specific LLM client implementation."""
from typing import List, Dict, Optional
from llm.base import BaseLLMClient
import os


class HuggingFaceLLMClient(BaseLLMClient):
    """HuggingFace-specific implementation of the LLM client."""
    
    def __init__(self, model: str = "meta-llama/Llama-3.2-3B-Instruct"):
        super().__init__()
        from huggingface_hub import InferenceClient
        api_key = os.getenv("HUGGINGFACE_API_KEY")
        self.client = InferenceClient(model=model, token=api_key)
        self.model = model or os.getenv("HUGGINGFACE_MODEL", "meta-llama/Llama-3.2-3B-Instruct")
    
    def generate(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """Generate response using HuggingFace Inference API."""
        try:
            # Prepare messages for chat completion format
            full_messages = []
            if system:
                full_messages.append({"role": "system", "content": system})
            full_messages.extend(messages)
            
            # Generate response
            response = self.client.chat.completions.create(
                model=self.model,
                messages=full_messages,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )
            
            # Extract usage for cost tracking (approximation)
            input_tokens = sum(len(msg['content'].split()) for msg in full_messages)
            output_tokens = len(response.choices[0].message.content.split())
            self.cost_tracker.track_usage(input_tokens, output_tokens, self.model)
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error calling HuggingFace API: {e}")
            raise
    
    def get_provider_name(self) -> str:
        return "huggingface"
    
    def count_tokens(self, text: str) -> int:
        """Count tokens approximately."""
        import tiktoken
        # Use a common tokenizer for approximation
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))