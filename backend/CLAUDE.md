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

**Implementation Status**: Phase 6 Complete (95% - 2025-11-14)
- ✅ Multi-LLM provider support (Anthropic, OpenAI, Gemini, HuggingFace, Qwen)
- ✅ Cost tracking across all providers
- ✅ Structured logging infrastructure
- ✅ Base agent architecture
- ✅ MCP tool manager (Phase 1 complete - subprocess + fallback)
- ✅ Migration Planner Agent (complete with 7 unit tests + robust multi-LLM parsing + npm registry integration)
- ✅ Runtime Validator Agent (complete with Docker isolation + functional tests)
- ✅ Error Analyzer Agent (complete with 19 unit tests + smart error categorization)
- ✅ Staging Deployer Agent (complete with 19 unit tests + GitHub PR creation)
- ✅ Docker validation tools (complete with auto-cleanup of existing containers)
- ✅ Sample Express.js project (complete in target_repos/)
- ✅ End-to-end integration tests (complete)
- ✅ Comprehensive testing guide (TESTING_GUIDE.md)
- ✅ LangGraph workflow (complete with 18 unit tests + 4-agent orchestration + conditional routing + retry logic)
- ✅ FastAPI backend (complete with WebSocket support + report generation)
- ✅ Report generation (HTML/Markdown/JSON with comprehensive insights)
- ✅ Report content APIs (view in browser + download in multiple formats)
- ✅ React frontend (complete with real-time WebSocket updates + report viewing/downloading)

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

**Implemented Agents** (4-Agent Architecture - 100% Complete):

1. ✅ **Migration Planner** (`agents/migration_planner.py`) - COMPLETE
   - Analyzes `package.json` and `requirements.txt`
   - **npm Registry Integration**: Fetches real latest versions from registry.npmjs.org
   - Identifies outdated dependencies via LLM analysis with accurate version comparison
   - Researches breaking changes between current and target versions
   - Creates phased migration plans with risk assessment (low/medium/high)
   - **Robust Multi-LLM Parsing**: Handles varying response formats from different providers
     - Normalizes field names: camelCase ↔ snake_case (e.g., `currentVersion` → `current_version`)
     - Supports both array and object dependency formats
     - Handles multiple phase naming conventions (`phase1`, `phase_1`, `phases` array)
     - Extracts risk levels from assessment text
     - **Critical Fix**: Ensures current_version remains exact from package.json (not overwritten with latest)
   - **Tests**: 7 unit tests, all passing (`tests/test_migration_planner.py`)
   - **Tested with**: Gemini 2.0 Flash (~$0.001/run), Anthropic Claude Sonnet 4 (~$0.015/run)

2. ✅ **Runtime Validator** (`agents/runtime_validator.py`) - COMPLETE
   - Uses DockerValidator for isolated testing in containers
   - **Auto-cleanup**: Detects and removes existing containers before creating new ones
   - Creates containers, applies upgrades, runs application
   - Executes functional test suites (Jest for Node.js, pytest for Python)
   - Performs health checks (process monitoring)
   - LLM-powered analysis of validation results
   - Provides recommendations (proceed/fix/rollback)
   - **Container Management**: Stops running containers gracefully before removal

3. ✅ **Error Analyzer** (`agents/error_analyzer.py`) - COMPLETE
   - Parses error logs (npm, pip, runtime errors)
   - Extracts errors using regex patterns for JavaScript/Python
   - Identifies root causes via LLM analysis
   - Generates fix suggestions with priority levels (high/medium/low)
   - Provides code context extraction (5 lines before/after error)
   - Proposes alternative strategies for recovery
   - **Smart Fallback Categorization**: Avoids false positives (e.g., "TypeError" vs "peer dependency")
   - **Conditional Execution**: Only runs when validation fails (workflow optimization)
   - **Tests**: 19 unit tests, all passing (`tests/test_error_analyzer.py`)

4. ✅ **Staging Deployer** (`agents/staging_deployer.py`) - COMPLETE
   - Creates Git branches with timestamp-based naming (`upgrade/dependencies-YYYYMMDD-HHMMSS`)
   - Updates dependency files (package.json, requirements.txt) with target versions
   - Generates conventional commit messages with upgrade details
   - Creates detailed PR descriptions with migration info, breaking changes, and test results
   - Integrates with GitHub via MCP tools (mock for now)
   - **Human-in-the-Loop**: All changes go through PR review (safety gate)
   - **Rollback Instructions**: Provides clear rollback steps in deployment result
   - **Tests**: 19 unit tests, all passing (`tests/test_staging_deployer.py`)

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
- ✅ **Auto-cleanup existing containers**: Detects, stops, and removes containers with same name
- ✅ Copy project files (excludes node_modules, venv, .git)
- ✅ Apply dependency upgrades from migration plans
- ✅ Install Node.js/Python dependencies
- ✅ Start applications
- ✅ **Execute functional tests**: Runs Jest (Node.js) or pytest (Python) test suites
- ✅ Run health checks (process monitoring)
- ✅ Collect logs
- ✅ Automatic cleanup on success/failure
- ✅ **Port mapping**: Maps container ports to host for browser access (3000 for Node.js, 5000 for Python)

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

### LangGraph Workflow ✅ Complete

**Status**: Fully implemented and tested with 4-agent orchestration
**Files**: `graph/workflow.py`, `graph/state.py`

**4-Agent Architecture**:
```python
workflow.add_node("plan", migration_planner_node)      # Agent 1: Migration Planner
workflow.add_node("validate", runtime_validator_node)  # Agent 2: Runtime Validator
workflow.add_node("analyze", error_analyzer_node)      # Agent 3: Error Analyzer
workflow.add_node("deploy", staging_deployer_node)     # Agent 4: Staging Deployer
```

**Features**:
- ✅ **State Schema** (`graph/state.py`) - `MigrationState` TypedDict passed between all 4 agents
- ✅ **Conditional Routing** - Smart routing based on validation results
  - Success → Staging Deployer
  - Failure + retries available → Error Analyzer
  - Failure + max retries → END (with error state)
- ✅ **Retry Logic** - Up to 3 fix attempts (configurable via `max_retries`)
- ✅ **Cost Tracking** - Aggregates LLM costs across all 4 agents
- ✅ **Error Recovery** - Error Analyzer generates fixes, validator retries
- ✅ **Deployment** - Creates GitHub PR via Staging Deployer on successful validation

**Workflow Flow (4 Agents)**:
```
User Request → [1] Migration Planner → [2] Runtime Validator → [Success/Failure]
                                               ↓ Failure (retries < max)
                                         [3] Error Analyzer → [2] Runtime Validator (retry)
                                               ↓ Success
                                         [4] Staging Deployer → GitHub PR
```

**State Fields**:
```python
# Project info
project_path: str
project_type: str

# Agent outputs
migration_plan: Optional[Dict]
validation_result: Optional[Dict]
error_analysis: Optional[Dict]
deployment_result: Optional[Dict]

# Workflow control
status: str  # initializing, plan_created, validated, deployed, error
retry_count: int
max_retries: int
validation_success: bool

# Results
pr_url: Optional[str]
branch_name: Optional[str]
errors: List[str]

# Cost tracking
total_cost: float
agent_costs: Dict[str, float]
```

**Test Coverage**: 18 unit tests (15 routing/state + 3 integration)
- Routing logic tests (8 tests)
- Workflow graph structure (2 tests)
- State management (3 tests)
- Integration tests with mocked agents (2 tests)
- Full workflow execution (1 test, requires API keys)

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

### Report Generation ✅ Complete

**Status**: Fully implemented with comprehensive insights
**File**: `utils/report_generator.py`

**Features**:
- ✅ **Multiple Formats**: HTML, Markdown, and JSON reports
- ✅ **Branch-Based Organization**: Reports saved in folders named after target branch
- ✅ **Comprehensive Content**:
  - Project metadata (path, type, status, risk level)
  - **Source and Target Branches**: Clear Git workflow visibility
  - Dependencies analysis with current → target versions
  - Breaking changes detail per package
  - Migration strategy with phased approach
  - Validation results (build, install, runtime, health checks, **functional tests**)
  - **Workflow execution diagram**: ASCII visualization of 4-agent flow
  - **Agent execution summary**: Status, cost, and details for each agent
  - **Agent roles & responsibilities**: Detailed description of all 4 agents
  - **AI/LLM insights**: Transparency into decision-making process
  - Cost breakdown per agent
- ✅ **Styling**: Professional HTML reports with responsive CSS grid layout

**Report Structure**:
```
reports/
  └── upgrade_dependencies-YYYYMMDD-HHMMSS/
      ├── project_migration_report_TIMESTAMP.html      # Rich HTML report
      ├── project_migration_report_TIMESTAMP.md        # Markdown for GitHub
      └── project_migration_report_TIMESTAMP.json      # Raw data
```

**Usage**:
```python
from utils.report_generator import ReportGenerator

generator = ReportGenerator(output_dir="reports")
paths = generator.generate_all_reports(workflow_state, "my-project")
# Returns: {"html": "path/to/report.html", "markdown": "...", "json": "..."}
```

### FastAPI Backend ✅ Complete

**Status**: Fully implemented with REST API and WebSocket support
**File**: `api/main.py`

**Features**:
- ✅ **In-Memory Storage**: Migration runs stored in dictionary (migrations_db)
- ✅ **Background Tasks**: Workflow execution in thread pool
- ✅ **Automatic Report Generation**: HTML/Markdown/JSON after workflow completion
- ✅ **CORS**: Configured for frontend (localhost:5173)

**Endpoints**:
- `GET /` - Root endpoint with API information
- `GET /api/health` - Health check (Docker, API keys, migrations count)
- `POST /api/migrations/start` - Start new migration workflow (returns migration_id)
- `GET /api/migrations/{id}` - Get migration status and results with report links
- `GET /api/migrations` - List all migrations with pagination
- `GET /api/migrations/{id}/report?type=html|markdown|json` - Download reports (file download)
- `GET /api/migrations/{id}/report_content?type=html|markdown|json` - Get report content (JSON response for browser viewing)
- `WS /ws/migrations/{id}` - WebSocket endpoint for real-time migration updates
- `DELETE /api/migrations/{id}` - Delete a migration record

**Running**:
```bash
cd backend
# Activate virtual environment
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
# API docs: http://localhost:8000/docs
```

## Quick Start - Testing Current Implementation

### Complete Testing Guide ✅
See `TESTING_GUIDE.md` for comprehensive testing documentation including:
- Quick start commands
- Expected test times and costs
- Provider comparison (Gemini ~$0.001 vs Claude ~$0.015 per test)
- Troubleshooting guide
- Performance benchmarks

### Test End-to-End Workflow ✅ NEW
```bash
# Full workflow: Migration Planner → Runtime Validator
".venv/Scripts/python.exe" tests/test_end_to_end.py

# Quick tests
".venv/Scripts/python.exe" tests/test_end_to_end.py --test planner  # ~30s, ~$0.001 with Gemini
".venv/Scripts/python.exe" tests/test_end_to_end.py --test docker   # ~60s, no LLM cost
```

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
# Run unit tests (mocked LLM - fast, free)
".venv/Scripts/python.exe" -m pytest tests/test_migration_planner.py -v
# ✅ 7 tests PASSED in <1s, $0 cost

# Run standalone with real LLM (requires API key)
".venv/Scripts/python.exe" -m agents.migration_planner
# ✅ Works with all providers: Gemini (~$0.0005), Claude (~$0.015)
# ✅ Robust parsing handles different LLM response formats
```

### Test Docker Validation Tools ✅
```bash
# Test with sample Express app
".venv/Scripts/python.exe" -m tools.docker_tools
# ✅ All stages successful (~60 seconds)
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
pytest tests/ -v                           # All unit tests (66 tests, fast, mocked)
pytest tests/test_migration_planner.py -v  # Migration planner tests (7 tests)
pytest tests/test_staging_deployer.py -v   # Staging deployer tests (19 tests)
pytest tests/test_error_analyzer.py -v     # Error analyzer tests (19 tests)
pytest tests/test_workflow.py -v           # Workflow routing/state tests (15 tests)
pytest tests/test_workflow_integration.py -v  # Workflow integration tests (3 tests)
pytest tests/ --cov=. --cov-report=html    # With coverage report
pytest tests/ -v -s                        # Show print statements

# Integration tests (require API keys and Docker)
python tests/test_end_to_end.py            # Full E2E workflow (3 tests)
python tests/test_end_to_end.py --test planner  # Just migration planner
python tests/test_end_to_end.py --test docker   # Just Docker validation

# Test complete LangGraph workflow
python -m graph.workflow                   # Full 4-agent workflow (requires API keys + Docker)
```

### MCP Server Installation (Optional - Not Required Yet)
```bash
npm install -g @modelcontextprotocol/server-github
npm install -g @modelcontextprotocol/server-filesystem

# Test MCP connection (uses fallback mode without servers)
python tools/test_mcp.py
```

**Note for Windows Users**: The configuration has been updated to use `npx.cmd` instead of `npx` to ensure proper subprocess execution on Windows systems.

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

**Overall**: 95% complete (6/7 phases) - Updated 2025-11-14

**Completed**:
- ✅ Phase 1: Core Infrastructure (100%)
- ✅ Phase 2: Base Agent Infrastructure (100%)
- ✅ Phase 3: Core Agents (100% - All 4 agents complete)
- ✅ Phase 4: LangGraph Workflow (100% - 4-agent orchestration complete)
- ✅ Phase 5: FastAPI Backend (100% - REST API + WebSocket + report generation)
- ✅ Phase 6: Frontend (100% - React app with real-time updates, report viewing/downloading)

**Current**: Phase 7 - Production Ready (95%)

**Completed Features**:
1. ✅ All 4 agents (Migration Planner, Runtime Validator, Error Analyzer, Staging Deployer) - COMPLETE
2. ✅ LangGraph workflow with 4-agent orchestration - COMPLETE
3. ✅ FastAPI backend with REST endpoints + WebSocket - COMPLETE
4. ✅ Comprehensive report generation (HTML/Markdown/JSON) - COMPLETE
5. ✅ Frontend with real-time updates via WebSocket - COMPLETE
6. ✅ Report viewing in browser + Download dropdown (HTML/Markdown/JSON) - COMPLETE
7. ✅ Migration ID bug fix (proper state management) - COMPLETE

**Next Steps**:
1. Production deployment (containerization, environment setup)
2. Advanced features (GitHub OAuth, PR auto-approval workflows)
3. Performance optimization (caching, database integration)

**Test Coverage** (66 total tests, all passing):
- Migration Planner: 7 tests ✅
- Staging Deployer: 19 tests ✅
- Error Analyzer: 19 tests ✅
- Workflow Routing/State: 15 tests ✅
- Workflow Integration: 3 tests ✅
- End-to-End Integration: 3 tests ✅

**4-Agent Workflow Capabilities**:
- **Agent 1 (Migration Planner)**: npm registry integration + accurate version detection
- **Agent 2 (Runtime Validator)**: Docker isolation + functional tests + auto-cleanup
- **Agent 3 (Error Analyzer)**: Conditional execution + smart error categorization
- **Agent 4 (Staging Deployer)**: GitHub PR creation + timestamp-based branching
- Conditional routing based on validation results
- Automatic retry logic (up to 3 fix attempts)
- Error recovery with intelligent fix suggestions
- Cost tracking across all 4 agents
- Comprehensive report generation (HTML/Markdown/JSON)

See `DEVELOPMENT_PLAN_STATUS.md` for detailed tracking and `docs/IMPLEMENTATION_PROGRESS.md` for comprehensive progress report.
