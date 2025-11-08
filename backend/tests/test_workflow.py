"""Unit tests for LangGraph Workflow."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from graph.workflow import (
    should_validate,
    should_retry_or_deploy,
    should_retry_validation,
    deployment_complete,
    create_workflow
)
from graph.state import MigrationState, create_initial_state


class TestWorkflowRouting:
    """Test cases for workflow routing logic."""

    def test_should_validate_success(self):
        """Test routing to validation when plan is created."""
        state = create_initial_state("/test/project")
        state["status"] = "plan_created"
        state["migration_plan"] = {"dependencies": {}}

        result = should_validate(state)
        assert result == "validate"

    def test_should_validate_failure(self):
        """Test routing to end when planning fails."""
        state = create_initial_state("/test/project")
        state["status"] = "error"
        state["migration_plan"] = None

        result = should_validate(state)
        assert result == "end"

    def test_should_retry_or_deploy_success(self):
        """Test routing to deployment when validation succeeds."""
        state = create_initial_state("/test/project")
        state["validation_success"] = True

        result = should_retry_or_deploy(state)
        assert result == "deploy"

    def test_should_retry_or_deploy_retry(self):
        """Test routing to error analysis when validation fails with retries available."""
        state = create_initial_state("/test/project", max_retries=3)
        state["validation_success"] = False
        state["retry_count"] = 0

        result = should_retry_or_deploy(state)
        assert result == "analyze"

    def test_should_retry_or_deploy_max_retries(self):
        """Test routing to end when max retries exceeded."""
        state = create_initial_state("/test/project", max_retries=3)
        state["validation_success"] = False
        state["retry_count"] = 3

        result = should_retry_or_deploy(state)
        assert result == "end"

    def test_should_retry_validation_with_fixes(self):
        """Test routing to retry validation when fixes available."""
        state = create_initial_state("/test/project")
        state["status"] = "analyzed"
        state["fix_suggestions"] = [{"priority": 1, "description": "Fix something"}]

        result = should_retry_validation(state)
        assert result == "validate"
        assert state["retry_count"] == 1

    def test_should_retry_validation_no_fixes(self):
        """Test routing to end when no fixes available."""
        state = create_initial_state("/test/project")
        state["status"] = "analyzed"
        state["fix_suggestions"] = None

        result = should_retry_validation(state)
        assert result == "end"

    def test_deployment_complete(self):
        """Test routing to end after deployment."""
        state = create_initial_state("/test/project")
        state["status"] = "deployed"

        result = deployment_complete(state)
        assert result == "end"


class TestWorkflowGraph:
    """Test cases for workflow graph structure."""

    def test_create_workflow(self):
        """Test workflow graph creation."""
        workflow = create_workflow()

        # Verify graph has correct nodes
        assert workflow is not None

        # Compile the graph
        app = workflow.compile()
        assert app is not None

    def test_workflow_structure(self):
        """Test workflow has all required nodes and edges."""
        workflow = create_workflow()

        # Check nodes exist
        nodes = workflow.nodes
        assert "plan" in nodes
        assert "validate" in nodes
        assert "analyze" in nodes
        assert "deploy" in nodes


class TestStateManagement:
    """Test cases for state management."""

    def test_create_initial_state(self):
        """Test initial state creation."""
        state = create_initial_state("/test/project", "nodejs", max_retries=5)

        assert state["project_path"] == "/test/project"
        assert state["project_type"] == "nodejs"
        assert state["max_retries"] == 5
        assert state["retry_count"] == 0
        assert state["status"] == "initializing"
        assert state["validation_success"] is False
        assert state["errors"] == []
        assert state["total_cost"] == 0.0

    def test_state_updates(self):
        """Test state can be updated."""
        state = create_initial_state("/test/project")

        # Update various fields
        state["status"] = "plan_created"
        state["migration_plan"] = {"dependencies": {"express": {}}}
        state["retry_count"] = 1
        state["total_cost"] = 0.05

        assert state["status"] == "plan_created"
        assert state["migration_plan"] is not None
        assert state["retry_count"] == 1
        assert state["total_cost"] == 0.05

    def test_cost_tracking(self):
        """Test cost tracking in state."""
        state = create_initial_state("/test/project")

        # Simulate agent costs
        state["agent_costs"]["migration_planner"] = 0.01
        state["agent_costs"]["runtime_validator"] = 0.02
        state["agent_costs"]["error_analyzer"] = 0.015
        state["total_cost"] = sum(state["agent_costs"].values())

        assert state["total_cost"] == 0.045
        assert len(state["agent_costs"]) == 3


class TestWorkflowIntegration:
    """Test cases for workflow integration (mocked agents)."""

    @pytest.fixture
    def mock_agents(self):
        """Mock all agents."""
        with patch('graph.workflow.MigrationPlannerAgent') as mock_planner, \
             patch('graph.workflow.RuntimeValidatorAgent') as mock_validator, \
             patch('graph.workflow.ErrorAnalyzerAgent') as mock_analyzer, \
             patch('graph.workflow.StagingDeployerAgent') as mock_deployer:

            # Mock Migration Planner
            planner_instance = Mock()
            planner_instance.execute.return_value = {
                "status": "success",
                "migration_plan": {
                    "dependencies": {"express": {"action": "upgrade"}},
                    "project_type": "nodejs"
                },
                "cost_report": {"total_cost_usd": 0.01}
            }
            mock_planner.return_value = planner_instance

            # Mock Runtime Validator (success)
            validator_instance = Mock()
            validator_instance.execute.return_value = {
                "status": "success",
                "overall_assessment": "proceed",
                "build_success": True,
                "install_success": True,
                "runtime_success": True,
                "cost_report": {"total_cost_usd": 0.02}
            }
            mock_validator.return_value = validator_instance

            # Mock Error Analyzer
            analyzer_instance = Mock()
            analyzer_instance.execute.return_value = {
                "status": "success",
                "analysis": {
                    "error_category": "missing_dependency",
                    "fix_suggestions": []
                },
                "cost_report": {"total_cost_usd": 0.015}
            }
            mock_analyzer.return_value = analyzer_instance

            # Mock Staging Deployer
            deployer_instance = Mock()
            deployer_instance.execute.return_value = {
                "status": "success",
                "branch": "upgrade/express-5.0.0",
                "pr_url": "https://github.com/test/repo/pull/1"
            }
            mock_deployer.return_value = deployer_instance

            yield {
                "planner": mock_planner,
                "validator": mock_validator,
                "analyzer": mock_analyzer,
                "deployer": mock_deployer
            }

    def test_successful_workflow_path(self, mock_agents):
        """Test complete successful workflow path."""
        from graph.workflow import run_workflow

        # Run workflow
        final_state = run_workflow("/test/project", "nodejs", max_retries=3)

        # Verify successful completion
        assert final_state["status"] == "deployed"
        assert final_state["validation_success"] is True
        assert final_state["pr_url"] == "https://github.com/test/repo/pull/1"
        assert final_state["total_cost"] == 0.03  # planner + validator

    def test_validation_failure_workflow(self, mock_agents):
        """Test workflow with validation failure."""
        # Modify validator to fail
        validator_instance = mock_agents["validator"].return_value
        validator_instance.execute.return_value = {
            "status": "error",
            "overall_assessment": "fix",
            "build_success": True,
            "install_success": False,
            "runtime_success": False,
            "cost_report": {"total_cost_usd": 0.02}
        }

        from graph.workflow import run_workflow

        # Run workflow
        final_state = run_workflow("/test/project", "nodejs", max_retries=1)

        # Should have called error analyzer
        assert mock_agents["analyzer"].return_value.execute.called

        # Verify validation failed
        assert final_state["validation_success"] is False


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
