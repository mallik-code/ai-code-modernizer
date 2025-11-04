# CLAUDE.md - Backend

This file provides guidance to Claude Code (claude.ai/code) when working with the backend codebase.

## ⚠️ CRITICAL: Read These Standards First

Before writing any backend code, **MUST READ** these standards documents in `.claude/`:

1. **`.claude/agentic-security.md`** - Security guidelines for AI agents (prompt injection prevention, input validation, Docker isolation, secrets management, human-in-the-loop)
2. **`.claude/python-standards.md`** - Python best practices (PEP 8, type hints, docstrings, error handling, dataclasses, async patterns, testing)
3. **`.claude/api-design-standards.md`** - API design standards (RESTful conventions, request/response models, status codes, authentication, rate limiting, WebSocket)
4. **`.claude/testing-standards.md`** - Testing standards (unit tests, integration tests, mocking, fixtures, coverage requirements)

These documents contain mandatory patterns and anti-patterns. All code must comply with these standards.

## Backend Overview

Python backend using LangGraph to orchestrate AI agents that analyze, validate, and upgrade code dependencies. Agents use Claude Sonnet 4 for reasoning and MCP (Model Context Protocol) for tool access.

## Architecture

### Multi-Agent System
All agents inherit from `BaseAgent` (`agents/base.py`) which provides:
- LLM client integration (`llm/client.py`)
- MCP tool manager access (`tools/mcp_tools.py`)
- Structured logging (`utils/logger.py`)
- Conversation history tracking

**Four Specialized Agents:**
1. **Migration Planner** (`agents/migration_planner.py`) - Analyzes `package.json`/`requirements.txt`, identifies outdated dependencies, researches breaking changes, creates phased migration plans
2. **Runtime Validator** (`agents/runtime_validator.py`) - Creates Docker containers, applies upgrades, runs application, tests health endpoints, returns validation results
3. **Error Analyzer** (`agents/error_analyzer.py`) - Parses error logs, identifies root causes, generates fix suggestions, proposes alternative strategies
4. **Staging Deployer** (`agents/staging_deployer.py`) - Creates Git branches, commits changes, creates PRs via MCP GitHub tools

### MCP Tool Manager (`tools/mcp_tools.py`)
Manages connections to MCP servers and exposes tools to agents:

**Configuration** (`mcp_config.json`):
- GitHub MCP server (requires `GITHUB_TOKEN` env var)
- Filesystem MCP server

**Key Methods:**
- `read_file(path)` - Read local files
- `write_file(path, content)` - Write local files
- `github_get_file(owner, repo, path)` - Get file from GitHub
- `github_create_pr(owner, repo, title, body, head, base)` - Create PR
- `call_tool(tool_name, arguments)` - Generic tool call

### LangGraph Workflow (`graph/workflow.py`)
Orchestrates agents in a stateful workflow:
- **State Schema** (`graph/state.py`) - `MigrationState` TypedDict passed between agents
- **Conditional Routing** - Routes to error analyzer on validation failure
- **Retry Logic** - Attempts fixes up to 3 times (configurable)
- **Human Interrupts** - Workflow pauses for approval before deployment

**State Fields:**
```python
project_path: str           # Path to project
dependencies: Dict          # Dependency info
migration_strategy: Optional[Dict]  # Upgrade plan
validation_result: Optional[Dict]   # Docker validation results
errors: List[str]           # Errors encountered
retry_count: int            # Current retry attempt
status: str                 # analyzing, validating, error, complete
```

### Cost Tracking (`utils/cost_tracker.py`)
`LLMClient` automatically tracks token usage and costs. Pricing per 1M tokens:
- Claude Sonnet 4: Input $3.00, Output $15.00

Access with: `self.llm.cost_tracker.get_report()`

### Docker Validation (`tools/docker_tools.py`)
`DockerValidator` class handles:
1. Create container from project code
2. Install upgraded dependencies
3. Start application
4. Run health checks
5. Collect logs
6. Cleanup containers

## Development Commands

### Setup
```bash
cd backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with ANTHROPIC_API_KEY and GITHUB_TOKEN
```

### Running Backend
```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

API docs: http://localhost:8000/docs

### Testing Individual Components
**Critical Pattern**: Each component is independently executable for testing:

```bash
# Test LLM client
python llm/client.py

# Test MCP tools
python tools/mcp_tools.py

# Test cost tracker
python utils/cost_tracker.py

# Test logger
python utils/logger.py

# Test base agent
python agents/base.py

# Test specific agent
python agents/migration_planner.py --project ./test-projects/express-app
python agents/runtime_validator.py --project ./test-projects/express-app --strategy strategy.json
python agents/error_analyzer.py --logs validation_logs.txt

# Test workflow
python graph/workflow.py
```

### Running Tests
```bash
pytest tests/ -v                           # All tests
pytest tests/test_agents.py -v             # Specific test file
pytest tests/test_agents.py::test_name -v  # Specific test
pytest tests/ --cov=. --cov-report=html    # With coverage
pytest tests/ -v -s                        # Show print statements
```

### MCP Server Installation
```bash
npm install -g @modelcontextprotocol/server-github
npm install -g @modelcontextprotocol/server-filesystem

# Test MCP connection
python tools/test_mcp.py
```

## Agent Implementation Pattern

When creating a new agent:

```python
from agents.base import BaseAgent
from typing import Dict

class MyAgent(BaseAgent):
    """Description of what this agent does"""

    def __init__(self):
        super().__init__(
            name="my_agent",
            system_prompt="""Your system instructions here.
            Be specific about the agent's role and capabilities."""
        )

    def execute(self, input_data: Dict) -> Dict:
        """Execute agent logic

        Args:
            input_data: Input data dictionary

        Returns:
            Result dictionary with agent outputs
        """
        # 1. Extract inputs
        project_path = input_data.get("project_path")

        # 2. Use tools
        content = self.tools.read_file(f"{project_path}/package.json")

        # 3. Use LLM for reasoning
        analysis = self.think(f"Analyze this: {content}")

        # 4. Return structured output
        return {
            "analysis": analysis,
            "status": "success"
        }

# CRITICAL: Add standalone test
if __name__ == "__main__":
    agent = MyAgent()
    result = agent.execute({"project_path": "./test-projects/example"})
    print("Result:", result)
```

**Key Methods from BaseAgent:**
- `self.think(prompt)` - Send prompt to LLM, get response
- `self.use_tool(tool_name, args)` - Call MCP tool
- `self.tools.read_file(path)` - Read file via MCP
- `self.logger.info(msg, **context)` - Structured logging
- `self.reset()` - Clear conversation history

## API Layer (`api/`)

### FastAPI Application (`api/main.py`)
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="AI Code Modernizer API")

# CORS configured for frontend (localhost:5173)
app.add_middleware(CORSMiddleware, ...)
```

### Endpoints
- `GET /api/health` - Health check
- `GET /api/` - Root endpoint
- `POST /api/projects/analyze` - Analyze project dependencies
- `POST /api/projects/upgrade` - Start upgrade workflow
- `GET /api/projects/{id}/status` - Get workflow status

### WebSocket (`api/websocket.py`)
Real-time updates sent to frontend:
- Agent state changes
- Thinking stream (LLM reasoning)
- Graph node transitions
- Validation results

## Environment Variables

Required in `.env`:
```bash
# Required
ANTHROPIC_API_KEY=sk-ant-xxxxx
GITHUB_TOKEN=ghp_xxxxx

# Optional
LANGCHAIN_TRACING_V2=false
LANGCHAIN_API_KEY=ls__xxxxx
DATABASE_URL=sqlite:///./modernizer.db
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
DOCKER_TIMEOUT=300
MAX_RETRY_ATTEMPTS=3
ENABLE_STAGING_DEPLOYMENT=true
ENABLE_AUTO_FIX=true
```

## Logging Pattern

Use structured logging with context:
```python
self.logger.info("reading_file", path=file_path, size=len(content))
self.logger.error("validation_failed", error=str(e), retry_count=retry_count)
```

## Critical Design Principles

1. **Testability First** - Every component must have `if __name__ == "__main__"` block for standalone testing
2. **Stateless Agents** - State passed via LangGraph `MigrationState`, never stored in agent instances
3. **Docker Isolation** - All validation in containers, never execute user code on host
4. **Tool-Based Architecture** - Agents access external systems only through MCP tools
5. **Cost Awareness** - Track and log token usage for all LLM calls
6. **Structured Logging** - Use structlog with rich output, include context in all logs

## Debugging

- **MCP issues**: Run `python tools/mcp_tools.py` to test connectivity
- **Agent issues**: Run agent standalone with test data
- **Workflow issues**: Check state transitions and conditional logic in `graph/workflow.py`
- **Docker issues**: Ensure Docker Desktop running, test with `docker ps`
- **API issues**: Visit FastAPI auto-docs at http://localhost:8000/docs
- **Import errors**: Ensure virtual environment activated, dependencies installed

## Dependencies

Key packages in `requirements.txt`:
- `anthropic>=0.18.0` - Claude API
- `langgraph>=0.2.16` - Multi-agent orchestration
- `mcp>=0.1.0` - Model Context Protocol
- `fastapi>=0.104.0` - Web framework
- `docker>=6.1.0` - Container management
- `structlog>=23.2.0` - Structured logging
- `tiktoken>=0.5.0` - Token counting
- `pytest>=7.4.0` - Testing

## Common Tasks

### Add New Tool
1. Add tool to MCP server or create custom tool in `tools/`
2. Add wrapper method to `MCPToolManager` if MCP-based
3. Document tool usage in agent system prompts

### Modify Workflow
1. Update `graph/state.py` if state schema changes
2. Modify `graph/workflow.py` for routing logic
3. Update agents to handle new state fields
4. Test with `python graph/workflow.py`

### Add New Agent
1. Create file in `agents/` inheriting from `BaseAgent`
2. Implement `execute()` method
3. Add standalone test in `if __name__ == "__main__"`
4. Register in workflow (`graph/workflow.py`)
5. Test standalone, then in workflow

## Next Steps

See `DEVELOPMENT_PLAN.md` for detailed 5-day implementation plan with checklists for each component.
