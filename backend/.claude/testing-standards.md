# Testing Standards

## Test Structure and Organization

### Directory Structure
```
tests/
├── __init__.py
├── conftest.py                 # Shared fixtures
├── unit/                       # Unit tests
│   ├── test_agents.py
│   ├── test_llm_client.py
│   ├── test_mcp_tools.py
│   └── test_cost_tracker.py
├── integration/                # Integration tests
│   ├── test_workflow.py
│   ├── test_api_endpoints.py
│   └── test_mcp_integration.py
├── e2e/                        # End-to-end tests
│   ├── test_full_workflow.py
│   └── test_user_scenarios.py
└── fixtures/                   # Test data
    ├── sample_package_json.py
    └── mock_responses.py
```

### Test Naming Convention
```python
# ✅ CORRECT - Descriptive test names
def test_migration_planner_identifies_outdated_dependencies():
    """Test that planner correctly identifies outdated packages."""
    pass

def test_runtime_validator_handles_docker_timeout_gracefully():
    """Test validator behavior when Docker container times out."""
    pass

def test_error_analyzer_extracts_root_cause_from_logs():
    """Test error analyzer parsing of validation logs."""
    pass

def test_base_agent_raises_error_when_tool_execution_fails():
    """Test error handling in base agent."""
    pass

# ❌ INCORRECT - Vague test names
def test_planner():
    pass

def test_validator_1():
    pass

def test_stuff():
    pass
```

## Unit Testing

### Test Isolation
Each test should be independent:

```python
# ✅ CORRECT - Isolated tests with fixtures
import pytest
from unittest.mock import Mock, patch, MagicMock

@pytest.fixture
def mock_llm_client():
    """Mock LLM client for testing."""
    client = Mock()
    client.generate.return_value = "Mock response"
    client.cost_tracker = Mock()
    client.cost_tracker.total_cost = 0.05
    return client

@pytest.fixture
def mock_mcp_tools():
    """Mock MCP tools for testing."""
    tools = Mock()
    tools.read_file.return_value = '{"dependencies": {"express": "4.16.0"}}'
    tools.github_get_file.return_value = "# README"
    return tools

@pytest.fixture
def agent(mock_llm_client, mock_mcp_tools):
    """Create agent with mocked dependencies."""
    with patch('agents.base.LLMClient', return_value=mock_llm_client):
        with patch('agents.base.MCPToolManager', return_value=mock_mcp_tools):
            return MigrationPlannerAgent()

def test_execute_success(agent, mock_mcp_tools):
    """Test successful execution."""
    result = agent.execute({"project_path": "/test/project"})

    assert result["status"] == "success"
    assert "strategy" in result
    mock_mcp_tools.read_file.assert_called_once()

def test_execute_with_invalid_path(agent):
    """Test execution with invalid path."""
    with pytest.raises(ValueError, match="project_path is required"):
        agent.execute({"project_path": ""})

# ❌ INCORRECT - Tests depend on each other
class TestAgent:
    agent = None  # Shared state

    def test_create_agent(self):
        self.agent = MigrationPlannerAgent()
        assert self.agent is not None

    def test_execute(self):
        # Depends on previous test
        result = self.agent.execute({"project_path": "/test"})
```

### Mocking External Dependencies
```python
# ✅ CORRECT - Mock external dependencies
from unittest.mock import Mock, patch, call
import pytest

def test_llm_client_tracks_cost():
    """Test that LLM client tracks token usage."""
    with patch('anthropic.Anthropic') as mock_anthropic:
        # Setup mock response
        mock_response = Mock()
        mock_response.content = [Mock(text="Generated text")]
        mock_response.usage = Mock(input_tokens=100, output_tokens=50)
        mock_anthropic.return_value.messages.create.return_value = mock_response

        # Test
        client = LLMClient()
        result = client.generate(messages=[{"role": "user", "content": "test"}])

        # Assertions
        assert result == "Generated text"
        assert client.cost_tracker.total_input_tokens == 100
        assert client.cost_tracker.total_output_tokens == 50
        assert client.cost_tracker.total_cost > 0

def test_mcp_tool_manager_handles_connection_failure():
    """Test MCP manager behavior when server connection fails."""
    with patch('subprocess.Popen', side_effect=OSError("Connection failed")):
        with pytest.raises(MCPConnectionError, match="Failed to connect"):
            MCPToolManager()

def test_agent_retries_on_tool_failure():
    """Test agent retry logic when tool fails."""
    agent = MigrationPlannerAgent()

    # Mock tool that fails twice then succeeds
    agent.tools.read_file = Mock(
        side_effect=[
            ToolExecutionError("timeout"),
            ToolExecutionError("timeout"),
            '{"dependencies": {}}'
        ]
    )

    result = agent.execute({"project_path": "/test"})

    # Should have retried and succeeded
    assert result["status"] == "success"
    assert agent.tools.read_file.call_count == 3
```

### Parametrized Tests
```python
# ✅ CORRECT - Test multiple scenarios efficiently
import pytest

@pytest.mark.parametrize("version,latest,expected", [
    ("4.16.0", "4.18.2", True),   # Patch update
    ("4.18.2", "4.18.2", False),  # Same version
    ("4.16.0", "5.0.0", True),    # Major update
    ("5.0.0", "4.18.2", False),   # Downgrade
])
def test_needs_upgrade(version, latest, expected):
    """Test upgrade detection for various version scenarios."""
    dep = Dependency(
        name="express",
        current_version=version,
        latest_version=latest
    )
    assert dep.needs_upgrade() == expected

@pytest.mark.parametrize("path,should_raise", [
    ("/valid/path", False),
    ("../../../etc/passwd", True),
    ("~/secret", True),
    ("C:\\Windows\\System32", True),
    ("/tmp/safe", False),
])
def test_path_validation(path, should_raise):
    """Test path validation for security."""
    agent = MigrationPlannerAgent()

    if should_raise:
        with pytest.raises(ValueError):
            agent._validate_path(path)
    else:
        result = agent._validate_path(path)
        assert result is not None
```

### Test Coverage
```python
# ✅ CORRECT - Comprehensive test coverage
class TestMigrationPlannerAgent:
    """Complete test suite for MigrationPlannerAgent."""

    # Happy path
    def test_execute_success_with_valid_project(self, agent):
        """Test successful execution with valid project."""
        pass

    # Error cases
    def test_execute_raises_error_for_missing_path(self, agent):
        """Test error when project_path is missing."""
        pass

    def test_execute_handles_file_not_found(self, agent):
        """Test handling when dependency file doesn't exist."""
        pass

    def test_execute_handles_malformed_json(self, agent):
        """Test handling of malformed package.json."""
        pass

    # Edge cases
    def test_execute_with_empty_dependencies(self, agent):
        """Test behavior with no dependencies."""
        pass

    def test_execute_with_very_large_dependency_list(self, agent):
        """Test performance with 100+ dependencies."""
        pass

    # Integration points
    def test_execute_calls_llm_with_correct_prompt(self, agent, mock_llm):
        """Test LLM is called with properly formatted prompt."""
        pass

    def test_execute_uses_mcp_tools_correctly(self, agent, mock_tools):
        """Test MCP tools are called with correct arguments."""
        pass

    # Business logic
    def test_execute_identifies_breaking_changes(self, agent):
        """Test identification of dependencies with breaking changes."""
        pass

    def test_execute_calculates_risk_score(self, agent):
        """Test risk score calculation."""
        pass
```

## Integration Testing

### API Integration Tests
```python
# ✅ CORRECT - API integration tests
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_create_and_retrieve_project():
    """Test full project lifecycle."""
    # Create project
    create_response = client.post(
        "/api/v1/projects",
        json={
            "name": "Test Project",
            "repository_url": "https://github.com/user/repo",
            "branch": "main"
        }
    )

    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    # Retrieve project
    get_response = client.get(f"/api/v1/projects/{project_id}")

    assert get_response.status_code == 200
    assert get_response.json()["name"] == "Test Project"

def test_project_analysis_workflow():
    """Test complete analysis workflow."""
    # Create project
    create_response = client.post("/api/v1/projects", json={...})
    project_id = create_response.json()["id"]

    # Start analysis
    analyze_response = client.post(f"/api/v1/projects/{project_id}/analyze")
    assert analyze_response.status_code == 202

    # Check status
    status_response = client.get(f"/api/v1/projects/{project_id}/status")
    assert status_response.json()["status"] in ["analyzing", "completed"]

def test_api_authentication():
    """Test API key authentication."""
    # Without API key
    response = client.post("/api/v1/projects", json={...})
    assert response.status_code == 401

    # With valid API key
    response = client.post(
        "/api/v1/projects",
        json={...},
        headers={"X-API-Key": "valid_key"}
    )
    assert response.status_code == 201

def test_rate_limiting():
    """Test rate limiting enforcement."""
    # Make requests up to limit
    for i in range(10):
        response = client.post("/api/v1/projects", json={...})
        assert response.status_code in [201, 429]

    # Next request should be rate limited
    response = client.post("/api/v1/projects", json={...})
    assert response.status_code == 429
```

### Database Integration Tests
```python
# ✅ CORRECT - Database integration tests
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture(scope="function")
def db_session():
    """Create test database session."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    session.close()

def test_project_crud_operations(db_session):
    """Test CRUD operations on project model."""
    # Create
    project = Project(
        name="Test",
        repository_url="https://github.com/user/repo"
    )
    db_session.add(project)
    db_session.commit()

    # Read
    retrieved = db_session.query(Project).filter_by(name="Test").first()
    assert retrieved is not None
    assert retrieved.repository_url == "https://github.com/user/repo"

    # Update
    retrieved.status = "analyzing"
    db_session.commit()

    updated = db_session.query(Project).filter_by(name="Test").first()
    assert updated.status == "analyzing"

    # Delete
    db_session.delete(updated)
    db_session.commit()

    deleted = db_session.query(Project).filter_by(name="Test").first()
    assert deleted is None
```

### LangGraph Workflow Tests
```python
# ✅ CORRECT - Workflow integration tests
def test_workflow_happy_path():
    """Test workflow with successful validation."""
    workflow = create_workflow()

    initial_state = MigrationState(
        project_path="/test/project",
        dependencies={},
        status="analyzing",
        errors=[],
        retry_count=0
    )

    # Run workflow
    final_state = workflow.invoke(initial_state)

    # Assertions
    assert final_state["status"] == "completed"
    assert final_state["migration_strategy"] is not None
    assert final_state["validation_result"]["success"] is True
    assert len(final_state["errors"]) == 0

def test_workflow_with_validation_failure_and_retry():
    """Test workflow retry logic on validation failure."""
    workflow = create_workflow()

    initial_state = MigrationState(
        project_path="/test/project",
        dependencies={},
        status="analyzing",
        errors=[],
        retry_count=0
    )

    # Mock validator to fail first time, succeed second
    with patch.object(RuntimeValidatorAgent, 'execute') as mock_validate:
        mock_validate.side_effect = [
            {"status": "error", "errors": ["Test failed"]},
            {"status": "success", "validation_result": {...}}
        ]

        final_state = workflow.invoke(initial_state)

    # Should have retried and succeeded
    assert final_state["status"] == "completed"
    assert final_state["retry_count"] == 1
    assert mock_validate.call_count == 2

def test_workflow_max_retries_exceeded():
    """Test workflow stops after max retries."""
    workflow = create_workflow()

    initial_state = MigrationState(
        project_path="/test/project",
        dependencies={},
        status="analyzing",
        errors=[],
        retry_count=0
    )

    # Mock validator to always fail
    with patch.object(RuntimeValidatorAgent, 'execute') as mock_validate:
        mock_validate.return_value = {"status": "error", "errors": ["Failed"]}

        final_state = workflow.invoke(initial_state)

    # Should have stopped after 3 retries
    assert final_state["status"] == "failed"
    assert final_state["retry_count"] == 3
    assert mock_validate.call_count == 3
```

## End-to-End Testing

```python
# ✅ CORRECT - E2E test
@pytest.mark.e2e
def test_complete_upgrade_workflow():
    """Test complete workflow from project upload to PR creation."""
    # 1. Create project
    project = create_test_project()

    # 2. Start analysis
    analysis_result = start_analysis(project.id)
    assert analysis_result["status"] == "accepted"

    # 3. Wait for analysis to complete (with timeout)
    strategy = wait_for_analysis(project.id, timeout=60)
    assert strategy is not None

    # 4. Approve strategy
    approval_result = approve_strategy(project.id, strategy.id)
    assert approval_result["approved"] is True

    # 5. Wait for validation
    validation_result = wait_for_validation(project.id, timeout=300)
    assert validation_result["success"] is True

    # 6. Approve deployment
    deployment_result = approve_deployment(project.id)
    assert deployment_result["approved"] is True

    # 7. Wait for PR creation
    pr = wait_for_pr(project.id, timeout=60)
    assert pr is not None
    assert pr["status"] == "open"

    # Cleanup
    cleanup_test_project(project.id)

@pytest.mark.e2e
def test_workflow_with_docker_validation_failure():
    """Test workflow handles validation failures gracefully."""
    # Create project with known breaking changes
    project = create_test_project_with_breaking_changes()

    # Start workflow
    start_analysis(project.id)

    # Should detect failure and attempt fixes
    wait_for_analysis(project.id)
    validation_result = wait_for_validation(project.id)

    # Should have detected failure
    assert validation_result["success"] is False
    assert len(validation_result["errors"]) > 0

    # Should have triggered error analyzer
    fix_suggestions = wait_for_fix_suggestions(project.id)
    assert len(fix_suggestions) > 0
```

## Test Fixtures and Helpers

```python
# ✅ CORRECT - Reusable fixtures in conftest.py
# tests/conftest.py
import pytest
from typing import Generator

@pytest.fixture(scope="session")
def docker_client():
    """Docker client for integration tests."""
    import docker
    client = docker.from_env()
    yield client
    # Cleanup any test containers
    for container in client.containers.list(filters={"label": "test"}):
        container.stop()
        container.remove()

@pytest.fixture
def sample_package_json():
    """Sample package.json for testing."""
    return {
        "name": "test-project",
        "version": "1.0.0",
        "dependencies": {
            "express": "4.16.0",
            "lodash": "4.17.15",
            "axios": "0.21.1"
        },
        "devDependencies": {
            "jest": "26.0.0"
        }
    }

@pytest.fixture
def test_project_directory(tmp_path):
    """Create temporary test project directory."""
    project_dir = tmp_path / "test-project"
    project_dir.mkdir()

    # Create package.json
    (project_dir / "package.json").write_text('{"dependencies": {}}')

    # Create README
    (project_dir / "README.md").write_text("# Test Project")

    yield project_dir

    # Cleanup handled by tmp_path

@pytest.fixture
def mock_api_responses():
    """Mock external API responses."""
    return {
        "npm_registry": {
            "express": {
                "dist-tags": {"latest": "4.18.2"},
                "versions": {"4.18.2": {...}}
            }
        },
        "github": {
            "changelog": "# Changelog\n\n## 4.18.2\n- Bug fixes"
        }
    }
```

## Performance Testing

```python
# ✅ CORRECT - Performance tests
import pytest
import time

@pytest.mark.performance
def test_agent_execution_time():
    """Test agent execution completes within time limit."""
    agent = MigrationPlannerAgent()

    start_time = time.time()
    result = agent.execute({"project_path": "/test/large-project"})
    duration = time.time() - start_time

    # Should complete within 30 seconds
    assert duration < 30.0
    assert result["status"] == "success"

@pytest.mark.performance
def test_concurrent_agent_execution():
    """Test multiple agents can run concurrently."""
    import concurrent.futures

    agents = [MigrationPlannerAgent() for _ in range(10)]

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(agent.execute, {"project_path": f"/test/proj{i}"})
            for i, agent in enumerate(agents)
        ]

        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    # All should succeed
    assert all(r["status"] == "success" for r in results)

@pytest.mark.performance
def test_memory_usage():
    """Test agent doesn't leak memory."""
    import psutil
    import os

    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB

    agent = MigrationPlannerAgent()

    # Run agent 100 times
    for i in range(100):
        agent.execute({"project_path": f"/test/proj{i}"})
        agent.reset()  # Clear conversation history

    final_memory = process.memory_info().rss / 1024 / 1024  # MB
    memory_increase = final_memory - initial_memory

    # Memory increase should be less than 100MB
    assert memory_increase < 100
```

## Testing Checklist

- [ ] Unit tests for all agents
- [ ] Unit tests for all tools
- [ ] Unit tests for all utilities
- [ ] Integration tests for API endpoints
- [ ] Integration tests for LangGraph workflow
- [ ] Integration tests for MCP tools
- [ ] E2E tests for critical user workflows
- [ ] Tests for error handling
- [ ] Tests for edge cases
- [ ] Tests for security (path traversal, injection)
- [ ] Performance tests
- [ ] Tests use proper fixtures and mocks
- [ ] Tests are isolated and independent
- [ ] Test coverage > 80%
- [ ] All tests pass before commit
- [ ] Slow tests marked with `@pytest.mark.slow`
- [ ] E2E tests marked with `@pytest.mark.e2e`
