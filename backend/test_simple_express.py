"""Test workflow with simple_express_app project."""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from graph.workflow import run_workflow

def main():
    """Run workflow on simple_express_app."""

    print("=" * 80)
    print("TESTING WORKFLOW WITH SIMPLE EXPRESS APP")
    print("=" * 80)

    # Path to your project
    project_path = str(Path(__file__).parent / "tmp" / "projects" / "simple_express_app")

    print(f"\nProject Path: {project_path}")
    print(f"Project Type: nodejs")
    print(f"Max Retries: 3")

    print("\n" + "=" * 80)
    print("STARTING WORKFLOW")
    print("=" * 80)
    print("\nThis will execute:")
    print("  1. Migration Planner - Analyze dependencies")
    print("  2. Runtime Validator - Test in Docker")
    print("  3. Error Analyzer - If validation fails")
    print("  4. Staging Deployer - Create PR (if successful)")
    print()

    # Run workflow
    try:
        final_state = run_workflow(
            project_path=project_path,
            project_type="nodejs",
            max_retries=3
        )

        # Print results
        print("\n" + "=" * 80)
        print("WORKFLOW COMPLETE")
        print("=" * 80)

        print(f"\nFinal Status: {final_state['status']}")
        print(f"Retry Count: {final_state['retry_count']}/{final_state['max_retries']}")
        print(f"Validation Success: {final_state.get('validation_success', False)}")
        print(f"Total Cost: ${final_state['total_cost']:.4f}")

        if final_state.get('pr_url'):
            print(f"\nPR Created: {final_state['pr_url']}")

        if final_state.get('branch_name'):
            print(f"Branch: {final_state['branch_name']}")

        if final_state['errors']:
            print(f"\nErrors ({len(final_state['errors'])}):")
            for i, error in enumerate(final_state['errors'], 1):
                print(f"  {i}. {error}")

        # Print agent costs
        if final_state.get('agent_costs'):
            print(f"\nAgent Costs:")
            for agent, cost in final_state['agent_costs'].items():
                print(f"  {agent}: ${cost:.4f}")

        # Print migration plan summary
        if final_state.get('migration_plan'):
            plan = final_state['migration_plan']
            deps = plan.get('dependencies', {})
            print(f"\nMigration Plan:")
            print(f"  Dependencies to upgrade: {len(deps)}")
            print(f"  Overall risk: {plan.get('overall_risk', 'unknown')}")

            if 'migration_strategy' in plan:
                phases = plan['migration_strategy'].get('phases', [])
                print(f"  Migration phases: {len(phases)}")

        return 0

    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
