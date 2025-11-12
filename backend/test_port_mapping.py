"""Test script to verify port mapping in Docker validation."""

import os
import sys
import time
import requests

# Set environment to keep container for testing
os.environ["DOCKER_CLEANUP_CONTAINERS"] = "false"

from tools.docker_tools import DockerValidator

def main():
    print("=" * 80)
    print("PORT MAPPING TEST")
    print("=" * 80)

    validator = DockerValidator(timeout=300, cleanup_containers=False)

    print("\n1. Running Docker validation with port mapping...")
    result = validator.validate_project(
        project_path="tmp/projects/simple_express_app",
        project_type="nodejs",
        migration_plan=None
    )

    print("\n2. Validation Results:")
    print(f"   Status: {result['status']}")
    print(f"   Container ID: {result['container_id']}")
    print(f"   Container Name: {result['container_name']}")
    print(f"   Port: {result['port']}")
    print(f"   Build Success: {result['build_success']}")
    print(f"   Install Success: {result['install_success']}")
    print(f"   Runtime Success: {result['runtime_success']}")
    print(f"   Health Check Success: {result['health_check_success']}")
    print(f"   Tests Run: {result['tests_run']}")
    print(f"   Tests Passed: {result['tests_passed']}")

    if result['status'] == 'success':
        print(f"\n3. Testing browser access at http://localhost:{result['port']}...")

        # Wait a moment for server to be ready
        time.sleep(2)

        try:
            response = requests.get(f"http://localhost:{result['port']}/", timeout=5)
            print(f"   Response Status: {response.status_code}")
            print(f"   Response Body: {response.json()}")

            if response.status_code == 200:
                print("\n✓ SUCCESS: Application is accessible from browser!")
                print(f"\n   You can now open your browser and visit:")
                print(f"   - http://localhost:{result['port']}/")
                print(f"   - http://localhost:{result['port']}/health")
                print(f"   - http://localhost:{result['port']}/api/users")

                print(f"\n   Container '{result['container_name']}' is kept running for testing.")
                print(f"   To stop it: docker stop {result['container_name']}")
                return 0
            else:
                print(f"\n✗ FAILED: Unexpected status code {response.status_code}")
                return 1

        except requests.exceptions.RequestException as e:
            print(f"\n✗ FAILED: Cannot connect to application: {e}")
            return 1
    else:
        print(f"\n✗ FAILED: Validation failed")
        print(f"   Errors: {result['errors']}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
