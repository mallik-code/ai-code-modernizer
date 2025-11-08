# Project Overview

This is the backend for an AI-powered code modernization platform. It uses a multi-agent architecture orchestrated by LangGraph to automate the process of upgrading and modernizing existing codebases.

**Key Technologies:**

*   Python 3.11+
*   FastAPI
*   LangGraph
*   Model Context Protocol (MCP)
*   Docker
*   LLM Providers: Anthropic, OpenAI, Gemini, Hugging Face, Qwen

**Architecture:**

The backend follows a layered architecture:

1.  **Presentation Layer (api/)**: Handles external communication via REST API and WebSockets.
2.  **Orchestration Layer (graph/)**: Coordinates the workflow using LangGraph and manages the state.
3.  **Agent Layer (agents/)**: Contains autonomous agents that perform specific tasks, such as migration planning, runtime validation, and error analysis.
4.  **Infrastructure Layer:**
    *   **LLM Provider Abstraction (llm/)**: Provides a unified interface for different LLM providers.
    *   **Tool Integration (tools/)**: Integrates external tools via MCP.
    *   **Utilities (utils/)**: Provides cross-cutting functionalities like cost tracking and logging.

**Multi-Agent System:**

All agents inherit from `BaseAgent` which provides:

*   Flexible LLM client (configurable per agent)
*   MCP tool manager access
*   Structured logging
*   Conversation history tracking

**LLM Provider Abstraction:**

The system supports multiple LLM providers through a flexible factory pattern. Key components include:

*   Base Interface (`llm/base.py`): Abstract base class for all LLM providers.
*   Provider Implementations: `anthropic_client.py`, `openai_client.py`, `gemini_client.py`, `huggingface_client.py`, `qwen_client.py`
*   Factory Pattern (`llm/factory.py`): Creates appropriate LLM client based on configuration.

**MCP Servers:**

The project uses two MCP servers:

*   `github`: Provides access to GitHub repositories. Requires a `GITHUB_TOKEN` environment variable.
*   `filesystem`: Provides access to the local file system.

## Building and Running

**Prerequisites:**

*   Python 3.11+
*   Virtual environment
*   Docker Desktop
*   API keys for LLM providers (Anthropic, OpenAI, Gemini, etc.)
*   MCP servers installed (`npm install -g @modelcontextprotocol/server-github @modelcontextprotocol/server-filesystem`)

**Setup:**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows, use .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with API keys and tokens
```

**Running the API:**

```bash
cd api
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API docs: http://localhost:8000/docs

**Running Tests:**

```bash
pytest tests/ -v
```

**Testing Individual Components:**

Each component is independently executable for testing:

```bash
# Test flexible LLM system
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
```

## Development Conventions

*   Follow PEP 8 style guide with comprehensive type hints.
*   Use Google-style docstrings for all public functions and classes.
*   Create custom exception hierarchies for domain-specific errors.
*   Use dataclasses for mutable data and TypedDict for dictionaries.
*   Apply context managers for resource cleanup.
*   Implement async/await patterns for I/O-bound operations.
*   Use structured logging with rich context information.
*   Comprehensive test coverage including happy path and error cases.
*   Parametrized tests for multiple scenarios.
*   Async test support for async operations.
*   Mock usage for external dependencies.
*   Performance and load testing.

**Security Guidelines:**

*   Principle of least privilege: Agents have minimal required tool access.
*   Input validation and sanitization before processing.
*   Prompt injection prevention with structured inputs.
*   Tool call validation before execution.
*   Docker isolation for all code execution.
*   Rate limiting and resource controls.
*   Secure secrets management without logging or exposure.
*   Comprehensive audit logging for all agent actions.
*   Human approval required for critical operations.