"""Simple test agent to verify the flexible LLM system."""
from agents.base import BaseAgent
from typing import Dict


class EchoAgent(BaseAgent):
    """Simple test agent that echoes input using configurable LLM provider."""

    def __init__(self, llm_provider: str = "anthropic", llm_model: str = None):
        super().__init__(
            name="echo",
            system_prompt="You are a helpful assistant that echoes back what the user says.",
            llm_provider=llm_provider,
            llm_model=llm_model
        )

    def execute(self, input_data: Dict) -> Dict:
        message = input_data.get("message", "")
        response = self.think(f"Echo this message: {message}")
        return {"response": response, "provider": self.llm.get_provider_name()}


if __name__ == "__main__":
    import os
    
    print("Testing EchoAgent with different LLM providers...")
    
    providers = ["anthropic", "openai", "gemini", "huggingface"]
    
    for provider in providers:
        # Set environment variable for the provider being tested
        if provider == "anthropic":
            os.environ["LLM_PROVIDER"] = "anthropic"
        elif provider == "openai":
            os.environ["LLM_PROVIDER"] = "openai"
        elif provider == "gemini":
            os.environ["LLM_PROVIDER"] = "gemini"
        elif provider == "huggingface":
            os.environ["LLM_PROVIDER"] = "huggingface"
        
        try:
            agent = EchoAgent(llm_provider=provider)
            result = agent.execute({"message": f"Hello from {provider}!"})
            print(f"{provider.capitalize()} agent: {result}")
        except Exception as e:
            print(f"{provider.capitalize()} agent failed: {e}")
    
    # Test cost tracking
    print("\n--- Cost tracking summary ---")
    agent = EchoAgent()
    report = agent.llm.cost_tracker.get_report()
    print(f"Total cost: ${report['total_cost_usd']}")
    print(f"Total tokens: {report['total_input_tokens']} input + {report['total_output_tokens']} output")