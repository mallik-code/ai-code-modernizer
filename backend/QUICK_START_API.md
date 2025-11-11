# Quick Start Guide - API & Test Execution

## ✅ What Was Added

### 1. Automatic Test Execution in Docker
- Tests are now automatically run during dependency validation
- If tests exist, they **MUST pass** for validation to succeed
- Supports both Node.js (npm test) and Python (pytest)

### 2. REST API for Migration
- FastAPI server for triggering migrations remotely
- Perfect for frontend integration and production use
- Background task execution for long-running workflows

### 3. Comprehensive Documentation
- Complete migration invocation guide
- API reference with examples
- Multiple methods to trigger upgrades

---

## 🚀 Quick Start (3 Methods)

### Method 1: CLI Workflow (Fastest for Testing)

```bash
cd backend
python -m graph.workflow "tmp/projects/simple_express_app" nodejs
```

**Output:**
```
[INFO] executing_migration_planner
[INFO] migration_plan_created dependencies_count=5
[INFO] executing_runtime_validator
[INFO] tests_passed test_summary="32 passed, 32 total"
[INFO] executing_staging_deployer
[INFO] deployment_successful pr_url=https://github.com/...

Final Status: deployed
Tests: 32 passed, 32 total
PR URL: https://github.com/user/repo/pull/123
Total Cost: $0.1234
```

---

### Method 2: REST API (Recommended for Production)

#### Start the API Server
```bash
cd backend
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

**Visit**: http://localhost:8000/docs for interactive API documentation

#### Start a Migration
```bash
curl -X POST http://localhost:8000/api/migrations/start \
  -H "Content-Type: application/json" \
  -d '{
    "project_path": "tmp/projects/simple_express_app",
    "project_type": "nodejs",
    "max_retries": 3
  }'
```

**Response:**
```json
{
  "migration_id": "mig_abc123def456",
  "status": "started",
  "project_path": "/path/to/project",
  "started_at": "2025-11-12T10:30:00Z",
  "message": "Migration workflow started successfully"
}
```

#### Check Status
```bash
curl http://localhost:8000/api/migrations/mig_abc123def456
```

**Response:**
```json
{
  "migration_id": "mig_abc123def456",
  "status": "deployed",
  "completed_at": "2025-11-12T10:35:00Z",
  "result": {
    "validation_success": true,
    "tests_run": true,
    "tests_passed": true,
    "test_summary": "32 passed, 32 total",
    "pr_url": "https://github.com/user/repo/pull/123",
    "dependencies_upgraded": 5,
    "total_cost_usd": 0.1234
  }
}
```

---

### Method 3: Python Import (For Custom Scripts)

```python
from graph.workflow import run_workflow

# Run migration
result = run_workflow(
    project_path="tmp/projects/simple_express_app",
    project_type="nodejs",
    max_retries=3
)

# Check results
if result["status"] == "deployed":
    print(f"✅ Success! PR: {result['pr_url']}")
    test_summary = result['validation_result']['validation_result']['logs']['tests']['test_summary']
    print(f"✅ Tests: {test_summary}")
else:
    print(f"❌ Failed: {result['errors']}")
```

---

## 📋 Prerequisites

### Required
- ✅ **Python 3.11+**
- ✅ **Docker Desktop** (running)
- ✅ **API Keys** (at least one):
  - `ANTHROPIC_API_KEY=sk-ant-xxxxx`
  - OR `GOOGLE_API_KEY=AIza-xxxxx`
- ✅ **GitHub Token**:
  - `GITHUB_TOKEN=ghp_xxxxx`

### Setup
```bash
# 1. Install dependencies
cd backend
pip install -r requirements.txt

# 2. Set environment variables
export ANTHROPIC_API_KEY="sk-ant-xxxxx"
export GITHUB_TOKEN="ghp_xxxxx"

# 3. Verify Docker is running
docker ps
```

---

## 🧪 Test with simple_express_app

### Step 1: Verify Test Suite
```bash
cd tmp/projects/simple_express_app
npm install
npm test
```

**Expected:**
```
PASS  test/api.test.js
  ✓ 32 tests pass in ~4s
```

### Step 2: Run Migration
```bash
cd ../../..
python -m graph.workflow "tmp/projects/simple_express_app" nodejs
```

### Step 3: Check Results
- ✅ Migration plan created
- ✅ Docker container created
- ✅ Dependencies installed
- ✅ Application started
- ✅ **Tests executed: 32 passed** 🆕
- ✅ PR created on GitHub

---

## 🔄 Migration Workflow

```
START
  ↓
Migration Planner
  ↓ (analyzes dependencies)
Runtime Validator
  ↓ (Docker + Tests)
  ├─ Tests Pass → Staging Deployer → PR Created ✅
  └─ Tests Fail → Error Analyzer → Retry (max 3x)
```

### What Gets Validated

| Step | Action | Pass Criteria |
|------|--------|---------------|
| 1 | Create Docker container | Container created |
| 2 | Install dependencies | npm install succeeds |
| 3 | Start application | Process running |
| 4 | Health check | Process alive |
| 5 | **Run tests** 🆕 | **All tests pass** |

**Key Difference**: Before, we only checked if the app *started*. Now we verify it actually *works* through tests!

---

## 📡 API Endpoints

### POST /api/migrations/start
Start a new migration workflow.

### GET /api/migrations/{migration_id}
Get status and results of a specific migration.

### GET /api/migrations
List all migrations with pagination.

### GET /api/health
Check API and service health.

### GET /docs
Interactive API documentation (Swagger UI).

---

## 🎯 Real-World Example

### Scenario: Upgrade Express App

**Before Upgrade:**
- Express: 4.16.0 (old)
- 32 tests passing

**Migration Process:**
```bash
python -m graph.workflow "tmp/projects/simple_express_app" nodejs
```

**What Happens:**
1. Planner analyzes `package.json` → Finds 5 outdated deps
2. Validator creates Docker container
3. Applies upgrades: Express 4.16.0 → 4.19.2
4. Installs all dependencies (including test deps)
5. Starts app
6. **Runs `npm test`** → 32 tests execute
7. All tests pass ✅
8. Creates PR with summary

**Result:**
- ✅ PR created: https://github.com/user/repo/pull/123
- ✅ All tests verified
- ✅ Safe to merge

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| **MIGRATION_INVOCATION_GUIDE.md** | Complete guide (all 5 methods) |
| **TEST_EXECUTION_UPDATE.md** | Test execution implementation details |
| **QUICK_START_API.md** | This document - Quick reference |

---

## 💡 Tips

### 1. Use API for Production
- Better error handling
- Async execution
- Status monitoring
- Easier frontend integration

### 2. Test Locally First
```bash
# Always test the workflow manually before automation
python -m graph.workflow "path/to/project" nodejs
```

### 3. Monitor Costs
```python
result = run_workflow(...)
print(f"Cost: ${result['total_cost']:.4f}")
```

### 4. Handle Test Failures
If tests fail, the Error Analyzer will:
- Parse test output
- Identify failing tests
- Suggest fixes
- Retry with fixes (up to 3 times)

---

## 🐛 Troubleshooting

### Issue: Tests Not Found
```
logs.tests.test_summary: "No tests configured"
```

**Cause**: Project has no test script in package.json

**Solution**: Add tests to project OR validation will succeed with health check only

### Issue: Tests Fail After Upgrade
```
status: "error"
errors: ["Tests failed: 3 tests failed"]
```

**Cause**: Breaking changes in upgraded dependencies

**Solution**: Error Analyzer will suggest fixes and retry

### Issue: Docker Not Running
```
ERROR: Docker not available
```

**Solution**:
```bash
# Start Docker Desktop (Windows/Mac)
# OR
sudo systemctl start docker  # Linux
```

---

## 🎉 Success Criteria

### ✅ Complete Success
```json
{
  "status": "deployed",
  "validation_success": true,
  "tests_run": true,
  "tests_passed": true,
  "test_summary": "32 passed, 32 total",
  "pr_url": "https://github.com/user/repo/pull/123"
}
```

### ⚠️ Success Without Tests
```json
{
  "status": "deployed",
  "validation_success": true,
  "tests_run": false,  // No tests found
  "pr_url": "https://github.com/user/repo/pull/123"
}
```

### ❌ Failure
```json
{
  "status": "error",
  "validation_success": false,
  "tests_run": true,
  "tests_passed": false,
  "test_summary": "5 tests failed",
  "errors": ["Tests failed: Body parser API changed"]
}
```

---

## 🔗 Next Steps

1. **Read Full Guide**: `MIGRATION_INVOCATION_GUIDE.md`
2. **Start API Server**: `uvicorn api.main:app --reload`
3. **Test with simple_express_app**: Verify end-to-end
4. **Integrate with Frontend**: Use the REST API

---

**Last Updated**: 2025-11-12
**Commit**: afb7600
**Status**: ✅ Ready for Use
