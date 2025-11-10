"""Test Migration Planner only with simple_express_app."""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from agents.migration_planner import MigrationPlannerAgent

def main():
    """Test Migration Planner on simple_express_app."""

    print("=" * 80)
    print("TESTING MIGRATION PLANNER - SIMPLE EXPRESS APP")
    print("=" * 80)

    # Path to your project
    project_path = str(Path(__file__).parent / "tmp" / "projects" / "simple_express_app")

    print(f"\nProject: {project_path}")

    # Create agent
    print("\nCreating Migration Planner Agent...")
    agent = MigrationPlannerAgent()
    print(f"  Provider: {agent.llm.get_provider_name()}")
    print(f"  Model: {agent.llm.model}")

    # Execute analysis
    print("\nAnalyzing dependencies...")
    result = agent.execute({"project_path": project_path})

    # Display results
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)

    if result["status"] == "error":
        print(f"\nERROR: {result['error']}")
        return 1

    plan = result["migration_plan"]

    print(f"\nProject Type: {plan.get('project_type', 'unknown').upper()}")
    print(f"Overall Risk: {plan.get('overall_risk', 'unknown').upper()}")
    print(f"Estimated Time: {plan.get('estimated_total_time', 'unknown')}")

    # Dependencies
    deps = plan.get('dependencies', {})
    print(f"\n--- DEPENDENCIES ({len(deps)}) ---")
    for pkg_name, pkg_info in deps.items():
        action = pkg_info.get('action', 'unknown')
        risk = pkg_info.get('risk', '?')
        current = pkg_info.get('current_version', '?')
        target = pkg_info.get('target_version', '?')

        print(f"\n{pkg_name}:")
        print(f"  Action: {action.upper()}")
        print(f"  Current: {current} -> Target: {target}")
        print(f"  Risk: {risk.upper()}")

        if pkg_info.get('breaking_changes'):
            print(f"  Breaking Changes:")
            for change in pkg_info['breaking_changes'][:3]:  # Show first 3
                print(f"    - {change}")

    # Migration Strategy
    strategy = plan.get('migration_strategy', {})
    phases = strategy.get('phases', [])
    print(f"\n--- MIGRATION STRATEGY ({len(phases)} phases) ---")
    for phase in phases:
        print(f"\nPhase {phase.get('phase', '?')}: {phase.get('name', 'Unknown')}")
        print(f"  Dependencies: {', '.join(phase.get('dependencies', []))}")
        print(f"  Time: {phase.get('estimated_time', 'unknown')}")

    # Cost Report
    print("\n" + "=" * 80)
    print("COST REPORT")
    print("=" * 80)
    cost_report = result["cost_report"]
    print(f"Total Cost: ${cost_report['total_cost_usd']:.4f}")
    print(f"Total Tokens: {cost_report['total_input_tokens'] + cost_report['total_output_tokens']:,}")

    # Save plan to file
    output_file = Path(__file__).parent / "migration_plan_output.json"
    with open(output_file, 'w') as f:
        json.dump(plan, f, indent=2)
    print(f"\nFull plan saved to: {output_file}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
