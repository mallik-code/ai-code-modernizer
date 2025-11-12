"""Docker Validation Tools

Provides utilities for creating Docker containers, installing dependencies,
running applications, and validating upgrades in isolated environments.

Capabilities:
- Create containers from project code
- Install Node.js/Python dependencies
- Start applications (Express, Flask, etc.)
- Run health checks
- Collect logs and error output
- Automatic cleanup
"""

import os
import sys
import time
import tarfile
import io
import tempfile
from typing import Dict, List, Optional, Tuple
from pathlib import Path

try:
    import docker
    from docker.models.containers import Container
    from docker.errors import DockerException, ImageNotFound, ContainerError
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False
    Container = None

from utils.logger import setup_logger


class DockerValidator:
    """Docker-based validation for dependency upgrades."""

    def __init__(self, timeout: int = 300, cleanup_containers: Optional[bool] = None):
        """Initialize Docker validator.

        Args:
            timeout: Maximum time in seconds for operations (default: 300)
            cleanup_containers: Whether to cleanup containers after validation.
                              If None, reads from DOCKER_CLEANUP_CONTAINERS env var (default: True)

        Raises:
            RuntimeError: If Docker is not available
        """
        if not DOCKER_AVAILABLE:
            raise RuntimeError("Docker SDK not installed. Run: pip install docker")

        self.timeout = timeout
        self.logger = setup_logger("docker_validator")
        self.containers: List[Container] = []

        # Read cleanup setting from env var or use provided value
        if cleanup_containers is None:
            cleanup_env = os.getenv("DOCKER_CLEANUP_CONTAINERS", "true").lower()
            self.cleanup_containers = cleanup_env in ("true", "1", "yes")
        else:
            self.cleanup_containers = cleanup_containers

        try:
            self.client = docker.from_env()
            # Test connection
            self.client.ping()
            self.logger.info("docker_connected", version=self.client.version()["Version"])
        except DockerException as e:
            self.logger.error("docker_connection_failed", error=str(e))
            raise RuntimeError(f"Docker not available: {str(e)}")

    def validate_project(
        self,
        project_path: str,
        project_type: str,
        migration_plan: Optional[Dict] = None
    ) -> Dict:
        """Validate project with optional dependency upgrades.

        Args:
            project_path: Path to project directory
            project_type: "nodejs" or "python"
            migration_plan: Optional migration plan with upgraded dependencies

        Returns:
            Dictionary with validation results:
            {
                "status": "success" | "error",
                "container_id": "...",
                "container_name": "...",
                "port": int,  # Port exposed to host for browser access (3000 for nodejs, 5000 for python)
                "build_success": bool,
                "install_success": bool,
                "runtime_success": bool,
                "health_check_success": bool,
                "tests_run": bool,
                "tests_passed": bool,
                "logs": {
                    "install": "...",
                    "startup": "...",
                    "health_check": {...},
                    "tests": {
                        "success": bool,
                        "tests_found": bool,
                        "exit_code": int,
                        "output": "...",
                        "test_summary": "..."
                    }
                },
                "errors": [...]
            }
        """
        self.logger.info("starting_validation",
                        project_path=project_path,
                        project_type=project_type,
                        has_migration_plan=migration_plan is not None)

        result = {
            "status": "error",
            "container_id": None,
            "container_name": None,
            "port": None,
            "build_success": False,
            "install_success": False,
            "runtime_success": False,
            "health_check_success": False,
            "tests_run": False,
            "tests_passed": False,
            "logs": {},
            "errors": []
        }

        container = None
        try:
            # Create container
            container, image_name, app_port = self._create_container(project_path, project_type)
            result["container_id"] = container.id[:12]
            result["container_name"] = container.name
            result["port"] = app_port
            result["build_success"] = True
            self.logger.info("container_created", container_id=result["container_id"], name=result["container_name"])

            # Copy project files
            self._copy_project_to_container(container, project_path)
            self.logger.info("project_copied", container_id=result["container_id"])

            # Apply migration plan if provided
            if migration_plan:
                self._apply_migration_plan(container, project_type, migration_plan)
                self.logger.info("migration_applied", container_id=result["container_id"])

            # Install dependencies
            install_output = self._install_dependencies(container, project_type)
            result["logs"]["install"] = install_output
            result["install_success"] = True
            self.logger.info("dependencies_installed", container_id=result["container_id"])

            # Start application
            app_output = self._start_application(container, project_type, project_path)
            result["logs"]["startup"] = app_output
            result["runtime_success"] = True
            self.logger.info("application_started", container_id=result["container_id"])

            # Run health checks
            health_result = self._run_health_check(container, project_type)
            result["logs"]["health_check"] = health_result
            result["health_check_success"] = health_result.get("success", False)

            # Run tests if available
            test_result = self._run_tests(container, project_type)
            result["logs"]["tests"] = test_result
            result["tests_run"] = test_result.get("tests_found", False)
            result["tests_passed"] = test_result.get("success", False)

            # Determine overall validation status
            # Validation is successful if:
            # 1. Health check passed
            # 2. If tests exist, they must pass
            # 3. If no tests exist, health check is sufficient
            if result["health_check_success"]:
                if result["tests_run"]:
                    # Tests were found and run
                    if result["tests_passed"]:
                        result["status"] = "success"
                        self.logger.info("validation_successful_with_tests",
                                       container_id=result["container_id"],
                                       test_summary=test_result.get("test_summary", ""))

                        # Restart application after tests (tests may have killed the background process)
                        # Only restart if container will be kept for debugging/browser access
                        if not self.cleanup_containers:
                            self.logger.info("restarting_app_after_tests", container_id=result["container_id"])
                            try:
                                self._start_application(container, project_type, project_path)
                                self.logger.info("app_restarted_for_browser_access",
                                               container_id=result["container_id"],
                                               port=result["port"])
                            except Exception as e:
                                self.logger.warning("app_restart_failed", error=str(e))
                    else:
                        result["status"] = "error"
                        result["errors"].append(f"Tests failed: {test_result.get('test_summary', 'Unknown error')}")
                        self.logger.error("validation_failed_tests",
                                        container_id=result["container_id"],
                                        test_summary=test_result.get("test_summary", ""))
                else:
                    # No tests found, health check is sufficient
                    result["status"] = "success"
                    self.logger.info("validation_successful_no_tests",
                                   container_id=result["container_id"])
            else:
                result["errors"].append("Health check failed")
                self.logger.warning("health_check_failed", container_id=result["container_id"])

        except Exception as e:
            error_msg = str(e)
            result["errors"].append(error_msg)
            self.logger.error("validation_failed", error=error_msg, exc_info=True)

        finally:
            # Cleanup based on configuration
            if container and self.cleanup_containers:
                self._cleanup_container(container)
            elif container:
                self.logger.info("container_kept_for_debugging",
                               container_id=result["container_id"],
                               container_name=result["container_name"])

        return result

    def _create_container(self, project_path: str, project_type: str) -> Tuple[Container, str, int]:
        """Create Docker container with appropriate base image.

        Args:
            project_path: Path to project
            project_type: "nodejs" or "python"

        Returns:
            Tuple of (Container, image_name, port)
        """
        if project_type == "nodejs":
            image_name = "node:18-alpine"
            working_dir = "/app"
            # Default port for Node.js apps (Express, etc.)
            app_port = 3000
        elif project_type == "python":
            image_name = "python:3.11-slim"
            working_dir = "/app"
            # Default port for Python apps (Flask, FastAPI, etc.)
            app_port = 5000
        else:
            raise ValueError(f"Unsupported project type: {project_type}")

        self.logger.info("pulling_image", image=image_name)

        try:
            # Pull image if not present
            self.client.images.pull(image_name)
        except Exception as e:
            self.logger.warning("image_pull_failed", error=str(e))

        # Generate container name from project path
        project_name = Path(project_path).name
        # Sanitize name for Docker (lowercase, alphanumeric, hyphens, underscores only)
        container_name = f"ai-modernizer-{project_name.lower().replace('_', '-')}"

        # Remove any existing container with same name
        try:
            old_container = self.client.containers.get(container_name)
            self.logger.info("removing_old_container", name=container_name)
            old_container.remove(force=True)
        except Exception:
            pass  # Container doesn't exist, which is fine

        # Create container with port mapping for browser access
        container = self.client.containers.create(
            image=image_name,
            name=container_name,
            command="tail -f /dev/null",  # Keep container running
            working_dir=working_dir,
            detach=True,
            network_mode="bridge",
            ports={f'{app_port}/tcp': app_port}  # Map container port to host port
        )

        self.logger.info("container_created_with_port_mapping",
                        container_id=container.id[:12],
                        name=container_name,
                        port=app_port)
        container.start()
        self.containers.append(container)

        return container, image_name, app_port

    def _copy_project_to_container(self, container: Container, project_path: str):
        """Copy project files to container.

        Args:
            container: Docker container
            project_path: Path to project directory
        """
        # Create tar archive of project
        project_dir = Path(project_path)
        tar_stream = io.BytesIO()

        with tarfile.open(fileobj=tar_stream, mode='w') as tar:
            for item in project_dir.iterdir():
                # Skip node_modules, venv, __pycache__, .git
                if item.name in ['node_modules', 'venv', '.venv', '__pycache__', '.git', '.pytest_cache']:
                    continue

                arcname = item.name
                tar.add(str(item), arcname=arcname, recursive=True)

        tar_stream.seek(0)

        # Copy to container
        container.put_archive("/app", tar_stream)

    def _apply_migration_plan(self, container: Container, project_type: str, migration_plan: Dict):
        """Apply migration plan to project files in container.

        Args:
            container: Docker container
            project_type: "nodejs" or "python"
            migration_plan: Migration plan with upgraded dependencies
        """
        if project_type == "nodejs":
            self._update_package_json(container, migration_plan)
        elif project_type == "python":
            self._update_requirements_txt(container, migration_plan)

    def _update_package_json(self, container: Container, migration_plan: Dict):
        """Update package.json with upgraded dependencies.

        Args:
            container: Docker container
            migration_plan: Migration plan
        """
        import json

        # Read current package.json
        exit_code, output = container.exec_run("cat /app/package.json")
        if exit_code != 0:
            raise RuntimeError("Failed to read package.json")

        package_data = json.loads(output.decode())

        # Apply upgrades
        for dep_name, dep_info in migration_plan.get("dependencies", {}).items():
            action = dep_info.get("action", "keep")
            target_version = dep_info.get("target_version", "")

            if action == "upgrade" and target_version:
                # Update in both dependencies and devDependencies
                if dep_name in package_data.get("dependencies", {}):
                    package_data["dependencies"][dep_name] = target_version
                if dep_name in package_data.get("devDependencies", {}):
                    package_data["devDependencies"][dep_name] = target_version

            elif action == "remove":
                # Remove from both
                package_data.get("dependencies", {}).pop(dep_name, None)
                package_data.get("devDependencies", {}).pop(dep_name, None)

        # Write updated package.json
        updated_json = json.dumps(package_data, indent=2)

        # Write the JSON to a temp file in container, then move it
        # This avoids shell escaping issues
        import base64
        encoded_json = base64.b64encode(updated_json.encode()).decode()

        container.exec_run(f'sh -c "echo {encoded_json} | base64 -d > /app/package.json"')

        self.logger.info("package_json_updated", dependencies=len(package_data.get("dependencies", {})))

    def _update_requirements_txt(self, container: Container, migration_plan: Dict):
        """Update requirements.txt with upgraded dependencies.

        Args:
            container: Docker container
            migration_plan: Migration plan
        """
        # Read current requirements.txt
        exit_code, output = container.exec_run("cat /app/requirements.txt")
        if exit_code != 0:
            raise RuntimeError("Failed to read requirements.txt")

        lines = output.decode().split("\n")
        updated_lines = []

        # Parse and update
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                updated_lines.append(line)
                continue

            # Extract package name
            pkg_name = line.split("==")[0].split(">=")[0].split("<=")[0].strip()

            dep_info = migration_plan.get("dependencies", {}).get(pkg_name)
            if dep_info:
                action = dep_info.get("action", "keep")
                target_version = dep_info.get("target_version", "")

                if action == "upgrade" and target_version:
                    updated_lines.append(f"{pkg_name}=={target_version}")
                elif action == "keep":
                    updated_lines.append(line)
                # Skip if action == "remove"
            else:
                updated_lines.append(line)

        # Write updated requirements.txt
        updated_content = "\n".join(updated_lines)
        container.exec_run(f'sh -c "echo {repr(updated_content)} > /app/requirements.txt"')

        self.logger.info("requirements_txt_updated", lines=len(updated_lines))

    def _install_dependencies(self, container: Container, project_type: str) -> str:
        """Install dependencies in container.

        Args:
            container: Docker container
            project_type: "nodejs" or "python"

        Returns:
            Installation output
        """
        if project_type == "nodejs":
            # Install all dependencies including devDependencies (for tests)
            cmd = "npm install"
        elif project_type == "python":
            cmd = "pip install -r requirements.txt"
        else:
            raise ValueError(f"Unsupported project type: {project_type}")

        self.logger.info("installing_dependencies", command=cmd)

        exit_code, output = container.exec_run(cmd, workdir="/app")
        output_str = output.decode()

        if exit_code != 0:
            raise RuntimeError(f"Dependency installation failed: {output_str}")

        return output_str

    def _start_application(self, container: Container, project_type: str, project_path: str) -> str:
        """Start application in container.

        Args:
            container: Docker container
            project_type: "nodejs" or "python"
            project_path: Original project path

        Returns:
            Startup output
        """
        if project_type == "nodejs":
            # Determine start command from package.json
            exit_code, output = container.exec_run("cat /app/package.json")
            if exit_code == 0:
                import json
                package_data = json.loads(output.decode())
                start_script = package_data.get("scripts", {}).get("start", "node index.js")
                # Use nohup to prevent the process from becoming a zombie
                cmd = f"sh -c 'nohup {start_script} > /tmp/app.log 2>&1 &'"
            else:
                cmd = "sh -c 'nohup node index.js > /tmp/app.log 2>&1 &'"

        elif project_type == "python":
            # Look for main.py, app.py, or server.py
            cmd = "sh -c 'nohup python app.py > /tmp/app.log 2>&1 &' || sh -c 'nohup python main.py > /tmp/app.log 2>&1 &' || sh -c 'nohup python server.py > /tmp/app.log 2>&1 &'"

        self.logger.info("starting_application", command=cmd)

        exit_code, output = container.exec_run(cmd, workdir="/app", detach=False)

        # Wait for startup
        time.sleep(5)

        # Get process list
        exit_code, ps_output = container.exec_run("ps aux")
        self.logger.info("processes_running", output=ps_output.decode()[:500])

        return output.decode() if output else "Application started in background"

    def _run_health_check(self, container: Container, project_type: str) -> Dict:
        """Run health checks on running application.

        Args:
            container: Docker container
            project_type: "nodejs" or "python"

        Returns:
            Health check results
        """
        self.logger.info("running_health_check")

        # Check if process is running
        if project_type == "nodejs":
            check_cmd = "sh -c 'ps aux | grep \"node\" | grep -v grep'"
        else:
            check_cmd = "sh -c 'ps aux | grep \"python\" | grep -v grep'"

        exit_code, output = container.exec_run(check_cmd)
        output_str = output.decode().strip()
        process_running = exit_code == 0 and len(output_str) > 0

        # For now, a running process is considered successful
        # In future, we could add actual HTTP health checks with curl/wget
        result = {
            "success": process_running,
            "process_running": process_running,
            "checks_performed": ["process_check"],
            "process_output": output_str[:200] if process_running else None
        }

        if not process_running:
            # Get logs if process not running
            exit_code, logs = container.exec_run("cat /tmp/*.log || echo 'No logs found'")
            result["logs"] = logs.decode()[:1000]
            self.logger.warning("process_not_running", project_type=project_type)
        else:
            self.logger.info("process_running_successfully",
                           project_type=project_type,
                           process_count=output_str.count('\n') + 1)

        return result

    def _run_tests(self, container: Container, project_type: str) -> Dict:
        """Run test suite in container.

        Args:
            container: Docker container
            project_type: "nodejs" or "python"

        Returns:
            Test results dictionary with:
            {
                "success": bool,
                "tests_found": bool,
                "exit_code": int,
                "output": str,
                "test_summary": str
            }
        """
        self.logger.info("running_tests", project_type=project_type)

        result = {
            "success": False,
            "tests_found": False,
            "exit_code": None,
            "output": "",
            "test_summary": ""
        }

        try:
            # Determine test command based on project type
            if project_type == "nodejs":
                # Check if test script exists in package.json
                exit_code, pkg_output = container.exec_run("cat /app/package.json")
                if exit_code == 0:
                    import json
                    package_data = json.loads(pkg_output.decode())
                    test_script = package_data.get("scripts", {}).get("test", "")

                    # Skip if no test script or placeholder script
                    if not test_script or "no test" in test_script.lower() or "exit 0" in test_script:
                        self.logger.info("no_tests_configured", project_type=project_type)
                        result["test_summary"] = "No tests configured in package.json"
                        return result

                    result["tests_found"] = True
                    cmd = "npm test"
                else:
                    self.logger.warning("cannot_read_package_json")
                    return result

            elif project_type == "python":
                # Check if pytest or unittest tests exist
                exit_code, test_check = container.exec_run(
                    "sh -c 'ls test_*.py tests/ 2>/dev/null || ls *_test.py 2>/dev/null'"
                )

                if exit_code == 0 and test_check.decode().strip():
                    result["tests_found"] = True
                    cmd = "pytest -v || python -m unittest discover"
                else:
                    self.logger.info("no_tests_found", project_type=project_type)
                    result["test_summary"] = "No test files found"
                    return result

            # Run tests with timeout
            self.logger.info("executing_tests", command=cmd)
            exit_code, output = container.exec_run(
                cmd,
                workdir="/app",
                environment={"CI": "true", "NODE_ENV": "test"}
            )

            output_str = output.decode()
            result["exit_code"] = exit_code
            result["output"] = output_str
            result["success"] = exit_code == 0

            # Extract test summary
            if project_type == "nodejs":
                # Look for Jest summary: "Tests: X passed, Y total"
                import re
                match = re.search(r'Tests?:\s+(\d+)\s+passed.*?(\d+)\s+total', output_str, re.IGNORECASE)
                if match:
                    result["test_summary"] = f"{match.group(1)} passed, {match.group(2)} total"
                elif exit_code == 0:
                    result["test_summary"] = "All tests passed"
                else:
                    # Look for failure info
                    fail_match = re.search(r'(\d+)\s+failed', output_str, re.IGNORECASE)
                    if fail_match:
                        result["test_summary"] = f"{fail_match.group(1)} tests failed"
                    else:
                        result["test_summary"] = "Tests failed"

            elif project_type == "python":
                # Look for pytest summary
                import re
                match = re.search(r'(\d+)\s+passed', output_str)
                if match:
                    result["test_summary"] = f"{match.group(1)} passed"
                elif exit_code == 0:
                    result["test_summary"] = "All tests passed"
                else:
                    result["test_summary"] = "Tests failed"

            # Log results
            if result["success"]:
                self.logger.info("tests_passed",
                               summary=result["test_summary"],
                               exit_code=exit_code)
            else:
                self.logger.error("tests_failed",
                                summary=result["test_summary"],
                                exit_code=exit_code,
                                output_preview=output_str[:500])

        except Exception as e:
            self.logger.error("test_execution_error", error=str(e), exc_info=True)
            result["output"] = f"Error running tests: {str(e)}"
            result["test_summary"] = f"Test execution error: {str(e)}"

        return result

    def _cleanup_container(self, container: Container):
        """Stop and remove container.

        Args:
            container: Docker container
        """
        try:
            container_id = container.id[:12]
            self.logger.info("cleaning_up_container", container_id=container_id)

            container.stop(timeout=5)
            container.remove()

            if container in self.containers:
                self.containers.remove(container)

        except Exception as e:
            self.logger.warning("cleanup_failed", error=str(e))

    def cleanup_all(self):
        """Stop and remove all containers created by this validator."""
        if not self.cleanup_containers:
            self.logger.info("container_cleanup_disabled", count=len(self.containers))
            return

        self.logger.info("cleaning_up_all_containers", count=len(self.containers))

        for container in list(self.containers):
            self._cleanup_container(container)

    def __del__(self):
        """Cleanup on destruction."""
        if hasattr(self, 'containers'):
            self.cleanup_all()


def main():
    """Standalone test of Docker validation tools."""
    import sys
    from pathlib import Path

    print("=" * 80)
    print("DOCKER VALIDATION TOOLS - STANDALONE TEST")
    print("=" * 80)

    if not DOCKER_AVAILABLE:
        print("\nERROR: Docker SDK not installed")
        print("Install with: pip install docker")
        return 1

    # Test with sample Express app
    test_project = Path(__file__).parent.parent / "tests" / "sample_projects" / "express-app"

    if not test_project.exists():
        print(f"\nERROR: Test project not found at {test_project}")
        return 1

    print(f"\nTest Project: {test_project}")
    print("Project Type: nodejs")

    try:
        # Create validator
        print("\n1. Creating Docker Validator...")
        validator = DockerValidator(timeout=300)
        print(f"   Docker Version: {validator.client.version()['Version']}")

        # Test without migration (baseline)
        print("\n2. Testing baseline (no migration)...")
        result = validator.validate_project(
            project_path=str(test_project),
            project_type="nodejs",
            migration_plan=None
        )

        print("\n" + "=" * 80)
        print("RESULTS - BASELINE TEST")
        print("=" * 80)
        print(f"Status: {result['status'].upper()}")
        print(f"Container ID: {result['container_id']}")
        print(f"Build: {'SUCCESS' if result['build_success'] else 'FAILED'}")
        print(f"Install: {'SUCCESS' if result['install_success'] else 'FAILED'}")
        print(f"Runtime: {'SUCCESS' if result['runtime_success'] else 'FAILED'}")
        print(f"Health Check: {'SUCCESS' if result['health_check_success'] else 'FAILED'}")

        if result['errors']:
            print(f"\nErrors: {len(result['errors'])}")
            for error in result['errors']:
                print(f"  - {error}")

        # Cleanup
        validator.cleanup_all()

        print("\n" + "=" * 80)
        print("TEST COMPLETE")
        print("=" * 80)

        return 0 if result['status'] == 'success' else 1

    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
