# AI Code Modernizer

AI Code Modernizer is an advanced multi-agent system that automates the process of upgrading software dependencies in projects. It leverages LangGraph to orchestrate AI agents for analyzing, validating, and upgrading code dependencies safely.

## Table of Contents
- [Architecture](#architecture)
- [Design Details](#design-details)
- [Features](#features)
- [How to Run](#how-to-run)
- [API Endpoints](#api-endpoints)
- [WebSocket Streaming](#websocket-streaming)
- [Frontend UI](#frontend-ui)
- [Development](#development)

## Architecture

The system follows a microservices architecture with the following components:

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Frontend Dashboard                           │
│                        (React + TypeScript)                         │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  • Live agent visualization                                 │   │
│  │  • Graph workflow display                                   │   │
│  │  • Real-time thinking stream                                │   │
│  │  • Human decision prompts                                   │   │
│  │  • Cost tracking & ROI metrics                              │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                    ↕ WebSocket
┌─────────────────────────────────────────────────────────────────────┐
│                        Backend API Layer                            │
│                        (FastAPI)                                    │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  • REST API endpoints                                       │   │
│  │  • WebSocket endpoint for real-time updates                 │   │
│  │  • Migration management                                     │   │
│  │  • Report generation                                        │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                    ↕
┌─────────────────────────────────────────────────────────────────────┐
│                   LangGraph Agent Orchestrator                      │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────┐     │
│  │  Migration Strategy Agent                                 │     │
│  │  • Analyzes codebase structure                           │     │
│  │  • Researches breaking changes                           │     │
│  │  • Creates phased migration plans                        │     │
│  │  Tools: MCP(GitHub, Filesystem), Web Search              │     │
│  └──────────────────────────────────────────────────────────┘     │
│                            ↓                                        │
│  ┌──────────────────────────────────────────────────────────┐     │
│  │  Runtime Validation Agent                                 │     │
│  │  • Creates Docker test environment                       │     │
│  │  • Applies upgrades safely                               │     │
│  │  • Runs application + smoke tests                        │     │
│  │  • Validates critical flows                              │     │
│  │  Tools: Docker SDK, API Tester                           │     │
│  └──────────────────────────────────────────────────────────┘     │
│                            ↓                                        │
│  ┌──────────────────────────────────────────────────────────┐     │
│  │  Error Analysis Agent (conditional)                       │     │
│  │  • Diagnoses validation failures                         │     │
│  │  • Researches similar issues                             │     │
│  │  • Generates fixes automatically                         │     │
│  │  • Suggests alternative strategies                       │     │
│  │  Tools: MCP(GitHub), Web Search, Log Analyzer           │     │
│  └──────────────────────────────────────────────────────────┘     │
│                            ↓                                        │
│  ┌──────────────────────────────────────────────────────────┐     │
│  │  Staging Deployment Agent                                 │     │
│  │  • Creates feature branch                                │     │
│  │  • Pushes validated changes                              │     │
│  │  • Triggers CI/CD pipeline                               │     │
│  │  • Monitors deployment health                            │     │
│  │  • Notifies QA team                                      │     │
│  │  Tools: MCP(GitHub), CI/CD APIs                          │     │
│  └──────────────────────────────────────────────────────────┘     │
│                                                                     │
│  Human-in-the-Loop Decision Points:                                │
│  • After 3 failed retry attempts                                   │
│  • When multiple viable strategies exist                           │
│  • Before staging deployment (optional)                            │
│  • For production approval (always)                                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────────────┐
│                MCP Layer (Tool Integration)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐            │
│  │   GitHub     │  │  Filesystem  │  │  Slack      │            │
│  │  MCP Server  │  │  MCP Server  │  │ MCP Server  │            │
│  └──────────────┘  └──────────────┘  └─────────────┘            │
└─────────────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────────────┐
│                  Custom Tools (Non-MCP)                             │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐            │
│  │    Docker    │  │     Code     │  │    CI/CD    │            │
│  │  Validator   │  │   Analyzer   │  │  Integrator │            │
│  └──────────────┘  └──────────────┘  └─────────────┘            │
└─────────────────────────────────────────────────────────────────────┘
```

## Design Details

### Multi-Agent System
- **Migration Planner**: Analyzes dependencies and creates migration strategies
- **Runtime Validator**: Tests upgrades in Docker containers
- **Error Analyzer**: Diagnoses failures and suggests fixes
- **Staging Deployer**: Creates Git branches and PRs

### Key Components

#### LangGraph Workflow
- Multi-agent orchestration with state management
- Conditional routing and retry logic
- Checkpointing for resuming from any point
- Human-in-the-loop primitives

#### Flexible LLM System
- Support for multiple providers (Anthropic, OpenAI, Gemini, HuggingFace, Qwen)
- Automatic cost tracking across all providers
- Provider selection via environment variables

#### MCP (Model Context Protocol)
- Standardized tool integration
- Secure access to GitHub and filesystem
- Future-proof architecture with pluggable tools

#### Docker Isolation
- Safe validation in containerized environments
- Auto-cleanup of containers after validation
- Support for both Node.js and Python projects

#### WebSocket Streaming
- Real-time updates during agent execution
- Structured message format with metadata
- Comprehensive logging to file

## Features

- ✅ Multi-LLM provider support (Anthropic, OpenAI, Gemini, HuggingFace, Qwen)
- ✅ Cost tracking across all providers
- ✅ Structured logging infrastructure
- ✅ Base agent architecture with WebSocket support
- ✅ MCP tool manager (filesystem operations with fallback)
- ✅ Migration Planner Agent with npm registry integration
- ✅ Runtime Validator Agent with Docker isolation
- ✅ Error Analyzer Agent with smart error categorization
- ✅ Staging Deployer Agent with GitHub PR creation
- ✅ Docker validation tools with auto-cleanup
- ✅ Sample Node.js project for testing
- ✅ End-to-end integration tests
- ✅ Comprehensive testing guide
- ✅ LangGraph workflow with 4-agent orchestration
- ✅ FastAPI backend with WebSocket support
- ✅ Report generation (HTML/Markdown/JSON)
- ✅ Git branch management
- ✅ GitHub token integration
- ✅ Professional UI with real-time updates, custom logo, and report download capability

## How to Run

### Prerequisites
- Python 3.11+
- Docker Desktop (for containerized validation)
- Node.js (for MCP server installation)
- API keys for your preferred LLM provider (Anthropic, OpenAI, Gemini, etc.)

### Backend Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd ai-code-modernizer/backend
   ```

2. **Create and activate virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and other settings
   ```

5. **Install MCP tools** (optional):
   ```bash
   npm install -g @modelcontextprotocol/server-github
   npm install -g @modelcontextprotocol/server-filesystem
   ```

6. **Run the backend server**:
   ```bash
   uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend Setup

1. **Navigate to frontend directory**:
   ```bash
   cd ../frontend
   ```

2. **Serve the frontend with a local web server** (recommended):

   **Option 1: Using Python's built-in server:**
   ```bash
   cd frontend
   python -m http.server 5500
   ```
   Then open http://localhost:5500 in your browser

   **Option 2: Using Node's http-server:**
   ```bash
   cd frontend
   npx http-server
   ```
   Then open the provided URL in your browser

   **Option 3: Using Live Server extension in VS Code:**
   - Right-click `index.html` and select "Open with Live Server"

3. **Alternative: Direct file access** (requires backend CORS configuration):
   - Simply double-click the `index.html` file or open it with your preferred browser
   - Note: You will encounter CORS issues when making API calls from file:// protocol
   - To resolve this, set `CORS_ALLOW_ALL=true` in your `.env` file in the backend directory:
     ```
     CORS_ALLOW_ALL=true
     ```
   - Then restart the backend server

4. **Frontend Documentation**: See `frontend/README.md` for detailed frontend-specific instructions

### API Documentation
API documentation is available at: `http://localhost:8000/docs`

## API Endpoints

### Health Check
- `GET /api/health` - Check service health and configuration

### Migration Management
- `POST /api/migrations/start` - Start new migration workflow
- `GET /api/migrations/{migration_id}` - Get specific migration status
- `GET /api/migrations` - List all migrations with pagination
- `GET /api/migrations/{migration_id}/report` - Download migration report
- `DELETE /api/migrations/{migration_id}` - Delete a migration record

### WebSocket
- `WS /ws/migrations/{migration_id}` - Real-time migration updates

## WebSocket Streaming

The application includes WebSocket support for real-time updates during migration workflows:

### Message Format
```json
{
  "type": "agent_completion",
  "agent": "migration_planner",
  "status": "success",
  "message": "Migration plan created successfully",
  "dependencies_count": 5,
  "timestamp": "2023-10-27T10:30:00.123456"
}
```

### Message Types
- `connection`: When a client connects
- `workflow_start`: When the workflow begins
- `workflow_status`: Status updates about which agent is running
- `agent_completion`: When an agent completes (success or failure)
- `workflow_complete`: When the entire workflow completes
- `workflow_error`: If the workflow encounters an error
- `agent_thinking`: When an agent is using LLM to think
- `agent_thinking_complete`: When an agent completes thinking
- `tool_use`: When an agent uses a tool
- `tool_complete`: When a tool use completes

## Frontend UI

The frontend UI provides a complete interface for:

1. Starting new migrations
2. Monitoring real-time progress via WebSocket
3. Viewing migration details and status
4. Accessing generated reports when available

### Features
- Professional ribbon with logo and user icon
- Migration form with project configuration
- Real-time status indicator
- Progress bar visualization
- WebSocket log viewer with color-coded messages
- Report viewer with embedded iframe
- Responsive design for all device sizes

## Development

### Testing
Run the test suite:
```bash
# Run all unit tests
pytest tests/ -v

# Run specific test modules
pytest tests/test_migration_planner.py -v
pytest tests/test_staging_deployer.py -v
pytest tests/test_error_analyzer.py -v
pytest tests/test_workflow.py -v
pytest tests/test_workflow_integration.py -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

### Adding New Agents
1. Create new agent file in `agents/` inheriting from `BaseAgent`
2. Implement `execute()` method
3. Add standalone test in `if __name__ == "__main__"`
4. Register in workflow (`graph/workflow.py`)
5. Test standalone, then in workflow

### Environment Variables
Required in `.env`:
```bash
# LLM Provider Configuration
LLM_PROVIDER=anthropic  # or openai, gemini, huggingface, qwen

# Anthropic API (if using Anthropic)
ANTHROPIC_API_KEY=sk-ant-xxxxx
ANTHROPIC_MODEL=claude-sonnet-4-20250514

# OpenAI API (if using OpenAI)
OPENAI_API_KEY=sk-xxxxx
OPENAI_MODEL=gpt-4o

# Google Gemini API (if using Gemini)
GOOGLE_API_KEY=xxxxx
GEMINI_MODEL=gemini-2.0-flash

# HuggingFace API (if using HuggingFace)
HUGGINGFACE_API_KEY=hf_xxxxx
HUGGINGFACE_MODEL=meta-llama/Llama-3.2-3B-Instruct

# Qwen API (if using Qwen)
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

## Logging

WebSocket messages are automatically logged to `websocket_messages.log` in the backend directory, providing a complete record of all real-time communication during migration workflows.