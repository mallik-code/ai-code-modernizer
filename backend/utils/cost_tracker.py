"""Cost tracking for multiple LLM providers."""
import tiktoken
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class CostEntry:
    """Represents a single cost tracking entry."""
    model: str
    input_tokens: int
    output_tokens: int
    input_cost: float
    output_cost: float
    timestamp: float


class CostTracker:
    """Track costs across multiple LLM providers."""

    # Pricing per 1M tokens (as of 2025)
    PRICING = {
        # Anthropic models
        "claude-sonnet-4-20250514": {"input": 3.00, "output": 15.00},
        "claude-opus-4-20250514": {"input": 15.00, "output": 75.00},
        "claude-haiku-4-20250514": {"input": 0.25, "output": 1.25},
        
        # OpenAI models
        "gpt-4o": {"input": 5.00, "output": 15.00},
        "gpt-4o-2024-08-06": {"input": 2.50, "output": 10.00},
        "gpt-4-turbo": {"input": 10.00, "output": 30.00},
        "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
        
        # Google Gemini models
        "gemini-2.0-flash": {"input": 0.35, "output": 1.05},
        "gemini-2.0-pro": {"input": 3.50, "output": 10.50},
        "gemini-3.0-pro": {"input": 4.00, "output": 12.00},
        
        # Qwen models
        "qwen-turbo": {"input": 0.10, "output": 0.20},
        "qwen-plus": {"input": 0.40, "output": 1.20},
        "qwen-max": {"input": 1.00, "output": 3.00},
        "qwen-72b-chat": {"input": 0.80, "output": 2.40},
        "qwen-14b-chat": {"input": 0.30, "output": 0.90},
        
        # Common open-source model pricing (approximate)
        "meta-llama/Llama-3.2-3B-Instruct": {"input": 0.05, "output": 0.05},
        "meta-llama/Llama-3.1-8B-Instruct": {"input": 0.10, "output": 0.10},
        "microsoft/DialoGPT-large": {"input": 0.08, "output": 0.08},
    }

    def __init__(self):
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0
        self.entries: List[CostEntry] = []

    def track_usage(self, input_tokens: int, output_tokens: int, model: str):
        """Track token usage and calculate cost."""
        from time import time
        
        # Get pricing for the model, with fallback to a default
        pricing = self.PRICING.get(model, self.PRICING.get("gpt-3.5-turbo", {"input": 0.50, "output": 1.50}))
        
        # Calculate costs (per token, not per million)
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        total_cost = input_cost + output_cost
        
        # Update totals
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_cost += total_cost
        
        # Add entry to history
        entry = CostEntry(
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            input_cost=input_cost,
            output_cost=output_cost,
            timestamp=time()
        )
        self.entries.append(entry)

    def get_report(self) -> Dict:
        """Get cost report."""
        return {
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_cost_usd": round(self.total_cost, 6),
            "model_costs": self._get_model_breakdown()
        }
    
    def _get_model_breakdown(self) -> Dict[str, Dict]:
        """Get cost breakdown by model."""
        model_breakdown = {}
        for entry in self.entries:
            if entry.model not in model_breakdown:
                model_breakdown[entry.model] = {
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cost_usd": 0.0
                }
            
            model_breakdown[entry.model]["input_tokens"] += entry.input_tokens
            model_breakdown[entry.model]["output_tokens"] += entry.output_tokens
            model_breakdown[entry.model]["cost_usd"] += (entry.input_cost + entry.output_cost)
        
        return model_breakdown

    def reset(self):
        """Reset all tracked costs."""
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0
        self.entries = []