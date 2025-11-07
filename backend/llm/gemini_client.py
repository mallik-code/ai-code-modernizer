"""Google Gemini-specific LLM client implementation."""
from typing import List, Dict, Optional
from llm.base import BaseLLMClient
import os


class GeminiLLMClient(BaseLLMClient):
    """Google Gemini-specific implementation of the LLM client."""
    
    def __init__(self, model: str = "gemini-2.0-flash"):
        super().__init__()
        import google.generativeai as genai
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable must be set for Gemini provider")
        
        genai.configure(api_key=api_key)
        self.model_name = model or os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        self.model = genai.GenerativeModel(self.model_name)
    
    def generate(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """Generate response using Google Gemini API."""
        try:
            # Convert messages to Gemini format
            # Gemini expects a different format, with alternating user/assistant messages
            gemini_history = []
            for msg in messages:
                role = "user" if msg["role"] in ["user", "system"] else "model"  # Gemini uses "model" for assistant
                gemini_history.append({
                    "role": role,
                    "parts": [msg["content"]]
                })
            
            # Generate response
            chat = self.model.start_chat(history=gemini_history[:-1] if len(gemini_history) > 1 else [])
            response = chat.send_message(
                gemini_history[-1]["parts"][0] if gemini_history else "Hello",
                generation_config={
                    "max_output_tokens": max_tokens,
                    "temperature": temperature
                }
            )
            
            # Extract usage for cost tracking
            # Note: Gemini doesn't provide usage in the same way as other APIs, so we'll estimate
            input_tokens = sum(len(msg['content'].split()) for msg in messages)
            output_tokens = len(response.text.split())
            self.cost_tracker.track_usage(input_tokens, output_tokens, self.model_name)
            
            return response.text
            
        except Exception as e:
            print(f"Error calling Google Gemini API: {e}")
            raise
    
    def get_provider_name(self) -> str:
        return "gemini"
    
    def count_tokens(self, text: str) -> int:
        """Count tokens using Gemini's tokenizer."""
        import google.generativeai as genai
        result = self.model.count_tokens(text)
        return result.total_tokens if hasattr(result, 'total_tokens') else len(text.split())