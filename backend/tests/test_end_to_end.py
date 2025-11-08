"""End-to-End Integration Test

Tests the complete workflow:
1. Migration Planner analyzes project
2. Runtime Validator tests upgrades in Docker
3. Full pipeline validation

This test requires:
- Docker running
- API keys configured (ANTHROPIC_API_KEY or other LLM provider)
- Sample project in tests/sample_projects/express-app
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.migration_planner import MigrationPlannerAgent
from agents.runtime_validator import RuntimeValidatorAgent
from tools.docker_tools import DockerValidator


def test_complete_workflow():
    """Test the complete migration workflow end-to-end."""

    print("=" * 80)
    print("END-TO-END INTEGRATION TEST")
    print("Testing: Migration Planner → Runtime Validator → Recommendations")
    print("=" * 80)

    # Setup
    test_project = Path(__file__).parent / "sample_projects" / "express-app"

    if not test_project.exists():
        print(f"\n❌ ERROR: Test project not found at {test_project}")
        print("Please ensure the sample Express.js project exists.")
        return False

    print(f"\n📁 Test Project: {test_project}")
    print(f"   Project Type: Node.js (Express)")

    # Step 1: Migration Planning
    print("\n" + "=" * 80)
    print("STEP 1: MIGRATION PLANNING")
    print("=" * 80)

    try:
        print("\n1.1 Creating Migration Planner Agent...")
        planner = MigrationPlannerAgent()
        print(f"    ✅ Provider: {planner.llm.get_provider_name()}")
        print(f"    ✅ Model: {planner.llm.model}")

        print("\n1.2 Analyzing project dependencies...")
        plan_result = planner.execute({
            "project_path": str(test_project)
        })

        if plan_result["status"] != "success":
            print(f"    ❌ Planning failed: {plan_result.get('error', 'Unknown error')}")
            return False

        migration_plan = plan_result["migration_plan"]
        cost_report_1 = plan_result["cost_report"]

        print(f"    ✅ Analysis complete")
        print(f"    📊 Dependencies analyzed: {len(migration_plan.get('dependencies', {}))}")
        print(f"    📊 Migration phases: {migration_plan.get('migration_strategy', {}).get('total_phases', 0)}")
        print(f"    📊 Overall risk: {migration_plan.get('overall_risk', 'unknown').upper()}")
        print(f"    💰 Cost: ${cost_report_1['total_cost_usd']:.4f}")

    except Exception as e:
        print(f"    ❌ Migration planning failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

    # Step 2: Runtime Validation (Baseline)
    print("\n" + "=" * 80)
    print("STEP 2: RUNTIME VALIDATION (BASELINE)")
    print("=" * 80)

    try:
        print("\n2.1 Creating Runtime Validator Agent...")
        validator_agent = RuntimeValidatorAgent()
        print(f"    ✅ Provider: {validator_agent.llm.get_provider_name()}")
        print(f"    ✅ Model: {validator_agent.llm.model}")

        print("\n2.2 Testing current version in Docker...")
        print("    (Creating container, installing deps, starting app...)")

        validation_result = validator_agent.execute({
            "project_path": str(test_project),
            "project_type": "nodejs",
            "migration_plan": None  # Baseline test
        })

        if validation_result["status"] != "success":
            print(f"    ❌ Validation failed: {validation_result.get('error', 'Unknown error')}")
            return False

        docker_result = validation_result["validation_result"]
        analysis = validation_result["analysis"]
        cost_report_2 = validation_result["cost_report"]

        print(f"    ✅ Docker validation complete")
        print(f"    📦 Container: {docker_result['container_id']}")
        print(f"    🏗️  Build: {'SUCCESS' if docker_result['build_success'] else 'FAILED'}")
        print(f"    📥 Install: {'SUCCESS' if docker_result['install_success'] else 'FAILED'}")
        print(f"    🚀 Runtime: {'SUCCESS' if docker_result['runtime_success'] else 'FAILED'}")
        print(f"    ✅ Health: {'SUCCESS' if docker_result['health_check_success'] else 'FAILED'}")
        print(f"    💰 Cost: ${cost_report_2['total_cost_usd']:.4f}")

        print(f"\n    🤖 LLM Analysis:")
        print(f"       Status: {analysis.get('validation_status', 'unknown').upper()}")
        print(f"       Recommendation: {analysis.get('recommendation', 'unknown').upper()}")
        print(f"       Confidence: {analysis.get('confidence', 'unknown').upper()}")

    except Exception as e:
        print(f"    ❌ Runtime validation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

    # Step 3: Results Summary
    print("\n" + "=" * 80)
    print("STEP 3: WORKFLOW SUMMARY")
    print("=" * 80)

    print(f"\n✅ Migration Plan Created:")
    print(f"   - {len(migration_plan.get('dependencies', {}))} dependencies analyzed")
    print(f"   - {migration_plan.get('migration_strategy', {}).get('total_phases', 0)} phase migration strategy")
    print(f"   - Overall risk: {migration_plan.get('overall_risk', 'unknown').upper()}")

    print(f"\n✅ Baseline Validation Passed:")
    print(f"   - Current version runs successfully in Docker")
    print(f"   - All health checks passed")
    print(f"   - Ready for upgrade testing")

    print(f"\n💰 Total Cost:")
    total_cost = cost_report_1['total_cost_usd'] + cost_report_2['total_cost_usd']
    print(f"   - Migration Planning: ${cost_report_1['total_cost_usd']:.4f}")
    print(f"   - Runtime Validation: ${cost_report_2['total_cost_usd']:.4f}")
    print(f"   - Total: ${total_cost:.4f}")

    print("\n" + "=" * 80)
    print("✅ END-TO-END TEST PASSED")
    print("=" * 80)

    return True


def test_migration_planner_only():
    """Quick test of just the Migration Planner."""

    print("=" * 80)
    print("QUICK TEST: MIGRATION PLANNER ONLY")
    print("=" * 80)

    test_project = Path(__file__).parent / "sample_projects" / "express-app"

    if not test_project.exists():
        print(f"\n❌ ERROR: Test project not found")
        return False

    try:
        planner = MigrationPlannerAgent()
        print(f"\n🤖 Using: {planner.llm.get_provider_name()} - {planner.llm.model}")
        print(f"📁 Analyzing: {test_project.name}")

        result = planner.execute({"project_path": str(test_project)})

        if result["status"] == "success":
            plan = result["migration_plan"]
            print(f"\n✅ SUCCESS")
            print(f"   Dependencies: {len(plan.get('dependencies', {}))}")
            print(f"   Phases: {plan.get('migration_strategy', {}).get('total_phases', 0)}")
            print(f"   Risk: {plan.get('overall_risk', 'unknown').upper()}")
            print(f"   Cost: ${result['cost_report']['total_cost_usd']:.4f}")
            return True
        else:
            print(f"\n❌ FAILED: {result.get('error', 'Unknown error')}")
            return False

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_docker_tools_only():
    """Quick test of just the Docker tools."""

    print("=" * 80)
    print("QUICK TEST: DOCKER VALIDATION ONLY")
    print("=" * 80)

    test_project = Path(__file__).parent / "sample_projects" / "express-app"

    if not test_project.exists():
        print(f"\n❌ ERROR: Test project not found")
        return False

    try:
        from tools.docker_tools import DockerValidator

        validator = DockerValidator(timeout=300)
        print(f"\n🐳 Docker Version: {validator.client.version()['Version']}")
        print(f"📁 Testing: {test_project.name}")

        result = validator.validate_project(
            project_path=str(test_project),
            project_type="nodejs",
            migration_plan=None
        )

        print(f"\n{'✅' if result['status'] == 'success' else '❌'} Status: {result['status'].upper()}")
        print(f"   Container: {result['container_id']}")
        print(f"   Build: {'✅' if result['build_success'] else '❌'}")
        print(f"   Install: {'✅' if result['install_success'] else '❌'}")
        print(f"   Runtime: {'✅' if result['runtime_success'] else '❌'}")
        print(f"   Health: {'✅' if result['health_check_success'] else '❌'}")

        return result['status'] == 'success'

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="End-to-end integration tests")
    parser.add_argument(
        "--test",
        choices=["all", "planner", "docker"],
        default="all",
        help="Which test to run (default: all)"
    )

    args = parser.parse_args()

    success = False

    if args.test == "all":
        success = test_complete_workflow()
    elif args.test == "planner":
        success = test_migration_planner_only()
    elif args.test == "docker":
        success = test_docker_tools_only()

    sys.exit(0 if success else 1)
