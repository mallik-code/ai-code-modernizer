"""Test Docker upgrade functionality."""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from tools.docker_tools import DockerValidator

def main():
    """Test Docker upgrade."""

    print("=" * 80)
    print("TESTING DOCKER UPGRADE")
    print("=" * 80)

    # Load migration plan
    with open("migration_plan_output.json") as f:
        migration_plan = json.load(f)

    project_path = str(Path(__file__).parent / "tmp" / "projects" / "simple_express_app")

    print(f"\nProject: {project_path}")
    print(f"Dependencies to upgrade: {len(migration_plan.get('dependencies', {}))}")

    # Show what will be upgraded
    print("\nUpgrades:")
    for pkg, info in migration_plan.get('dependencies', {}).items():
        print(f"  {pkg}: {info.get('current_version')} -> {info.get('target_version')}")

    print("\nCreating Docker validator...")
    validator = DockerValidator(cleanup_containers=False)

    print("\nRunning validation with migration plan...")
    result = validator.validate_project(
        project_path=project_path,
        project_type="nodejs",
        migration_plan=migration_plan
    )

    print("\n" + "=" * 80)
    print("VALIDATION RESULTS")
    print("=" * 80)
    print(f"Status: {result['status']}")
    print(f"Container: {result['container_name']}")
    print(f"Build: {'SUCCESS' if result['build_success'] else 'FAILED'}")
    print(f"Install: {'SUCCESS' if result['install_success'] else 'FAILED'}")
    print(f"Runtime: {'SUCCESS' if result['runtime_success'] else 'FAILED'}")
    print(f"Health Check: {'SUCCESS' if result['health_check_success'] else 'FAILED'}")

    if result.get('errors'):
        print(f"\nErrors: {len(result['errors'])}")
        for error in result['errors']:
            print(f"  - {error}")

    # Now check what's actually in the container
    print("\n" + "=" * 80)
    print("CHECKING CONTAINER PACKAGE.JSON")
    print("=" * 80)

    import docker
    client = docker.from_env()
    container = client.containers.get(result['container_name'])

    exit_code, output = container.exec_run("cat /app/package.json")
    if exit_code == 0:
        package_data = json.loads(output.decode())
        print("\nDependencies in container:")
        for pkg in ['express', 'body-parser', 'cors', 'dotenv', 'morgan']:
            version = package_data.get('dependencies', {}).get(pkg, 'N/A')
            print(f"  {pkg}: {version}")

        print("\nDevDependencies in container:")
        for pkg in ['nodemon']:
            version = package_data.get('devDependencies', {}).get(pkg, 'N/A')
            print(f"  {pkg}: {version}")

        # Compare with migration plan
        print("\n" + "=" * 80)
        print("VERIFICATION")
        print("=" * 80)

        all_match = True
        for pkg, info in migration_plan.get('dependencies', {}).items():
            target = info.get('target_version')
            actual = package_data.get('dependencies', {}).get(pkg) or package_data.get('devDependencies', {}).get(pkg)

            if actual == target:
                print(f"✓ {pkg}: {target} (CORRECT)")
            else:
                print(f"✗ {pkg}: Expected {target}, got {actual} (WRONG)")
                all_match = False

        if all_match:
            print("\n✓✓✓ ALL VERSIONS CORRECT! ✓✓✓")
        else:
            print("\n✗✗✗ VERSION MISMATCH! ✗✗✗")

    return 0


if __name__ == "__main__":
    sys.exit(main())
