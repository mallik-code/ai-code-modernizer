# Backend Requirements

## Project Overview
**AI-Powered Code Modernization Platform** - A multi-agent system that autonomously upgrades code dependencies through intelligent analysis, runtime validation in Docker containers, and staged deployment via GitHub.

## Implementation Status

### ✅ Implemented (Phase 1: Core Infrastructure)
- **Flexible LLM System** with support for multiple providers
- **Cost Tracking** across all LLM providers
- **Structured Logging** with rich console output
- **Base Agent Infrastructure** with provider-agnostic design
- **MCP Tool Manager** (placeholder, ready for full integration)

### 🚧 In Progress
- **MCP Server Integration** (configuration present, awaiting full connection)

### ❌ Not Yet Implemented
- **Core Agents** (Migration Planner, Runtime Validator, Error Analyzer, Staging Deployer)
- **LangGraph Workflow**
- **Docker Validation Tools**
- **FastAPI Backend**
- **WebSocket Communication**
- **State Persistence**

---

## Functional Requirements

### 1. Multi-LLM Provider Support ✅
**Status**: Implemented

**Description**: System must support multiple LLM providers interchangeably.

**Supported Providers**:
- Anthropic (Claude Sonnet 4, Opus 4, Haiku 4)
- OpenAI (GPT-4o, GPT-4 Turbo, GPT-3.5 Turbo)
- Google Gemini (Gemini 2.0 Flash/Pro, Gemini 3.0 Pro)
- HuggingFace (Llama 3.2, Llama 3.1, DialoGPT)
- Qwen (via DashScope - Turbo, Plus, Max, 72B, 14B)

**Implementation**:
- Factory pattern (`llm/factory.py`) for creating provider-specific clients
- Abstract base class (`llm/base.py`) defining interface
- Provider-specific implementations:
  - `llm/anthropic_client.py`
  - `llm/openai_client.py`
  - `llm/gemini_client.py`
  - `llm/huggingface_client.py`
  - `llm/qwen_client.py`

**Configuration**:
```bash
# Set in .env
LLM_PROVIDER=anthropic  # or openai, gemini, huggingface, qwen
```

**Acceptance Criteria**: ✅
- [x] Can switch providers via environment variable
- [x] All providers implement common interface
- [x] Token counting works for all providers
- [x] Cost tracking works across providers

---

### 2. Cost Tracking & Monitoring ✅
**Status**: Implemented

**Description**: Track token usage and costs across all LLM API calls.

**Features**:
- Real-time token tracking (input/output)
- Cost calculation per model
- Historical cost entries with timestamps
- Model-specific pricing database
- Cost breakdown by model
- Total cost reporting

**Pricing Database** (updated 2025):
- Anthropic: Sonnet 4 ($3/$15), Opus 4 ($15/$75), Haiku 4 ($0.25/$1.25)
- OpenAI: GPT-4o ($5/$15), GPT-4 Turbo ($10/$30), GPT-3.5 Turbo ($0.50/$1.50)
- Gemini: 2.0 Flash ($0.35/$1.05), 2.0 Pro ($3.50/$10.50), 3.0 Pro ($4/$12)
- Qwen: Turbo ($0.10/$0.20), Plus ($0.40/$1.20), Max ($1/$3)

**Implementation**: `utils/cost_tracker.py`

**Acceptance Criteria**: ✅
- [x] Tracks all LLM API calls
- [x] Calculates costs accurately
- [x] Provides detailed reports
- [x] Supports all providers
- [x] Stores cost history

---

### 3. Structured Logging ✅
**Status**: Implemented

**Description**: Comprehensive structured logging for debugging and monitoring.

**Features**:
- ISO timestamp on all logs
- Log levels (INFO, DEBUG, ERROR, WARNING)
- Structured context fields
- Rich console output with colors
- Stack trace rendering for errors

**Implementation**: `utils/logger.py`

**Libraries Used**:
- `structlog` - Structured logging
- `rich` - Rich console output

**Acceptance Criteria**: ✅
- [x] Logs are structured and parseable
- [x] Console output is readable
- [x] Context is preserved across calls
- [x] Errors include stack traces

---

### 4. Base Agent Infrastructure ✅
**Status**: Implemented

**Description**: Reusable base class for all agents with LLM and tool integration.

**Features**:
- Abstract base class for agent implementation
- LLM integration (provider-agnostic)
- MCP tool manager integration
- Conversation history tracking
- Structured logging per agent
- `think()` method for LLM reasoning
- `use_tool()` method for tool execution
- `reset()` method to clear history

**Implementation**: `agents/base.py`

**Agent Interface**:
```python
class BaseAgent(ABC):
    def __init__(self, name: str, system_prompt: str,
                 llm_provider: Optional[str] = None,
                 llm_model: Optional[str] = None)

    @abstractmethod
    def execute(self, input_data: Dict) -> Dict

    def think(self, prompt: str, context: Optional[Dict] = None) -> str
    def use_tool(self, tool_name: str, arguments: Dict) -> Any
    def reset(self)
```

**Acceptance Criteria**: ✅
- [x] All agents inherit from BaseAgent
- [x] LLM provider can be configured per agent
- [x] Conversation history maintained
- [x] Tools accessible via MCP
- [x] Logging works for all agents

---

### 5. MCP Tool Manager 🚧
**Status**: Partially Implemented

**Description**: Manage connections to MCP (Model Context Protocol) servers and expose tools to agents.

**Target MCP Servers**:
- **GitHub MCP** (@modelcontextprotocol/server-github)
  - Read files from repositories
  - Create branches
  - Create pull requests
  - List repositories
- **Filesystem MCP** (@modelcontextprotocol/server-filesystem)
  - Read local files
  - Write local files
  - List directories

**Current Implementation**: `tools/mcp_tools.py`
- Configuration loading (`mcp_config.json`)
- Placeholder for server connections
- Mock implementations for testing
- Direct filesystem operations (not via MCP yet)

**Required**:
- [ ] Actual MCP server process management
- [ ] STDIO communication with MCP servers
- [ ] Tool listing from MCP servers
- [ ] Tool invocation via JSON-RPC
- [ ] Error handling for MCP failures

**Acceptance Criteria**:
- [ ] Can connect to GitHub MCP server
- [ ] Can connect to Filesystem MCP server
- [ ] Can list available tools
- [ ] Can invoke tools successfully
- [ ] Handles disconnections gracefully

---

### 6. Migration Planner Agent ❌
**Status**: Not Implemented

**Description**: Analyze codebases and create intelligent upgrade strategies.

**Capabilities**:
- Read dependency files (package.json, requirements.txt, etc.)
- Identify outdated dependencies
- Research breaking changes via web search
- Analyze impact of upgrades
- Create phased migration plans with fallbacks
- Generate upgrade strategies

**Inputs**:
- Project path
- Dependency manifest file
- Target versions (optional)

**Outputs**:
```json
{
  "dependencies": {
    "express": {
      "current": "4.16.0",
      "target": "5.0.0",
      "breaking_changes": ["..."],
      "risk_level": "medium"
    }
  },
  "strategy": {
    "phases": [
      {
        "name": "Update Express",
        "steps": ["..."],
        "dependencies": ["passport@0.7.0"]
      }
    ]
  }
}
```

**Required**:
- [ ] File reading via MCP
- [ ] Dependency version checking
- [ ] Breaking change research
- [ ] Strategy generation logic
- [ ] Risk assessment

**Acceptance Criteria**:
- [ ] Analyzes Node.js projects (package.json)
- [ ] Analyzes Python projects (requirements.txt)
- [ ] Identifies all outdated packages
- [ ] Creates sensible migration order
- [ ] Explains breaking changes
- [ ] Provides risk assessment

---

### 7. Runtime Validator Agent ❌
**Status**: Not Implemented

**Description**: Validate upgrades in isolated Docker environments.

**Capabilities**:
- Create Docker containers from project code
- Install upgraded dependencies
- Run application startup
- Execute health checks
- Run smoke tests
- Collect application logs
- Return validation results

**Docker Validation Levels**:
1. **Basic Startup**: Application starts without crashes
2. **Health Endpoints**: Health check endpoints respond
3. **Critical Flows**: Key API endpoints work
4. **Performance**: No performance regression

**Inputs**:
- Project path
- Migration strategy
- Validation level (1-4)

**Outputs**:
```json
{
  "status": "success|failure",
  "level_completed": 3,
  "startup_time": 2.5,
  "health_checks": {"passed": 10, "failed": 0},
  "logs": "...",
  "errors": []
}
```

**Required Tools**:
- [ ] Docker SDK integration (`tools/docker_tools.py`)
- [ ] Container creation logic
- [ ] Dependency installation automation
- [ ] Application startup monitoring
- [ ] Health check execution
- [ ] Log collection

**Acceptance Criteria**:
- [ ] Creates Docker containers successfully
- [ ] Installs dependencies correctly
- [ ] Starts applications
- [ ] Runs health checks
- [ ] Detects failures accurately
- [ ] Returns detailed validation results

---

### 8. Error Analyzer Agent ❌
**Status**: Not Implemented

**Description**: Diagnose validation failures and generate fixes.

**Capabilities**:
- Parse Docker validation logs
- Extract error patterns
- Identify root causes
- Research similar issues
- Generate code fixes
- Create alternative strategies
- Confidence scoring for fixes

**Error Analysis Process**:
1. Parse logs for stack traces
2. Identify error types (syntax, import, runtime, etc.)
3. Web search for solutions
4. Generate fix strategies
5. Rank by confidence
6. Return to workflow

**Inputs**:
- Validation logs
- Error messages
- Current migration strategy

**Outputs**:
```json
{
  "root_cause": "Passport middleware signature changed",
  "error_type": "runtime",
  "confidence": 0.85,
  "fixes": [
    {
      "description": "Update Passport to 0.7 first",
      "code_changes": [...],
      "success_probability": 0.9
    }
  ],
  "alternative_strategy": {...}
}
```

**Required**:
- [ ] Log parsing logic
- [ ] Error pattern matching
- [ ] Web search integration
- [ ] Fix generation via LLM
- [ ] Confidence scoring

**Acceptance Criteria**:
- [ ] Parses complex error logs
- [ ] Identifies root causes accurately
- [ ] Generates working fixes >80% of time
- [ ] Provides alternatives
- [ ] Knows when to escalate to humans

---

### 9. Staging Deployer Agent ❌
**Status**: Not Implemented

**Description**: Deploy validated changes to GitHub staging.

**Capabilities**:
- Create Git branches via MCP
- Commit code changes
- Push to remote
- Create pull requests
- Add detailed PR descriptions
- Trigger CI/CD pipelines
- Monitor deployment status
- Notify QA team

**Deployment Process**:
1. Create branch (e.g., `upgrade-express-5.0`)
2. Apply all migration changes
3. Commit with detailed message
4. Push to remote
5. Create PR with:
   - Migration summary
   - Breaking changes
   - Validation results
   - Testing checklist
6. Trigger CI/CD
7. Monitor deployment

**Inputs**:
- Project path
- Migration changes
- Validation results

**Outputs**:
```json
{
  "branch": "upgrade-express-5.0",
  "pr_url": "https://github.com/owner/repo/pull/123",
  "ci_status": "running",
  "deployment_url": "https://staging.app.com"
}
```

**Required**:
- [ ] GitHub MCP integration
- [ ] Git operations (branch, commit, push)
- [ ] PR creation with templates
- [ ] CI/CD triggering (GitHub Actions)

**Acceptance Criteria**:
- [ ] Creates branches successfully
- [ ] Commits changes with good messages
- [ ] Creates PRs with complete descriptions
- [ ] Links to validation results
- [ ] Triggers CI/CD pipelines

---

### 10. LangGraph Workflow ❌
**Status**: Not Implemented

**Description**: Orchestrate agents in a stateful workflow with conditional routing and retry logic.

**Workflow Graph**:
```
Start → Migration Planner → Runtime Validator
                                  ↓
                            [Success?]
                           ↙         ↘
                    Staging Deployer   Error Analyzer
                           ↓                 ↓
                          End          [Retry < 3?]
                                       ↙         ↘
                              Runtime Validator  Human Escalation
```

**State Schema** (`graph/state.py`):
```python
class MigrationState(TypedDict):
    project_path: str
    dependencies: Dict
    migration_strategy: Optional[Dict]
    validation_result: Optional[Dict]
    errors: List[str]
    retry_count: int
    status: str  # analyzing, validating, error, complete
    current_agent: str
```

**Features**:
- Conditional routing based on validation results
- Retry logic (max 3 attempts)
- Human-in-the-loop interrupts
- State persistence (checkpointing)
- Workflow visualization

**Required**:
- [ ] State schema definition
- [ ] Workflow graph construction
- [ ] Agent node implementations
- [ ] Conditional edge logic
- [ ] Retry mechanism
- [ ] Checkpointing
- [ ] Human interrupt points

**Acceptance Criteria**:
- [ ] Agents execute in correct order
- [ ] Failures route to error analyzer
- [ ] Retry logic works (max 3)
- [ ] State persists across restarts
- [ ] Humans can intervene at decision points
- [ ] Workflow can be visualized

---

### 11. FastAPI Backend ❌
**Status**: Not Implemented

**Description**: RESTful API for frontend communication.

**Endpoints Required**:

```
GET  /api/health
GET  /api/
POST /api/projects/analyze
POST /api/projects/upgrade
GET  /api/projects/{id}/status
GET  /api/projects/{id}/logs
POST /api/projects/{id}/approve
POST /api/projects/{id}/cancel
GET  /api/cost/report
```

**API Features**:
- CORS for frontend (localhost:5173)
- Request validation (Pydantic models)
- Error handling
- Rate limiting
- Authentication (future)
- Auto-generated docs (Swagger/OpenAPI)

**Required Files**:
- [ ] `api/main.py` - FastAPI app
- [ ] `api/routes.py` - Route handlers
- [ ] `api/models.py` - Request/response models
- [ ] `api/middleware.py` - CORS, auth, etc.

**Acceptance Criteria**:
- [ ] All endpoints implemented
- [ ] Validation works
- [ ] Error messages are clear
- [ ] CORS configured correctly
- [ ] Auto-docs accessible at /docs

---

### 12. WebSocket Communication ❌
**Status**: Not Implemented

**Description**: Real-time updates to frontend during workflow execution.

**WebSocket Events**:
- `agent_started` - Agent begins execution
- `agent_thinking` - LLM reasoning in progress
- `agent_tool_call` - Agent using a tool
- `agent_completed` - Agent finished successfully
- `agent_failed` - Agent encountered error
- `workflow_status` - Overall workflow state change
- `cost_update` - Cost tracker update

**Event Format**:
```json
{
  "type": "agent_thinking",
  "agent": "migration_planner",
  "message": "Analyzing dependencies...",
  "timestamp": "2025-01-15T10:30:00Z",
  "metadata": {...}
}
```

**Required**:
- [ ] WebSocket endpoint (`/ws`)
- [ ] Event broadcasting
- [ ] Connection management
- [ ] Reconnection handling
- [ ] Event filtering per client

**Acceptance Criteria**:
- [ ] Frontend can connect via WebSocket
- [ ] Real-time updates work
- [ ] Reconnection works after disconnect
- [ ] Multiple clients supported
- [ ] Events are timestamped

---

### 13. State Persistence ❌
**Status**: Not Implemented

**Description**: Persist workflow state to survive crashes and enable resumption.

**Storage**:
- SQLite database (`modernizer.db`)
- LangGraph checkpointing
- Workflow snapshots

**Data to Persist**:
- Workflow execution state
- Agent outputs
- Conversation history
- Cost tracking data
- Validation results
- Error logs

**Required**:
- [ ] SQLAlchemy models
- [ ] Database schema
- [ ] Checkpoint saving
- [ ] Checkpoint restoration
- [ ] Migration scripts

**Acceptance Criteria**:
- [ ] Workflows can resume after crash
- [ ] State is consistent
- [ ] Historical runs queryable
- [ ] Audit trail maintained

---

## Non-Functional Requirements

### Performance
- **Analysis Time**: < 2 minutes per project
- **Validation Time**: < 5 minutes per upgrade
- **End-to-End Time**: < 10 minutes total
- **API Response Time**: < 200ms (non-workflow endpoints)
- **WebSocket Latency**: < 100ms

### Reliability
- **Uptime**: 99.9% for API
- **Agent Success Rate**: > 90% for common frameworks
- **Data Persistence**: No data loss on crashes
- **Retry Mechanism**: Automatic retry on transient failures

### Scalability
- **Concurrent Projects**: Support 10+ simultaneous migrations
- **Project Size**: Handle projects up to 10,000 files
- **Dependencies**: Analyze up to 500 dependencies
- **Historical Data**: Store 1000+ workflow runs

### Security
- **API Keys**: Secure storage (never in code)
- **Docker Isolation**: All validation in sandboxed containers
- **GitHub Tokens**: Minimal required scopes
- **Input Validation**: All user inputs validated
- **Rate Limiting**: Prevent abuse

### Cost Efficiency
- **LLM Costs**: < $0.50 per upgrade
- **Infrastructure**: Run on single server initially
- **Docker Resources**: Clean up containers after use
- **API Caching**: Cache dependency metadata

### Usability
- **Documentation**: Comprehensive API docs
- **Error Messages**: Clear, actionable errors
- **Logging**: Detailed logs for debugging
- **Observability**: Cost tracking, performance metrics

---

## Technical Constraints

### Languages & Frameworks
- **Backend**: Python 3.11+
- **Frontend**: React 18+ with TypeScript
- **Orchestration**: LangGraph 0.2.16+
- **API**: FastAPI 0.104+
- **Database**: SQLite (development), PostgreSQL (production)

### External Dependencies
- **LLM Providers**: Anthropic, OpenAI, Google, HuggingFace, Qwen
- **MCP Servers**: GitHub, Filesystem
- **Docker**: Required for validation
- **Git**: Required for deployment

### Environment Requirements
- **OS**: Linux, macOS, Windows (WSL)
- **Python**: 3.11 or higher
- **Node.js**: 18+ (for MCP servers)
- **Docker**: Latest stable version
- **Memory**: 4GB minimum, 8GB recommended
- **Disk**: 10GB free space

### Configuration
- **Environment Variables**: Via `.env` file
- **MCP Config**: `mcp_config.json`
- **Database**: `DATABASE_URL` environment variable
- **Feature Flags**: Environment-based toggles

---

## Development Priorities

### Phase 1: Core Infrastructure ✅ (COMPLETED)
- [x] Multi-LLM provider support
- [x] Cost tracking
- [x] Logging infrastructure
- [x] Base agent class
- [x] MCP tool manager (placeholder)

### Phase 2: Core Agents (NEXT)
- [ ] Migration Planner Agent
- [ ] Runtime Validator Agent
- [ ] Docker validation tools
- [ ] Test with sample projects

### Phase 3: Advanced Agents
- [ ] Error Analyzer Agent
- [ ] Staging Deployer Agent
- [ ] Full MCP integration
- [ ] GitHub PR creation

### Phase 4: Orchestration
- [ ] LangGraph workflow
- [ ] State persistence
- [ ] Retry logic
- [ ] Human-in-the-loop

### Phase 5: API & Integration
- [ ] FastAPI backend
- [ ] WebSocket communication
- [ ] Frontend integration
- [ ] End-to-end testing

### Phase 6: Production Readiness
- [ ] Error handling
- [ ] Monitoring
- [ ] Performance optimization
- [ ] Security hardening
- [ ] Documentation

---

## Success Metrics

### Technical Metrics
- **Success Rate**: > 90% for common frameworks
- **False Positive Rate**: < 5%
- **Validation Accuracy**: > 95%
- **Agent Completion Rate**: > 95%

### Business Metrics
- **Time Savings**: 4-6 hours → 8-10 minutes (94% reduction)
- **Cost per Upgrade**: < $0.50
- **ROI**: 3,000x+

### User Experience
- **Trust in Recommendations**: > 8.5/10
- **Ease of Use**: > 9/10
- **Repeat Usage**: > 85%

---

## Testing Requirements

### Unit Tests
- [ ] Test each LLM provider
- [ ] Test cost tracking
- [ ] Test each agent independently
- [ ] Test MCP tool manager
- [ ] Test workflow logic

### Integration Tests
- [ ] Test end-to-end workflows
- [ ] Test with real projects
- [ ] Test error recovery
- [ ] Test human escalation

### Test Coverage
- **Target**: > 80% code coverage
- **Critical Paths**: 100% coverage

---

## Documentation Requirements

- [x] Backend requirements (this document)
- [ ] Architecture documentation
- [ ] Design documentation
- [ ] API documentation (auto-generated)
- [ ] Agent development guide
- [ ] Deployment guide
- [ ] User guide

---

**Document Version**: 1.0
**Last Updated**: 2025-01-15
**Status**: Phase 1 Complete, Phase 2 In Planning
