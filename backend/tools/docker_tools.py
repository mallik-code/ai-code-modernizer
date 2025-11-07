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

    def __init__(self, timeout: int = 300):
        """Initialize Docker validator.

        Args:
            timeout: Maximum time in seconds for operations (default: 300)

        Raises:
            RuntimeError: If Docker is not available
        """
        if not DOCKER_AVAILABLE:
            raise RuntimeError("Docker SDK not installed. Run: pip install docker")

        self.timeout = timeout
        self.logger = setup_logger("docker_validator")
        self.containers: List[Container] = []

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
                "build_success": bool,
                "install_success": bool,
                "runtime_success": bool,
                "health_check_success": bool,
                "logs": {...},
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
            "build_success": False,
            "install_success": False,
            "runtime_success": False,
            "health_check_success": False,
            "logs": {},
            "errors": []
        }

        container = None
        try:
            # Create container
            container, image_name = self._create_container(project_path, project_type)
            result["container_id"] = container.id[:12]
            result["build_success"] = True
            self.logger.info("container_created", container_id=result["container_id"])

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

            if result["health_check_success"]:
                result["status"] = "success"
                self.logger.info("validation_successful", container_id=result["container_id"])
            else:
                result["errors"].append("Health check failed")
                self.logger.warning("health_check_failed", container_id=result["container_id"])

        except Exception as e:
            error_msg = str(e)
            result["errors"].append(error_msg)
            self.logger.error("validation_failed", error=error_msg, exc_info=True)

        finally:
            # Cleanup
            if container:
                self._cleanup_container(container)

        return result

    def _create_container(self, project_path: str, project_type: str) -> Tuple[Container, str]:
        """Create Docker container with appropriate base image.

        Args:
            project_path: Path to project
            project_type: "nodejs" or "python"

        Returns:
            Tuple of (Container, image_name)
        """
        if project_type == "nodejs":
            image_name = "node:18-alpine"
            working_dir = "/app"
        elif project_type == "python":
            image_name = "python:3.11-slim"
            working_dir = "/app"
        else:
            raise ValueError(f"Unsupported project type: {project_type}")

        self.logger.info("pulling_image", image=image_name)

        try:
            # Pull image if not present
            self.client.images.pull(image_name)
        except Exception as e:
            self.logger.warning("image_pull_failed", error=str(e))

        # Create container
        container = self.client.containers.create(
            image=image_name,
            command="tail -f /dev/null",  # Keep container running
            working_dir=working_dir,
            detach=True,
            network_mode="bridge"
        )

        container.start()
        self.containers.append(container)

        return container, image_name

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
        container.exec_run(f'sh -c "echo {repr(updated_json)} > /app/package.json"')

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
            cmd = "npm install --production"
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
                cmd = f"sh -c '{start_script} &'"
            else:
                cmd = "sh -c 'node index.js &'"

        elif project_type == "python":
            # Look for main.py, app.py, or server.py
            cmd = "sh -c 'python app.py &' || sh -c 'python main.py &' || sh -c 'python server.py &'"

        self.logger.info("starting_application", command=cmd)

        exit_code, output = container.exec_run(cmd, workdir="/app", detach=True)

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
