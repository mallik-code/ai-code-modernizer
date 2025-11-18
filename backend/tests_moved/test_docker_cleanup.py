"""Test Docker cleanup flag functionality."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from tools.docker_tools import DockerValidator

def main():
    """Test Docker cleanup configuration."""

    print("=" * 80)
    print("TESTING DOCKER CLEANUP FLAG")
    print("=" * 80)

    # Test project
    project_path = str(Path(__file__).parent / "tmp" / "projects" / "simple_express_app")

    # Test 1: With cleanup enabled (default)
    print("\n--- TEST 1: Cleanup Enabled (default) ---")
    print("Setting DOCKER_CLEANUP_CONTAINERS=true")
    os.environ["DOCKER_CLEANUP_CONTAINERS"] = "true"

    validator1 = DockerValidator()
    print(f"Cleanup enabled: {validator1.cleanup_containers}")

    print("\nRunning validation...")
    result1 = validator1.validate_project(
        project_path=project_path,
        project_type="nodejs",
        migration_plan=None
    )

    print(f"Validation status: {result1['status']}")
    print(f"Container ID: {result1['container_id']}")
    print("Container should be REMOVED after validation")

    # Test 2: With cleanup disabled
    print("\n" + "=" * 80)
    print("\n--- TEST 2: Cleanup Disabled ---")
    print("Setting DOCKER_CLEANUP_CONTAINERS=false")
    os.environ["DOCKER_CLEANUP_CONTAINERS"] = "false"

    validator2 = DockerValidator()
    print(f"Cleanup enabled: {validator2.cleanup_containers}")

    print("\nRunning validation...")
    result2 = validator2.validate_project(
        project_path=project_path,
        project_type="nodejs",
        migration_plan=None
    )

    print(f"Validation status: {result2['status']}")
    print(f"Container ID: {result2['container_id']}")
    print("Container should be KEPT for debugging")

    # Show container list
    print("\n" + "=" * 80)
    print("Current Docker Containers:")
    print("=" * 80)

    import docker
    client = docker.from_env()
    containers = client.containers.list(all=True, filters={"ancestor": "node:18-alpine"})

    if containers:
        print(f"\nFound {len(containers)} node:18-alpine container(s):")
        for c in containers:
            print(f"  ID: {c.id[:12]}")
            print(f"  Status: {c.status}")
            print(f"  Name: {c.name}")
            print()
    else:
        print("\nNo node:18-alpine containers found")

    print("\nTo manually cleanup the kept container, run:")
    if result2['container_id']:
        print(f"  docker stop {result2['container_id']} && docker rm {result2['container_id']}")

    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())
