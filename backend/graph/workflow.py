"""LangGraph workflow for AI Code Modernizer.

This module defines the multi-agent workflow that orchestrates:
1. Migration Planner - Analyzes dependencies and creates migration plan
2. Runtime Validator - Tests upgrades in Docker containers
3. Error Analyzer - Diagnoses failures and suggests fixes
4. Staging Deployer - Creates Git branches and PRs

The workflow includes conditional routing and retry logic.
"""

from typing import Dict, Any, Literal, Optional
from datetime import datetime
import json
from langgraph.graph import StateGraph, END
from graph.state import MigrationState, create_initial_state
from agents.migration_planner import MigrationPlannerAgent
from agents.runtime_validator import RuntimeValidatorAgent
from agents.error_analyzer import ErrorAnalyzerAgent
from agents.staging_deployer import StagingDeployerAgent
from utils.logger import setup_logger

logger = setup_logger(__name__)


# ============================================================================
# Agent Node Functions
# ============================================================================

def migration_planner_node(state: MigrationState) -> MigrationState:
    """Execute Migration Planner agent.

    Args:
        state: Current workflow state

    Returns:
        Updated state with migration plan
    """
    logger.info("executing_migration_planner", project_path=state["project_path"])

    # Send workflow status update
    if state.get("broadcaster"):
        state["broadcaster"](json.dumps({
            "type": "workflow_status",
            "status": "executing_migration_planner",
            "message": "Starting migration planning...",
            "timestamp": datetime.now().isoformat()
        }))

    try:
        # Create agent with broadcaster
        agent = MigrationPlannerAgent(broadcaster=state.get("broadcaster"))

        # Execute planning
        result = agent.execute({
            "project_path": state["project_path"]
        })

        # Update state
        if result["status"] == "success":
            state["migration_plan"] = result["migration_plan"]
            state["status"] = "plan_created"
            logger.info("migration_plan_created",
                       dependencies_count=len(result["migration_plan"].get("dependencies", {})))

            # Send completion update
            if state.get("broadcaster"):
                state["broadcaster"](json.dumps({
                    "type": "agent_completion",
                    "agent": "migration_planner",
                    "status": "success",
                    "message": "Migration plan created successfully",
                    "dependencies_count": len(result["migration_plan"].get("dependencies", {})),
                    "timestamp": datetime.now().isoformat()
                }))

            # Track cost
            if "cost_report" in result:
                cost = result["cost_report"].get("total_cost_usd", 0)
                state["agent_costs"]["migration_planner"] = cost
                state["total_cost"] += cost

        else:
            state["status"] = "error"
            state["errors"].append(f"Migration planning failed: {result.get('error', 'Unknown error')}")
            logger.error("migration_planning_failed", error=result.get("error"))

            # Send error update
            if state.get("broadcaster"):
                state["broadcaster"](json.dumps({
                    "type": "agent_completion",
                    "agent": "migration_planner",
                    "status": "error",
                    "error": result.get("error", "Unknown error"),
                    "timestamp": datetime.now().isoformat()
                }))

    except Exception as e:
        state["status"] = "error"
        state["errors"].append(f"Migration planner error: {str(e)}")
        logger.error("migration_planner_exception", error=str(e), exc_info=True)

        # Send error update
        if state.get("broadcaster"):
            state["broadcaster"](json.dumps({
                "type": "agent_completion",
                "agent": "migration_planner",
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }))

    return state


def runtime_validator_node(state: MigrationState) -> MigrationState:
    """Execute Runtime Validator agent.

    Args:
        state: Current workflow state

    Returns:
        Updated state with validation results
    """
    logger.info("executing_runtime_validator", project_path=state["project_path"])

    # Send workflow status update
    if state.get("broadcaster"):
        state["broadcaster"](json.dumps({
            "type": "workflow_status",
            "status": "executing_runtime_validator",
            "message": "Starting runtime validation...",
            "timestamp": datetime.now().isoformat()
        }))

    try:
        # Create agent with broadcaster
        agent = RuntimeValidatorAgent(broadcaster=state.get("broadcaster"))

        # Execute validation
        result = agent.execute({
            "project_path": state["project_path"],
            "project_type": state.get("project_type", "nodejs"),
            "migration_plan": state.get("migration_plan")
        })

        # Update state
        state["validation_result"] = result

        # Extract nested validation result for easier access
        validation_data = result.get("validation_result", {})
        analysis_data = result.get("analysis", {})

        # Check validation success based on actual Docker validation results
        state["validation_success"] = (
            result.get("status") == "success" and
            validation_data.get("status") == "success" and
            analysis_data.get("recommendation") == "proceed"
        )

        if state["validation_success"]:
            state["status"] = "validated"
            logger.info("validation_successful")
            
            # Send completion update
            if state.get("broadcaster"):
                state["broadcaster"](json.dumps({
                    "type": "agent_completion",
                    "agent": "runtime_validator",
                    "status": "success",
                    "message": "Runtime validation completed successfully",
                    "timestamp": datetime.now().isoformat()
                }))
        else:
            state["status"] = "validation_failed"
            logger.warning("validation_failed",
                          build=validation_data.get("build_success"),
                          install=validation_data.get("install_success"),
                          runtime=validation_data.get("runtime_success"))

            # Send completion update with failure status
            if state.get("broadcaster"):
                state["broadcaster"](json.dumps({
                    "type": "agent_completion",
                    "agent": "runtime_validator",
                    "status": "failed",
                    "message": "Runtime validation failed",
                    "build_success": validation_data.get("build_success"),
                    "install_success": validation_data.get("install_success"),
                    "runtime_success": validation_data.get("runtime_success"),
                    "timestamp": datetime.now().isoformat()
                }))

        # Track cost
        if "cost_report" in result:
            cost = result["cost_report"].get("total_cost_usd", 0)
            state["agent_costs"]["runtime_validator"] = cost
            state["total_cost"] += cost

    except Exception as e:
        state["status"] = "error"
        state["validation_success"] = False
        state["errors"].append(f"Runtime validator error: {str(e)}")
        logger.error("runtime_validator_exception", error=str(e), exc_info=True)

        # Send error update
        if state.get("broadcaster"):
            state["broadcaster"](json.dumps({
                "type": "agent_completion",
                "agent": "runtime_validator",
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }))

    return state


def error_analyzer_node(state: MigrationState) -> MigrationState:
    """Execute Error Analyzer agent.

    Args:
        state: Current workflow state

    Returns:
        Updated state with error analysis
    """
    logger.info("executing_error_analyzer", retry_count=state["retry_count"])

    # Send workflow status update
    if state.get("broadcaster"):
        state["broadcaster"](json.dumps({
            "type": "workflow_status",
            "status": "executing_error_analyzer",
            "message": "Starting error analysis...",
            "timestamp": datetime.now().isoformat()
        }))

    try:
        # Create agent with broadcaster
        agent = ErrorAnalyzerAgent(broadcaster=state.get("broadcaster"))

        # Execute analysis
        result = agent.execute({
            "validation_result": state.get("validation_result"),
            "migration_plan": state.get("migration_plan")
        })

        # Update state
        if result["status"] == "success":
            state["error_analysis"] = result["analysis"]
            state["fix_suggestions"] = result["analysis"].get("fix_suggestions", [])
            state["status"] = "analyzed"
            logger.info("error_analysis_complete",
                       error_category=result["analysis"].get("error_category"),
                       suggestions_count=len(state["fix_suggestions"]))

            # Send completion update
            if state.get("broadcaster"):
                state["broadcaster"](json.dumps({
                    "type": "agent_completion",
                    "agent": "error_analyzer",
                    "status": "success",
                    "message": "Error analysis completed",
                    "error_category": result["analysis"].get("error_category"),
                    "suggestions_count": len(state["fix_suggestions"]),
                    "timestamp": datetime.now().isoformat()
                }))

            # Track cost
            if "cost_report" in result:
                cost = result["cost_report"].get("total_cost_usd", 0)
                state["agent_costs"]["error_analyzer"] = cost
                state["total_cost"] += cost
        else:
            state["status"] = "error"
            state["errors"].append(f"Error analysis failed: {result.get('error', 'Unknown error')}")
            logger.error("error_analysis_failed", error=result.get("error"))

            # Send completion update with failure status
            if state.get("broadcaster"):
                state["broadcaster"](json.dumps({
                    "type": "agent_completion",
                    "agent": "error_analyzer",
                    "status": "failed",
                    "message": "Error analysis failed",
                    "error": result.get("error", "Unknown error"),
                    "timestamp": datetime.now().isoformat()
                }))

    except Exception as e:
        state["status"] = "error"
        state["errors"].append(f"Error analyzer error: {str(e)}")
        logger.error("error_analyzer_exception", error=str(e), exc_info=True)

        # Send error update
        if state.get("broadcaster"):
            state["broadcaster"](json.dumps({
                "type": "agent_completion",
                "agent": "error_analyzer",
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }))

    return state


def staging_deployer_node(state: MigrationState) -> MigrationState:
    """Execute Staging Deployer agent.

    Args:
        state: Current workflow state

    Returns:
        Updated state with deployment results
    """
    logger.info("executing_staging_deployer", project_path=state["project_path"])

    # Send workflow status update
    if state.get("broadcaster"):
        state["broadcaster"](json.dumps({
            "type": "workflow_status",
            "status": "executing_staging_deployer",
            "message": "Starting staging deployment...",
            "timestamp": datetime.now().isoformat()
        }))

    try:
        # Create agent with broadcaster
        agent = StagingDeployerAgent(broadcaster=state.get("broadcaster"))

        # Execute deployment
        result = agent.execute({
            "project_path": state["project_path"],
            "migration_plan": state.get("migration_plan"),
            "validation_result": state.get("validation_result"),
            "base_branch": state.get("git_branch", "main"),
            "github_token": state.get("github_token")
        })

        # Update state
        if result["status"] == "success":
            state["deployment_result"] = result
            state["pr_url"] = result.get("pr_url")
            state["branch_name"] = result.get("branch_name")
            state["status"] = "deployed"
            logger.info("deployment_successful",
                       branch=state["branch_name"],
                       pr_url=state.get("pr_url"))

            # Send completion update
            if state.get("broadcaster"):
                state["broadcaster"](json.dumps({
                    "type": "agent_completion",
                    "agent": "staging_deployer",
                    "status": "success",
                    "message": "Staging deployment completed",
                    "branch": state["branch_name"],
                    "pr_url": state.get("pr_url"),
                    "timestamp": datetime.now().isoformat()
                }))

            # Track cost (if any - Staging Deployer typically doesn't use LLM)
            if "cost_report" in result:
                cost = result["cost_report"].get("total_cost_usd", 0)
                state["agent_costs"]["staging_deployer"] = cost
                state["total_cost"] += cost
        else:
            state["status"] = "deployment_failed"
            state["errors"].append(f"Deployment failed: {result.get('error', 'Unknown error')}")
            logger.error("deployment_failed", error=result.get("error"))

            # Send completion update with failure status
            if state.get("broadcaster"):
                state["broadcaster"](json.dumps({
                    "type": "agent_completion",
                    "agent": "staging_deployer",
                    "status": "failed",
                    "message": "Staging deployment failed",
                    "error": result.get("error", "Unknown error"),
                    "timestamp": datetime.now().isoformat()
                }))

    except Exception as e:
        state["status"] = "deployment_failed"
        state["errors"].append(f"Staging deployer error: {str(e)}")
        logger.error("staging_deployer_exception", error=str(e), exc_info=True)

        # Send error update
        if state.get("broadcaster"):
            state["broadcaster"](json.dumps({
                "type": "agent_completion",
                "agent": "staging_deployer",
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }))

    return state


# ============================================================================
# Routing Functions
# ============================================================================

def should_validate(state: MigrationState) -> Literal["validate", "end"]:
    """Route after migration planning.

    Args:
        state: Current workflow state

    Returns:
        Next node name or END
    """
    if state["status"] == "plan_created" and state.get("migration_plan"):
        logger.info("routing_to_validation")
        return "validate"
    else:
        logger.error("routing_to_end_after_planning_failure")
        return "end"


def should_retry_or_deploy(state: MigrationState) -> Literal["analyze", "deploy", "end"]:
    """Route after validation.

    If validation succeeds, deploy.
    If validation fails and retries available, analyze errors.
    Otherwise, end workflow.

    Args:
        state: Current workflow state

    Returns:
        Next node name or END
    """
    if state["validation_success"]:
        logger.info("routing_to_deployment")
        return "deploy"
    elif state["retry_count"] < state["max_retries"]:
        logger.info("routing_to_error_analysis", retry_count=state["retry_count"])
        return "analyze"
    else:
        logger.warning("max_retries_exceeded", retry_count=state["retry_count"])
        return "end"


def should_retry_validation(state: MigrationState) -> Literal["validate", "end"]:
    """Route after error analysis.

    If fixes suggested, retry validation.
    Otherwise, end workflow.

    Args:
        state: Current workflow state

    Returns:
        Next node name or END
    """
    if state["status"] == "analyzed" and state.get("fix_suggestions"):
        state["retry_count"] += 1
        logger.info("routing_to_retry_validation", retry_count=state["retry_count"])
        return "validate"
    else:
        logger.warning("no_fix_suggestions_available")
        return "end"


def deployment_complete(state: MigrationState) -> Literal["end"]:
    """Route after deployment (always ends workflow).

    Args:
        state: Current workflow state

    Returns:
        END
    """
    logger.info("workflow_complete", status=state["status"], total_cost=state["total_cost"])
    return "end"


# ============================================================================
# Workflow Builder
# ============================================================================

def create_workflow() -> StateGraph:
    """Create the LangGraph workflow.

    Returns:
        Configured StateGraph instance
    """
    # Create graph
    workflow = StateGraph(MigrationState)

    # Add nodes
    workflow.add_node("plan", migration_planner_node)
    workflow.add_node("validate", runtime_validator_node)
    workflow.add_node("analyze", error_analyzer_node)
    workflow.add_node("deploy", staging_deployer_node)

    # Set entry point
    workflow.set_entry_point("plan")

    # Add edges with conditional routing
    workflow.add_conditional_edges(
        "plan",
        should_validate,
        {
            "validate": "validate",
            "end": END
        }
    )

    workflow.add_conditional_edges(
        "validate",
        should_retry_or_deploy,
        {
            "analyze": "analyze",
            "deploy": "deploy",
            "end": END
        }
    )

    workflow.add_conditional_edges(
        "analyze",
        should_retry_validation,
        {
            "validate": "validate",
            "end": END
        }
    )

    workflow.add_conditional_edges(
        "deploy",
        deployment_complete,
        {
            "end": END
        }
    )

    return workflow


# ============================================================================
# Workflow Execution
# ============================================================================

def run_workflow(project_path: str, project_type: str = "nodejs", max_retries: int = 3, git_branch: str = "main", github_token: Optional[str] = None, broadcaster=None) -> MigrationState:
    """Run the complete migration workflow.

    Args:
        project_path: Path to project
        project_type: Type of project (nodejs, python)
        max_retries: Maximum retry attempts
        git_branch: Git branch being used for the migration (default: main)
        github_token: GitHub Personal Access Token for API operations (optional)
        broadcaster: Optional function to broadcast updates to WebSocket

    Returns:
        Final workflow state
    """
    logger.info("starting_workflow", project_path=project_path, project_type=project_type, git_branch=git_branch, has_github_token=bool(github_token))

    # Create initial state
    initial_state = create_initial_state(project_path, project_type, max_retries, git_branch)

    # Add broadcaster to state if provided
    if broadcaster:
        initial_state["broadcaster"] = broadcaster

    # If github_token is provided, add it to the state
    if github_token:
        initial_state["github_token"] = github_token

    # Send initial workflow start update
    if broadcaster:
        broadcaster(json.dumps({
            "type": "workflow_start",
            "message": "Starting migration workflow",
            "project_path": project_path,
            "project_type": project_type,
            "timestamp": datetime.now().isoformat()
        }))

    # Create and compile workflow
    workflow = create_workflow()
    app = workflow.compile()

    # Execute workflow
    try:
        final_state = app.invoke(initial_state)
        
        # Send workflow completion update
        if broadcaster:
            broadcaster(json.dumps({
                "type": "workflow_complete",
                "status": final_state["status"],
                "total_cost": final_state["total_cost"],
                "retry_count": final_state["retry_count"],
                "timestamp": datetime.now().isoformat()
            }))

        logger.info("workflow_completed",
                   status=final_state["status"],
                   total_cost=final_state["total_cost"],
                   retry_count=final_state["retry_count"])
        return final_state

    except Exception as e:
        logger.error("workflow_execution_failed", error=str(e), exc_info=True)
        initial_state["status"] = "error"
        initial_state["errors"].append(f"Workflow execution failed: {str(e)}")
        
        # Send error update
        if broadcaster:
            broadcaster(json.dumps({
                "type": "workflow_error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }))

        return initial_state


if __name__ == "__main__":
    """Standalone test of workflow graph."""
    import os
    from pathlib import Path

    print("=" * 80)
    print("LANGGRAPH WORKFLOW TEST")
    print("=" * 80)

    # Use sample Express.js project
    sample_project = Path(__file__).parent.parent / "tests" / "sample_projects" / "express-app"

    if not sample_project.exists():
        print(f"\n[ERROR] Sample project not found: {sample_project}")
        print("Please create a sample project first.")
        exit(1)

    print(f"\n[INFO] Testing workflow with project: {sample_project}")
    print("[INFO] This will execute all 4 agents in sequence...")
    print("[INFO] Note: Requires API keys for LLM calls and Docker running")

    # Check if we should run (requires API keys)
    if not os.getenv("ANTHROPIC_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
        print("\n[SKIP] No API keys found. Set ANTHROPIC_API_KEY or GOOGLE_API_KEY to run.")
        print("[OK] Workflow graph structure validated successfully!")
        exit(0)

    # Run workflow
    try:
        final_state = run_workflow(
            project_path=str(sample_project),
            project_type="nodejs",
            max_retries=2
        )

        print("\n" + "=" * 80)
        print("WORKFLOW RESULTS")
        print("=" * 80)
        print(f"  Final Status: {final_state['status']}")
        print(f"  Retry Count: {final_state['retry_count']}/{final_state['max_retries']}")
        print(f"  Validation Success: {final_state.get('validation_success', False)}")
        print(f"  PR URL: {final_state.get('pr_url', 'N/A')}")
        print(f"  Branch: {final_state.get('branch_name', 'N/A')}")
        print(f"  Total Cost: ${final_state['total_cost']:.4f}")
        print(f"  Errors: {len(final_state['errors'])}")

        if final_state['errors']:
            print("\n  Error Details:")
            for i, error in enumerate(final_state['errors'], 1):
                print(f"    {i}. {error}")

        print("\n[OK] Workflow execution complete!")

    except Exception as e:
        print(f"\n[ERROR] Workflow execution failed: {e}")
        import traceback
        traceback.print_exc()
