# Migration Invocation Guide

Complete guide on how to trigger dependency upgrades in the AI Code Modernizer system.

---

## Table of Contents

1. [Overview](#overview)
2. [Method 1: Direct Workflow Execution](#method-1-direct-workflow-execution)
3. [Method 2: Command Line with Arguments](#method-2-command-line-with-arguments)
4. [Method 3: Individual Agent Execution](#method-3-individual-agent-execution)
5. [Method 4: REST API Endpoint](#method-4-rest-api-endpoint)
6. [Method 5: Python Import](#method-5-python-import)
7. [Workflow Architecture](#workflow-architecture)
8. [API Reference](#api-reference)

---

## Overview

The AI Code Modernizer provides multiple ways to trigger dependency upgrades:

| Method | Use Case | Complexity | Control Level |
|--------|----------|------------|---------------|
| **REST API** | Production, Frontend integration | Low | High-level |
| **CLI Workflow** | Manual testing, CI/CD | Low | High-level |
| **Python Import** | Custom integrations, Scripting | Medium | Full control |
| **Individual Agents** | Debugging, Testing specific agents | High | Agent-level |

---

## Method 1: Direct Workflow Execution

### Description
Execute the complete LangGraph workflow with all 4 agents in sequence.

### When to Use
- ✅ Production migrations
- ✅ Automated CI/CD pipelines
- ✅ End-to-end testing
- ✅ Default recommendation for most users

### Command
```bash
cd backend
python -m graph.workflow <project_path> <project_type>
```

### Examples

#### Example 1: Upgrade Node.js Project
```bash
python -m graph.workflow "tmp/projects/simple_express_app" nodejs
```

#### Example 2: Upgrade Python Project
```bash
python -m graph.workflow "/path/to/python/project" python
```

#### Example 3: With Custom Retry Count
```python
# Edit graph/workflow.py __main__ section to change max_retries
run_workflow(
    project_path="path/to/project",
    project_type="nodejs",
    max_retries=5  # Default is 3
)
```

### Output
```
================================================================================
LANGGRAPH WORKFLOW TEST
================================================================================

[INFO] Testing workflow with project: tmp/projects/simple_express_app
[INFO] This will execute all 4 agents in sequence...

[INFO] executing_migration_planner project_path=tmp/projects/simple_express_app
[INFO] migration_plan_created dependencies_count=5
[INFO] executing_runtime_validator project_path=tmp/projects/simple_express_app
[INFO] validation_successful_with_tests test_summary="32 passed, 32 total"
[INFO] executing_staging_deployer project_path=tmp/projects/simple_express_app
[INFO] deployment_successful branch=upgrade/dependencies-20251112 pr_url=https://github.com/...

================================================================================
WORKFLOW RESULTS
================================================================================
  Final Status: deployed
  Retry Count: 0/3
  Validation Success: True
  PR URL: https://github.com/user/repo/pull/123
  Branch: upgrade/dependencies-20251112
  Total Cost: $0.1234
  Errors: 0

[OK] Workflow execution complete!
```

### Workflow Flow
```
START
  ↓
Migration Planner Agent
  ↓ (creates migration plan)
Runtime Validator Agent
  ↓ (validates in Docker + runs tests)
  ├─ SUCCESS → Staging Deployer Agent → END
  └─ FAILED → Error Analyzer Agent → retry validation (max 3 times)
```

---

## Method 2: Command Line with Arguments

### Description
Execute workflow with command-line arguments for automation.

### When to Use
- ✅ CI/CD pipelines
- ✅ Bash scripts
- ✅ Automated testing

### Command
```bash
# Basic usage
python -m graph.workflow <project_path> <project_type>

# With environment variables
ANTHROPIC_API_KEY=<key> GITHUB_TOKEN=<token> \
  python -m graph.workflow "/path/to/project" nodejs
```

### CI/CD Integration

#### GitHub Actions
```yaml
name: Dependency Upgrade

on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday
  workflow_dispatch:  # Manual trigger

jobs:
  upgrade:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt

      - name: Run AI Code Modernizer
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          cd backend
          python -m graph.workflow "$GITHUB_WORKSPACE/my-project" nodejs
```

#### GitLab CI
```yaml
upgrade_dependencies:
  script:
    - cd backend
    - pip install -r requirements.txt
    - python -m graph.workflow "/path/to/project" nodejs
  only:
    - schedules
```

---

## Method 3: Individual Agent Execution

### Description
Execute individual agents for testing or debugging.

### When to Use
- ✅ Debugging specific agent logic
- ✅ Testing agent implementations
- ✅ Understanding agent behavior
- ❌ NOT for production migrations

### Migration Planner Only
```bash
python agents/migration_planner.py --project ./tmp/projects/simple_express_app
```

**Output:**
```json
{
  "dependencies": {
    "express": {
      "current_version": "4.16.0",
      "target_version": "4.19.2",
      "action": "upgrade",
      "breaking_changes": [...],
      "risk_level": "low"
    },
    ...
  },
  "overall_risk": "low",
  "estimated_effort": "2-4 hours"
}
```

### Runtime Validator Only
```bash
python agents/runtime_validator.py
```

**Note**: Requires existing migration plan as input

### Error Analyzer Only
```bash
python agents/error_analyzer.py --logs validation_logs.txt
```

### Staging Deployer Only
```bash
python agents/staging_deployer.py
```

**Note**: Requires validated migration plan

---

## Method 4: REST API Endpoint

### Description
HTTP REST API for triggering migrations from web applications.

### When to Use
- ✅ **RECOMMENDED** for production
- ✅ Frontend/dashboard integration
- ✅ Microservices architecture
- ✅ Remote triggering

### Start the API Server

```bash
cd backend
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### API Endpoints

#### **POST /api/migrations/start** - Start Migration
Triggers the complete migration workflow.

**Request:**
```http
POST /api/migrations/start
Content-Type: application/json

{
  "project_path": "/path/to/project",
  "project_type": "nodejs",
  "max_retries": 3,
  "options": {
    "create_pr": true,
    "run_tests": true
  }
}
```

**Response (202 Accepted):**
```json
{
  "migration_id": "mig_abc123",
  "status": "started",
  "project_path": "/path/to/project",
  "project_type": "nodejs",
  "started_at": "2025-11-12T10:30:00Z",
  "message": "Migration workflow started successfully"
}
```

#### **GET /api/migrations/{migration_id}** - Get Status
Check migration progress and results.

**Request:**
```http
GET /api/migrations/mig_abc123
```

**Response (200 OK):**
```json
{
  "migration_id": "mig_abc123",
  "status": "deployed",
  "project_path": "/path/to/project",
  "project_type": "nodejs",
  "started_at": "2025-11-12T10:30:00Z",
  "completed_at": "2025-11-12T10:35:00Z",
  "duration_seconds": 300,
  "result": {
    "validation_success": true,
    "tests_run": true,
    "tests_passed": true,
    "test_summary": "32 passed, 32 total",
    "pr_url": "https://github.com/user/repo/pull/123",
    "branch_name": "upgrade/dependencies-20251112",
    "dependencies_upgraded": 5,
    "total_cost_usd": 0.1234
  },
  "errors": []
}
```

#### **GET /api/migrations** - List Migrations
Get all migration runs.

**Request:**
```http
GET /api/migrations?limit=10&offset=0
```

**Response:**
```json
{
  "total": 25,
  "limit": 10,
  "offset": 0,
  "migrations": [
    {
      "migration_id": "mig_abc123",
      "status": "deployed",
      "project_path": "/path/to/project",
      "started_at": "2025-11-12T10:30:00Z",
      "completed_at": "2025-11-12T10:35:00Z"
    },
    ...
  ]
}
```

### cURL Examples

**Start Migration:**
```bash
curl -X POST http://localhost:8000/api/migrations/start \
  -H "Content-Type: application/json" \
  -d '{
    "project_path": "/path/to/project",
    "project_type": "nodejs"
  }'
```

**Check Status:**
```bash
curl http://localhost:8000/api/migrations/mig_abc123
```

### Python Requests Example
```python
import requests

# Start migration
response = requests.post('http://localhost:8000/api/migrations/start', json={
    "project_path": "/path/to/project",
    "project_type": "nodejs",
    "max_retries": 3
})

migration_id = response.json()["migration_id"]
print(f"Started migration: {migration_id}")

# Poll for status
import time
while True:
    status_response = requests.get(f'http://localhost:8000/api/migrations/{migration_id}')
    status_data = status_response.json()

    print(f"Status: {status_data['status']}")

    if status_data['status'] in ['deployed', 'error']:
        break

    time.sleep(10)  # Poll every 10 seconds

print(f"Final result: {status_data['result']}")
```

### JavaScript/TypeScript Example
```typescript
// Start migration
const response = await fetch('http://localhost:8000/api/migrations/start', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    project_path: '/path/to/project',
    project_type: 'nodejs'
  })
});

const { migration_id } = await response.json();

// Poll for status
const checkStatus = async () => {
  const statusRes = await fetch(`http://localhost:8000/api/migrations/${migration_id}`);
  const status = await statusRes.json();

  if (status.status === 'deployed') {
    console.log('Migration completed!', status.result);
  } else if (status.status === 'error') {
    console.error('Migration failed:', status.errors);
  } else {
    setTimeout(checkStatus, 10000); // Poll every 10 seconds
  }
};

checkStatus();
```

---

## Method 5: Python Import

### Description
Import and use the workflow programmatically in Python code.

### When to Use
- ✅ Custom automation scripts
- ✅ Integration with other Python tools
- ✅ Advanced control and customization

### Example: Basic Usage
```python
from graph.workflow import run_workflow
from pathlib import Path

# Run workflow
final_state = run_workflow(
    project_path="/path/to/project",
    project_type="nodejs",
    max_retries=3
)

# Check results
if final_state["status"] == "deployed":
    print(f"✅ Success! PR: {final_state['pr_url']}")
    print(f"✅ Tests passed: {final_state['validation_result']['validation_result']['logs']['tests']['test_summary']}")
else:
    print(f"❌ Failed: {final_state['errors']}")
```

### Example: Custom Post-Processing
```python
from graph.workflow import run_workflow
import json

def upgrade_and_notify(project_path: str):
    """Upgrade project and send Slack notification"""

    # Run migration
    result = run_workflow(project_path, "nodejs")

    # Extract key info
    status = result["status"]
    pr_url = result.get("pr_url")
    tests_passed = result.get("validation_result", {}).get("validation_result", {}).get("tests_passed")
    cost = result["total_cost"]

    # Send notification
    slack_message = {
        "text": f"Migration {'succeeded' if status == 'deployed' else 'failed'}",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Project*: {project_path}\n" +
                            f"*Status*: {status}\n" +
                            f"*Tests*: {'✅ Passed' if tests_passed else '❌ Failed'}\n" +
                            f"*PR*: <{pr_url}|View PR>\n" +
                            f"*Cost*: ${cost:.4f}"
                }
            }
        ]
    }

    # Send to Slack (implement your webhook)
    send_to_slack(slack_message)

    return result

# Usage
upgrade_and_notify("/path/to/my/project")
```

### Example: Batch Processing
```python
from graph.workflow import run_workflow
from concurrent.futures import ThreadPoolExecutor
import logging

def upgrade_multiple_projects(projects: list[dict]):
    """Upgrade multiple projects in parallel"""

    def upgrade_single(project):
        try:
            result = run_workflow(
                project_path=project["path"],
                project_type=project["type"],
                max_retries=2
            )
            return {
                "project": project["name"],
                "success": result["status"] == "deployed",
                "pr_url": result.get("pr_url"),
                "errors": result.get("errors", [])
            }
        except Exception as e:
            return {
                "project": project["name"],
                "success": False,
                "errors": [str(e)]
            }

    # Run in parallel (max 3 concurrent)
    with ThreadPoolExecutor(max_workers=3) as executor:
        results = list(executor.map(upgrade_single, projects))

    # Summary
    successful = sum(1 for r in results if r["success"])
    print(f"✅ {successful}/{len(projects)} projects upgraded successfully")

    return results

# Usage
projects = [
    {"name": "frontend", "path": "/apps/frontend", "type": "nodejs"},
    {"name": "backend", "path": "/apps/backend", "type": "python"},
    {"name": "api", "path": "/apps/api", "type": "nodejs"}
]

results = upgrade_multiple_projects(projects)
```

---

## Workflow Architecture

### Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                          START MIGRATION                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
         ┌────────────────────────────────────────┐
         │   MIGRATION PLANNER AGENT              │
         │                                        │
         │  • Reads package.json/requirements.txt │
         │  • Identifies outdated dependencies    │
         │  • Researches breaking changes         │
         │  • Creates migration plan              │
         │  • Risk assessment                     │
         └────────────────────────────────────────┘
                              │
                              ▼
                   plan_created?
                    /         \
                 YES           NO → END (error)
                  │
                  ▼
         ┌────────────────────────────────────────┐
         │   RUNTIME VALIDATOR AGENT              │
         │                                        │
         │  • Creates Docker container            │
         │  • Copies project files                │
         │  • Applies upgrades to package.json    │
         │  • Installs dependencies               │
         │  • Starts application                  │
         │  • Runs health checks                  │
         │  • 🆕 Runs test suite (npm test)       │
         │  • Validates functionality             │
         └────────────────────────────────────────┘
                              │
                              ▼
                     validation_success?
                        /      |      \
                      YES      NO      NO
                       │       │       │
                       │       │    retries < max?
                       │       │       │
                       │       │      YES
                       │       │       │
                       │       │       ▼
                       │       │  ┌──────────────────────────────┐
                       │       │  │  ERROR ANALYZER AGENT        │
                       │       │  │                              │
                       │       │  │  • Parses error logs         │
                       │       │  │  • Identifies root cause     │
                       │       │  │  • Suggests fixes            │
                       │       │  │  • Updates migration plan    │
                       │       │  └──────────────────────────────┘
                       │       │             │
                       │       │             │
                       │       │             ▼
                       │       │      fixes_available?
                       │       │        /          \
                       │       │      YES           NO
                       │       │       │             │
                       │       └───────┴─────────────┘
                       │               │             │
                       │               ▼             ▼
                       │          retry_count++    END (max retries)
                       │               │
                       │               └──────► RUNTIME VALIDATOR (retry)
                       │
                       ▼
         ┌────────────────────────────────────────┐
         │   STAGING DEPLOYER AGENT               │
         │                                        │
         │  • Creates Git branch                  │
         │  • Commits changes                     │
         │  • Pushes to remote                    │
         │  • Creates Pull Request                │
         │  • Adds PR description with summary    │
         └────────────────────────────────────────┘
                              │
                              ▼
                       ┌──────────────┐
                       │     END      │
                       │  (deployed)  │
                       └──────────────┘
```

### Agent Responsibilities

| Agent | Input | Output | LLM Used | Docker Used |
|-------|-------|--------|----------|-------------|
| **Migration Planner** | project_path | migration_plan | ✅ Yes | ❌ No |
| **Runtime Validator** | project_path, migration_plan | validation_result | ✅ Yes | ✅ Yes |
| **Error Analyzer** | validation_result, migration_plan | error_analysis, fix_suggestions | ✅ Yes | ❌ No |
| **Staging Deployer** | migration_plan, validation_result | pr_url, branch_name | ❌ No | ❌ No |

---

## API Reference

### REST API Endpoints

#### Authentication
Currently no authentication. Add API key authentication in production:

```python
# Add to api/main.py
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

API_KEY = "your-secret-key"
api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key
```

#### Rate Limiting
Add rate limiting for production:

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/migrations/start")
@limiter.limit("10/hour")  # Max 10 migrations per hour per IP
async def start_migration(...):
    ...
```

### WebSocket Support (Future)
For real-time progress updates:

```python
# Future enhancement
@app.websocket("/ws/migrations/{migration_id}")
async def migration_progress(websocket: WebSocket, migration_id: str):
    await websocket.accept()

    # Stream progress updates
    async for event in migration_events(migration_id):
        await websocket.send_json({
            "type": event.type,
            "agent": event.agent,
            "status": event.status,
            "progress": event.progress
        })
```

---

## Troubleshooting

### Common Issues

#### Issue 1: Docker Not Running
```
ERROR: Docker not available: Cannot connect to the Docker daemon
```

**Solution:**
```bash
# Start Docker Desktop (Windows/Mac)
# OR
sudo systemctl start docker  # Linux
```

#### Issue 2: API Keys Missing
```
ERROR: No API keys found. Set ANTHROPIC_API_KEY or GOOGLE_API_KEY
```

**Solution:**
```bash
export ANTHROPIC_API_KEY="sk-ant-xxxxx"
# OR
export GOOGLE_API_KEY="AIza xxxxx"
```

#### Issue 3: GitHub Token Missing
```
ERROR: GITHUB_TOKEN not found
```

**Solution:**
```bash
export GITHUB_TOKEN="ghp_xxxxx"
```

#### Issue 4: Project Path Not Found
```
ERROR: Project path does not exist
```

**Solution:**
Use absolute paths or verify the path exists:
```bash
python -m graph.workflow "$(pwd)/tmp/projects/simple_express_app" nodejs
```

---

## Best Practices

### 1. Use REST API for Production
- ✅ Better error handling
- ✅ Async execution
- ✅ Status monitoring
- ✅ Easier to integrate with UI

### 2. Test with CLI First
- ✅ Quick feedback
- ✅ See full output
- ✅ Easier debugging

### 3. Monitor Costs
- Track `total_cost_usd` in results
- Set budget alerts
- Use cost-effective models (Haiku for simple tasks)

### 4. Handle Failures Gracefully
```python
result = run_workflow(project_path, project_type)

if result["status"] != "deployed":
    # Log errors
    logger.error("Migration failed", errors=result["errors"])

    # Send alert
    send_alert(f"Migration failed: {result['errors']}")

    # Rollback if needed
    rollback_changes(project_path)
```

### 5. Validate Test Suite First
Before running migrations, ensure project has tests:
```bash
cd project_path
npm test  # Should pass
```

---

## Next Steps

1. **Try CLI Workflow**
   ```bash
   python -m graph.workflow "tmp/projects/simple_express_app" nodejs
   ```

2. **Start API Server**
   ```bash
   uvicorn api.main:app --reload
   ```

3. **Test API Endpoint**
   ```bash
   curl -X POST http://localhost:8000/api/migrations/start \
     -H "Content-Type: application/json" \
     -d '{"project_path": "tmp/projects/simple_express_app", "project_type": "nodejs"}'
   ```

4. **Integrate with Frontend**
   - Use the REST API
   - Display migration status
   - Show test results
   - Link to created PR

---

**Last Updated**: 2025-11-12
**Version**: 1.0.0
**Status**: Complete and Production-Ready
