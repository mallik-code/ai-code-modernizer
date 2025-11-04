# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-Powered Code Modernization Platform - A multi-agent system that autonomously upgrades code dependencies through intelligent analysis, runtime validation in Docker containers, and staged deployment via GitHub.

**Architecture**: Multi-agent system orchestrated by LangGraph, with React frontend and Python FastAPI backend.

## Repository Structure

```
ai-code-modernizer/
├── backend/           # Python backend with LangGraph agents
│   └── CLAUDE.md     # Backend-specific guidance
├── frontend/          # React + TypeScript frontend
│   └── CLAUDE.md     # Frontend-specific guidance
├── README.md          # Project documentation
├── PROJECT_STRUCTURE.md
├── QUICK_START.md
└── DEVELOPMENT_PLAN.md
```

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker Desktop (running)
- Anthropic API key (console.anthropic.com)
- GitHub Personal Access Token (needs `repo` scope)

### Setup
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with API keys

# MCP servers
npm install -g @modelcontextprotocol/server-github
npm install -g @modelcontextprotocol/server-filesystem

# Frontend
cd ../frontend
npm install
```

### Running
```bash
# Terminal 1 - Backend
cd backend
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend
cd frontend
npm run dev
```

Access: http://localhost:5173

## High-Level Architecture

### Multi-Agent System with LangGraph
Four specialized agents orchestrated in a stateful workflow:
1. **Migration Planner** - Analyzes dependencies, creates upgrade strategies
2. **Runtime Validator** - Tests upgrades in Docker containers
3. **Error Analyzer** - Diagnoses failures, generates fixes
4. **Staging Deployer** - Creates branches and PRs on GitHub

### MCP (Model Context Protocol) Integration
Agents access tools via MCP servers:
- **GitHub MCP** - Repository operations, file reads, PR creation
- **Filesystem MCP** - Local file operations

The `MCPToolManager` handles server connections and routes tool calls.

### State Flow
```
User Upload → Planner → Validator → [Pass: Deployer | Fail: Analyzer → Validator]
```

State (`MigrationState`) passes between agents via LangGraph containing project info, strategies, validation results, and errors.

### Frontend ↔ Backend Communication
- **REST API** - Project submission, status queries
- **WebSocket** - Real-time agent updates, thinking streams, graph state changes

## Development Workflow

The project follows a 5-day implementation plan (`DEVELOPMENT_PLAN.md`):
- **Day 1**: Core infrastructure (MCP, base agents, logging)
- **Day 2**: Core agents (planner, validator)
- **Day 3**: Advanced agents + LangGraph workflow
- **Day 4**: API layer + WebSocket + Frontend
- **Day 5**: Testing + demo

Build bottom-up:
1. Test MCP connectivity
2. Create and test individual agents standalone
3. Integrate agents into LangGraph workflow
4. Add API layer
5. Build frontend components

## Testing

```bash
# Backend
cd backend
pytest tests/ -v

# Frontend
cd frontend
npm test
```

## Key Design Principles

1. **Testability First** - Every component independently executable
2. **Stateless Agents** - All state via LangGraph, not stored in agents
3. **Docker Isolation** - Validation in containers, never on host
4. **Human-in-the-Loop** - Deployments require explicit approval
5. **Cost Tracking** - Monitor token usage for all LLM calls

## Component-Specific Guidance

For detailed backend development (agents, MCP, LangGraph): see `backend/CLAUDE.md`
For detailed frontend development (React, WebSocket, UI): see `frontend/CLAUDE.md`

## Tech Stack Summary

**Backend**: Python 3.11+, LangGraph 0.2.16+, Claude Sonnet 4, FastAPI, Docker SDK, MCP
**Frontend**: React 18, TypeScript, Vite, TailwindCSS, ReactFlow, Zustand
