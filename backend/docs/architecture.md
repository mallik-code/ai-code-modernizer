# Architecture Documentation
## AI-Powered Code Modernization Platform - Backend

**Version**: 2.0
**Last Updated**: 2025-11-08
**Implementation Status**: Phase 4 Complete (60% Overall)

---

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [System Layers](#system-layers)
3. [Component Architecture](#component-architecture)
4. [Deployment Architecture](#deployment-architecture)
5. [Data Architecture](#data-architecture)
6. [Integration Architecture](#integration-architecture)
7. [Security Architecture](#security-architecture)
8. [Scalability Architecture](#scalability-architecture)
9. [MCP Tools Summary](#mcp-tools-summary)
10. [Implementation Progress](#implementation-progress)

---

## Architecture Overview

### Architecture Style
**Layered + Event-Driven Multi-Agent System**

```
┌─────────────────────────────────────────────────────────┐
│               Presentation Layer                         │
│  • FastAPI endpoints                                     │
│  • WebSocket server                                      │
│  • Request/response models                               │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│              Orchestration Layer                         │
│  • LangGraph workflow engine                            │
│  • State management                                      │
│  • Event publishing                                      │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│                 Agent Layer                              │
│  • Autonomous specialized agents                        │
│  • LLM-powered reasoning                                 │
│  • Tool-based execution                                  │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│              Infrastructure Layer                        │
│  • LLM providers                                         │
│  • MCP tool servers                                      │
│  • Docker runtime                                        │
│  • Data persistence                                      │
└─────────────────────────────────────────────────────────┘
```

### Key Architectural Principles

1. **Separation of Concerns**: Each layer has distinct responsibilities
2. **Dependency Inversion**: High-level modules don't depend on low-level modules
3. **Open/Closed Principle**: Open for extension (new agents), closed for modification
4. **Interface Segregation**: Small, focused interfaces (BaseLLMClient, BaseAgent)
5. **Single Responsibility**: Each component has one reason to change

---

## System Layers

### Layer 1: Presentation Layer (`api/`)

**Responsibility**: External communication

**Components**:
- FastAPI application (`main.py`)
- REST API endpoints (`routes.py`)
- WebSocket server (`websocket.py`)
- Request/response models (`models.py`)
- Middleware (CORS, auth, rate limiting)

**Technology**:
- FastAPI 0.104+
- WebSockets
- Pydantic (validation)
- Uvicorn (ASGI server)

**Interfaces**:
```python
# REST API
POST /api/projects/analyze
POST /api/projects/upgrade
GET  /api/projects/{id}/status

# WebSocket
WS   /ws/{client_id}
```

**Current Status**: ❌ Not Implemented (Phase 5)

---

### Layer 2: Orchestration Layer (`graph/`)

**Responsibility**: Workflow coordination and state management

**Components**:
- Workflow graph (`workflow.py`)
- State schema (`state.py`)
- Node implementations (`nodes.py`)
- Checkpoint manager
- Event publisher

**Technology**:
- LangGraph 0.2.16+
- SQLite/PostgreSQL (state storage)
- Async Python

**Key Patterns**:
- **State Machine**: Workflow as directed graph
- **Command Pattern**: Each node is a command
- **Memento Pattern**: Checkpointing for undo/resume
- **Conditional Routing**: Routes based on validation success/failure
- **Retry Logic**: Automatic retry with configurable max attempts

**Current Status**: ✅ **COMPLETE** (Phase 4)
- ✅ State schema (`graph/state.py`) - MigrationState TypedDict
- ✅ Workflow graph (`graph/workflow.py`) - Complete orchestration
- ✅ Conditional routing - Validation success → Deploy, Failure → Analyze
- ✅ Retry logic - Up to 3 attempts (configurable)
- ✅ Cost tracking - Aggregated across all agents
- ✅ Error recovery - Routes failures to Error Analyzer
- ✅ 18 tests passing (15 unit + 3 integration)

---

### Layer 3: Agent Layer (`agents/`)

**Responsibility**: Intelligent task execution

**Components** (Current):
- ✅ Base agent (`base.py`) - Multi-provider support
- ✅ Migration Planner (`migration_planner.py`) - 7 tests passing
- ✅ Runtime Validator (`runtime_validator.py`) - Docker integration complete
- ✅ Error Analyzer (`error_analyzer.py`) - 19 tests passing
- ✅ Staging Deployer (`staging_deployer.py`) - 19 tests passing

**Technology**:
- Python 3.11+
- LLM providers (via factory)
- MCP tools

**Key Patterns**:
- **Template Method**: BaseAgent defines workflow
- **Strategy Pattern**: Interchangeable LLM providers
- **Facade Pattern**: Simplified tool access

**Agent Communication**: Via immutable state (no direct communication)

**Current Status**: ✅ **COMPLETE** (Phase 3)
- All 4 specialized agents fully implemented
- 52 agent tests passing (7 planner + 19 error analyzer + 19 deployer + 7 validator)
- Multi-provider LLM support in all agents
- Comprehensive error handling and fallback logic

---

### Layer 4: Infrastructure Layer

#### 4A: LLM Provider Abstraction (`llm/`)

**Responsibility**: Multi-provider LLM access

**Components**:
- ✅ Base interface (`base.py`)
- ✅ Factory (`factory.py`)
- ✅ Provider implementations:
  - `anthropic_client.py` (Claude Sonnet 4, Opus 4, Haiku 4)
  - `openai_client.py` (GPT-4o, GPT-4 Turbo, GPT-3.5 Turbo)
  - `gemini_client.py` (Gemini 2.0/3.0)
  - `huggingface_client.py` (Llama, etc.)
  - `qwen_client.py` (Qwen Turbo/Plus/Max)

**Technology**:
- `anthropic` SDK
- `openai` SDK
- `google-generativeai` SDK
- `huggingface_hub` SDK
- `dashscope` SDK (Qwen)

**Key Patterns**:
- **Abstract Factory**: Create provider-specific clients
- **Strategy Pattern**: Interchangeable LLM backends
- **Adapter Pattern**: Normalize different API interfaces

**Current Status**: ✅ **FULLY IMPLEMENTED** (Phase 1)
- 5 LLM providers fully functional
- Factory pattern with automatic provider selection
- Comprehensive cost tracking across all providers
- 20+ models with accurate pricing data

---

#### 4B: Tool Integration (`tools/`)

**Responsibility**: External tool access via Model Context Protocol (MCP)

**Components**:
- ✅ MCP Tool Manager (`mcp_tools.py`) - Phase 2 (75% complete)
- ✅ Docker Validator (`docker_tools.py`) - Fully functional
- ❌ Web Search Tool (future)

**Technology**:
- Model Context Protocol (MCP) - JSON-RPC 2.0 over STDIO
- Docker SDK for Python
- subprocess (for MCP servers)
- Node.js (for MCP servers)

### MCP (Model Context Protocol) Integration

**MCP** is a standardized protocol that allows AI agents to securely access external systems through JSON-RPC 2.0 communication over STDIO. This project uses MCP to provide agents with capabilities like GitHub operations and filesystem access.

#### MCP Servers Used

##### 1. GitHub MCP Server (`@modelcontextprotocol/server-github`)

**Purpose**: GitHub repository operations

**Capabilities**:
- `github_get_file` - Read repository files
- `github_create_pr` - Create pull requests
- `github_create_branch` - Create branches
- `github_push_files` - Push files to repository
- `github_list_repos` - List repositories
- `github_search_issues` - Search for similar issues

**Used By**:
- **Migration Planner** - Read `package.json`, `requirements.txt` from repositories
- **Staging Deployer** - Create branches, commit changes, create pull requests
- **Error Analyzer** - Search for similar issues on GitHub

**Configuration** (in `mcp_config.json`):
```json
{
  "github": {
    "command": "npx.cmd",
    "args": ["@modelcontextprotocol/server-github"],
    "env": {
      "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"
    }
  }
}
```

**Environment Variables Required**:
- `GITHUB_TOKEN` - Personal access token with `repo` and `workflow` scopes

##### 2. Filesystem MCP Server (`@modelcontextprotocol/server-filesystem`)

**Purpose**: Local file system operations

**Capabilities**:
- `read_file` - Read local files
- `write_file` - Write local files
- `list_directory` - List directories
- `delete_file` - Delete files
- `get_file_info` - Get file metadata

**Used By**:
- **Migration Planner** - Read local `package.json`, `requirements.txt`
- **All Agents** - Read configuration files, project files

**Configuration** (in `mcp_config.json`):
```json
{
  "filesystem": {
    "command": "npx.cmd",
    "args": ["@modelcontextprotocol/server-filesystem", "."]
  }
}
```

**Note**: The last argument (`.`) specifies the allowed directory root.

#### MCP Tool Manager (`tools/mcp_tools.py`)

**Location**: `backend/tools/mcp_tools.py`

**Key Methods**:

```python
class MCPToolManager:
    def __init__(self, config_path: str = "mcp_config.json"):
        """Initialize MCP tool manager with configuration."""

    async def connect(self):
        """Establish connections to all MCP servers."""

    def read_file(self, path: str) -> str:
        """Read file via filesystem MCP server."""

    def write_file(self, path: str, content: str) -> bool:
        """Write file via filesystem MCP server."""

    def github_get_file(self, owner: str, repo: str, path: str) -> str:
        """Get file from GitHub repository."""

    def github_create_pr(self, owner: str, repo: str, title: str,
                         body: str, head: str, base: str) -> str:
        """Create GitHub pull request. Returns PR URL."""

    def github_create_branch(self, owner: str, repo: str,
                            branch: str, from_branch: str = "main") -> bool:
        """Create new Git branch."""

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Generic tool invocation - routes to appropriate MCP server."""
```

**Example Usage**:
```python
from tools.mcp_tools import MCPToolManager

# Initialize
tools = MCPToolManager()

# Read local file
content = tools.read_file("package.json")

# Read from GitHub
gh_content = tools.github_get_file("owner", "repo", "path/to/file")

# Create PR
pr_url = tools.github_create_pr(
    owner="owner",
    repo="repo",
    title="Upgrade dependencies",
    body="Automated upgrade via AI Code Modernizer",
    head="upgrade-branch",
    base="main"
)

# Generic tool call
result = tools.call_tool("read_file", {"path": "package.json"})
```

#### Installing MCP Servers

```bash
# Install GitHub MCP server globally
npm install -g @modelcontextprotocol/server-github

# Install Filesystem MCP server globally
npm install -g @modelcontextprotocol/server-filesystem

# Test MCP connectivity
cd backend
python tools/mcp_tools.py
```

**Key Patterns**:
- **Facade Pattern**: Simplified tool interface via MCPToolManager
- **Proxy Pattern**: MCP servers proxy to external services (GitHub API, filesystem)
- **Adapter Pattern**: Convert JSON-RPC 2.0 protocol to Python methods
- **Process Isolation**: Each MCP server runs as separate subprocess

**Current Status**: ✅ **PHASE 2 COMPLETE** (75%)
- ✅ JSON-RPC 2.0 communication with MCP servers
- ✅ Server initialization handshake
- ✅ Dynamic tool discovery via `tools/list`
- ✅ Tool registry and routing
- ✅ Actual MCP server communication
- ✅ Fallback implementations (filesystem direct, GitHub mock)
- ✅ Docker validator fully functional
- ❌ Retry logic (TODO)
- ❌ Timeout handling (TODO)

---

#### 4C: Utilities (`utils/`)

**Responsibility**: Cross-cutting concerns

**Components**:
- ✅ Cost Tracker (`cost_tracker.py`)
- ✅ Logger (`logger.py`)

**Technology**:
- `structlog` (logging)
- `rich` (console output)
- `tiktoken` (token counting)

**Key Patterns**:
- **Observer Pattern**: Cost tracking
- **Decorator Pattern**: Logging
- **Singleton-like**: Shared tracker instances

**Current Status**: ✅ **FULLY IMPLEMENTED** (Phase 1)
- Multi-provider cost tracking with accurate pricing
- Structured logging with rich console output
- Historical cost entries with per-model breakdown

---

## Component Architecture

### LLM Provider Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Agent Layer                           │
│  agent.think("Analyze this code...")                     │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│                    LLM Factory                           │
│  create_llm_client(provider, model)                      │
│    ↓ Based on LLM_PROVIDER env var                      │
└─────────────────────────────────────────────────────────┘
                           ↓
         ┌─────────────────┴─────────────────┬─────────────┐
         ↓                 ↓                   ↓             ↓
┌────────────────┐ ┌────────────────┐ ┌────────────┐ ┌────────────┐
│   Anthropic    │ │     OpenAI     │ │   Gemini   │ │  Qwen/HF   │
│     Client     │ │     Client     │ │   Client   │ │   Clients  │
├────────────────┤ ├────────────────┤ ├────────────┤ ├────────────┤
│ generate()     │ │ generate()     │ │ generate() │ │ generate() │
│ count_tokens() │ │ count_tokens() │ │ count_tok. │ │ count_tok. │
│ get_provider() │ │ get_provider() │ │ get_prov.  │ │ get_prov.  │
└────────────────┘ └────────────────┘ └────────────┘ └────────────┘
         ↓                 ↓                   ↓             ↓
┌─────────────────────────────────────────────────────────┐
│                  Cost Tracker                            │
│  track_usage(input_tokens, output_tokens, model)         │
│  get_report() → total_cost, per-model breakdown          │
└─────────────────────────────────────────────────────────┘
```

**Design Highlights**:
- **Abstraction**: All providers implement `BaseLLMClient`
- **Factory**: Single entry point for client creation
- **Cost Tracking**: Automatic, transparent to agents
- **Extensibility**: Add new providers without changing agents

---

### Agent Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    BaseAgent (Abstract)                  │
│  ┌───────────────────────────────────────────────────┐  │
│  │ __init__(name, system_prompt, llm_provider, ...)  │  │
│  │   • self.llm = create_llm_client()                │  │
│  │   • self.tools = MCPToolManager()                 │  │
│  │   • self.logger = setup_logger()                  │  │
│  │   • self.conversation_history = []                │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────┐  │
│  │ think(prompt, **kwargs) → str                     │  │
│  │   • Add to conversation history                   │  │
│  │   • Call self.llm.generate()                      │  │
│  │   • Log activity                                  │  │
│  │   • Return response                               │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────┐  │
│  │ use_tool(tool_name, args) → Any                   │  │
│  │   • Log tool call                                 │  │
│  │   • Invoke via self.tools.call_tool()             │  │
│  │   • Return result                                 │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────┐  │
│  │ execute(input_data: Dict) → Dict  [ABSTRACT]     │  │
│  │   • Subclasses implement specific logic           │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                           ↓
        ┌──────────────────┴──────────────────┬──────────────┐
        ↓                  ↓                   ↓              ↓
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  Migration   │ │   Runtime    │ │    Error     │ │   Staging    │
│   Planner    │ │  Validator   │ │   Analyzer   │ │   Deployer   │
│    Agent     │ │    Agent     │ │    Agent     │ │    Agent     │
├──────────────┤ ├──────────────┤ ├──────────────┤ ├──────────────┤
│ execute():   │ │ execute():   │ │ execute():   │ │ execute():   │
│ • Read deps  │ │ • Create     │ │ • Parse logs │ │ • Create     │
│ • Analyze    │ │   Docker     │ │ • Diagnose   │ │   branch     │
│ • Research   │ │ • Validate   │ │ • Generate   │ │ • Commit     │
│ • Plan       │ │ • Test       │ │   fixes      │ │ • Create PR  │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
```

**Design Highlights**:
- **Template Method**: `think()` and `use_tool()` are reusable
- **Abstract Method**: `execute()` forces implementation
- **Dependency Injection**: LLM provider configurable
- **Separation**: Agents don't manage state (LangGraph does)

---

### MCP Tool Architecture

```
┌─────────────────────────────────────────────────────────┐
│            AI Agents (Python)                            │
│  • Migration Planner Agent                               │
│  • Runtime Validator Agent                               │
│  • Error Analyzer Agent                                  │
│  • Staging Deployer Agent                                │
│                                                           │
│  agent.use_tool("read_file", {"path": "package.json"})   │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│          MCPToolManager (Python)                         │
│  ┌───────────────────────────────────────────────────┐  │
│  │ call_tool(tool_name, arguments)                   │  │
│  │   1. Find server that owns tool                   │  │
│  │   2. Send JSON-RPC request via STDIN              │  │
│  │   3. Read JSON-RPC response from STDOUT           │  │
│  │   4. Parse and return result                      │  │
│  └───────────────────────────────────────────────────┘  │
│                                                           │
│  • Server lifecycle management (start/stop)              │
│  • Tool discovery and registry                           │
│  • Request/response parsing                              │
│  • Error handling and fallbacks                          │
└─────────────────────────────────────────────────────────┘
                           ↓
         ┌─────────────────┴─────────────────┐
         ↓                                    ↓
┌──────────────────────────┐    ┌──────────────────────────┐
│    GitHub MCP Server     │    │  Filesystem MCP Server   │
│  (Node.js subprocess)    │    │  (Node.js subprocess)    │
│  Communication: STDIO    │    │  Communication: STDIO    │
├──────────────────────────┤    ├──────────────────────────┤
│ Tools Available:         │    │ Tools Available:         │
│ • github_get_file        │    │ • read_file              │
│ • github_create_pr       │    │ • write_file             │
│ • github_list_repos      │    │ • list_directory         │
│ • github_create_branch   │    │ • delete_file            │
│ • github_push_files      │    │ • get_file_info          │
│ • github_search_issues   │    │                          │
└──────────────────────────┘    └──────────────────────────┘
         ↓                                    ↓
┌──────────────────────────┐    ┌──────────────────────────┐
│     GitHub REST API      │    │    Local Filesystem      │
│  • api.github.com        │    │  • Direct file I/O       │
│  • Requires GITHUB_TOKEN │    │  • Sandboxed to root dir │
└──────────────────────────┘    └──────────────────────────┘
```

**Communication Protocol** (JSON-RPC 2.0 over STDIO):

```json
// 1. Initialize handshake (on server start)
{
  "jsonrpc": "2.0",
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {},
    "clientInfo": {
      "name": "ai-code-modernizer",
      "version": "1.0.0"
    }
  },
  "id": "init-1"
}

// 2. Discover available tools
{
  "jsonrpc": "2.0",
  "method": "tools/list",
  "params": {},
  "id": "list-1"
}

// 3. Tool invocation (sent to MCP server stdin)
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "read_file",
    "arguments": {"path": "package.json"}
  },
  "id": "req-123"
}

// 4. Tool response (read from MCP server stdout)
{
  "jsonrpc": "2.0",
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\"name\": \"my-app\", \"version\": \"1.0.0\", ...}"
      }
    ]
  },
  "id": "req-123"
}

// 5. Error response (on failure)
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32602,
    "message": "File not found: package.json"
  },
  "id": "req-123"
}
```

**MCP Server Lifecycle**:

```python
# 1. Server Initialization (on MCPToolManager creation)
process = subprocess.Popen(
    ["npx.cmd", "@modelcontextprotocol/server-github"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    env={"GITHUB_PERSONAL_ACCESS_TOKEN": os.getenv("GITHUB_TOKEN")}
)

# 2. Handshake
send_json_rpc(process, "initialize", {...})
response = read_json_rpc(process)

# 3. Tool Discovery
send_json_rpc(process, "tools/list", {})
tools = read_json_rpc(process)  # Returns list of available tools

# 4. Tool Invocations (during agent execution)
send_json_rpc(process, "tools/call", {"name": "read_file", "arguments": {...}})
result = read_json_rpc(process)

# 5. Cleanup (on exit)
process.terminate()
```

**Agent-Specific MCP Usage**:

| Agent | MCP Tools Used | Purpose |
|-------|----------------|---------|
| **Migration Planner** | `read_file` (filesystem)<br>`github_get_file` (GitHub) | Read `package.json`, `requirements.txt` from local or GitHub repos |
| **Runtime Validator** | None (uses Docker SDK directly) | Validates in isolated containers |
| **Error Analyzer** | `github_search_issues` (GitHub) | Search for similar error reports |
| **Staging Deployer** | `github_create_branch` (GitHub)<br>`github_push_files` (GitHub)<br>`github_create_pr` (GitHub) | Create upgrade branch, commit changes, open PR |

**Design Highlights**:
- **Facade**: MCPToolManager hides complexity from agents
- **Proxy**: MCP servers proxy to external services (GitHub API, filesystem)
- **Process Isolation**: Each MCP server = separate Node.js subprocess
- **Standardization**: JSON-RPC 2.0 protocol ensures interoperability
- **Async Communication**: Non-blocking I/O with subprocesses
- **Error Recovery**: Fallback implementations for critical tools
- **Security**: GitHub token passed via environment, not exposed in code

---

### Workflow Architecture (LangGraph)

```
┌─────────────────────────────────────────────────────────┐
│                    Workflow Graph                        │
│                                                           │
│  ┌──────────┐                                            │
│  │  START   │                                            │
│  └────┬─────┘                                            │
│       ↓                                                   │
│  ┌────────────────┐                                      │
│  │   Migration    │                                      │
│  │    Planner     │                                      │
│  └────┬───────────┘                                      │
│       ↓                                                   │
│  ┌────────────────┐                                      │
│  │    Runtime     │                                      │
│  │   Validator    │                                      │
│  └────┬───────────┘                                      │
│       ↓                                                   │
│  [Validation Success?]                                   │
│       ├─ YES ──→ ┌──────────────┐                       │
│       │          │   Staging    │                       │
│       │          │   Deployer   │                       │
│       │          └──────┬───────┘                       │
│       │                 ↓                                 │
│       │          ┌──────────┐                           │
│       │          │   END    │                           │
│       │          └──────────┘                           │
│       │                                                   │
│       └─ NO ───→ ┌──────────────┐                       │
│                  │    Error     │                       │
│                  │   Analyzer   │                       │
│                  └──────┬───────┘                       │
│                         ↓                                 │
│                  [Retry Count < 3?]                      │
│                         ├─ YES ──→ [Runtime Validator]  │
│                         │                                 │
│                         └─ NO ───→ [Human Interrupt]    │
│                                    ↓                      │
│                             [User Decision]              │
│                               ├─ Approve ──→ [Deployer] │
│                               └─ Abort ────→ [END]      │
└─────────────────────────────────────────────────────────┘
```

**State Flow**:

```python
# 1. Initial state
state = {
    "project_path": "/path/to/project",
    "status": "analyzing",
    "retry_count": 0
}

# 2. After Migration Planner
state = {
    ...state,
    "dependencies": {...},
    "migration_strategy": {...},
    "status": "validating"
}

# 3. After Runtime Validator (success)
state = {
    ...state,
    "validation_result": {"status": "success", ...},
    "status": "deploying"
}

# 4. After Staging Deployer
state = {
    ...state,
    "pr_url": "https://github.com/...",
    "status": "complete"
}
```

**Design Highlights**:
- **State Machine**: Workflow = graph of states
- **Conditional Routing**: Edges based on state
- **Immutable State**: Each node returns new state
- **Checkpointing**: State saved after each node
- **Resumable**: Can restart from any checkpoint

---

## Deployment Architecture

### Development Environment

```
┌─────────────────────────────────────────────────────────┐
│               Developer Laptop                           │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Backend (Python)                                  │  │
│  │  • FastAPI server (port 8000)                      │  │
│  │  • LangGraph workflows                             │  │
│  │  • Agents                                          │  │
│  │  • SQLite database                                 │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────┐  │
│  │  MCP Servers (Node.js)                             │  │
│  │  • GitHub MCP (npx)                                │  │
│  │  • Filesystem MCP (npx)                            │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Docker Engine                                     │  │
│  │  • Validation containers                           │  │
│  │  • Auto-cleanup                                    │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Frontend (React)                                  │  │
│  │  • Vite dev server (port 5173)                     │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│               External Services                          │
│  • Anthropic API                                         │
│  • OpenAI API                                            │
│  • Google Gemini API                                     │
│  • GitHub API                                            │
└─────────────────────────────────────────────────────────┘
```

**Start Commands**:
```bash
# Terminal 1: Backend
cd backend
source .venv/bin/activate
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev
```

---

### Production Architecture (Future)

```
┌─────────────────────────────────────────────────────────┐
│                    Load Balancer                         │
│  • HTTPS termination                                     │
│  • Health checks                                         │
│  • Rate limiting                                         │
└─────────────────────────────────────────────────────────┘
                           ↓
         ┌─────────────────┴─────────────────┐
         ↓                                    ↓
┌──────────────────────┐         ┌──────────────────────┐
│   Frontend Server    │         │  Backend Server 1-N  │
│  (Static files)      │         │  (FastAPI)           │
│  • React build       │         │  • Gunicorn workers  │
│  • CDN              │         │  • WebSocket support  │
└──────────────────────┘         └──────────────────────┘
                                            ↓
                         ┌──────────────────┴──────────────┐
                         ↓                                  ↓
              ┌──────────────────┐         ┌──────────────────┐
              │   PostgreSQL     │         │   Redis Cache    │
              │  • State storage │         │  • Session cache │
              │  • Workflows     │         │  • Rate limits   │
              └──────────────────┘         └──────────────────┘
```

**Scaling**:
- **Horizontal**: Multiple backend servers
- **Vertical**: Larger Docker host for validations
- **Database**: PostgreSQL with read replicas
- **Caching**: Redis for session/rate limiting

---

## Data Architecture

### Database Schema

```sql
-- Workflow executions table
CREATE TABLE workflow_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_name VARCHAR(255) NOT NULL,
    project_path TEXT NOT NULL,
    state JSONB NOT NULL,
    status VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    total_cost DECIMAL(10, 6)
);

CREATE INDEX idx_workflow_status ON workflow_executions(status);
CREATE INDEX idx_workflow_project ON workflow_executions(project_name);
CREATE INDEX idx_workflow_created ON workflow_executions(created_at);

-- Checkpoints table (LangGraph)
CREATE TABLE checkpoints (
    workflow_id UUID REFERENCES workflow_executions(id),
    checkpoint_id VARCHAR(255) PRIMARY KEY,
    state JSONB NOT NULL,
    checkpoint_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_checkpoint_workflow ON checkpoints(workflow_id);

-- Cost tracking table
CREATE TABLE cost_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID REFERENCES workflow_executions(id),
    model VARCHAR(100) NOT NULL,
    input_tokens INTEGER NOT NULL,
    output_tokens INTEGER NOT NULL,
    input_cost DECIMAL(10, 6) NOT NULL,
    output_cost DECIMAL(10, 6) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_cost_workflow ON cost_entries(workflow_id);
CREATE INDEX idx_cost_model ON cost_entries(model);

-- Audit log table
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID REFERENCES workflow_executions(id),
    event_type VARCHAR(100) NOT NULL,
    agent_name VARCHAR(100),
    event_data JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_workflow ON audit_log(workflow_id);
CREATE INDEX idx_audit_event ON audit_log(event_type);
```

---

## Integration Architecture

### LLM Provider Integration

```
Application Code
    ↓
LLM Factory (create_llm_client)
    ↓
BaseLLMClient Interface
    ↓
┌─────────────────────────────────────────────────────────┐
│            Provider-Specific Clients                     │
├──────────────┬──────────────┬──────────────┬───────────┤
│  Anthropic   │   OpenAI     │   Gemini     │ Qwen/HF   │
│  Client      │   Client     │   Client     │ Clients   │
└──────────────┴──────────────┴──────────────┴───────────┘
    ↓              ↓              ↓              ↓
┌──────────────┐ ┌────────────┐ ┌────────────┐ ┌────────┐
│ anthropic    │ │  openai    │ │  google.   │ │ dash   │
│   SDK        │ │   SDK      │ │  genai SDK │ │ scope  │
└──────────────┘ └────────────┘ └────────────┘ └────────┘
    ↓              ↓              ↓              ↓
┌─────────────────────────────────────────────────────────┐
│              External LLM APIs                           │
│  • api.anthropic.com                                     │
│  • api.openai.com                                        │
│  • generativelanguage.googleapis.com                     │
│  • dashscope.aliyuncs.com                                │
│  • api-inference.huggingface.co                          │
└─────────────────────────────────────────────────────────┘
```

---

### GitHub Integration (via MCP)

```
┌─────────────────────────────────────────────────────────┐
│          AI Agents (Python)                              │
│  agent.use_tool("github_create_pr", {...})               │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│          MCPToolManager (Python)                         │
│  • Routes tool call to GitHub MCP server                 │
│  • Formats JSON-RPC request                              │
│  • Handles authentication (GITHUB_TOKEN)                 │
└─────────────────────────────────────────────────────────┘
    ↓ JSON-RPC over STDIN/STDOUT
┌─────────────────────────────────────────────────────────┐
│    GitHub MCP Server (Node.js subprocess)                │
│  @modelcontextprotocol/server-github                     │
│  • Parses JSON-RPC requests                              │
│  • Executes GitHub operations                            │
│  • Returns results as JSON-RPC responses                 │
└─────────────────────────────────────────────────────────┘
    ↓ HTTPS
┌─────────────────────────────────────────────────────────┐
│          GitHub REST API (v3)                            │
│  https://api.github.com                                  │
│  • Authenticated via Personal Access Token               │
│  • Operations: repos, branches, commits, PRs, issues     │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│          GitHub.com                                      │
│  • User's repositories                                   │
│  • Pull requests                                         │
│  • CI/CD workflows                                       │
└─────────────────────────────────────────────────────────┘
```

**GitHub MCP Server Operations**:

| Tool | Description | Used By | Example |
|------|-------------|---------|---------|
| `github_get_file` | Read file from repository | Migration Planner | Read `package.json` from GitHub repo |
| `github_create_branch` | Create new branch | Staging Deployer | Create `upgrade/dependencies-20250110` |
| `github_push_files` | Commit and push files | Staging Deployer | Push updated `package.json` |
| `github_create_pr` | Create pull request | Staging Deployer | Open PR with upgrade changes |
| `github_list_repos` | List user repositories | Future features | Browse available projects |
| `github_search_issues` | Search issues | Error Analyzer | Find similar error reports |

**Example Usage Flow**:

```python
# 1. Staging Deployer creates branch
tools.github_create_branch(
    owner="user",
    repo="my-app",
    branch="upgrade/dependencies-20250110",
    from_branch="main"
)

# 2. Push upgraded files
tools.github_push_files(
    owner="user",
    repo="my-app",
    branch="upgrade/dependencies-20250110",
    files={
        "package.json": updated_package_json,
        "package-lock.json": updated_package_lock
    },
    message="chore: upgrade dependencies\n\n🤖 Generated with AI Code Modernizer"
)

# 3. Create pull request
pr_url = tools.github_create_pr(
    owner="user",
    repo="my-app",
    title="Upgrade dependencies to latest versions",
    body="""## Summary
- express: 4.16.0 → 4.19.2
- body-parser: 1.18.3 → 1.20.2
- cors: 2.8.4 → 2.8.5

## Validation
✅ Build successful
✅ Install successful
✅ Runtime successful
✅ Health check passed

🤖 Generated with AI Code Modernizer""",
    head="upgrade/dependencies-20250110",
    base="main"
)

print(f"PR created: {pr_url}")
```

**Authentication**:
```bash
# Generate Personal Access Token at: https://github.com/settings/tokens
# Scopes required: repo, workflow

# Add to .env file
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxx
```

**Security Features**:
- Token passed via environment variable (never hardcoded)
- Token not logged or exposed in responses
- MCP server runs in isolated subprocess
- Operations limited to user's accessible repositories

---

### Docker Integration

```
Runtime Validator Agent
    ↓
DockerValidator (tools/docker_tools.py)
    ↓
Docker SDK for Python
    ↓
Docker Engine API
    ↓
Docker Daemon
    ↓
Containers (isolated environments)
```

**Operations**:
- Create containers from images
- Execute commands in containers
- Copy files to/from containers
- Monitor container logs
- Cleanup containers

---

## Security Architecture

### Authentication & Authorization (Future)

```
┌─────────────────────────────────────────────────────────┐
│                      Client                              │
└─────────────────────────────────────────────────────────┘
                           ↓
                   [API Gateway]
                           ↓
                  [Auth Middleware]
                  • JWT validation
                  • Role checking
                  • Rate limiting
                           ↓
                  [Backend Services]
```

### Secrets Management

```
┌─────────────────────────────────────────────────────────┐
│              Environment Variables                       │
│  • .env file (development)                               │
│  • Docker secrets (production)                           │
│  • AWS Secrets Manager (future)                          │
└─────────────────────────────────────────────────────────┘
                           ↓
                  [Application Code]
                  • os.getenv("API_KEY")
                  • Never hardcoded
                  • Never committed
```

### Docker Isolation

```
┌─────────────────────────────────────────────────────────┐
│                   Host System                            │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Docker Container (Validation)                     │  │
│  │  • No network access                               │  │
│  │  • Read-only project files                         │  │
│  │  • Resource limits (CPU, memory)                   │  │
│  │  • Automatic cleanup                               │  │
│  │  • No access to host filesystem                    │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## Scalability Architecture

### Horizontal Scaling

```
┌─────────────────────────────────────────────────────────┐
│                  Load Balancer                           │
│  • Round-robin distribution                              │
│  • Health checking                                       │
│  • Session affinity (for WebSocket)                      │
└─────────────────────────────────────────────────────────┘
                           ↓
         ┌─────────────────┼─────────────────┐
         ↓                 ↓                  ↓
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Backend 1   │  │  Backend 2   │  │  Backend 3   │
│  (FastAPI)   │  │  (FastAPI)   │  │  (FastAPI)   │
└──────────────┘  └──────────────┘  └──────────────┘
         ↓                 ↓                  ↓
┌─────────────────────────────────────────────────────────┐
│              Shared State (PostgreSQL)                   │
│  • Workflow executions                                   │
│  • Checkpoints                                           │
└─────────────────────────────────────────────────────────┘
```

### Resource Optimization

**LLM Costs**:
- Cache common responses
- Use cheaper models for simple tasks
- Batch requests when possible
- Stream responses (reduce latency perception)

**Docker Containers**:
- Reuse base images (layer caching)
- Parallel container execution
- Resource limits prevent runaway processes
- Automatic cleanup after validation

**Database**:
- Index frequently queried fields
- Archive old workflow data
- Read replicas for queries
- Connection pooling

---

## Technology Decisions

### Language: Python 3.11+
- **Why**: Excellent AI/ML ecosystem, async support, type hints
- **Alternatives Considered**: Node.js (less mature AI libs), Go (harder AI integration)

### Orchestration: LangGraph
- **Why**: Built for multi-agent, state management, human-in-the-loop
- **Alternatives Considered**: AutoGen (experimental), CrewAI (less flexible)

### API Framework: FastAPI
- **Why**: Modern, async, auto-docs, type safety
- **Alternatives Considered**: Flask (no async), Django (too heavy)

### Database: SQLite → PostgreSQL
- **Why**: SQLite for dev simplicity, Postgres for production scale
- **Alternatives Considered**: MongoDB (overkill for structured data)

### Containerization: Docker
- **Why**: Standard, cross-platform, isolation
- **Alternatives Considered**: VMs (too heavy), Podman (less adoption)

### Tool Protocol: MCP
- **Why**: Anthropic-backed, standardized, future-proof
- **Alternatives Considered**: Custom tool API (more work, less standard)

---

## Observability

### Logging Strategy

**Levels**:
- **DEBUG**: Detailed execution traces
- **INFO**: Normal operations (agent start/complete)
- **WARNING**: Recoverable issues (retries)
- **ERROR**: Failures requiring attention

**Structured Logs**:
```json
{
  "timestamp": "2025-01-15T10:30:00Z",
  "level": "info",
  "event": "agent_started",
  "agent": "migration_planner",
  "workflow_id": "abc-123",
  "project": "express-app"
}
```

### Metrics (Future)

- **Workflow Metrics**: Success rate, duration, retry count
- **Agent Metrics**: Execution time, failure rate
- **LLM Metrics**: Token usage, cost, latency
- **System Metrics**: CPU, memory, container count

### Tracing (Future)

- **LangSmith**: Agent execution tracing
- **OpenTelemetry**: Distributed tracing

---

## MCP Tools Summary

This project uses **Model Context Protocol (MCP)** to provide AI agents with standardized access to external tools and services. MCP is a JSON-RPC 2.0 protocol over STDIO that enables secure, sandboxed communication between agents and external systems.

### MCP Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                  AI Agents                               │
│  Migration Planner | Validator | Analyzer | Deployer    │
└─────────────────────────────────────────────────────────┘
                     ↓ Python API
┌─────────────────────────────────────────────────────────┐
│              MCPToolManager (Python)                     │
│  • Lifecycle: Start/stop MCP server subprocesses         │
│  • Communication: JSON-RPC 2.0 over STDIN/STDOUT         │
│  • Discovery: Dynamic tool listing                       │
│  • Routing: Tool name → appropriate server               │
└─────────────────────────────────────────────────────────┘
                     ↓ JSON-RPC 2.0
         ┌───────────┴───────────┐
         ↓                       ↓
┌──────────────────┐    ┌──────────────────┐
│  GitHub MCP      │    │ Filesystem MCP   │
│  Server          │    │ Server           │
│  (Node.js)       │    │ (Node.js)        │
└──────────────────┘    └──────────────────┘
         ↓                       ↓
┌──────────────────┐    ┌──────────────────┐
│  GitHub API      │    │ Local FS         │
└──────────────────┘    └──────────────────┘
```

### MCP Servers in Use

#### 1. GitHub MCP Server
**NPM Package**: `@modelcontextprotocol/server-github`
**Purpose**: GitHub repository operations
**Installation**: `npm install -g @modelcontextprotocol/server-github`

**Available Tools**:
- `github_get_file` - Read files from repositories
- `github_create_branch` - Create Git branches
- `github_push_files` - Commit and push changes
- `github_create_pr` - Create pull requests
- `github_list_repos` - List accessible repositories
- `github_search_issues` - Search for issues

**Environment Variables**: `GITHUB_TOKEN` (Personal Access Token with `repo` + `workflow` scopes)

#### 2. Filesystem MCP Server
**NPM Package**: `@modelcontextprotocol/server-filesystem`
**Purpose**: Local file system operations
**Installation**: `npm install -g @modelcontextprotocol/server-filesystem`

**Available Tools**:
- `read_file` - Read local files
- `write_file` - Write local files
- `list_directory` - List directory contents
- `delete_file` - Delete files
- `get_file_info` - Get file metadata

**Configuration**: Last argument specifies allowed directory root (e.g., `.` for current directory)

### Agent → MCP Tool Mapping

| Agent | Tools Used | Purpose |
|-------|------------|---------|
| **Migration Planner** | `read_file` (filesystem)<br>`github_get_file` (GitHub) | Read `package.json`, `requirements.txt` from local or remote repos |
| **Runtime Validator** | None | Uses Docker SDK directly for container validation |
| **Error Analyzer** | `github_search_issues` (GitHub) | Search for similar error reports and solutions |
| **Staging Deployer** | `github_create_branch` (GitHub)<br>`github_push_files` (GitHub)<br>`github_create_pr` (GitHub) | Create upgrade branches, commit changes, open PRs |

### MCP Configuration

**File**: `backend/mcp_config.json`

```json
{
  "github": {
    "command": "npx.cmd",
    "args": ["@modelcontextprotocol/server-github"],
    "env": {
      "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"
    }
  },
  "filesystem": {
    "command": "npx.cmd",
    "args": ["@modelcontextprotocol/server-filesystem", "."]
  }
}
```

### MCP Usage Example

```python
from tools.mcp_tools import MCPToolManager

# Initialize tool manager
tools = MCPToolManager()

# Read local file
package_json = tools.read_file("package.json")

# Read from GitHub
readme = tools.github_get_file(
    owner="user",
    repo="my-app",
    path="README.md"
)

# Create branch and PR
tools.github_create_branch(
    owner="user",
    repo="my-app",
    branch="upgrade/dependencies-20250110",
    from_branch="main"
)

tools.github_push_files(
    owner="user",
    repo="my-app",
    branch="upgrade/dependencies-20250110",
    files={"package.json": updated_content},
    message="chore: upgrade dependencies"
)

pr_url = tools.github_create_pr(
    owner="user",
    repo="my-app",
    title="Upgrade dependencies",
    body="Automated upgrade",
    head="upgrade/dependencies-20250110",
    base="main"
)
```

### MCP Security Features

- **Process Isolation**: Each MCP server runs in separate subprocess
- **Sandboxing**: Filesystem server restricted to configured root directory
- **Token Management**: GitHub token passed via environment, never hardcoded
- **No Logging**: Sensitive data (tokens, file contents) not logged
- **Least Privilege**: Agents only have access to tools they need

### Testing MCP Tools

```bash
# Test MCP connectivity and tool discovery
cd backend
python tools/mcp_tools.py

# Expected output:
# ✓ GitHub MCP server connected
# ✓ Filesystem MCP server connected
# ✓ Tools discovered: github_get_file, read_file, write_file, ...
```

### MCP Implementation Status

✅ **Completed**:
- JSON-RPC 2.0 communication protocol
- Server lifecycle management (start/stop/restart)
- Dynamic tool discovery via `tools/list`
- Tool routing and invocation
- Error handling and fallbacks
- GitHub and Filesystem server integration

❌ **Future Enhancements**:
- Retry logic with exponential backoff
- Request timeout handling
- Connection pooling for multiple agents
- Additional MCP servers (e.g., web search, database)

---

## Implementation Progress

### ✅ Phase 1: Core Infrastructure (100%)
- ✅ LLM infrastructure (5 providers)
- ✅ Cost tracking (multi-provider)
- ✅ Logging (structured)
- ✅ MCP Tool Manager (Phase 2 - 75%)

### ✅ Phase 2: Base Agent Infrastructure (100%)
- ✅ Base Agent class
- ✅ Multi-provider support
- ✅ Tool integration patterns

### ✅ Phase 3: Core Agents (100%)
- ✅ Migration Planner (7 tests)
- ✅ Runtime Validator (Docker integration)
- ✅ Error Analyzer (19 tests)
- ✅ Staging Deployer (19 tests)

### ✅ Phase 4: LangGraph Workflow (100%)
- ✅ State schema (`graph/state.py`)
- ✅ Workflow orchestration (`graph/workflow.py`)
- ✅ Conditional routing
- ✅ Retry logic (configurable)
- ✅ Error recovery
- ✅ 18 workflow tests passing

### ❌ Phase 5: API Layer (0%)
- ❌ FastAPI main application
- ❌ REST API endpoints
- ❌ WebSocket server
- ❌ Request/response models

### ❌ Phase 6: Testing & Polish (0%)
- ❌ Integration tests
- ❌ End-to-end tests
- ❌ Demo application
- ❌ Documentation

### Future: Production Readiness
- ❌ SQLite → PostgreSQL
- ❌ Local deployment → Cloud deployment
- ❌ No auth → JWT authentication
- ❌ Basic observability → Full monitoring

**Overall Progress**: 60% (4/7 phases complete)

---

**Document Version**: 2.0
**Last Updated**: 2025-11-08
**Next Review**: After Phase 5 (API Layer) implementation

---

## Test Coverage Summary

**Total Tests**: 70+ passing
- **LLM Providers**: Multi-provider tests
- **Migration Planner**: 7 tests
- **Error Analyzer**: 19 tests
- **Staging Deployer**: 19 tests
- **Workflow**: 18 tests (15 unit + 3 integration)
- **Runtime Validator**: Integration with Docker

**Test Execution**:
```bash
# All tests
pytest tests/ -v                           # 70+ tests

# Specific components
pytest tests/test_migration_planner.py -v  # 7 tests
pytest tests/test_error_analyzer.py -v     # 19 tests
pytest tests/test_staging_deployer.py -v   # 19 tests
pytest tests/test_workflow.py -v           # 15 tests
pytest tests/test_workflow_integration.py -v # 3 tests
```
