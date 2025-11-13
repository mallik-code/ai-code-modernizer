"""Base class for all agents with flexible LLM support."""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from llm.factory import create_llm_client
from tools.mcp_tools import MCPToolManager
from utils.logger import setup_logger
import json


class BaseAgent(ABC):
    """Base class for all agents with flexible LLM provider support."""

    def __init__(self, name: str, system_prompt: str, llm_provider: Optional[str] = None, llm_model: Optional[str] = None, broadcaster: Optional[Callable] = None):
        self.name = name
        self.system_prompt = system_prompt
        self.llm = create_llm_client(llm_provider, llm_model)
        self.tools = MCPToolManager()
        self.logger = setup_logger(f"agent.{name}")
        self.conversation_history = []
        self.broadcaster = broadcaster  # New broadcaster for WebSocket updates

    def send_update(self, message: str, message_type: str = "info", extra_data: Optional[Dict] = None):
        """Send update to WebSocket if available."""
        if self.broadcaster:
            try:
                update_data = {
                    "type": message_type,
                    "agent": self.name,
                    "message": message,
                    "timestamp": datetime.now().isoformat()
                }
                if extra_data:
                    update_data.update(extra_data)
                
                self.broadcaster(json.dumps(update_data))
            except Exception as e:
                self.logger.warning(f"Failed to broadcast message: {e}")

    @abstractmethod
    def execute(self, input_data: Dict) -> Dict:
        """Execute agent logic - must be implemented by subclasses"""
        pass

    def think(self, prompt: str, context: Optional[Dict] = None, **kwargs) -> str:
        """Use LLM to think/reason."""
        self.logger.info("thinking", prompt_preview=prompt[:100], llm_provider=self.llm.get_provider_name())

        # Send update about thinking process
        self.send_update(
            message="Thinking and analyzing...",
            message_type="agent_thinking",
            extra_data={"prompt_preview": prompt[:100]}
        )

        messages = self.conversation_history.copy()
        messages.append({"role": "user", "content": prompt})

        response = self.llm.generate(
            messages=messages,
            system=self.system_prompt,
            **kwargs
        )

        self.conversation_history.append({"role": "user", "content": prompt})
        self.conversation_history.append({"role": "assistant", "content": response})

        # Send update when thinking is complete
        self.send_update(
            message="Analysis complete",
            message_type="agent_thinking_complete",
            extra_data={"response_preview": response[:200]}
        )

        return response

    def use_tool(self, tool_name: str, arguments: Dict) -> Any:
        """Use a tool."""
        self.logger.info("using_tool", tool=tool_name, args=arguments)
        
        # Send update about tool usage
        self.send_update(
            message=f"Using tool: {tool_name}",
            message_type="tool_use",
            extra_data={"tool": tool_name, "arguments": arguments}
        )
        
        result = self.tools.call_tool(tool_name, arguments)
        
        # Send update about tool completion
        self.send_update(
            message=f"Tool {tool_name} completed",
            message_type="tool_complete",
            extra_data={"tool": tool_name, "result_preview": str(result)[:200]}
        )
        
        return result

    def reset(self):
        """Reset conversation history."""
        self.conversation_history = []