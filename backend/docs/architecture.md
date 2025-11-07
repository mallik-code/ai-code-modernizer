# Architecture Documentation
## AI-Powered Code Modernization Platform - Backend

**Version**: 1.0
**Last Updated**: 2025-01-15
**Implementation Status**: Phase 1 Complete

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

**Current Status**: ❌ Not Implemented

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

**Current Status**: ❌ Not Implemented

---

### Layer 3: Agent Layer (`agents/`)

**Responsibility**: Intelligent task execution

**Components** (Current):
- ✅ Base agent (`base.py`)
- ❌ Migration Planner (`migration_planner.py`)
- ❌ Runtime Validator (`runtime_validator.py`)
- ❌ Error Analyzer (`error_analyzer.py`)
- ❌ Staging Deployer (`staging_deployer.py`)

**Technology**:
- Python 3.11+
- LLM providers (via factory)
- MCP tools

**Key Patterns**:
- **Template Method**: BaseAgent defines workflow
- **Strategy Pattern**: Interchangeable LLM providers
- **Facade Pattern**: Simplified tool access

**Agent Communication**: Via immutable state (no direct communication)

**Current Status**: 🚧 Base infrastructure implemented, agents pending

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

**Current Status**: ✅ Fully Implemented

---

#### 4B: Tool Integration (`tools/`)

**Responsibility**: External tool access

**Components**:
- 🚧 MCP Tool Manager (`mcp_tools.py`) - Placeholder
- ❌ Docker Validator (`docker_tools.py`)
- ❌ Web Search Tool (future)

**Technology**:
- Model Context Protocol (MCP)
- Docker SDK for Python
- subprocess (for MCP servers)

**MCP Servers**:
- GitHub (`@modelcontextprotocol/server-github`)
- Filesystem (`@modelcontextprotocol/server-filesystem`)

**Key Patterns**:
- **Facade Pattern**: Simplified tool interface
- **Proxy Pattern**: MCP as proxy to external services
- **Adapter Pattern**: Convert MCP protocol to Python

**Current Status**: 🚧 Placeholder implementation

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

**Current Status**: ✅ Fully Implemented

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
│                      Agent                               │
│  agent.use_tool("read_file", {"path": "package.json"})   │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│                  MCPToolManager                          │
│  ┌───────────────────────────────────────────────────┐  │
│  │ call_tool(tool_name, arguments)                   │  │
│  │   1. Find server that owns tool                   │  │
│  │   2. Send JSON-RPC request                        │  │
│  │   3. Read JSON-RPC response                       │  │
│  │   4. Return result                                │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                           ↓
         ┌─────────────────┴─────────────────┐
         ↓                                    ↓
┌──────────────────────────┐    ┌──────────────────────────┐
│    GitHub MCP Server     │    │  Filesystem MCP Server   │
│  (subprocess, STDIO)     │    │   (subprocess, STDIO)    │
├──────────────────────────┤    ├──────────────────────────┤
│ Tools:                   │    │ Tools:                   │
│ • github_get_file        │    │ • read_file              │
│ • github_create_pr       │    │ • write_file             │
│ • github_list_repos      │    │ • list_directory         │
│ • github_create_branch   │    │ • delete_file            │
└──────────────────────────┘    └──────────────────────────┘
         ↓                                    ↓
┌──────────────────────────┐    ┌──────────────────────────┐
│     GitHub API           │    │    Local Filesystem      │
└──────────────────────────┘    └──────────────────────────┘
```

**Communication Protocol** (JSON-RPC 2.0 over STDIO):

```json
// Request (sent to MCP server stdin)
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "read_file",
    "arguments": {"path": "package.json"}
  },
  "id": "req-123"
}

// Response (read from MCP server stdout)
{
  "jsonrpc": "2.0",
  "result": {
    "content": "{\"name\": \"my-app\", ...}"
  },
  "id": "req-123"
}
```

**Design Highlights**:
- **Facade**: MCPToolManager hides complexity
- **Proxy**: MCP servers proxy to external services
- **Process Isolation**: Each MCP server = separate process
- **Standardization**: JSON-RPC 2.0 protocol

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
Agent (use_tool)
    ↓
MCPToolManager
    ↓
GitHub MCP Server (subprocess)
    ↓ JSON-RPC over STDIO
GitHub MCP Server Implementation
    ↓
Octokit/PyGithub
    ↓
GitHub REST API v3
    ↓
GitHub.com
```

**Operations**:
- Read repository files
- Create branches
- Commit changes
- Create pull requests
- Trigger workflows

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

## Migration Path

### Phase 1 → Phase 2 (Current)
- ✅ LLM infrastructure → ❌ Core agents
- ✅ Cost tracking → ❌ Docker validation
- ✅ Logging → ❌ MCP integration

### Phase 2 → Phase 3
- ❌ Core agents → ❌ Advanced agents
- ❌ Docker validation → ❌ Full workflow

### Phase 3 → Phase 4
- ❌ Agent system → ❌ API layer
- ❌ Workflow → ❌ WebSocket

### Phase 4 → Production
- ❌ SQLite → PostgreSQL
- ❌ Local deployment → Cloud deployment
- ❌ No auth → JWT authentication
- ❌ Basic observability → Full monitoring

---

**Document Version**: 1.0
**Last Updated**: 2025-01-15
**Next Review**: After Phase 2 implementation
