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

Python backend using LangGraph to orchestrate AI agents that analyze, validate, and upgrade code dependencies. The system features flexible multi-LLM provider support and MCP (Model Context Protocol) for tool access.

**Implementation Status**: Phase 3 In Progress (50% Complete - 2025-11-07)
- ✅ Multi-LLM provider support (Anthropic, OpenAI, Gemini, HuggingFace, Qwen)
- ✅ Cost tracking across all providers
- ✅ Structured logging infrastructure
- ✅ Base agent architecture
- ✅ MCP tool manager (Phase 1 complete - subprocess + fallback)
- ✅ Migration Planner Agent (complete with 7 unit tests)
- ✅ Runtime Validator Agent (complete)
- ✅ Docker validation tools (complete and tested)
- ✅ Sample Express.js project (complete)
- ❌ Error Analyzer Agent (not yet implemented)
- ❌ Staging Deployer Agent (not yet implemented)
- ❌ LangGraph workflow (not yet implemented)
- ❌ FastAPI backend (not yet implemented)

See `DEVELOPMENT_PLAN_STATUS.md` for detailed status and `docs/IMPLEMENTATION_PROGRESS.md` for comprehensive progress report.

## Architecture

### Flexible LLM System ✅
**Factory Pattern** (`llm/factory.py`) creates provider-specific clients:
- All providers implement `BaseLLMClient` interface (`llm/base.py`)
- Automatic cost tracking via `CostTracker` (`utils/cost_tracker.py`)
- Provider selection via environment variable or parameter

**Supported Providers:**
1. **Anthropic** (`llm/anthropic_client.py`) - Claude Sonnet 4, Opus 4, Haiku 4
2. **OpenAI** (`llm/openai_client.py`) - GPT-4o, GPT-4 Turbo, GPT-3.5 Turbo
3. **Gemini** (`llm/gemini_client.py`) - Gemini 2.0 Flash/Pro, 3.0 Pro
4. **HuggingFace** (`llm/huggingface_client.py`) - Llama 3.2, Llama 3.1, DialoGPT, etc.
5. **Qwen** (`llm/qwen_client.py`) - Qwen Turbo, Plus, Max, 72B, 14B

**Configuration**:
```bash
LLM_PROVIDER=anthropic  # Default provider (or openai, gemini, etc.)
ANTHROPIC_API_KEY=sk-ant-xxxxx
ANTHROPIC_MODEL=claude-sonnet-4-20250514
```

### Multi-Agent System

All agents inherit from `BaseAgent` (`agents/base.py`) which provides:
- Flexible LLM client (configurable per agent via `create_llm_client()`)
- MCP tool manager access (`tools/mcp_tools.py`)
- Structured logging (`utils/logger.py`)
- Conversation history tracking

**Implemented Agents** (Phase 3 - 50% Complete):

1. ✅ **Migration Planner** (`agents/migration_planner.py`) - COMPLETE
   - Analyzes `package.json` and `requirements.txt`
   - Identifies outdated dependencies via LLM analysis
   - Researches breaking changes
   - Creates phased migration plans with risk assessment
   - **Test**: 7 unit tests, all passing (`tests/test_migration_planner.py`)

2. ✅ **Runtime Validator** (`agents/runtime_validator.py`) - COMPLETE
   - Uses DockerValidator for isolated testing
   - Creates containers, applies upgrades, runs application
   - Tests health endpoints
   - LLM-powered analysis of validation results
   - Provides recommendations (proceed/fix/rollback)

**Planned Agents** (Phase 4 - Not Yet Implemented):

3. ❌ **Error Analyzer** (`agents/error_analyzer.py`) - NOT IMPLEMENTED
   - Will parse error logs
   - Will identify root causes
   - Will generate fix suggestions
   - Will propose alternative strategies

4. ❌ **Staging Deployer** (`agents/staging_deployer.py`) - NOT IMPLEMENTED
   - Will create Git branches
   - Will commit changes
   - Will create PRs via MCP GitHub tools

### MCP Tool Manager ✅ Phase 1 Complete

**Status**: Phase 1 complete (subprocess + fallback), ready for Phase 2 (JSON-RPC)
**File**: `tools/mcp_tools.py`
**Documentation**: `docs/MCP_IMPLEMENTATION.md`

**Current Implementation (Phase 1)**:
- ✅ Configuration loading from `mcp_config.json`
- ✅ Subprocess management for MCP servers
- ✅ Process lifecycle (start/cleanup)
- ✅ Fallback implementations for development
- ✅ Direct filesystem operations (bypass MCP)
- ✅ Mock GitHub operations
- ✅ Comprehensive test suite (6 tests, all passing)

**Planned (Phase 2)**:
- ❌ JSON-RPC communication over STDIO
- ❌ Tool discovery from live MCP servers
- ❌ Actual GitHub MCP integration

**Available Methods**:
```python
manager = MCPToolManager()
manager.read_file(path)              # Direct filesystem (fallback)
manager.write_file(path, content)    # Direct filesystem (fallback)
manager.github_get_file(...)         # Mock implementation (fallback)
manager.github_create_pr(...)        # Mock implementation (fallback)
manager.call_tool(tool_name, args)   # Generic interface
```

### Docker Validation Tools ✅ Complete

**Status**: Fully implemented and tested
**File**: `tools/docker_tools.py`

**Capabilities**:
- ✅ Create containers from project code
- ✅ Copy project files (excludes node_modules, venv, .git)
- ✅ Apply dependency upgrades from migration plans
- ✅ Install Node.js/Python dependencies
- ✅ Start applications
- ✅ Run health checks (process monitoring)
- ✅ Collect logs
- ✅ Automatic cleanup

**Test Results**:
```bash
".venv/Scripts/python.exe" -m tools.docker_tools
# ✅ All stages successful
# Container creation: SUCCESS
# Project copy: SUCCESS
# Dependency installation: SUCCESS
# Application startup: SUCCESS
# Health check: SUCCESS
```

**Usage**:
```python
from tools.docker_tools import DockerValidator

validator = DockerValidator(timeout=300)
result = validator.validate_project(
    project_path="./project",
    project_type="nodejs",
    migration_plan=migration_plan  # Optional
)
# Returns: build_success, install_success, runtime_success, health_check_success
```

### LangGraph Workflow ❌ Not Yet Implemented

**Status**: Not yet implemented - planned for Phase 5
**File**: `graph/workflow.py`

**Will orchestrate** agents in a stateful workflow:
- **State Schema** (`graph/state.py`) - `MigrationState` TypedDict passed between agents
- **Conditional Routing** - Routes to error analyzer on validation failure
- **Retry Logic** - Attempts fixes up to 3 times (configurable)
- **Human Interrupts** - Workflow pauses for approval before deployment

**Planned State Fields:**
```python
project_path: str           # Path to project
dependencies: Dict          # Dependency info
migration_strategy: Optional[Dict]  # Upgrade plan
validation_result: Optional[Dict]   # Docker validation results
errors: List[str]           # Errors encountered
retry_count: int            # Current retry attempt
status: str                 # analyzing, validating, error, complete
```

### Cost Tracking ✅ Complete

**Status**: Fully implemented and working
**File**: `utils/cost_tracker.py`

All LLM clients automatically track token usage and costs.

**Pricing Database** (per 1M tokens, updated 2025):
- **Anthropic**: Sonnet 4 ($3/$15), Opus 4 ($15/$75), Haiku 4 ($0.25/$1.25)
- **OpenAI**: GPT-4o ($5/$15), GPT-4 Turbo ($10/$30), GPT-3.5 Turbo ($0.50/$1.50)
- **Gemini**: 2.0 Flash ($0.35/$1.05), 2.0 Pro ($3.50/$10.50), 3.0 Pro ($4/$12)
- **Qwen**: Turbo ($0.10/$0.20), Plus ($0.40/$1.20), Max ($1/$3)
- **HuggingFace**: Llama 3.2 ($0.05/$0.05), Llama 3.1 ($0.10/$0.10)

**Usage**:
```python
# Automatic tracking via LLM clients
report = agent.llm.cost_tracker.get_report()
# Returns: total_input_tokens, total_output_tokens, total_cost, model_costs
```

## Quick Start - Testing Current Implementation

### Test Flexible LLM System ✅
```bash
# Test all LLM providers
".venv/Scripts/python.exe" -m llm.test_flexible_llm

# Expected output:
# ✅ Anthropic client working (if API key configured)
# ✅ Gemini client working (if API key configured)
# ✅ HuggingFace client working (if API key configured)
# ❌ OpenAI/Qwen errors if API keys not configured
```

### Test Migration Planner Agent ✅
```bash
# Run unit tests (mocked LLM)
".venv/Scripts/python.exe" -m pytest tests/test_migration_planner.py -v
# ✅ 7 tests PASSED in 0.27s

# Run standalone (requires API key)
# ".venv/Scripts/python.exe" -m agents.migration_planner
```

### Test Docker Validation Tools ✅
```bash
# Test with sample Express app
".venv/Scripts/python.exe" -m tools.docker_tools
# ✅ All stages successful
```

### Test MCP Tools ✅
```bash
# Test MCP Phase 1 (subprocess + fallback)
".venv/Scripts/python.exe" tools/test_mcp.py
# ✅ All 6 tests passing
```

### Test Individual Components ✅
```bash
# Test cost tracker
python -m utils.cost_tracker

# Test logger
python -m utils.logger

# Test base agent
python -m agents.base

# Test LLM providers
python -m tests.test_llm_providers
```

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

### Running Backend (Not Yet Implemented)
```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

API docs: http://localhost:8000/docs (when implemented)

### Testing Individual Components
**Critical Pattern**: Each component is independently executable for testing:

```bash
# Test LLM system
python -m llm.test_flexible_llm

# Test MCP tools
python tools/test_mcp.py

# Test cost tracker
python -m utils.cost_tracker

# Test logger
python -m utils.logger

# Test base agent
python -m agents.base

# Test Migration Planner (with mocks)
python -m pytest tests/test_migration_planner.py -v

# Test Docker tools
python -m tools.docker_tools

# Test Runtime Validator (requires API key)
# python -m agents.runtime_validator
```

### Running Tests
```bash
pytest tests/ -v                           # All tests
pytest tests/test_migration_planner.py -v  # Migration planner tests (7 tests)
pytest tests/ --cov=. --cov-report=html    # With coverage
pytest tests/ -v -s                        # Show print statements
```

### MCP Server Installation (Optional - Not Required Yet)
```bash
npm install -g @modelcontextprotocol/server-github
npm install -g @modelcontextprotocol/server-filesystem

# Test MCP connection (uses fallback mode without servers)
python tools/test_mcp.py
```

## Agent Implementation Pattern

When creating a new agent:

```python
from agents.base import BaseAgent
from typing import Dict, Optional

class MyAgent(BaseAgent):
    """Description of what this agent does"""

    def __init__(self, llm_provider: Optional[str] = None, llm_model: Optional[str] = None):
        super().__init__(
            name="my_agent",
            system_prompt="""Your system instructions here.
            Be specific about the agent's role and capabilities.""",
            llm_provider=llm_provider,
            llm_model=llm_model
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

## API Layer (Not Yet Implemented)

### FastAPI Application (`api/main.py`) ❌
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="AI Code Modernizer API")

# CORS configured for frontend (localhost:5173)
app.add_middleware(CORSMiddleware, ...)
```

### Endpoints (Planned)
- `GET /api/health` - Health check
- `GET /api/` - Root endpoint
- `POST /api/projects/analyze` - Analyze project dependencies
- `POST /api/projects/upgrade` - Start upgrade workflow
- `GET /api/projects/{id}/status` - Get workflow status

### WebSocket (`api/websocket.py`) ❌
Real-time updates sent to frontend:
- Agent state changes
- Thinking stream (LLM reasoning)
- Graph node transitions
- Validation results

## Environment Variables

Required in `.env`:
```bash
# LLM Provider Configuration
LLM_PROVIDER=anthropic  # or openai, gemini, huggingface, qwen

# Anthropic API
ANTHROPIC_API_KEY=sk-ant-xxxxx
ANTHROPIC_MODEL=claude-sonnet-4-20250514

# OpenAI API (Optional)
OPENAI_API_KEY=sk-xxxxx
OPENAI_MODEL=gpt-4o

# Google Gemini API (Optional)
GOOGLE_API_KEY=xxxxx
GEMINI_MODEL=gemini-2.0-flash

# HuggingFace API (Optional)
HUGGINGFACE_API_KEY=hf_xxxxx
HUGGINGFACE_MODEL=meta-llama/Llama-3.2-3B-Instruct

# Qwen API (Optional)
QWEN_API_KEY=sk-xxxxx-xxx-xxx-xxx
QWEN_MODEL=qwen-turbo

# GitHub Integration (Required for Phase 4)
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

- **LLM issues**: Run `python -m llm.test_flexible_llm` to test all providers
- **MCP issues**: Run `python tools/test_mcp.py` to test connectivity
- **Agent issues**: Run agent standalone with test data
- **Docker issues**: Ensure Docker Desktop running, test with `docker ps`
- **Workflow issues**: Check state transitions (when implemented)
- **API issues**: Visit FastAPI auto-docs (when implemented)
- **Import errors**: Ensure virtual environment activated, dependencies installed

## Dependencies

Key packages in `requirements.txt`:
- `anthropic>=0.18.0` - Claude API
- `openai>=1.35.0` - OpenAI GPT models
- `google-generativeai>=0.8.0` - Google Gemini
- `huggingface_hub>=0.20.0` - HuggingFace models
- `dashscope>=1.13.0` - Qwen models
- `langgraph>=0.2.16` - Multi-agent orchestration (planned)
- `mcp>=0.1.0` - Model Context Protocol
- `fastapi>=0.104.0` - Web framework (planned)
- `docker>=6.1.0` - Container management ✅
- `structlog>=23.2.0` - Structured logging ✅
- `tiktoken>=0.5.0` - Token counting ✅
- `pytest>=7.4.0` - Testing ✅

## Common Tasks

### Add New Tool
1. Add tool to MCP server or create custom tool in `tools/`
2. Add wrapper method to `MCPToolManager` if MCP-based
3. Document tool usage in agent system prompts

### Modify Workflow (When Implemented)
1. Update `graph/state.py` if state schema changes
2. Modify `graph/workflow.py` for routing logic
3. Update agents to handle new state fields
4. Test with `python graph/workflow.py`

### Add New Agent
1. Create file in `agents/` inheriting from `BaseAgent`
2. Implement `execute()` method
3. Add standalone test in `if __name__ == "__main__"`
4. Register in workflow (`graph/workflow.py`) when ready
5. Test standalone, then in workflow

## Progress Summary

**Overall**: 40% complete (2.5/7 phases)

**Completed**:
- ✅ Phase 1: Core Infrastructure (100%)
- ✅ Phase 2: Base Agent Infrastructure (100%)
- 🚧 Phase 3: Core Agents (50% - 2/4 agents complete)

**Next Steps**:
1. Build Error Analyzer Agent
2. Build Staging Deployer Agent
3. Create LangGraph workflow
4. Build FastAPI backend

See `DEVELOPMENT_PLAN_STATUS.md` for detailed tracking and `docs/IMPLEMENTATION_PROGRESS.md` for comprehensive progress report.
