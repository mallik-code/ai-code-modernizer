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

## Architecture

### Multi-Agent System
All agents inherit from `BaseAgent` which provides:
- LLM client integration with Anthropic API
- MCP tool manager access for secure operations
- Structured logging with rich context
- Conversation history tracking

**Four Specialized Agents**:
1. **Migration Planner** - Analyzes dependency files, identifies outdated dependencies, researches breaking changes, and creates phased migration plans
2. **Runtime Validator** - Creates Docker containers, applies upgrades, runs applications, tests health endpoints, and returns validation results
3. **Error Analyzer** - Parses error logs, identifies root causes, generates fix suggestions, and proposes alternative strategies
4. **Staging Deployer** - Creates Git branches, commits changes, and creates pull requests via MCP GitHub tools

### Core Components
- **MCP Tool Manager** (`tools/mcp_tools.py`) - Manages connections to MCP servers and exposes tools for file operations and GitHub integration
- **LangGraph Workflow** (`graph/workflow.py`) - Orchestrates agents in a stateful workflow with conditional routing and retry logic
- **Cost Tracker** (`utils/cost_tracker.py`) - Automatically tracks token usage and costs for LLM operations
- **Docker Validator** (`tools/docker_tools.py`) - Handles containerized validation of code changes

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

### Running Backend
```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

API docs: http://localhost:8000/docs

### Testing Individual Components
Each component is independently executable for testing:
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
- `POST /api/projects/analyze` - Analyze project dependencies
- `POST /api/projects/upgrade` - Start upgrade workflow
- `GET /api/projects/{id}/status` - Get workflow status

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

## Key Dependencies

- `anthropic>=0.18.0` - Claude API for AI reasoning
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

- **MCP issues**: Run `python tools/mcp_tools.py` to test connectivity
- **Agent issues**: Run agent standalone with test data
- **Workflow issues**: Check state transitions and conditional logic in `graph/workflow.py`
- **Docker issues**: Ensure Docker Desktop running, test with `docker ps`
- **API issues**: Visit FastAPI auto-docs at http://localhost:8000/docs
- **Import errors**: Ensure virtual environment activated, dependencies installed