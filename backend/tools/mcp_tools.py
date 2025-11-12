"""MCP Tool Manager to connect to MCP servers and expose tools."""
import subprocess
import json
import os
from typing import List, Dict, Any, Optional
from utils.logger import setup_logger


class MCPToolManager:
    """Manage MCP server connections and tool calls.

    This manager handles communication with MCP (Model Context Protocol) servers
    via JSON-RPC 2.0 over STDIO. It supports multiple MCP servers and provides
    a unified interface for tool execution.
    """

    def __init__(self, config_path: str = "mcp_config.json", auto_connect: bool = False):
        """Initialize MCP Tool Manager.

        Args:
            config_path: Path to MCP configuration file
            auto_connect: If True, automatically connect to servers on init
        """
        self.config_path = config_path
        self.servers = {}  # server_name -> {"process": subprocess.Popen, "tools": List[Dict]}
        self.logger = setup_logger("mcp_tools")
        self._load_config()

        if auto_connect:
            self._connect_servers()

    def _load_config(self):
        """Load MCP configuration from JSON file."""
        try:
            with open(self.config_path) as f:
                config = json.load(f)
                self.config = config.get("mcpServers", {})
                self.logger.info("mcp_config_loaded", servers=list(self.config.keys()))
        except FileNotFoundError:
            self.logger.warning("mcp_config_not_found", path=self.config_path)
            self.config = {}
        except json.JSONDecodeError as e:
            self.logger.error("mcp_config_parse_error", error=str(e))
            self.config = {}

    def _connect_servers(self):
        """Connect to all configured MCP servers by starting them as subprocesses.

        Each server is started with STDIO communication for JSON-RPC.
        """
        for server_name, server_config in self.config.items():
            try:
                self._connect_server(server_name, server_config)
            except Exception as e:
                self.logger.error("server_connection_failed",
                                server=server_name,
                                error=str(e))

    def _connect_server(self, server_name: str, server_config: Dict):
        """Connect to a single MCP server.

        Args:
            server_name: Name of the server
            server_config: Configuration dict with 'command', 'args', 'env'
        """
        self.logger.info("connecting_to_server", server=server_name)

        # Prepare environment variables
        env = os.environ.copy()
        if "env" in server_config:
            for key, value in server_config["env"].items():
                # Substitute environment variables
                if value.startswith("${") and value.endswith("}"):
                    env_var = value[2:-1]
                    env[key] = os.getenv(env_var, "")
                else:
                    env[key] = value

        # Start MCP server as subprocess
        command = [server_config["command"]] + server_config.get("args", [])

        try:
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                text=True,
                bufsize=1  # Line buffered
            )

            # Initialize the server by sending the initialize request
            initialize_request = {
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "version": "1.0",
                    "capabilities": {}
                },
                "id": 1
            }
            self._send_jsonrpc(process, initialize_request)

            # Get available tools from the server
            tools = self._get_server_tools(process)

            self.servers[server_name] = {
                "process": process,
                "config": server_config,
                "tools": tools
            }

            self.logger.info("server_connected", server=server_name, pid=process.pid, tools_count=len(tools))

        except Exception as e:
            self.logger.error("server_start_failed", server=server_name, error=str(e))
            raise

    def _send_jsonrpc(self, process: subprocess.Popen, request: Dict) -> Optional[Dict]:
        """Send a JSON-RPC request to the server and optionally return the response."""
        try:
            process.stdin.write(json.dumps(request) + "\n")
            process.stdin.flush()

            # If this is a request that expects a response (has an 'id')
            if "id" in request:
                # Read the response
                response_line = process.stdout.readline()
                if response_line:
                    response = json.loads(response_line.strip())
                    return response
            return None
        except Exception as e:
            self.logger.error("jsonrpc_send_error", error=str(e))
            return None

    def _get_server_tools(self, process: subprocess.Popen) -> List[Dict]:
        """Get list of available tools from the server."""
        try:
            # Request the list of available tools
            tools_request = {
                "jsonrpc": "2.0",
                "method": "tools/list",
                "id": 2
            }
            response = self._send_jsonrpc(process, tools_request)

            if response and "result" in response:
                tools_result = response["result"]
                
                # Handle different possible formats of the tools result
                if isinstance(tools_result, dict) and "tools" in tools_result:
                    # Some servers return a dict with a "tools" key
                    tools = tools_result["tools"]
                elif isinstance(tools_result, list):
                    # Some servers return a list directly
                    tools = tools_result
                else:
                    # If it's neither, treat the whole response as the tools list
                    tools = tools_result

                if isinstance(tools, list):
                    self.logger.info("server_tools_retrieved", count=len(tools))
                    return tools
                else:
                    self.logger.warning("tools_not_list_format", tools_type=type(tools), tools=tools_result)
                    return []
            else:
                self.logger.warning("no_tools_retrieved", response=response)
                return []
        except Exception as e:
            self.logger.error("tools_retrieval_error", error=str(e))
            return []

    def list_tools(self) -> List[Dict]:
        """List all available tools from all connected servers.

        Returns:
            List of tool dictionaries with name, description, server
        """
        all_tools = []
        for server_name, server_data in self.servers.items():
            tools = server_data.get("tools", [])
            for tool in tools:
                # Handle different possible tool formats
                if isinstance(tool, str):
                    # If it's just a string, convert to a basic tool dict
                    all_tools.append({
                        "name": tool,
                        "description": f"Tool {tool} from {server_name}",
                        "server": server_name
                    })
                elif isinstance(tool, dict):
                    # If it's already a dict, add the server info
                    all_tools.append({
                        **tool,
                        "server": server_name
                    })
                else:
                    self.logger.warning("unknown_tool_format", tool=tool, server=server_name)

        # If no servers connected or no tools retrieved, return mock tools for development
        if not all_tools:
            self.logger.warning("no_servers_connected", returning="mock_tools")
            return [
                {"name": "read_file", "description": "Read file contents", "server": "filesystem_mock"},
                {"name": "write_file", "description": "Write file contents", "server": "filesystem_mock"},
                {"name": "github_get_file", "description": "Get file from GitHub", "server": "github_mock"},
                {"name": "github_create_pr", "description": "Create GitHub pull request", "server": "github_mock"}
            ]

        return all_tools

    def call_tool(self, tool_name: str, arguments: Dict) -> Any:
        """Call a specific tool via MCP.

        Args:
            tool_name: Name of the tool to call
            arguments: Tool-specific arguments

        Returns:
            Tool result

        Raises:
            ValueError: If tool is unknown or server not connected
        """
        self.logger.info("calling_tool", tool=tool_name, args=arguments)

        # Find which server owns this tool
        server_name = self._find_tool_server(tool_name)
        
        # If no server owns this tool or no servers connected, fallback to direct implementation
        if not server_name:
            self.logger.warning("no_server_for_tool", tool=tool_name)
            return self._fallback_tool_call(tool_name, arguments)

        # Call the tool on the appropriate server
        try:
            server_data = self.servers[server_name]
            process = server_data["process"]
            
            # Create the tool call request
            tool_call_request = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                },
                "id": 3
            }
            
            response = self._send_jsonrpc(process, tool_call_request)
            
            if response and "result" in response:
                self.logger.info("tool_call_success", tool=tool_name, server=server_name)
                return response["result"]
            elif response and "error" in response:
                self.logger.error("tool_call_error", tool=tool_name, error=response["error"])
                raise ValueError(f"Tool call failed: {response['error']}")
            else:
                self.logger.warning("tool_call_no_response", tool=tool_name)
                return self._fallback_tool_call(tool_name, arguments)
        except Exception as e:
            self.logger.error("tool_call_exception", tool=tool_name, error=str(e))
            return self._fallback_tool_call(tool_name, arguments)

    def _find_tool_server(self, tool_name: str) -> Optional[str]:
        """Find which server provides a specific tool.
        
        Args:
            tool_name: Name of the tool to find
            
        Returns:
            Name of the server that provides the tool, or None if not found
        """
        for server_name, server_data in self.servers.items():
            tools = server_data.get("tools", [])
            for tool in tools:
                # Check if tool name matches (accounting for possible variations)
                if tool.get("name") == tool_name:
                    return server_name
        return None

    def _fallback_tool_call(self, tool_name: str, arguments: Dict) -> Any:
        """Fallback implementation when MCP servers are not connected.

        This allows development to continue while MCP integration is being completed.
        """
        if tool_name == "read_file":
            return self.read_file(arguments.get("path", ""))
        elif tool_name == "write_file":
            return self.write_file(arguments.get("path", ""), arguments.get("content", ""))
        elif tool_name == "github_get_file":
            return f"Content of {arguments.get('path', 'unknown file')} from GitHub (mock)"
        elif tool_name == "github_create_pr":
            return {"status": "success", "pr_url": "https://github.com/example/repo/pull/1 (mock)"}
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    # GitHub tools
    def github_get_file(self, owner: str, repo: str, path: str) -> str:
        """Get file contents from GitHub"""
        return self.call_tool("github_get_file", {
            "owner": owner,
            "repo": repo,
            "path": path
        })

    def github_create_pr(self, owner: str, repo: str, title: str, body: str, head: str, base: str, token: Optional[str] = None):
        """Create a GitHub pull request

        Args:
            owner: Repository owner
            repo: Repository name
            title: PR title
            body: PR description
            head: Source branch
            base: Target branch
            token: GitHub Personal Access Token (optional)
        """
        args = {
            "owner": owner,
            "repo": repo,
            "title": title,
            "body": body,
            "head": head,
            "base": base
        }
        if token:
            args["token"] = token
        return self.call_tool("github_create_pr", args)

    # Filesystem tools (direct implementation)
    def read_file(self, path: str) -> str:
        """Read file contents (direct filesystem access)."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            self.logger.error("file_read_error", path=path, error=str(e))
            raise

    def write_file(self, path: str, content: str):
        """Write file contents (direct filesystem access)."""
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            return {"status": "success", "path": path}
        except Exception as e:
            self.logger.error("file_write_error", path=path, error=str(e))
            raise

    def cleanup(self):
        """Cleanup all MCP server connections."""
        self.logger.info("cleaning_up_servers", count=len(self.servers))

        for server_name, server_data in self.servers.items():
            try:
                process = server_data["process"]
                if process.poll() is None:  # Process still running
                    process.terminate()
                    process.wait(timeout=5)
                    self.logger.info("server_terminated", server=server_name)
            except Exception as e:
                self.logger.error("server_cleanup_error",
                                server=server_name,
                                error=str(e))

        self.servers = {}

    def __del__(self):
        """Destructor to ensure cleanup."""
        self.cleanup()