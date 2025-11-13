"""State schema for LangGraph workflow.

This module defines the state that flows through the multi-agent workflow.
"""

from typing import TypedDict, Optional, Dict, List, Any, Callable
from typing_extensions import Annotated
from langgraph.graph import add_messages


class MigrationState(TypedDict, total=False):
    """State passed between agents in the workflow.

    This TypedDict defines all fields that can be present in the workflow state.
    Using total=False allows fields to be optional.

    Attributes:
        project_path: Absolute path to the project being analyzed
        project_type: Type of project (nodejs, python)

        # Migration Planning
        dependency_file_content: Raw content of package.json or requirements.txt
        migration_plan: Complete migration plan from Migration Planner

        # Runtime Validation
        validation_result: Results from Docker validation
        validation_success: Boolean indicating if validation passed

        # Error Analysis
        error_analysis: Analysis from Error Analyzer
        fix_suggestions: List of suggested fixes

        # Staging Deployment
        deployment_result: Results from Staging Deployer
        pr_url: URL of created pull request
        branch_name: Name of created Git branch

        # Workflow Control
        status: Current workflow status (analyzing, validating, error, deploying, complete)
        retry_count: Number of retry attempts for validation
        max_retries: Maximum allowed retry attempts
        errors: List of error messages encountered
        messages: Conversation history (for LangGraph message passing)

        # Cost Tracking
        total_cost: Total cost of all LLM calls in workflow
        agent_costs: Dictionary of costs per agent
        
        # Real-time updates
        broadcaster: Optional[Callable]
    """

    # Project information
    project_path: str
    project_type: str
    git_branch: str

    # Migration Planning
    dependency_file_content: str
    migration_plan: Optional[Dict[str, Any]]

    # Runtime Validation
    validation_result: Optional[Dict[str, Any]]
    validation_success: bool

    # Error Analysis
    error_analysis: Optional[Dict[str, Any]]
    fix_suggestions: Optional[List[Dict[str, Any]]]

    # Staging Deployment
    deployment_result: Optional[Dict[str, Any]]
    pr_url: Optional[str]
    branch_name: Optional[str]

    # Workflow Control
    status: str
    retry_count: int
    max_retries: int
    errors: List[str]
    messages: Annotated[List, add_messages]

    # Cost Tracking
    total_cost: float
    agent_costs: Dict[str, float]
    
    # Real-time updates
    broadcaster: Optional[Callable]


def create_initial_state(project_path: str, project_type: str = "nodejs", max_retries: int = 3, git_branch: str = "main") -> MigrationState:
    """Create initial state for workflow.

    Args:
        project_path: Path to project
        project_type: Type of project (nodejs, python)
        max_retries: Maximum retry attempts
        git_branch: Git branch being used for the migration (default: main)

    Returns:
        Initial state dictionary
    """
    return MigrationState(
        project_path=project_path,
        project_type=project_type,
        git_branch=git_branch,
        dependency_file_content="",
        migration_plan=None,
        validation_result=None,
        validation_success=False,
        error_analysis=None,
        fix_suggestions=None,
        deployment_result=None,
        pr_url=None,
        branch_name=None,
        status="initializing",
        retry_count=0,
        max_retries=max_retries,
        errors=[],
        messages=[],
        total_cost=0.0,
        agent_costs={},
        broadcaster=None
    )


if __name__ == "__main__":
    """Test state creation."""
    print("=" * 80)
    print("LANGGRAPH STATE SCHEMA TEST")
    print("=" * 80)

    # Create initial state
    state = create_initial_state(
        project_path="/path/to/project",
        project_type="nodejs",
        max_retries=3
    )

    print("\n[OK] Initial state created:")
    print(f"  Project Path: {state['project_path']}")
    print(f"  Project Type: {state['project_type']}")
    print(f"  Status: {state['status']}")
    print(f"  Max Retries: {state['max_retries']}")
    print(f"  Retry Count: {state['retry_count']}")
    print(f"  Validation Success: {state['validation_success']}")

    # Simulate state updates
    state['status'] = 'analyzing'
    state['migration_plan'] = {'dependencies': {}}
    print("\n[OK] State updated:")
    print(f"  Status: {state['status']}")
    print(f"  Migration Plan: {bool(state['migration_plan'])}")

    print("\n[OK] State schema validation complete!")
