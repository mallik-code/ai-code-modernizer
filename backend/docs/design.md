# System Design Document
## AI-Powered Code Modernization Platform

**Version**: 1.0
**Last Updated**: 2025-01-15
**Status**: Phase 1 Complete

---

## Table of Contents
1. [Design Philosophy](#design-philosophy)
2. [System Architecture](#system-architecture)
3. [Component Design](#component-design)
4. [Data Flow](#data-flow)
5. [Agent Design](#agent-design)
6. [LLM Integration Design](#llm-integration-design)
7. [MCP Integration Design](#mcp-integration-design)
8. [State Management](#state-management)
9. [Error Handling](#error-handling)
10. [Security Design](#security-design)

---

## Design Philosophy

### Core Principles

#### 1. **Provider Agnosticism**
- **Rationale**: Avoid vendor lock-in, enable cost optimization
- **Implementation**: Abstract base classes + factory pattern
- **Benefits**:
  - Switch LLM providers without code changes
  - Compare provider performance
  - Optimize costs by routing to cheapest provider

#### 2. **Testability First**
- **Rationale**: Enable confident iteration and deployment
- **Implementation**:
  - Every component has standalone `if __name__ == "__main__"` test
  - Agents executable independently before integration
  - Mock implementations for external dependencies
- **Benefits**:
  - Fast feedback loops
  - Easy debugging
  - Confident refactoring

#### 3. **Human-in-the-Loop**
- **Rationale**: Balance automation with safety
- **Implementation**: Workflow interrupts at critical decision points
- **Decision Points**:
  - After 3 failed retries (escalate)
  - Before staging deployment (approve)
  - When multiple valid strategies exist (choose)
  - For production deployment (always approve)

#### 4. **Stateless Agents, Stateful Workflow**
- **Rationale**: Simplify agent development, enable checkpointing
- **Implementation**:
  - Agents don't store state (pure functions)
  - LangGraph manages all state
  - State persisted to database
- **Benefits**:
  - Agents easily testable
  - Workflow can resume after crashes
  - Audit trails automatic

#### 5. **Fail Fast, Recover Gracefully**
- **Rationale**: Detect issues early, provide clear paths forward
- **Implementation**:
  - Validation at every step
  - Structured errors with context
  - Automatic retry with exponential backoff
  - Clear escalation paths

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React)                         │
│  • Project upload UI                                         │
│  • Agent activity visualization                              │
│  • Real-time workflow graph                                  │
│  • Human decision prompts                                    │
│  • Cost & metrics dashboard                                  │
└─────────────────────────────────────────────────────────────┘
                           ↕ REST API + WebSocket
┌─────────────────────────────────────────────────────────────┐
│                    Backend API Layer                         │
│  • FastAPI application (api/)                                │
│  • Request validation                                        │
│  • WebSocket manager                                         │
│  • Authentication (future)                                   │
└─────────────────────────────────────────────────────────────┘
                           ↕
┌─────────────────────────────────────────────────────────────┐
│              LangGraph Orchestrator (graph/)                 │
│  • Workflow state management                                 │
│  • Agent routing                                             │
│  • Conditional logic                                         │
│  • Retry mechanism                                           │
│  • Checkpointing                                             │
│  • Human interrupts                                          │
└─────────────────────────────────────────────────────────────┘
                           ↕
┌─────────────────────────────────────────────────────────────┐
│                  Multi-Agent System (agents/)                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Migration   │  │   Runtime    │  │    Error     │     │
│  │   Planner    │  │  Validator   │  │   Analyzer   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│  ┌──────────────┐                                           │
│  │   Staging    │    All inherit from BaseAgent             │
│  │   Deployer   │                                           │
│  └──────────────┘                                           │
└─────────────────────────────────────────────────────────────┘
                           ↕
┌─────────────────────────────────────────────────────────────┐
│               Infrastructure Layer                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  LLM Factory │  │   MCP Tool   │  │    Docker    │     │
│  │   (llm/)     │  │   Manager    │  │  Validator   │     │
│  │              │  │  (tools/)    │  │  (tools/)    │     │
│  │ • Anthropic  │  │              │  │              │     │
│  │ • OpenAI     │  │ • GitHub     │  │ • Container  │     │
│  │ • Gemini     │  │ • Filesystem │  │   creation   │     │
│  │ • HuggingF   │  │ • Custom     │  │ • Validation │     │
│  │ • Qwen       │  │              │  │ • Cleanup    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │     Cost     │  │   Logging    │                        │
│  │   Tracker    │  │   (utils/)   │                        │
│  │  (utils/)    │  │              │                        │
│  └──────────────┘  └──────────────┘                        │
└─────────────────────────────────────────────────────────────┘
                           ↕
┌─────────────────────────────────────────────────────────────┐
│                 External Services                            │
│  • LLM APIs (Anthropic, OpenAI, Google, Qwen, HF)          │
│  • GitHub API                                                │
│  • Docker Engine                                             │
│  • Web Search (optional)                                     │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Design

### 1. LLM Factory (`llm/`)

#### Design Pattern: Factory + Strategy

```python
# Abstract interface
class BaseLLMClient(ABC):
    def generate(messages, system, **kwargs) -> str
    def get_provider_name() -> str
    def count_tokens(text) -> int

# Factory function
def create_llm_client(provider, model) -> BaseLLMClient:
    if provider == "anthropic":
        return AnthropicLLMClient(model)
    elif provider == "openai":
        return OpenAILLMClient(model)
    # ... etc
```

#### Provider Implementations

**Anthropic Client** (`llm/anthropic_client.py`):
- Uses `anthropic` SDK
- Supports Claude Sonnet 4, Opus 4, Haiku 4
- Token counting via API response
- Streaming support (future)

**OpenAI Client** (`llm/openai_client.py`):
- Uses `openai` SDK
- Supports GPT-4o, GPT-4 Turbo, GPT-3.5 Turbo
- Token counting via `tiktoken`
- Function calling (future)

**Gemini Client** (`llm/gemini_client.py`):
- Uses `google-generativeai` SDK
- Supports Gemini 2.0 Flash/Pro, 3.0 Pro
- Token counting via API
- Safety settings configurable

**HuggingFace Client** (`llm/huggingface_client.py`):
- Uses `huggingface_hub` inference API
- Supports Llama, DialoGPT, etc.
- Token counting approximate (via `tiktoken`)

**Qwen Client** (`llm/qwen_client.py`):
- Uses `dashscope` SDK
- Supports Qwen Turbo, Plus, Max, 72B, 14B
- Token counting via API
- Streaming support

#### Configuration

```bash
# .env
LLM_PROVIDER=anthropic  # Default provider
ANTHROPIC_API_KEY=sk-ant-xxx
ANTHROPIC_MODEL=claude-sonnet-4-20250514
```

#### Cost Integration

All clients automatically track costs via `CostTracker`:
- Input/output tokens counted
- Costs calculated per pricing table
- Historical entries stored
- Reports generated

---

### 2. Cost Tracker (`utils/cost_tracker.py`)

#### Design Pattern: Observer + Singleton-like

```python
class CostTracker:
    PRICING = {
        "claude-sonnet-4-20250514": {"input": 3.00, "output": 15.00},
        # ... all models
    }

    def track_usage(input_tokens, output_tokens, model):
        # Calculate costs
        # Update totals
        # Store entry with timestamp

    def get_report() -> Dict:
        # Total tokens
        # Total cost
        # Per-model breakdown
```

#### Features
- **Automatic Tracking**: LLM clients call automatically
- **Historical Data**: All entries stored with timestamps
- **Model Breakdown**: Costs separated by model
- **Pricing Database**: Centralized pricing (easy updates)

---

### 3. Logging System (`utils/logger.py`)

#### Design Pattern: Decorator

```python
def setup_logger(name: str, level="INFO"):
    # Configure structlog
    # Add rich console handler
    # Return configured logger

# Usage
logger = setup_logger("agent.planner")
logger.info("analyzing_dependencies",
            project="express-app",
            dependency_count=47)
```

#### Features
- **Structured Output**: Key-value pairs, not just messages
- **Rich Console**: Colors, formatting, stack traces
- **ISO Timestamps**: All logs timestamped
- **Context Preservation**: Fields flow through calls

---

### 4. Base Agent (`agents/base.py`)

#### Design Pattern: Template Method

```python
class BaseAgent(ABC):
    def __init__(self, name, system_prompt, llm_provider, llm_model):
        self.llm = create_llm_client(llm_provider, llm_model)
        self.tools = MCPToolManager()
        self.logger = setup_logger(f"agent.{name}")
        self.conversation_history = []

    @abstractmethod
    def execute(self, input_data: Dict) -> Dict:
        """Subclasses implement specific logic"""
        pass

    def think(self, prompt, **kwargs) -> str:
        """Template method for LLM reasoning"""
        # Add to conversation history
        # Call LLM
        # Track cost
        # Log activity
        # Return response

    def use_tool(self, tool_name, arguments) -> Any:
        """Template method for tool use"""
        # Log tool call
        # Invoke via MCP
        # Return result
```

#### Benefits
- **Consistent Interface**: All agents work the same way
- **Reusable Logic**: Don't repeat LLM/tool code
- **Easy Testing**: Mock LLM/tools at base level
- **Flexible Providers**: Override per agent if needed

---

### 5. MCP Tool Manager (`tools/mcp_tools.py`)

#### Design Pattern: Facade + Adapter

**Current State**: Placeholder with mock implementations

**Target Design**:

```python
class MCPToolManager:
    def __init__(self, config_path="mcp_config.json"):
        self.servers = {}  # server_name -> process
        self._load_config()
        self._connect_servers()

    def _connect_servers(self):
        # Start each MCP server as subprocess
        # STDIO communication
        # Initialize JSON-RPC

    def call_tool(self, tool_name, arguments):
        # Determine which server owns tool
        # Send JSON-RPC request
        # Parse response
        # Return result
```

**MCP Protocol**:
- **Transport**: STDIO (stdin/stdout)
- **Format**: JSON-RPC 2.0
- **Messages**:
  - `initialize`: Handshake
  - `tools/list`: Get available tools
  - `tools/call`: Invoke tool

**Configuration** (`mcp_config.json`):
```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem"]
    }
  }
}
```

---

## Data Flow

### 1. Project Analysis Flow

```
User uploads project
    ↓
API validates request
    ↓
Create workflow execution
    ↓
Initialize MigrationState
    ↓
LangGraph starts workflow
    ↓
Migration Planner Agent
    │
    ├─ Read dependency file (MCP: filesystem)
    ├─ Call LLM to analyze dependencies
    ├─ Research breaking changes (MCP: web search)
    ├─ Generate migration strategy
    ├─ Update state
    │
    ↓
Return to workflow
    ↓
Update state: migration_strategy = {...}
    ↓
Checkpoint state to database
    ↓
WebSocket: broadcast agent_completed event
    ↓
Continue to Runtime Validator
```

### 2. Validation Flow

```
Runtime Validator Agent receives state
    ↓
Extract migration_strategy from state
    ↓
Create Docker container (Docker SDK)
    ↓
Copy project files into container
    ↓
Install upgraded dependencies
    ↓
Start application
    ↓
Run health checks
    ↓
Collect logs
    ↓
[Success?]
   ↓
   ├─ YES → Return validation_result: success
   │         Update state: status = "validated"
   │         Cleanup container
   │         → Continue to Staging Deployer
   │
   ├─ NO → Return validation_result: failure
           Update state: status = "error", errors = [...]
           Cleanup container
           → Route to Error Analyzer
```

### 3. Error Recovery Flow

```
Error Analyzer receives failed state
    ↓
Parse errors from validation logs
    ↓
Call LLM to diagnose root cause
    ↓
Research similar issues (MCP: web search)
    ↓
Generate fix strategies
    ↓
Rank by confidence
    ↓
[Confidence > 0.8 AND retry_count < 3?]
   ↓
   ├─ YES → Update migration_strategy with fix
   │         Increment retry_count
   │         Update state: status = "retrying"
   │         → Route back to Runtime Validator
   │
   ├─ NO → Update state: status = "requires_human"
           → Human-in-the-loop interrupt
           → Present options to user
           → User chooses strategy
           → Continue or abort
```

### 4. Deployment Flow

```
Staging Deployer receives validated state
    ↓
Extract migration_strategy and validation_result
    ↓
Create Git branch (MCP: GitHub)
    ↓
Apply code changes
    ↓
Commit changes
    ↓
Push to remote
    ↓
Create pull request (MCP: GitHub)
    │
    ├─ Title: "Upgrade [dependency] to [version]"
    ├─ Body:
    │   • Migration summary
    │   • Breaking changes
    │   • Validation results
    │   • Testing checklist
    │
    ↓
Trigger CI/CD (GitHub Actions)
    ↓
Monitor deployment status
    ↓
Update state: status = "deployed"
    ↓
WebSocket: broadcast deployment_complete event
    ↓
Return PR URL to user
```

---

## Agent Design

### Agent Lifecycle

```python
# 1. Initialization
agent = MigrationPlannerAgent(
    llm_provider="anthropic",  # or from env
    llm_model="claude-sonnet-4-20250514"
)

# 2. Execution
result = agent.execute(input_data={
    "project_path": "/path/to/project",
    "dependency_file": "package.json"
})

# 3. Output
{
    "status": "success",
    "dependencies": {...},
    "strategy": {...},
    "estimated_cost": 0.15
}
```

### Agent Communication

Agents communicate via **immutable state objects**, not directly:

```python
# BAD: Direct agent-to-agent communication
planner_result = planner.execute(...)
validator_result = validator.execute(planner_result)

# GOOD: Via workflow state
state = workflow.invoke(initial_state)
# LangGraph routes between agents based on state
```

### Agent Patterns

#### Pattern 1: Analysis Agent (Migration Planner)
```python
def execute(self, input_data):
    # 1. Read inputs
    project_path = input_data["project_path"]

    # 2. Gather data via tools
    deps = self.tools.read_file(f"{project_path}/package.json")

    # 3. LLM reasoning
    analysis = self.think(f"Analyze these dependencies: {deps}")

    # 4. Return structured output
    return {
        "status": "success",
        "analysis": analysis,
        "next_steps": [...]
    }
```

#### Pattern 2: Execution Agent (Runtime Validator)
```python
def execute(self, input_data):
    # 1. Extract configuration
    strategy = input_data["migration_strategy"]

    # 2. Execute external operations
    container = self.docker.create_container(...)
    self.docker.install_dependencies(container, strategy)

    # 3. Validate results
    health = self.docker.check_health(container)

    # 4. Cleanup
    self.docker.cleanup(container)

    # 5. Return results
    return {
        "status": "success" if health else "failure",
        "validation_result": {...}
    }
```

#### Pattern 3: Diagnostic Agent (Error Analyzer)
```python
def execute(self, input_data):
    # 1. Extract error context
    logs = input_data["validation_result"]["logs"]
    errors = input_data["errors"]

    # 2. LLM diagnosis
    diagnosis = self.think(f"Diagnose this error: {errors}\n\nLogs: {logs}")

    # 3. Generate fixes
    fixes = self.think(f"Generate fixes for: {diagnosis}")

    # 4. Rank by confidence
    ranked_fixes = self._rank_fixes(fixes)

    # 5. Return best fix or escalate
    if ranked_fixes[0]["confidence"] > 0.8:
        return {"status": "fix_available", "fix": ranked_fixes[0]}
    else:
        return {"status": "requires_human", "options": ranked_fixes}
```

---

## LLM Integration Design

### Prompt Engineering Strategy

#### System Prompts
Each agent has a carefully crafted system prompt:

**Migration Planner**:
```
You are an expert software engineer specializing in dependency management.
Your task is to analyze projects and create safe, phased migration strategies.

Guidelines:
- Identify all outdated dependencies
- Research breaking changes for each upgrade
- Consider dependency relationships and order
- Create conservative, staged upgrade plans
- Assess risk for each change
- Provide clear rationale for all decisions

Output format: JSON with dependencies, strategy, and risk assessment.
```

**Runtime Validator**:
```
You are a validation engineer who tests software upgrades.
You don't write code—you interpret logs and determine success/failure.

Guidelines:
- Analyze application logs for errors
- Identify startup failures vs runtime errors
- Assess health check responses
- Determine if application is functional
- Return structured validation results

Output format: JSON with status, level_completed, and detailed findings.
```

### Conversation Management

**Short-lived Conversations**:
- Each agent execution = fresh conversation
- No history carried between workflow steps
- Prevents context pollution

**History Within Execution**:
```python
# Agent receives: "Analyze this package.json"
agent.think("Analyze this package.json: {...}")

# History: [user: analyze, assistant: analysis]
agent.think("What's the migration risk?")

# Agent has context from first question
# History: [user: analyze, assistant: analysis, user: risk?, assistant: risk_assessment]
```

---

## MCP Integration Design

### Server Lifecycle

```python
# 1. Load configuration
config = load_mcp_config("mcp_config.json")

# 2. Start servers as subprocesses
for server_name, server_config in config.items():
    process = subprocess.Popen(
        [server_config["command"]] + server_config["args"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        env=server_config.get("env", {})
    )
    servers[server_name] = process

# 3. Initialize each server (JSON-RPC)
for server_name, process in servers.items():
    send_jsonrpc(process, "initialize", {...})
    response = read_jsonrpc(process)

# 4. List available tools
for server_name, process in servers.items():
    tools = send_jsonrpc(process, "tools/list", {})
    tool_registry[server_name] = tools
```

### Tool Invocation

```python
def call_tool(tool_name, arguments):
    # 1. Find server that owns tool
    server = find_server_for_tool(tool_name)

    # 2. Send JSON-RPC request
    request = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        },
        "id": generate_request_id()
    }

    # 3. Write to server stdin
    server.stdin.write(json.dumps(request) + "\n")
    server.stdin.flush()

    # 4. Read from server stdout
    response = server.stdout.readline()
    result = json.loads(response)

    # 5. Handle errors
    if "error" in result:
        raise MCPError(result["error"])

    # 6. Return result
    return result["result"]
```

---

## State Management

### Workflow State Schema

```python
from typing import TypedDict, List, Dict, Optional

class MigrationState(TypedDict, total=False):
    # Identity
    workflow_id: str
    project_path: str
    project_name: str

    # Analysis Phase
    dependency_file: str
    dependencies: Dict[str, Dict]  # name -> {current, target, ...}

    # Planning Phase
    migration_strategy: Optional[Dict]
    estimated_risk: str  # low, medium, high

    # Validation Phase
    validation_result: Optional[Dict]
    validation_level: int  # 1-4

    # Error Recovery
    errors: List[str]
    retry_count: int

    # Workflow Control
    status: str  # analyzing, planning, validating, error, complete
    current_agent: str
    requires_human_decision: bool

    # Deployment
    branch_name: Optional[str]
    pr_url: Optional[str]
    deployment_url: Optional[str]

    # Metadata
    started_at: str
    completed_at: Optional[str]
    total_cost: float
```

### State Persistence

**Checkpointing Strategy**:
- After each agent completes
- Before human-in-the-loop interrupts
- After each retry attempt

**Storage**:
```python
# SQLite for development
DATABASE_URL=sqlite:///./modernizer.db

# PostgreSQL for production
DATABASE_URL=postgresql://user:pass@localhost/modernizer
```

**Schema**:
```sql
CREATE TABLE workflow_executions (
    id TEXT PRIMARY KEY,
    state JSONB NOT NULL,
    checkpoint_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_workflow_status ON workflow_executions(state->>'status');
CREATE INDEX idx_workflow_project ON workflow_executions(state->>'project_name');
```

---

## Error Handling

### Error Hierarchy

```python
class ModernizerError(Exception):
    """Base exception for all errors"""
    pass

class AgentError(ModernizerError):
    """Agent execution failed"""
    pass

class ValidationError(ModernizerError):
    """Validation failed"""
    def __init__(self, logs, health_checks, errors):
        self.logs = logs
        self.health_checks = health_checks
        self.errors = errors

class MCPError(ModernizerError):
    """MCP tool call failed"""
    pass

class LLMError(ModernizerError):
    """LLM API call failed"""
    def __init__(self, provider, model, message):
        self.provider = provider
        self.model = model
        super().__init__(message)
```

### Error Recovery Strategies

| Error Type | Strategy | Max Retries |
|------------|----------|-------------|
| LLM API timeout | Exponential backoff | 3 |
| LLM rate limit | Wait + retry | 5 |
| MCP connection failure | Reconnect | 3 |
| Validation failure | Error analysis → Fix → Retry | 3 |
| Docker failure | Cleanup → Recreate | 2 |
| Unknown error | Log + escalate to human | 0 |

### Retry Logic

```python
@retry(
    max_attempts=3,
    backoff=ExponentialBackoff(base=2),
    retry_on=(LLMError, MCPError),
    escalate_on=ValidationError
)
def agent_execute(self, input_data):
    # Agent logic here
    pass
```

---

## Security Design

### API Key Management

**Storage**:
- Environment variables only (`.env` file)
- Never in code or version control
- `.env.example` for documentation

**Access**:
```python
# BAD
ANTHROPIC_API_KEY = "sk-ant-xxx"

# GOOD
import os
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY not set")
```

### Docker Isolation

**Principles**:
- All validation in isolated containers
- No access to host filesystem
- No network access during validation (future)
- Resource limits (CPU, memory)
- Auto-cleanup after execution

**Implementation**:
```python
container = docker_client.containers.run(
    image="node:18-alpine",
    command="npm start",
    detach=True,
    mem_limit="512m",
    cpu_quota=50000,  # 50% of 1 CPU
    network_mode="none",  # No network
    volumes={
        project_path: {"bind": "/app", "mode": "ro"}  # Read-only
    },
    remove=True  # Auto-cleanup
)
```

### Input Validation

**All user inputs validated**:
```python
from pydantic import BaseModel, validator

class ProjectAnalysisRequest(BaseModel):
    project_path: str

    @validator('project_path')
    def path_is_safe(cls, v):
        # Prevent path traversal
        if '..' in v or v.startswith('/'):
            raise ValueError("Invalid project path")
        return v
```

### GitHub Token Scopes

**Minimal required scopes**:
- `repo` (read/write repositories)
- ~~`admin:org`~~ (not needed)
- ~~`delete_repo`~~ (not needed)

**Token rotation**:
- Rotate every 90 days
- Revoke on compromise
- Use fine-grained tokens (future)

---

## Design Decisions & Rationale

### Why LangGraph over AutoGen/CrewAI?
- **LangGraph**: Production-ready, state management, human-in-the-loop primitives
- **AutoGen**: Too experimental, unpredictable agent behavior
- **CrewAI**: Less flexible for complex conditional workflows

### Why Multiple LLM Providers?
- **Cost Optimization**: Route simple tasks to cheaper models
- **Redundancy**: Failover if one provider is down
- **Comparison**: A/B test provider performance
- **Future-Proofing**: Not locked into one vendor

### Why MCP over Direct API Calls?
- **Standardization**: Consistent interface for tools
- **Security**: Sandboxed execution
- **Extensibility**: Easy to add new tools
- **Future-Proofing**: Anthropic-backed protocol

### Why SQLite for State?
- **Simplicity**: No separate database server
- **Portability**: Single file database
- **Sufficient**: Handle 1000s of workflows
- **Upgradeable**: Can migrate to Postgres later

### Why Docker for Validation?
- **Isolation**: Can't break host system
- **Reproducibility**: Same environment every time
- **Cleanup**: Automatic resource management
- **Cross-platform**: Works on Linux, macOS, Windows

---

**Document Version**: 1.0
**Last Updated**: 2025-01-15
**Next Review**: After Phase 2 implementation
