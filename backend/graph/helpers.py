"""Helper functions for workflow state management."""
from typing import Optional, Callable
from graph.state import MigrationState, create_initial_state


def create_initial_state_with_broadcaster(
    project_path: str, 
    project_type: str = "nodejs", 
    max_retries: int = 3, 
    git_branch: str = "main", 
    broadcaster: Optional[Callable] = None
) -> MigrationState:
    """Create initial state for workflow with broadcaster."""
    state = create_initial_state(
        project_path=project_path,
        project_type=project_type,
        max_retries=max_retries,
        git_branch=git_branch
    )
    state["broadcaster"] = broadcaster
    return state