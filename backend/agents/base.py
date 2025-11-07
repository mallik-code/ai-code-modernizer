"""Base class for all agents with flexible LLM support."""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from llm.factory import create_llm_client
from tools.mcp_tools import MCPToolManager
from utils.logger import setup_logger


class BaseAgent(ABC):
    """Base class for all agents with flexible LLM provider support."""

    def __init__(self, name: str, system_prompt: str, llm_provider: Optional[str] = None, llm_model: Optional[str] = None):
        self.name = name
        self.system_prompt = system_prompt
        self.llm = create_llm_client(llm_provider, llm_model)
        self.tools = MCPToolManager()
        self.logger = setup_logger(f"agent.{name}")
        self.conversation_history = []

    @abstractmethod
    def execute(self, input_data: Dict) -> Dict:
        """Execute agent logic - must be implemented by subclasses"""
        pass

    def think(self, prompt: str, context: Optional[Dict] = None, **kwargs) -> str:
        """Use LLM to think/reason."""
        self.logger.info("thinking", prompt_preview=prompt[:100], llm_provider=self.llm.get_provider_name())

        messages = self.conversation_history.copy()
        messages.append({"role": "user", "content": prompt})

        response = self.llm.generate(
            messages=messages,
            system=self.system_prompt,
            **kwargs
        )

        self.conversation_history.append({"role": "user", "content": prompt})
        self.conversation_history.append({"role": "assistant", "content": response})

        return response

    def use_tool(self, tool_name: str, arguments: Dict) -> Any:
        """Use a tool."""
        self.logger.info("using_tool", tool=tool_name, args=arguments)
        return self.tools.call_tool(tool_name, arguments)

    def reset(self):
        """Reset conversation history."""
        self.conversation_history = []