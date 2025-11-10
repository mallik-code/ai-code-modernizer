"""Integration tests for complete LangGraph workflow.

These tests execute the full workflow with real or mocked agents.
"""

import os
import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from graph.workflow import run_workflow
from graph.state import create_initial_state


# Skip tests if no API keys available
SKIP_INTEGRATION = not (os.getenv("ANTHROPIC_API_KEY") or os.getenv("GOOGLE_API_KEY"))
SKIP_REASON = "No API keys found. Set ANTHROPIC_API_KEY or GOOGLE_API_KEY to run integration tests."


@pytest.mark.skipif(SKIP_INTEGRATION, reason=SKIP_REASON)
class TestWorkflowIntegration:
    """Integration tests for complete workflow (requires API keys + Docker)."""

    @pytest.fixture
    def sample_project_path(self):
        """Path to sample Express.js project."""
        return str(Path(__file__).parent / "sample_projects" / "express-app")

    def test_workflow_structure_only(self):
        """Test workflow graph structure (no execution)."""
        from graph.workflow import create_workflow

        # Create workflow
        workflow = create_workflow()
        app = workflow.compile()

        assert app is not None
        print("\n[OK] Workflow graph structure validated")

    @pytest.mark.slow
    @pytest.mark.integration
    def test_full_workflow_execution(self, sample_project_path):
        """Test complete workflow execution with real agents.

        WARNING: This test:
        - Requires API keys (Anthropic or Gemini)
        - Requires Docker running
        - Takes ~2-3 minutes
        - Costs ~$0.01-0.05 depending on provider
        """
        # Verify sample project exists
        if not Path(sample_project_path).exists():
            pytest.skip(f"Sample project not found: {sample_project_path}")

        print(f"\n[INFO] Running full workflow on: {sample_project_path}")
        print("[INFO] This may take 2-3 minutes...")

        # Run workflow
        final_state = run_workflow(
            project_path=sample_project_path,
            project_type="nodejs",
            max_retries=2
        )

        # Print results
        print("\n" + "=" * 80)
        print("WORKFLOW RESULTS")
        print("=" * 80)
        print(f"  Final Status: {final_state['status']}")
        print(f"  Retry Count: {final_state['retry_count']}/{final_state['max_retries']}")
        print(f"  Validation Success: {final_state.get('validation_success', False)}")
        print(f"  Total Cost: ${final_state['total_cost']:.4f}")

        if final_state.get('pr_url'):
            print(f"  PR URL: {final_state['pr_url']}")
        if final_state.get('branch_name'):
            print(f"  Branch: {final_state['branch_name']}")

        if final_state['errors']:
            print(f"\n  Errors ({len(final_state['errors'])}):")
            for i, error in enumerate(final_state['errors'], 1):
                print(f"    {i}. {error}")

        # Assertions
        assert final_state['status'] in ['deployed', 'validated', 'validation_failed', 'error', 'analyzed']
        assert final_state['total_cost'] > 0  # Should have some LLM cost
        assert 'migration_planner' in final_state.get('agent_costs', {})

        print("\n[OK] Full workflow integration test complete")

    @pytest.mark.quick
    def test_workflow_with_mocked_agents(self, sample_project_path):
        """Test workflow with mocked agents (fast, no API keys needed)."""
        from unittest.mock import patch, Mock

        # Mock all agents
        with patch('graph.workflow.MigrationPlannerAgent') as mock_planner, \
             patch('graph.workflow.RuntimeValidatorAgent') as mock_validator, \
             patch('graph.workflow.StagingDeployerAgent') as mock_deployer:

            # Mock Migration Planner
            planner_instance = Mock()
            planner_instance.execute.return_value = {
                "status": "success",
                "migration_plan": {
                    "dependencies": {
                        "express": {
                            "current_version": "4.16.0",
                            "target_version": "4.19.2",
                            "action": "upgrade",
                            "risk": "low"
                        }
                    },
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
                "health_check_success": True,
                "cost_report": {"total_cost_usd": 0.02}
            }
            mock_validator.return_value = validator_instance

            # Mock Staging Deployer
            deployer_instance = Mock()
            deployer_instance.execute.return_value = {
                "status": "success",
                "branch": "upgrade/express-4.19.2",
                "pr_url": "https://github.com/test/repo/pull/1"
            }
            mock_deployer.return_value = deployer_instance

            # Run workflow
            final_state = run_workflow(
                project_path=sample_project_path,
                project_type="nodejs",
                max_retries=2
            )

            # Verify
            assert final_state['status'] == 'deployed'
            assert final_state['validation_success'] is True
            assert final_state['pr_url'] == 'https://github.com/test/repo/pull/1'
            assert final_state['total_cost'] == 0.03

            print("\n[OK] Mocked workflow test complete")


def main():
    """Run integration tests with reporting."""
    print("=" * 80)
    print("WORKFLOW INTEGRATION TESTS")
    print("=" * 80)

    # Check environment
    if SKIP_INTEGRATION:
        print(f"\n[SKIP] {SKIP_REASON}")
        print("[INFO] Running structure-only tests...")

        # Just test structure
        from graph.workflow import create_workflow
        workflow = create_workflow()
        app = workflow.compile()
        print("[OK] Workflow graph compiles successfully!")

    else:
        print("\n[INFO] API keys found. Running full integration tests...")
        print("[WARNING] This will:")
        print("  - Use real LLM API calls (~$0.01-0.05)")
        print("  - Require Docker running")
        print("  - Take 2-3 minutes")

        # Run pytest with integration tests
        pytest.main([__file__, "-v", "-m", "integration or quick"])


if __name__ == "__main__":
    main()
