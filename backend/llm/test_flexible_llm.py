"""Test script to verify the flexible LLM system works with different providers."""
import os
from dotenv import load_dotenv
from llm.factory import create_llm_client
from llm.anthropic_client import AnthropicLLMClient
from llm.openai_client import OpenAILLMClient
from llm.gemini_client import GeminiLLMClient
from llm.huggingface_client import HuggingFaceLLMClient
from llm.qwen_client import QwenLLMClient


def test_llm_client(provider_name: str, model: str = None):
    """Test a specific LLM provider."""
    print(f"\n--- Testing {provider_name} ---")
    try:
        client = create_llm_client(provider_name, model)
        print(f"Provider: {client.get_provider_name()}")
        
        # Simple test - count some tokens
        test_text = "This is a test of the token counting system."
        token_count = client.count_tokens(test_text)
        print(f"Token count for '{test_text}': {token_count}")
        
        # Note: Actual generation would require API keys to be set
        print(f"Client created successfully for {provider_name}")
        
    except Exception as e:
        print(f"Error with {provider_name}: {e}")


if __name__ == "__main__":
    print("Testing flexible LLM system...")
    
    # Load environment variables from .env file
    dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)
        print(f"Loaded environment variables from {dotenv_path}")
    else:
        print(f"Warning: .env file not found at {dotenv_path}")
    
    # Test each provider (will work if proper environment variables are set)
    providers = [
        ("anthropic", "claude-sonnet-4-20250514"),
        ("openai", "gpt-4o"),
        ("gemini", "gemini-2.0-flash"),
        ("huggingface", "meta-llama/Llama-3.2-3B-Instruct"),
        ("qwen", "qwen-turbo")  # Added Qwen provider
    ]
    
    for provider, model in providers:
        test_llm_client(provider, model)
    
    # Test default provider
    print(f"\n--- Testing default provider ---")
    default_client = create_llm_client()
    print(f"Default provider: {default_client.get_provider_name()}")
    
    # Show cost tracking
    print(f"\n--- Cost tracking ---")
    report = default_client.cost_tracker.get_report()
    print(f"Cost report: {report}")