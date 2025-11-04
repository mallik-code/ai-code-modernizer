# Python Development Standards

## Code Style and Formatting

### PEP 8 Compliance
Follow PEP 8 style guide with these specifics:

```python
# ✅ CORRECT - PEP 8 compliant
from typing import Dict, List, Optional
import os

class MigrationPlannerAgent(BaseAgent):
    """Analyze project dependencies and create migration strategy.

    This agent reads package.json or requirements.txt, identifies
    outdated dependencies, and creates a phased upgrade plan.
    """

    MAX_RETRY_ATTEMPTS = 3
    DEFAULT_TIMEOUT = 300

    def __init__(self, config: Optional[Dict] = None):
        super().__init__(name="planner", system_prompt=self._get_prompt())
        self.config = config or {}
        self._cache = {}

    def execute(self, input_data: Dict) -> Dict:
        """Execute migration planning logic.

        Args:
            input_data: Dictionary containing project_path and options

        Returns:
            Dictionary with migration strategy and recommendations

        Raises:
            ValueError: If project_path is invalid
            RuntimeError: If analysis fails
        """
        project_path = self._validate_path(input_data.get("project_path"))

        dependencies = self._read_dependencies(project_path)
        strategy = self._create_strategy(dependencies)

        return {
            "strategy": strategy,
            "dependencies": dependencies,
            "status": "success"
        }

    def _validate_path(self, path: str) -> str:
        """Validate and normalize project path."""
        if not path:
            raise ValueError("project_path is required")
        return os.path.normpath(path)

# ❌ INCORRECT - Poor style
class migration_planner_agent:  # Class names should be PascalCase
    def execute(self,input_data):  # Missing space after comma
        projectPath=input_data.get("project_path")  # Use snake_case
        Dependencies=self.read_deps(projectPath)  # Variable name should be lowercase
        return {"strategy":self.create_strat(Dependencies)}  # Unclear abbreviations
```

### Type Hints
Always use type hints for function signatures and class attributes:

```python
# ✅ CORRECT - Complete type hints
from typing import Dict, List, Optional, Union, Any, TypedDict

class MigrationStrategy(TypedDict):
    """Type definition for migration strategy."""
    phases: List[Dict[str, Any]]
    dependencies: Dict[str, str]
    risks: List[str]

class BaseAgent(ABC):
    def __init__(
        self,
        name: str,
        system_prompt: str,
        config: Optional[Dict[str, Any]] = None
    ) -> None:
        self.name: str = name
        self.system_prompt: str = system_prompt
        self.config: Dict[str, Any] = config or {}
        self.conversation_history: List[Dict[str, str]] = []

    @abstractmethod
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent logic."""
        pass

    def think(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Use LLM to generate response."""
        return self.llm.generate(messages=[...])

# ❌ INCORRECT - No type hints
class BaseAgent(ABC):
    def __init__(self, name, system_prompt, config=None):
        self.name = name
        self.config = config or {}

    def execute(self, input_data):
        pass

    def think(self, prompt, context=None):
        return self.llm.generate(messages=[...])
```

### Docstrings
Use Google-style docstrings for all public functions and classes:

```python
# ✅ CORRECT - Comprehensive docstrings
def analyze_dependencies(
    project_path: str,
    include_dev: bool = True,
    max_depth: int = 3
) -> Dict[str, Any]:
    """Analyze project dependencies and identify upgrade candidates.

    Reads package.json or requirements.txt from the project directory,
    checks each dependency against the latest version, and identifies
    breaking changes between current and latest versions.

    Args:
        project_path: Absolute path to project root directory
        include_dev: Whether to include dev dependencies in analysis
        max_depth: Maximum depth for transitive dependency analysis

    Returns:
        Dictionary containing:
            - dependencies: Dict mapping package names to current versions
            - upgrades: List of recommended upgrades with versions
            - breaking_changes: List of packages with breaking changes
            - risks: Risk assessment for each upgrade

    Raises:
        FileNotFoundError: If project_path doesn't exist
        ValueError: If dependency file is malformed
        RuntimeError: If dependency resolution fails

    Example:
        >>> result = analyze_dependencies("/path/to/project")
        >>> print(result["upgrades"])
        [{"package": "express", "from": "4.16.0", "to": "4.18.2"}]

    Note:
        This function may make external API calls to package registries.
        Network errors are logged but don't cause failure.
    """
    if not os.path.exists(project_path):
        raise FileNotFoundError(f"Project path not found: {project_path}")

    # Implementation
    pass

# ❌ INCORRECT - Poor or missing docstring
def analyze_dependencies(project_path, include_dev=True, max_depth=3):
    """Analyze dependencies."""  # Too brief, no details
    pass
```

## Error Handling

### Exception Hierarchy
Create custom exception hierarchy:

```python
# ✅ CORRECT - Custom exception hierarchy
class AgentError(Exception):
    """Base exception for all agent errors."""
    pass

class AgentConfigurationError(AgentError):
    """Raised when agent configuration is invalid."""
    pass

class AgentExecutionError(AgentError):
    """Raised when agent execution fails."""
    pass

class ToolExecutionError(AgentError):
    """Raised when tool execution fails."""

    def __init__(self, tool_name: str, message: str, original_error: Optional[Exception] = None):
        self.tool_name = tool_name
        self.original_error = original_error
        super().__init__(f"Tool '{tool_name}' failed: {message}")

# Usage
try:
    result = self.tools.call_tool("read_file", {"path": path})
except Exception as e:
    raise ToolExecutionError("read_file", str(e), e)
```

### Specific Exception Handling
Catch specific exceptions, not bare `except`:

```python
# ✅ CORRECT - Specific exception handling
def execute(self, input_data: Dict) -> Dict:
    try:
        result = self._analyze(input_data)
        return {"status": "success", "result": result}

    except FileNotFoundError as e:
        self.logger.error("file_not_found", path=str(e))
        return {"status": "error", "error_code": "FILE_NOT_FOUND"}

    except ValueError as e:
        self.logger.error("invalid_input", error=str(e))
        return {"status": "error", "error_code": "INVALID_INPUT"}

    except ToolExecutionError as e:
        self.logger.error("tool_failed", tool=e.tool_name, error=str(e))
        return {"status": "error", "error_code": "TOOL_EXECUTION_FAILED"}

    except Exception as e:
        # Catch-all for unexpected errors
        self.logger.exception("unexpected_error")
        raise AgentExecutionError(f"Unexpected error in {self.name}") from e

# ❌ INCORRECT - Bare except
def execute(self, input_data: Dict) -> Dict:
    try:
        result = self._analyze(input_data)
        return result
    except:  # Catches everything, including KeyboardInterrupt
        return {"error": "something failed"}
```

### Resource Cleanup
Always use context managers for resource cleanup:

```python
# ✅ CORRECT - Context managers
from contextlib import contextmanager
from typing import Generator

@contextmanager
def docker_container(
    project_path: str,
    **kwargs
) -> Generator[str, None, None]:
    """Context manager for Docker container lifecycle.

    Args:
        project_path: Path to project
        **kwargs: Additional docker options

    Yields:
        Container ID
    """
    container_id = None
    try:
        container_id = self.docker.create_container(project_path, **kwargs)
        self.logger.info("container_created", container_id=container_id)
        yield container_id
    finally:
        if container_id:
            self.docker.cleanup(container_id)
            self.logger.info("container_cleaned", container_id=container_id)

# Usage
def validate_upgrade(self, project_path: str) -> Dict:
    with docker_container(project_path, memory_limit="512m") as container_id:
        result = self.docker.run_tests(container_id)
        return result

# ❌ INCORRECT - Manual cleanup (easy to forget)
def validate_upgrade(self, project_path: str) -> Dict:
    container_id = self.docker.create_container(project_path)
    result = self.docker.run_tests(container_id)
    self.docker.cleanup(container_id)  # Skipped if run_tests raises
    return result
```

## Data Structures and Classes

### Dataclasses and TypedDict
Use dataclasses for mutable data, TypedDict for dictionaries:

```python
# ✅ CORRECT - Dataclasses
from dataclasses import dataclass, field
from typing import List, TypedDict

@dataclass
class Dependency:
    """Represents a project dependency."""
    name: str
    current_version: str
    latest_version: str
    has_breaking_changes: bool = False
    risk_level: str = "low"
    changelog_url: str = ""

    def needs_upgrade(self) -> bool:
        """Check if upgrade is needed."""
        return self.current_version != self.latest_version

@dataclass
class MigrationPlan:
    """Complete migration plan."""
    dependencies: List[Dependency] = field(default_factory=list)
    phases: List[Dict] = field(default_factory=list)
    estimated_duration: int = 0  # minutes
    risk_score: float = 0.0

    def add_dependency(self, dep: Dependency) -> None:
        """Add dependency to plan."""
        self.dependencies.append(dep)
        self._recalculate_risk()

    def _recalculate_risk(self) -> None:
        """Recalculate overall risk score."""
        if not self.dependencies:
            self.risk_score = 0.0
            return

        risk_values = {"low": 1, "medium": 2, "high": 3}
        total = sum(risk_values.get(d.risk_level, 1) for d in self.dependencies)
        self.risk_score = total / len(self.dependencies)

# Usage
dep = Dependency(
    name="express",
    current_version="4.16.0",
    latest_version="4.18.2",
    has_breaking_changes=False,
    risk_level="low"
)

plan = MigrationPlan()
plan.add_dependency(dep)
```

### Properties and Private Methods
Use properties for computed attributes, prefix private methods with underscore:

```python
# ✅ CORRECT - Properties and private methods
class LLMClient:
    def __init__(self):
        self._client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self._cost_tracker = CostTracker()
        self._request_count = 0

    @property
    def total_cost(self) -> float:
        """Get total cost of all requests."""
        return self._cost_tracker.total_cost

    @property
    def request_count(self) -> int:
        """Get total number of requests made."""
        return self._request_count

    def generate(self, messages: List[Dict], **kwargs) -> str:
        """Generate response from LLM."""
        response = self._make_request(messages, **kwargs)
        self._track_usage(response)
        return response.content[0].text

    def _make_request(self, messages: List[Dict], **kwargs) -> Any:
        """Make API request (private helper)."""
        self._request_count += 1
        return self._client.messages.create(
            model=self.model,
            messages=messages,
            **kwargs
        )

    def _track_usage(self, response: Any) -> None:
        """Track token usage and cost (private helper)."""
        self._cost_tracker.track_usage(
            response.usage.input_tokens,
            response.usage.output_tokens,
            self.model
        )

# ❌ INCORRECT - Public methods for internal logic
class LLMClient:
    def __init__(self):
        self.client = Anthropic()  # Should be private
        self.total_cost = 0.0  # Should be property

    def make_request(self, messages):  # Internal method exposed as public
        return self.client.messages.create(...)
```

## Async/Await Patterns

Use async/await for I/O-bound operations:

```python
# ✅ CORRECT - Async operations
import asyncio
from typing import List

class MCPToolManager:
    async def call_tool_async(
        self,
        tool_name: str,
        arguments: Dict
    ) -> Any:
        """Call tool asynchronously."""
        self.logger.info("tool_call_start", tool=tool_name)

        # Simulate async tool execution
        result = await self._execute_tool_async(tool_name, arguments)

        self.logger.info("tool_call_complete", tool=tool_name)
        return result

    async def call_tools_parallel(
        self,
        tool_calls: List[tuple[str, Dict]]
    ) -> List[Any]:
        """Execute multiple tool calls in parallel."""
        tasks = [
            self.call_tool_async(tool_name, args)
            for tool_name, args in tool_calls
        ]
        return await asyncio.gather(*tasks, return_exceptions=True)

# Usage
async def analyze_project(self, project_path: str) -> Dict:
    """Analyze project with parallel tool calls."""

    # Execute multiple reads in parallel
    results = await self.tools.call_tools_parallel([
        ("read_file", {"path": f"{project_path}/package.json"}),
        ("read_file", {"path": f"{project_path}/README.md"}),
        ("github_get_file", {"owner": "user", "repo": "repo", "path": "LICENSE"})
    ])

    package_json, readme, license = results
    return self._process_results(package_json, readme, license)
```

## Testing Standards

### Pytest Conventions
```python
# ✅ CORRECT - Comprehensive tests
import pytest
from unittest.mock import Mock, patch, MagicMock
from agents.migration_planner import MigrationPlannerAgent

class TestMigrationPlannerAgent:
    """Test suite for MigrationPlannerAgent."""

    @pytest.fixture
    def agent(self):
        """Create agent instance for testing."""
        return MigrationPlannerAgent()

    @pytest.fixture
    def sample_package_json(self):
        """Sample package.json for testing."""
        return {
            "dependencies": {
                "express": "4.16.0",
                "lodash": "4.17.15"
            }
        }

    def test_execute_success(self, agent, sample_package_json):
        """Test successful execution."""
        with patch.object(agent.tools, 'read_file', return_value=sample_package_json):
            result = agent.execute({"project_path": "/test/project"})

            assert result["status"] == "success"
            assert "strategy" in result
            assert len(result["dependencies"]) == 2

    def test_execute_invalid_path(self, agent):
        """Test execution with invalid path."""
        with pytest.raises(ValueError, match="project_path is required"):
            agent.execute({"project_path": ""})

    def test_execute_file_not_found(self, agent):
        """Test execution when file doesn't exist."""
        with patch.object(agent.tools, 'read_file', side_effect=FileNotFoundError):
            result = agent.execute({"project_path": "/test/project"})
            assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_async_operation(self, agent):
        """Test async operations."""
        result = await agent.analyze_async({"project_path": "/test"})
        assert result is not None

    @pytest.mark.parametrize("version,expected", [
        ("4.16.0", True),
        ("4.18.2", False),
        ("5.0.0", True),
    ])
    def test_needs_upgrade(self, agent, version, expected):
        """Test upgrade detection with multiple versions."""
        dep = Dependency(name="express", current_version=version, latest_version="4.18.2")
        assert dep.needs_upgrade() == expected
```

## Performance Optimization

### Caching
```python
# ✅ CORRECT - Efficient caching
from functools import lru_cache
from typing import Optional
import hashlib

class MigrationPlannerAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="planner", system_prompt="...")
        self._cache: Dict[str, Any] = {}

    def execute(self, input_data: Dict) -> Dict:
        # Cache based on input hash
        cache_key = self._get_cache_key(input_data)

        if cache_key in self._cache:
            self.logger.info("cache_hit", key=cache_key)
            return self._cache[cache_key]

        result = self._execute_impl(input_data)
        self._cache[cache_key] = result

        return result

    def _get_cache_key(self, data: Dict) -> str:
        """Generate cache key from input data."""
        serialized = json.dumps(data, sort_keys=True)
        return hashlib.sha256(serialized.encode()).hexdigest()

    @lru_cache(maxsize=128)
    def _get_latest_version(self, package_name: str) -> Optional[str]:
        """Get latest version with LRU cache."""
        # Expensive operation cached automatically
        return self._fetch_from_registry(package_name)
```

### Lazy Loading
```python
# ✅ CORRECT - Lazy initialization
class BaseAgent(ABC):
    def __init__(self, name: str, system_prompt: str):
        self.name = name
        self.system_prompt = system_prompt
        self._llm: Optional[LLMClient] = None
        self._tools: Optional[MCPToolManager] = None

    @property
    def llm(self) -> LLMClient:
        """Lazy load LLM client."""
        if self._llm is None:
            self._llm = LLMClient()
        return self._llm

    @property
    def tools(self) -> MCPToolManager:
        """Lazy load MCP tools."""
        if self._tools is None:
            self._tools = MCPToolManager()
        return self._tools
```

## Logging Standards

```python
# ✅ CORRECT - Structured logging
import structlog

logger = structlog.get_logger(__name__)

def execute(self, input_data: Dict) -> Dict:
    logger.info(
        "agent_execution_start",
        agent=self.name,
        input_keys=list(input_data.keys())
    )

    try:
        result = self._analyze(input_data)

        logger.info(
            "agent_execution_success",
            agent=self.name,
            duration=time.time() - start_time,
            result_keys=list(result.keys())
        )

        return result

    except Exception as e:
        logger.error(
            "agent_execution_failed",
            agent=self.name,
            error=str(e),
            error_type=type(e).__name__,
            duration=time.time() - start_time,
            exc_info=True
        )
        raise
```

## Code Organization Checklist

- [ ] All public APIs have type hints
- [ ] All public functions have docstrings
- [ ] Custom exceptions defined for domain errors
- [ ] Context managers used for resource management
- [ ] Private methods prefixed with underscore
- [ ] Properties used for computed attributes
- [ ] Tests cover happy path and error cases
- [ ] Async used for I/O-bound operations
- [ ] Caching implemented for expensive operations
- [ ] Structured logging with context
- [ ] PEP 8 compliant (check with `black` and `ruff`)
