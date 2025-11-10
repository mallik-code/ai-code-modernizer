# Backend Development Plan

## 🎯 Goal: Build Executable, Testable Agents

This plan focuses on creating **runnable, testable agents** that can be executed independently before integrating into the full system.

**Current Status**: Phase 4 Complete (60% overall) - LangGraph Workflow Implemented ✅
**Last Updated**: 2025-11-08

---

## 📋 Prerequisites Checklist

### Environment Setup
- [ ] Python 3.11+ installed and verified
- [ ] Virtual environment created (`python -m venv .venv`)
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Docker Desktop installed and running
- [ ] `.env` file created with API keys

### API Keys & Tokens
- [ ] `ANTHROPIC_API_KEY` - Get from https://console.anthropic.com/
- [ ] `GITHUB_TOKEN` - Get from https://github.com/settings/tokens (needs `repo` scope)
- [ ] Test API connectivity

### MCP Setup
- [ ] Install MCP servers: `npm install -g @modelcontextprotocol/server-github @modelcontextprotocol/server-filesystem`
- [ ] Verify `mcp_config.json` configuration
- [ ] Test MCP server connections

### Verification Commands
```bash
# Test Python
python --version  # Should be 3.11+

# Test virtual environment
which python  # Should point to venv

# Test Docker
docker ps

# Test Anthropic API
python -c "import anthropic; print('OK')"

# Test MCP (we'll create this)
python tools/test_mcp.py
```

---

## 🏗️ Development Phases

**Progress Summary**:
- ✅ Phase 1: Core Infrastructure (100%)
- ✅ Phase 2: Base Agent Infrastructure (100%)
- ✅ Phase 3: Core Agents (100%)
- ✅ Phase 4: LangGraph Workflow (100%)
- ❌ Phase 5: API Layer (0%)
- ❌ Phase 6: Testing & Polish (0%)

---

## Phase 1: Core Infrastructure ✅ COMPLETE (Day 1 - 4 hours)

### 1.1 LLM Client Setup (30 minutes)
**File**: `llm/client.py`

**Goal**: Reusable Anthropic client with cost tracking

**Implementation**:
```python
# llm/client.py
from anthropic import Anthropic
import os
from typing import List, Dict, Optional
from utils.cost_tracker import CostTracker

class LLMClient:
    """Wrapper for Anthropic API with cost tracking"""

    def __init__(self):
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.cost_tracker = CostTracker()
        self.model = "claude-sonnet-4-20250514"

    def generate(
        self,
        messages: List[Dict],
        system: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> str:
        """Generate response with cost tracking"""
        # Implementation
        pass

# Test it
if __name__ == "__main__":
    client = LLMClient()
    response = client.generate(
        messages=[{"role": "user", "content": "Hello!"}]
    )
    print(response)
```

**Test**:
```bash
python llm/client.py
# Should print: "Hello! How can I help you today?"
```

**Checklist**:
- [ ] File created
- [ ] Can initialize client
- [ ] Can make API call
- [ ] Handles errors gracefully
- [ ] Manual test passes

---

### 1.2 Cost Tracker Utility (30 minutes)
**File**: `utils/cost_tracker.py`

**Goal**: Track API usage and costs

**Implementation**:
```python
# utils/cost_tracker.py
import tiktoken
from typing import List, Dict

class CostTracker:
    """Track Anthropic API costs"""

    # Pricing per 1M tokens (as of 2024)
    PRICING = {
        "claude-sonnet-4-20250514": {
            "input": 3.00,
            "output": 15.00,
        }
    }

    def __init__(self):
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0

    def track_usage(self, input_tokens: int, output_tokens: int, model: str):
        """Track token usage and calculate cost"""
        # Implementation
        pass

    def get_report(self) -> Dict:
        """Get cost report"""
        return {
            "input_tokens": self.total_input_tokens,
            "output_tokens": self.total_output_tokens,
            "total_cost": self.total_cost,
        }

# Test it
if __name__ == "__main__":
    tracker = CostTracker()
    tracker.track_usage(1000, 500, "claude-sonnet-4-20250514")
    print(tracker.get_report())
```

**Checklist**:
- [ ] File created
- [ ] Can track tokens
- [ ] Cost calculation correct
- [ ] Manual test passes

---

### 1.3 MCP Tool Manager ✅ COMPLETE (2 hours)
**File**: `tools/mcp_tools.py`

**Goal**: Connect to MCP servers and expose tools

**Status**: Phase 2 (75% complete)
- ✅ Configuration loading from mcp_config.json
- ✅ Subprocess management for MCP servers
- ✅ **JSON-RPC 2.0 communication** (NEW)
- ✅ **Server initialization handshake** (NEW)
- ✅ **Dynamic tool discovery via tools/list** (NEW)
- ✅ **Tool registry and routing** (NEW)
- ✅ **Actual MCP server communication** (NEW)
- ✅ Fallback implementations (filesystem direct, GitHub mock)
- ❌ Retry logic (TODO)
- ❌ Timeout handling (TODO)

**Implementation**:
```python
# tools/mcp_tools.py
import subprocess
import json
from typing import List, Dict, Any

class MCPToolManager:
    """Manage MCP server connections and tool calls"""

    def __init__(self, config_path: str = "mcp_config.json"):
        self.config_path = config_path
        self.servers = {}
        self._load_config()
        self._connect_servers()

    def _load_config(self):
        """Load MCP configuration"""
        with open(self.config_path) as f:
            self.config = json.load(f)

    def _connect_servers(self):
        """Connect to all configured MCP servers"""
        # Implementation to start MCP servers
        pass

    def list_tools(self) -> List[Dict]:
        """List all available tools from all servers"""
        # Implementation
        pass

    def call_tool(self, tool_name: str, arguments: Dict) -> Any:
        """Call a specific tool"""
        # Implementation
        pass

    # GitHub tools
    def github_get_file(self, owner: str, repo: str, path: str) -> str:
        """Get file contents from GitHub"""
        return self.call_tool("github_get_file", {
            "owner": owner,
            "repo": repo,
            "path": path
        })

    def github_create_pr(self, owner: str, repo: str, title: str, body: str, head: str, base: str):
        """Create a GitHub pull request"""
        return self.call_tool("github_create_pr", {
            "owner": owner,
            "repo": repo,
            "title": title,
            "body": body,
            "head": head,
            "base": base
        })

    # Filesystem tools
    def read_file(self, path: str) -> str:
        """Read file contents"""
        return self.call_tool("read_file", {"path": path})

    def write_file(self, path: str, content: str):
        """Write file contents"""
        return self.call_tool("write_file", {
            "path": path,
            "content": content
        })

# Test it
if __name__ == "__main__":
    manager = MCPToolManager()
    print("Available tools:", manager.list_tools())

    # Test file read
    content = manager.read_file("README.md")
    print(f"README.md preview: {content[:100]}...")
```

**Test**:
```bash
python tools/mcp_tools.py
# Should list available tools and read README.md
```

**Checklist**:
- [x] File created
- [x] MCP servers connect successfully
- [x] Can list available tools
- [x] Can read files via filesystem MCP (fallback mode)
- [x] Can call GitHub API via GitHub MCP (fallback mode)
- [x] JSON-RPC communication implemented
- [x] Tool discovery working
- [x] Error handling implemented
- [x] Manual test passes (6 tests passing)

---

### 1.4 Logger Utility (30 minutes)
**File**: `utils/logger.py`

**Goal**: Structured logging for debugging

**Implementation**:
```python
# utils/logger.py
import structlog
import logging
from rich.logging import RichHandler

def setup_logger(name: str, level: str = "INFO"):
    """Setup structured logger with rich output"""

    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[RichHandler(rich_tracebacks=True)]
    )

    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.ConsoleRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )

    return structlog.get_logger(name)

# Test it
if __name__ == "__main__":
    logger = setup_logger("test")
    logger.info("test_message", agent="planner", action="analyzing")
    logger.error("test_error", error="Something went wrong")
```

**Checklist**:
- [ ] File created
- [ ] Logger outputs nicely formatted logs
- [ ] Manual test passes

---

### 1.5 Test MCP Script (30 minutes)
**File**: `tools/test_mcp.py`

**Goal**: Verify MCP setup before building agents

**Implementation**:
```python
# tools/test_mcp.py
from mcp_tools import MCPToolManager
from utils.logger import setup_logger

logger = setup_logger("mcp_test")

def test_mcp_connection():
    """Test MCP server connections"""
    try:
        logger.info("Initializing MCP Tool Manager...")
        manager = MCPToolManager()

        logger.info("Testing filesystem MCP...")
        content = manager.read_file("README.md")
        assert len(content) > 0, "Failed to read README.md"
        logger.info("✓ Filesystem MCP working", chars_read=len(content))

        logger.info("Testing GitHub MCP...")
        # Test with a public repo
        tools = manager.list_tools()
        github_tools = [t for t in tools if 'github' in t['name'].lower()]
        assert len(github_tools) > 0, "No GitHub tools found"
        logger.info("✓ GitHub MCP working", tools_count=len(github_tools))

        logger.info("✅ All MCP tests passed!")
        return True

    except Exception as e:
        logger.error("❌ MCP test failed", error=str(e))
        return False

if __name__ == "__main__":
    success = test_mcp_connection()
    exit(0 if success else 1)
```

**Test**:
```bash
python tools/test_mcp.py
# Should show green checkmarks for all tests
```

**Checklist**:
- [ ] File created
- [ ] All tests pass
- [ ] Clear error messages if something fails

---

## Phase 2: Base Agent Infrastructure ✅ COMPLETE (Day 1 - 2 hours)

### 2.1 Base Agent Class (1.5 hours)
**File**: `agents/base.py`

**Goal**: Reusable base class for all agents

**Implementation**:
```python
# agents/base.py
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from llm.client import LLMClient
from tools.mcp_tools import MCPToolManager
from utils.logger import setup_logger

class BaseAgent(ABC):
    """Base class for all agents"""

    def __init__(self, name: str, system_prompt: str):
        self.name = name
        self.system_prompt = system_prompt
        self.llm = LLMClient()
        self.tools = MCPToolManager()
        self.logger = setup_logger(f"agent.{name}")
        self.conversation_history = []

    @abstractmethod
    def execute(self, input_data: Dict) -> Dict:
        """Execute agent logic - must be implemented by subclasses"""
        pass

    def think(self, prompt: str, context: Optional[Dict] = None) -> str:
        """Use LLM to think/reason"""
        self.logger.info("thinking", prompt_preview=prompt[:100])

        messages = self.conversation_history.copy()
        messages.append({"role": "user", "content": prompt})

        response = self.llm.generate(
            messages=messages,
            system=self.system_prompt
        )

        self.conversation_history.append({"role": "user", "content": prompt})
        self.conversation_history.append({"role": "assistant", "content": response})

        return response

    def use_tool(self, tool_name: str, arguments: Dict) -> Any:
        """Use a tool"""
        self.logger.info("using_tool", tool=tool_name, args=arguments)
        return self.tools.call_tool(tool_name, arguments)

    def reset(self):
        """Reset conversation history"""
        self.conversation_history = []

# Test Agent
class EchoAgent(BaseAgent):
    """Simple test agent that echoes input"""

    def __init__(self):
        super().__init__(
            name="echo",
            system_prompt="You are a helpful assistant that echoes back what the user says."
        )

    def execute(self, input_data: Dict) -> Dict:
        message = input_data.get("message", "")
        response = self.think(f"Echo this message: {message}")
        return {"response": response}

# Test it
if __name__ == "__main__":
    agent = EchoAgent()
    result = agent.execute({"message": "Hello, agent!"})
    print("Result:", result)
```

**Test**:
```bash
python agents/base.py
# Should echo back the message
```

**Checklist**:
- [ ] File created
- [ ] Base class with LLM integration
- [ ] Base class with MCP tools
- [ ] Conversation history tracking
- [ ] Test agent (EchoAgent) works
- [ ] Manual test passes

---

### 2.2 Simple Test Agent (30 minutes)
**File**: `agents/file_reader_agent.py`

**Goal**: Real working agent that uses MCP tools

**Implementation**:
```python
# agents/file_reader_agent.py
from agents.base import BaseAgent
from typing import Dict

class FileReaderAgent(BaseAgent):
    """Agent that reads and summarizes files"""

    def __init__(self):
        super().__init__(
            name="file_reader",
            system_prompt="""You are a file analysis agent.
            When given a file path, you read it and provide a concise summary.
            Focus on the key information and structure."""
        )

    def execute(self, input_data: Dict) -> Dict:
        """Read and summarize a file"""
        file_path = input_data.get("file_path")

        if not file_path:
            return {"error": "file_path required"}

        try:
            # Use MCP tool to read file
            self.logger.info("reading_file", path=file_path)
            content = self.tools.read_file(file_path)

            # Ask LLM to summarize
            prompt = f"""Analyze this file and provide a summary:

File: {file_path}
Content:
{content}

Provide:
1. File type/purpose
2. Key contents
3. Important observations"""

            summary = self.think(prompt)

            return {
                "file_path": file_path,
                "summary": summary,
                "char_count": len(content)
            }

        except Exception as e:
            self.logger.error("file_read_failed", error=str(e))
            return {"error": str(e)}

# Test it
if __name__ == "__main__":
    agent = FileReaderAgent()
    result = agent.execute({"file_path": "README.md"})

    print("\n" + "="*50)
    print("FILE ANALYSIS RESULT")
    print("="*50)
    print(f"File: {result['file_path']}")
    print(f"Size: {result['char_count']} characters")
    print(f"\nSummary:\n{result['summary']}")
```

**Test**:
```bash
python agents/file_reader_agent.py
# Should read and summarize README.md
```

**Checklist**:
- [ ] File created
- [ ] Agent uses MCP tools correctly
- [ ] Agent calls LLM for analysis
- [ ] Returns structured output
- [ ] Manual test passes

---

## Phase 3: Core Agents ✅ COMPLETE (Day 2 - 6 hours)

**Implemented Agents**:
- ✅ Migration Planner (7 tests passing)
- ✅ Runtime Validator (integration tested)
- ✅ Error Analyzer (19 tests passing)
- ✅ Staging Deployer (19 tests passing)

**Total Unit Tests**: 66 tests passing

### 3.1 Migration Planner Agent (2 hours)
**File**: `agents/migration_planner.py`

**Goal**: Analyze project and create upgrade strategy

**Key Capabilities**:
- Read `package.json` (Node.js) or `requirements.txt` (Python)
- Identify outdated dependencies
- Research breaking changes (via web search or documentation)
- Create phased migration plan

**Test**:
```bash
python agents/migration_planner.py --project ./test-projects/express-app
# Should output migration strategy
```

**Checklist**:
- [ ] File created
- [ ] Reads dependency files
- [ ] Identifies outdated packages
- [ ] Creates migration strategy
- [ ] Executable standalone
- [ ] Manual test with sample project

---

### 3.2 Runtime Validator Agent (2 hours)
**File**: `agents/runtime_validator.py`

**Goal**: Test upgrades in Docker

**Key Capabilities**:
- Create Docker container from project
- Apply dependency upgrades
- Run application
- Test health endpoints
- Return validation results

**Test**:
```bash
python agents/runtime_validator.py --project ./test-projects/express-app --strategy strategy.json
# Should validate in Docker and return results
```

**Checklist**:
- [ ] File created
- [ ] Creates Docker containers
- [ ] Applies upgrades
- [ ] Runs application
- [ ] Validates successfully
- [ ] Executable standalone
- [ ] Manual test passes

---

### 3.3 Docker Tools (1 hour)
**File**: `tools/docker_tools.py`

**Goal**: Wrapper for Docker SDK operations

**Implementation**:
```python
# tools/docker_tools.py
import docker
from typing import Dict, Optional

class DockerValidator:
    """Docker operations for validation"""

    def __init__(self):
        self.client = docker.from_env()

    def create_container(self, project_path: str, image: str = "node:18") -> str:
        """Create container from project"""
        # Implementation
        pass

    def install_dependencies(self, container_id: str, dependencies: Dict):
        """Install upgraded dependencies"""
        pass

    def start_application(self, container_id: str) -> bool:
        """Start the application"""
        pass

    def check_health(self, container_id: str, endpoint: str = "/health") -> bool:
        """Check application health"""
        pass

    def get_logs(self, container_id: str) -> str:
        """Get container logs"""
        pass

    def cleanup(self, container_id: str):
        """Remove container"""
        pass

# Test it
if __name__ == "__main__":
    validator = DockerValidator()
    print("Docker client connected:", validator.client.ping())
```

**Checklist**:
- [ ] File created
- [ ] Can create containers
- [ ] Can run commands
- [ ] Can get logs
- [ ] Manual test passes

---

### 3.4 Test Sample Projects (1 hour)
**Directory**: `tests/sample_projects/`

Create test projects:
- `express-app/` - Simple Express.js app with outdated dependencies
- `package.json` with Express 4.16.0
- Simple endpoints to test

**Checklist**:
- [ ] Sample Express app created
- [ ] Has outdated dependencies
- [ ] Can be tested manually
- [ ] Agents can analyze it

---

## Phase 4: LangGraph Workflow ✅ COMPLETE (Day 3 - 4 hours)

**Implemented Components**:
- ✅ State Schema (`graph/state.py`)
- ✅ Workflow Graph (`graph/workflow.py`)
- ✅ Conditional Routing Logic
- ✅ Retry Logic (configurable, default 3 attempts)
- ✅ Cost Tracking across all agents
- ✅ Error Recovery workflow

**Test Coverage**:
- ✅ Workflow routing tests (15 tests passing)
- ✅ Workflow integration tests (3 tests passing)

---

## Phase 5: API Layer ❌ NOT IMPLEMENTED (Day 4 - 4 hours)

### 5.1 FastAPI Main ❌ TODO (1 hour)
**File**: `api/main.py`

**Implementation**:
```python
# api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="AI Code Modernizer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
async def health():
    return {"status": "healthy"}

@app.get("/api/")
async def root():
    return {"message": "AI Code Modernizer API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Test**:
```bash
python api/main.py
# Visit http://localhost:8000/docs
```

**Checklist**:
- [ ] File created
- [ ] Server starts
- [ ] CORS configured
- [ ] Auto-docs working

---

### 5.2 API Routes ❌ TODO (2 hours)
**File**: `api/routes.py`

**Endpoints**:
- `POST /api/projects/analyze` - Analyze project
- `POST /api/projects/upgrade` - Start upgrade workflow
- `GET /api/projects/{id}/status` - Get workflow status

**Checklist**:
- [ ] File created
- [ ] All endpoints implemented
- [ ] Connected to workflow
- [ ] Error handling
- [ ] Tested with curl/Postman

---

### 6.3 WebSocket Handler (1 hour)
**File**: `api/websocket.py`

**Goal**: Real-time updates to frontend

**Checklist**:
- [ ] File created
- [ ] WebSocket endpoint working
- [ ] Sends agent updates
- [ ] Handles disconnections

---

## Phase 7: Testing & Polish (Day 5 - 4 hours)

### 7.1 Unit Tests
**Directory**: `tests/`

**Checklist**:
- [ ] Test MCP tools
- [ ] Test each agent independently
- [ ] Test workflow
- [ ] All tests pass

---

### 7.2 Integration Tests
**File**: `tests/integration/test_end_to_end.py`

**Checklist**:
- [ ] End-to-end workflow test
- [ ] Sample project test
- [ ] Error recovery test

---

### 7.3 Demo Preparation
- [ ] Demo script created
- [ ] Sample projects ready
- [ ] Docker images pre-built
- [ ] API keys verified
- [ ] Rehearsed 5+ times

---

## 🎯 Daily Checkpoints

### End of Day 1
- [ ] All prerequisites met
- [ ] MCP tools working
- [ ] Base agent can execute
- [ ] Test agent works

### End of Day 2
- [ ] Migration Planner works
- [ ] Runtime Validator works
- [ ] Both agents executable standalone

### End of Day 3
- [ ] Error Analyzer works
- [ ] LangGraph workflow complete
- [ ] End-to-end test passes

### End of Day 4
- [ ] API endpoints complete
- [ ] WebSocket working
- [ ] Frontend can connect

### End of Day 5
- [ ] All tests passing
- [ ] Demo ready
- [ ] Presentation practiced

---

## 🚀 Quick Commands

```bash
# Test individual components
python llm/client.py
python tools/mcp_tools.py
python agents/base.py
python agents/file_reader_agent.py

# Test core agents
python agents/migration_planner.py --project ./test-projects/express-app
python agents/runtime_validator.py --project ./test-projects/express-app

# Test workflow
python graph/workflow.py

# Run API
python api/main.py

# Run tests
pytest tests/ -v
```

---

**Status**: Ready for Day 1 implementation 🚀
**Focus**: Build executable, testable components first!
