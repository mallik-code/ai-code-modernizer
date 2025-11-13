# AI Code Modernizer Backend

## Project Overview

The AI Code Modernizer Backend is a sophisticated Python application that leverages LangGraph to orchestrate AI agents for analyzing, validating, and upgrading code dependencies. The system uses Claude Sonnet 4 for intelligent reasoning and MCP (Model Context Protocol) for secure tool access. It's designed to safely modernize codebases by identifying outdated dependencies, creating migration strategies, validating changes in isolated Docker containers, and deploying updates.

### Key Features
- **Multi-Agent Architecture**: Specialized agents for migration planning, runtime validation, error analysis, and staging deployment
- **LangGraph Orchestration**: Stateful workflow management with conditional routing and retry logic
- **Docker Isolation**: Safe code execution in containerized environments to prevent host system compromise
- **MCP Integration**: Secure tool access via Model Context Protocol for file operations and GitHub integration
- **Real-time Updates**: WebSocket-based communication for live progress monitoring
- **Cost Tracking**: Built-in token usage and cost monitoring for LLM operations
- **Comprehensive Security**: Multiple security layers including input validation, rate limiting, and human approval requirements
- **Git Branch Management**: Support for specifying target branches for migration consistency
- **GitHub Integration**: Enhanced GitHub operations with token-based authentication
- **Enhanced Reporting**: Comprehensive HTML/Markdown/JSON reports with workflow execution details and AI insights

## Architecture

### Multi-Agent System
All agents inherit from `BaseAgent` which provides:
- LLM client integration with flexible provider support (Anthropic, OpenAI, Gemini, HuggingFace, Qwen)
- MCP tool manager access for secure operations
- Structured logging with rich context
- Conversation history tracking

**Four Specialized Agents**:
1. **Migration Planner** ✅ - Analyzes dependency files, identifies outdated dependencies, researches breaking changes, and creates phased migration plans. Features robust multi-LLM response parsing that handles varying formats from different providers (Gemini, Claude, GPT, Qwen, Llama).
2. **Runtime Validator** ✅ - Creates Docker containers, applies upgrades, runs applications, tests health endpoints, and returns validation results with LLM-powered analysis.
3. **Error Analyzer** ✅ - Parses error logs (npm, pip, runtime), identifies root causes, generates fix suggestions with LLM-powered analysis and fallback categorization. Extracts code context and proposes alternative strategies. Features smart pattern matching to avoid false positives (e.g., "TypeError" vs "peer dependency").
4. **Staging Deployer** ✅ - Creates Git branches, updates dependency files (package.json/requirements.txt), generates conventional commits, creates detailed PR descriptions, and integrates with GitHub via MCP tools. Implements human-in-the-loop approval via pull requests.

### Multi-Provider LLM Architecture
The system supports multiple LLM providers through a flexible factory pattern:

- **Base Interface** (`llm/base.py`) - Abstract base class for all LLM providers
- **Provider Implementations**:
  - `llm/anthropic_client.py` - Anthropic Claude models
  - `llm/openai_client.py` - OpenAI GPT models  
  - `llm/gemini_client.py` - Google Gemini models
  - `llm/huggingface_client.py` - Hugging Face hosted models
  - `llm/qwen_client.py` - Qwen (Alibaba Cloud) models
- **Factory Pattern** (`llm/factory.py`) - Creates appropriate LLM client based on configuration
- **Flexible Agent Integration** (`agents/base.py`) - Supports provider selection per agent instance

### Core Components
- **MCP Tool Manager** (`tools/mcp_tools.py`) - Manages connections to MCP servers and exposes tools for file operations and GitHub integration
- **LangGraph Workflow** ✅ (`graph/workflow.py`) - Orchestrates all 4 agents in a stateful workflow with conditional routing, retry logic (up to 3 attempts), and automatic error recovery. Routes validation failures to Error Analyzer, retries with fixes, and deploys successful upgrades via Staging Deployer.
- **State Management** (`graph/state.py`) - Enhanced state schema with additional fields for git_branch tracking, github_token support, and improved branch_name handling
- **Cost Tracker** (`utils/cost_tracker.py`) - Automatically tracks token usage and costs for LLM operations across all providers
- **Docker Validator** (`tools/docker_tools.py`) - Handles containerized validation of code changes
- **Git Branch Management** - Enhanced workflow with support for specifying source branches and tracking target branches
- **GitHub Token Integration** - Secure GitHub operations with token-based authentication for PR creation and repository access
- **Enhanced Report Generator** - Comprehensive reporting with workflow execution diagrams, agent performance metrics, and AI decision insights

## Building and Running

### Prerequisites
- Python 3.11+
- Docker Desktop (for containerized validation)
- Anthropic API key
- GitHub personal access token
- Node.js (for MCP server installation)

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

### MCP Server Installation
```bash
npm install -g @modelcontextprotocol/server-github
npm install -g @modelcontextprotocol/server-filesystem
```

**Note for Windows Users**: The configuration has been updated to use `npx.cmd` instead of `npx` to ensure proper subprocess execution on Windows systems.

### Running Backend
```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

API docs: http://localhost:8000/docs

### Testing Individual Components
Each component is independently executable for testing:
```bash
# Test flexible LLM system (all providers)
python -m llm.test_flexible_llm

# Test MCP tools
python tools/test_mcp.py

# Test cost tracker
python -m utils.cost_tracker

# Test logger
python -m utils.logger

# Test base agent
python -m agents.base

# Test LLM providers
python -m tests.test_llm_providers

# Test Migration Planner (with real LLM)
python -m agents.migration_planner
# Works with any provider: Gemini (~$0.0005), Claude (~$0.015), Qwen (~$0.0001)

# Test Runtime Validator (requires Docker + API key)
python -m agents.runtime_validator

# Test Docker tools
python -m tools.docker_tools
```

### Running Tests
```bash
# Unit tests (fast, mocked, no API keys needed)
pytest tests/ -v                           # All unit tests (66 tests total)
pytest tests/test_migration_planner.py -v  # Migration planner (7 tests)
pytest tests/test_staging_deployer.py -v   # Staging deployer (19 tests)
pytest tests/test_error_analyzer.py -v     # Error analyzer (19 tests)
pytest tests/test_workflow.py -v           # Workflow routing/state (15 tests)
pytest tests/test_workflow_integration.py -v  # Workflow integration (3 tests)
pytest tests/ --cov=. --cov-report=html    # With coverage
pytest tests/ -v -s                        # Show print statements

# Integration tests (require API keys + Docker)
python tests/test_end_to_end.py            # Full E2E workflow
python tests/test_end_to_end.py --test planner  # Just migration planner (~30s)
python tests/test_end_to_end.py --test docker   # Just Docker validation (~60s)

# Test complete LangGraph workflow
python -m graph.workflow                   # Full workflow (requires API keys + Docker)
```

### Comprehensive Testing Guide
See `TESTING_GUIDE.md` for complete documentation including:
- Quick start commands for all test types
- Expected test times and costs per provider
- Provider cost comparison (Gemini: ~$0.001, Claude: ~$0.015, Qwen: ~$0.0005)
- Troubleshooting common issues
- Performance benchmarks
- Testing strategies by use case

## Development Conventions

### Python Standards
- Follow PEP 8 style guide with comprehensive type hints
- Use Google-style docstrings for all public functions and classes
- Create custom exception hierarchies for domain-specific errors
- Use dataclasses for mutable data and TypedDict for dictionaries
- Apply context managers for resource cleanup
- Implement async/await patterns for I/O-bound operations
- Use structured logging with rich context information

### Security Guidelines
- Principle of least privilege: Agents have minimal required tool access
- Input validation and sanitization before processing
- Prompt injection prevention with structured inputs
- Tool call validation before execution
- Docker isolation for all code execution
- Rate limiting and resource controls
- Secure secrets management without logging or exposure
- Comprehensive audit logging for all agent actions
- Human approval for critical operations

### Testing Standards
- Comprehensive test coverage including happy path and error cases
- Parametrized tests for multiple scenarios
- Async test support for async operations
- Mock usage for external dependencies
- Performance and load testing

## API Layer

### FastAPI Application (`api/main.py`)
- CORS configured for frontend (localhost:5173)
- Health check endpoints
- Project analysis and upgrade endpoints
- WebSocket for real-time updates

### Key Endpoints
- `GET /api/health` - Health check
- `GET /api/` - Root endpoint
- `POST /api/migrations/start` - Start migration workflow with support for:
  - `project_path` - Path to local project
  - `project_type` - 'nodejs' or 'python'
  - `max_retries` - Maximum retry attempts
  - `git_branch` - Git branch to use for migration (default: 'main')
  - `github_token` - GitHub Personal Access Token for API operations (optional)
- `GET /api/migrations/{migration_id}` - Get workflow status
- `GET /api/migrations` - List all migrations with pagination
- `GET /api/migrations/{migration_id}/report` - Download comprehensive reports
- `DELETE /api/migrations/{migration_id}` - Delete a migration record

## Enhanced Features

### Git Branch Management
- The system now supports specifying a specific branch for migration via the `git_branch` parameter
- Automatically checks out the specified branch before starting the migration
- Creates upgrade branches from the specified baseline for consistent results
- Tracks source and target branches in migration reports

### GitHub Token Integration
- Added support for GitHub Personal Access Token via the `github_token` parameter
- Token is securely passed through the workflow to enable authenticated GitHub operations
- Allows for actual GitHub API calls instead of mock responses when creating pull requests
- Enables proper PR links in migration reports

### Improved Migration Reports
- Enhanced HTML/Markdown/JSON reports with more detailed information
- Clear tracking of source branch → target branch transitions
- Detailed breakdown of test results and validation outcomes
- Workflow execution diagrams showing the 4-agent process
- Agent execution summaries with costs and details
- AI/LLM insights explaining decision-making processes
- Comprehensive dependency analysis with breaking changes details

## Environment Variables

Required in `.env`:
```bash
# LLM Provider Configuration
# Select which LLM provider to use (anthropic, openai, gemini, huggingface, qwen)
LLM_PROVIDER=anthropic

# Anthropic API
ANTHROPIC_API_KEY=sk-ant-xxxxx
ANTHROPIC_MODEL=claude-sonnet-4-20250514

# OpenAI API
OPENAI_API_KEY=sk-xxxxx
OPENAI_MODEL=gpt-4o

# Google Gemini API
GOOGLE_API_KEY=xxxxx
GEMINI_MODEL=gemini-2.0-flash

# HuggingFace API
HUGGINGFACE_API_KEY=hf_xxxxx
HUGGINGFACE_MODEL=meta-llama/Llama-3.2-3B-Instruct

# Qwen API (via DashScope)
QWEN_API_KEY=sk-xxxxx-xxx-xxx-xxx  # Also can use DASHSCOPE_API_KEY
QWEN_MODEL=qwen-turbo

# GitHub Integration
GITHUB_TOKEN=ghp_xxxxx

# LangChain Tracing (Optional)
LANGCHAIN_TRACING_V2=false
LANGCHAIN_API_KEY=ls__xxxxx

# OpenRouter (Future Use)
OPENROUTER_API_KEY=sk-or-xxxxx

# Database
DATABASE_URL=sqlite:///./modernizer.db

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Docker Configuration
DOCKER_TIMEOUT=300
MAX_RETRY_ATTEMPTS=3

# Feature Flags
ENABLE_STAGING_DEPLOYMENT=true
ENABLE_AUTO_FIX=true
```

## Migration Request Parameters

The `/api/migrations/start` endpoint now accepts the following parameters:

- **project_path** (required): Absolute or relative path to the project
- **project_type** (required): 'nodejs' or 'python'
- **max_retries** (optional): Maximum retry attempts for failed validations (default: 3)
- **git_branch** (optional): Git branch to use for the migration (default: 'main')
- **github_token** (optional): GitHub Personal Access Token for API operations
- **options** (optional): Additional options dictionary

## Key Dependencies

- `anthropic>=0.18.0` - Claude API for AI reasoning
- `openai>=1.35.0` - OpenAI API for GPT models
- `google-generativeai>=0.8.0` - Google Gemini API
- `huggingface_hub>=0.20.0` - Hugging Face model hub access
- `dashscope>=1.13.0` - Alibaba Cloud DashScope SDK for Qwen models
- `langgraph>=0.2.16` - Multi-agent orchestration framework
- `mcp>=0.1.0` - Model Context Protocol for secure tool access
- `fastapi>=0.104.0` - Web framework with automatic API documentation
- `docker>=6.1.0` - Container management for isolated validation
- `structlog>=23.2.0` - Structured logging with rich output
- `tiktoken>=0.5.0` - Token counting for cost tracking
- `pytest>=7.4.0` - Testing framework with coverage support

## Development Workflow

### Adding New Tools
1. Add tool to MCP server or create custom tool in `tools/`
2. Add wrapper method to `MCPToolManager` if MCP-based
3. Document tool usage in agent system prompts

### Modifying Workflow
1. Update `graph/state.py` if state schema changes
2. Modify `graph/workflow.py` for routing logic
3. Update agents to handle new state fields
4. Test with `python graph/workflow.py`

### Adding New Agent
1. Create file in `agents/` inheriting from `BaseAgent`
2. Implement `execute()` method
3. Add standalone test in `if __name__ == "__main__"`
4. Register in workflow (`graph/workflow.py`)
5. Test standalone, then in workflow

## Security First Approach

This project implements comprehensive security measures following the security-first principle:
- All code execution occurs in isolated Docker containers
- Input validation and sanitization at every layer
- Prompt injection prevention through structured inputs
- Rate limiting and resource controls to prevent abuse
- Complete audit logging for all agent actions
- Human approval required for critical operations
- Principle of least privilege for agent permissions
- Secure secrets management without exposure in logs

## Debugging

- **LLM issues**: Run `python -m llm.test_flexible_llm` to test all LLM providers
- **MCP issues**: Run `python tools/mcp_tools.py` to test connectivity
- **Agent issues**: Run agent standalone with test data
- **Workflow issues**: Check state transitions and conditional logic in `graph/workflow.py`
- **Docker issues**: Ensure Docker Desktop running, test with `docker ps`
- **API issues**: Visit FastAPI auto-docs at http://localhost:8000/docs
- **Import errors**: Ensure virtual environment activated, dependencies installed