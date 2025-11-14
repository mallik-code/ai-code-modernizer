# Testing Guide - AI Code Modernizer Backend

**Last Updated**: 2025-11-07
**Status**: Phase 3 Complete (50%)

---

## Quick Start - Test Everything

### Option 1: End-to-End Test (Recommended)
```bash
# Full workflow: Migration Planner → Runtime Validator
".venv/Scripts/python.exe" tests/test_end_to_end.py

# Expected: ~2-3 minutes, costs ~$0.02-0.03
```

### Option 2: Individual Component Tests
```bash
# Test just the Migration Planner (~30 seconds, ~$0.01)
".venv/Scripts/python.exe" tests/test_end_to_end.py --test planner

# Test just Docker validation (~60 seconds, no LLM cost)
".venv/Scripts/python.exe" tests/test_end_to_end.py --test docker
```

### Option 3: Unit Tests (Fastest, No API Calls)
```bash
# Run all unit tests with mocked LLMs
".venv/Scripts/python.exe" -m pytest tests/ -v

# Expected: <1 second, no cost
```

---

## Prerequisites

### Required
- ✅ Docker Desktop running (`docker ps` should work)
- ✅ Python virtual environment activated
- ✅ At least one LLM API key configured in `.env`:
  - `ANTHROPIC_API_KEY` (recommended) OR
  - `GEMINI_API_KEY` OR
  - `HUGGINGFACE_API_KEY` OR
  - `OPENAI_API_KEY` OR
  - `QWEN_API_KEY`

### Optional
- GitHub token (only needed for Phase 4 - Staging Deployer)
- MCP servers (not required yet - using fallback mode)

---

## Test Components Individually

### 1. Test LLM Providers ✅
```bash
# Test all configured LLM providers
".venv/Scripts/python.exe" -m llm.test_flexible_llm

# Expected output:
# ✅ Anthropic client working (if API key set)
# ✅ Gemini client working (if API key set)
# ❌ OpenAI errors (if no API key)
```

**Cost**: ~$0.001 per provider tested

---

### 2. Test Migration Planner ✅

#### Option A: Unit Tests (Mocked LLM - Fast, Free)
```bash
".venv/Scripts/python.exe" -m pytest tests/test_migration_planner.py -v

# Expected: 7 tests PASSED in <1 second
# Cost: $0 (uses mocks)
```

#### Option B: Live Test (Real LLM - Slower, Costs Money)
```bash
".venv/Scripts/python.exe" -m agents.migration_planner

# Expected: 10-15 seconds
# Cost: ~$0.01-0.02
```

**What it tests**:
- ✅ Reads package.json
- ✅ Identifies outdated dependencies
- ✅ Analyzes breaking changes
- ✅ Creates phased migration strategy
- ✅ Assesses risk levels

**Sample Output**:
```
Project Type: NODEJS
Dependencies: 6
Phases: 3
Overall Risk: MEDIUM
Cost: $0.015
```

---

### 3. Test Docker Tools ✅

```bash
".venv/Scripts/python.exe" -m tools.docker_tools

# Expected: 50-60 seconds
# Cost: $0 (no LLM calls)
```

**What it tests**:
- ✅ Pulls node:18-alpine image (first time only)
- ✅ Creates container
- ✅ Copies project files
- ✅ Installs dependencies (npm install)
- ✅ Starts Express app
- ✅ Verifies process running
- ✅ Cleans up container

**Sample Output**:
```
Status: SUCCESS
Build: SUCCESS
Install: SUCCESS
Runtime: SUCCESS
Health Check: SUCCESS
```

---

### 4. Test Runtime Validator ✅

```bash
".venv/Scripts/python.exe" -m agents.runtime_validator

# Expected: 60-70 seconds
# Cost: ~$0.005-0.01
```

**What it tests**:
- ✅ Uses DockerValidator
- ✅ LLM analyzes results
- ✅ Provides recommendations
- ✅ Identifies issues

**Sample Output**:
```
Docker Validation: SUCCESS
LLM Analysis: SUCCESS
Recommendation: PROCEED
Confidence: HIGH
```

---

### 5. Test MCP Tools ✅

```bash
".venv/Scripts/python.exe" tools/test_mcp.py

# Expected: <1 second
# Cost: $0
```

**What it tests**:
- ✅ Configuration loading
- ✅ Subprocess management
- ✅ Fallback file operations
- ✅ Mock GitHub tools

**Sample Output**:
```
[PASS] Configuration Loading
[PASS] Server Connection
[PASS] List Tools
[PASS] Filesystem Operations
[PASS] Generic Tool Call
[PASS] GitHub Tools Mock

ALL TESTS PASSED
```

---

## End-to-End Integration Tests

### Full Workflow Test
```bash
".venv/Scripts/python.exe" tests/test_end_to_end.py

# What it does:
# 1. Migration Planner analyzes express-app
# 2. Runtime Validator tests in Docker
# 3. Reports results and recommendations

# Expected: 2-3 minutes
# Cost: ~$0.02-0.03
```

**Sample Output**:
```
================================================================================
END-TO-END INTEGRATION TEST
================================================================================

STEP 1: MIGRATION PLANNING
    ✅ Analysis complete
    📊 Dependencies analyzed: 6
    📊 Migration phases: 3
    📊 Overall risk: MEDIUM
    💰 Cost: $0.015

STEP 2: RUNTIME VALIDATION (BASELINE)
    ✅ Docker validation complete
    📦 Container: abc123def456
    🏗️  Build: SUCCESS
    📥 Install: SUCCESS
    🚀 Runtime: SUCCESS
    ✅ Health: SUCCESS
    💰 Cost: $0.008

STEP 3: WORKFLOW SUMMARY
    ✅ Migration Plan Created
    ✅ Baseline Validation Passed
    💰 Total Cost: $0.023

✅ END-TO-END TEST PASSED
```

---

## Pytest Unit Tests

### Run All Tests
```bash
".venv/Scripts/python.exe" -m pytest tests/ -v
```

### Run Specific Test File
```bash
".venv/Scripts/python.exe" -m pytest tests/test_migration_planner.py -v
```

### Run with Coverage
```bash
".venv/Scripts/python.exe" -m pytest tests/ --cov=. --cov-report=html
# View: open htmlcov/index.html
```

### Run with Output
```bash
".venv/Scripts/python.exe" -m pytest tests/ -v -s
```

---

## Testing Strategy by Use Case

### "I just want to see if everything works"
```bash
".venv/Scripts/python.exe" tests/test_end_to_end.py --test planner
# Fast, cheap, shows core functionality
```

### "I want to test Docker integration"
```bash
".venv/Scripts/python.exe" tests/test_end_to_end.py --test docker
# Tests container management, no LLM cost
```

### "I want the full experience"
```bash
".venv/Scripts/python.exe" tests/test_end_to_end.py
# Complete workflow, best demonstration
```

### "I'm developing and need fast feedback"
```bash
".venv/Scripts/python.exe" -m pytest tests/ -v
# Unit tests only, instant feedback
```

---

## Test Data

### Sample Project
**Location**: `tests/sample_projects/express-app/`

**What it is**:
- Express.js 4.16.0 app (outdated)
- 6 dependencies (all outdated)
- 7 REST API endpoints
- Intentionally uses deprecated packages

**Purpose**:
- Test migration planning
- Test Docker validation
- Verify upgrade detection

---

## Expected Test Times

| Test | Time | Cost | LLM Calls |
|------|------|------|-----------|
| Unit Tests | <1s | $0 | 0 (mocked) |
| MCP Tests | <1s | $0 | 0 |
| LLM Providers | 5s | ~$0.001 | 1 per provider |
| Migration Planner | 10-15s | ~$0.01-0.02 | 1 |
| Docker Tools | 50-60s | $0 | 0 |
| Runtime Validator | 60-70s | ~$0.005-0.01 | 1 |
| End-to-End | 2-3min | ~$0.02-0.03 | 2 |

---

## Expected Costs

### Per Test Run
- **Unit Tests**: $0 (all mocked)
- **Migration Planner**: ~$0.01-0.02
- **Runtime Validator**: ~$0.005-0.01
- **End-to-End**: ~$0.02-0.03

### Provider Comparison (per test)
- **Anthropic Claude Sonnet 4**: ~$0.015
- **Google Gemini 2.0 Flash**: ~$0.001
- **HuggingFace Llama 3.2**: ~$0.0001
- **OpenAI GPT-4o**: ~$0.025
- **Qwen Turbo**: ~$0.0005

**Recommendation**: Use Gemini or HuggingFace for frequent testing, Claude for final validation.

---

## Troubleshooting

### "Docker connection failed"
```bash
# Check if Docker is running
docker ps

# Start Docker Desktop if not running
# Then retry test
```

### "API authentication failed"
```bash
# Check .env file has API key
cat .env | grep API_KEY

# Set provider
LLM_PROVIDER=anthropic  # or gemini, huggingface, etc.
```

### "Module not found"
```bash
# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Verify
which python  # Should point to .venv
```

### "Test timeout"
```bash
# Increase timeout (default: 2 minutes)
pytest tests/ -v --timeout=300
```

### "Container creation failed"
```bash
# Check Docker has space
docker system df

# Clean up if needed
docker system prune -a
```

---

## Continuous Integration

### GitHub Actions (Future)
```yaml
name: Backend Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v
      # Note: End-to-end tests require Docker + API keys
```

---

## Testing Best Practices

### Before Committing
```bash
# 1. Run unit tests (fast)
pytest tests/ -v

# 2. Run quick component test
python tests/test_end_to_end.py --test planner

# 3. If both pass, commit
```

### Before Pull Request
```bash
# 1. Run all unit tests with coverage
pytest tests/ --cov=. --cov-report=html

# 2. Run end-to-end test
python tests/test_end_to_end.py

# 3. Check coverage report
# 4. Create PR if >80% coverage
```

### Daily Development
```bash
# Use fast tests during development
pytest tests/test_migration_planner.py -v

# Run full tests before EOD
python tests/test_end_to_end.py
```

---

## Test Coverage

### Current Status
- ✅ Migration Planner: 7 unit tests
- ✅ MCP Tools: 6 integration tests
- ✅ Docker Tools: 1 standalone test
- ✅ End-to-End: 3 integration tests
- ❌ Runtime Validator: 0 unit tests (TODO)
- ❌ Error Analyzer: Not implemented
- ❌ Staging Deployer: Not implemented

### Coverage Goals
- Unit Tests: >80% line coverage
- Integration Tests: All major workflows
- End-to-End: Complete user journeys

---

## Performance Benchmarks

### Baseline Measurements (2025-11-07)
- Migration Planning: 12s (Claude Sonnet 4)
- Docker Validation: 55s (node:18-alpine)
- Runtime Analysis: 8s (Claude Sonnet 4)
- Total E2E: 2m 15s

### Optimization Opportunities
1. Cache Docker images (first pull: 30s, subsequent: 1s)
2. Use faster LLM for analysis (Gemini: 3s vs Claude: 12s)
3. Parallel container operations
4. Incremental dependency installs

---

## Next Steps

### Phase 4 Tests (Planned)
- [ ] Error Analyzer unit tests
- [ ] Staging Deployer unit tests
- [ ] GitHub integration tests (requires token)

### Phase 5 Tests (Planned)
- [ ] LangGraph workflow tests
- [ ] State transition tests
- [ ] Retry logic tests

### Phase 6 Tests (Planned)
- [ ] FastAPI endpoint tests
- [ ] WebSocket tests
- [ ] API integration tests

---

## Summary

**Current Test Status**: ✅ Comprehensive
- 16 total tests (7 unit + 6 integration + 3 E2E)
- All passing
- <3 minutes for full suite
- <$0.03 per full run

**Test Commands**:
```bash
# Quick (unit tests only)
pytest tests/ -v

# Medium (planner only)
python tests/test_end_to_end.py --test planner

# Full (complete workflow)
python tests/test_end_to_end.py
```

**Recommended for Demo**:
```bash
python tests/test_end_to_end.py
```

---

**Document Version**: 1.0
**Last Updated**: 2025-11-07
**Status**: Complete for Phase 3
