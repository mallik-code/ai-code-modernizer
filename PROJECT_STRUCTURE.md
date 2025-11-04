# Project Structure

## Overview

This document describes the complete project structure for the AI-Powered Code Modernization Platform.

## Directory Structure

```
ai-code-modernizer/
│
├── backend/                          # Python backend application
│   ├── agents/                       # AI Agent implementations
│   │   ├── __init__.py
│   │   ├── base.py                  # Base agent class
│   │   ├── migration_planner.py     # Migration strategy agent
│   │   ├── runtime_validator.py     # Docker validation agent
│   │   ├── error_analyzer.py        # Error diagnosis agent
│   │   └── staging_deployer.py      # Deployment agent
│   │
│   ├── graph/                        # LangGraph workflow
│   │   ├── __init__.py
│   │   ├── state.py                 # State schema definitions
│   │   ├── workflow.py              # Main workflow graph
│   │   └── nodes.py                 # Graph node implementations
│   │
│   ├── tools/                        # Tool implementations
│   │   ├── __init__.py
│   │   ├── mcp_tools.py             # MCP tool manager
│   │   ├── docker_tools.py          # Docker SDK wrapper
│   │   ├── code_analyzer.py         # Static code analysis
│   │   └── web_search.py            # Web search integration
│   │
│   ├── llm/                          # LLM client configuration
│   │   ├── __init__.py
│   │   └── client.py                # Anthropic API client
│   │
│   ├── config/                       # Configuration management
│   │   ├── __init__.py
│   │   └── model_config.py          # Model and agent configs
│   │
│   ├── utils/                        # Utility modules
│   │   ├── __init__.py
│   │   ├── cost_tracker.py          # API cost tracking
│   │   └── logger.py                # Structured logging
│   │
│   ├── api/                          # FastAPI application
│   │   ├── __init__.py
│   │   ├── main.py                  # FastAPI app entry point
│   │   ├── routes.py                # HTTP endpoints
│   │   └── websocket.py             # WebSocket handlers
│   │
│   ├── tests/                        # Test suite
│   │   ├── __init__.py
│   │   ├── test_mcp.py              # MCP integration tests
│   │   ├── test_agents.py           # Agent unit tests
│   │   ├── test_graph.py            # Workflow tests
│   │   └── integration/             # End-to-end tests
│   │       ├── test_end_to_end.py
│   │       └── test_scenarios.py
│   │
│   ├── requirements.txt              # Python dependencies
│   ├── .env.example                  # Environment variables template
│   ├── mcp_config.json               # MCP server configuration
│   └── .gitignore                    # Python-specific ignores
│
├── frontend/                         # React frontend application
│   ├── src/
│   │   ├── components/               # Reusable React components
│   │   │   ├── AgentCard.tsx        # Agent status display
│   │   │   ├── GraphView.tsx        # Workflow visualization
│   │   │   ├── ThinkingStream.tsx   # Live agent thinking
│   │   │   ├── DecisionModal.tsx    # Human approval UI
│   │   │   └── CostTracker.tsx      # Cost display
│   │   │
│   │   ├── pages/                    # Page components
│   │   │   ├── Dashboard.tsx        # Main dashboard
│   │   │   ├── ProjectUpload.tsx    # Project submission
│   │   │   └── Results.tsx          # Migration results
│   │   │
│   │   ├── hooks/                    # Custom React hooks
│   │   │   ├── useWebSocket.ts      # WebSocket connection
│   │   │   ├── useAgentState.ts     # Agent state management
│   │   │   └── useWorkflow.ts       # Workflow tracking
│   │   │
│   │   ├── lib/                      # Utilities and helpers
│   │   │   ├── api.ts               # API client
│   │   │   ├── utils.ts             # Helper functions
│   │   │   └── types.ts             # TypeScript types
│   │   │
│   │   ├── App.tsx                   # Root component
│   │   └── main.tsx                  # Entry point
│   │
│   ├── public/                       # Static assets
│   │   ├── index.html
│   │   └── favicon.ico
│   │
│   ├── package.json                  # Node dependencies
│   ├── tsconfig.json                 # TypeScript config
│   ├── tsconfig.node.json            # TypeScript node config
│   ├── vite.config.ts                # Vite build config
│   ├── tailwind.config.js            # TailwindCSS config
│   ├── postcss.config.js             # PostCSS config
│   └── .gitignore                    # Frontend-specific ignores
│
├── README.md                         # Project documentation
├── PROJECT_STRUCTURE.md              # This file
├── QUICK_START.md                    # Quick setup guide
└── .gitignore                        # Root gitignore

```

## Key Files Description

### Backend

#### `backend/agents/base.py`
Base class for all agents with common functionality:
- LLM interaction
- Tool execution
- Error handling
- State management

#### `backend/graph/workflow.py`
Main LangGraph workflow definition:
- Agent orchestration
- Conditional routing
- Retry logic
- Human-in-the-loop interrupts

#### `backend/tools/mcp_tools.py`
MCP Tool Manager for standardized tool integration:
- GitHub MCP server connection
- Filesystem MCP server connection
- Tool call routing
- Error handling

#### `backend/api/main.py`
FastAPI application entry point:
- API route registration
- WebSocket setup
- CORS configuration
- Middleware setup

### Frontend

#### `frontend/src/components/GraphView.tsx`
ReactFlow-based workflow visualization:
- Real-time graph updates
- Node highlighting
- Edge animations
- Interactive controls

#### `frontend/src/hooks/useWebSocket.ts`
WebSocket connection management:
- Auto-reconnection
- Message handling
- State synchronization
- Error recovery

### Configuration

#### `backend/mcp_config.json`
MCP server configuration:
- Server definitions (GitHub, Filesystem)
- Environment variables
- Command-line arguments

#### `backend/.env.example`
Environment variables template:
- API keys (Anthropic, GitHub)
- Configuration settings
- Feature flags

## Development Workflow

### Day 1: Foundation
1. Set up MCP tools (`backend/tools/mcp_tools.py`)
2. Create base agent (`backend/agents/base.py`)
3. Test connections

### Day 2: Core Agents
1. Implement Migration Planner (`backend/agents/migration_planner.py`)
2. Implement Runtime Validator (`backend/agents/runtime_validator.py`)
3. Test individual agents

### Day 3: Advanced Features
1. Implement Error Analyzer (`backend/agents/error_analyzer.py`)
2. Create LangGraph workflow (`backend/graph/workflow.py`)
3. Add retry logic and checkpointing

### Day 4: Integration
1. Implement Staging Deployer (`backend/agents/staging_deployer.py`)
2. Create FastAPI endpoints (`backend/api/`)
3. Add comprehensive testing

### Day 5: UI & Demo
1. Build React dashboard (`frontend/src/`)
2. Create demo scenarios
3. Polish and practice presentation

## Getting Started

See [README.md](./README.md) for detailed setup instructions.

## Tech Stack Summary

**Backend:**
- Python 3.11+
- LangGraph + LangChain
- Claude Sonnet 4 (Anthropic)
- FastAPI + WebSockets
- Docker SDK
- MCP (Model Context Protocol)

**Frontend:**
- React 18 + TypeScript
- Vite
- TailwindCSS
- ReactFlow
- Zustand

**Tools:**
- MCP GitHub Server
- MCP Filesystem Server
- Docker
- Git

## Next Steps

1. Install dependencies (see README.md)
2. Configure API keys (`.env`)
3. Start with Day 1 tasks
4. Follow the implementation plan in `ai-powered-code-moderizer-platform.md`
