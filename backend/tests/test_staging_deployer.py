"""Unit tests for Staging Deployer Agent."""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.staging_deployer import StagingDeployerAgent


class TestStagingDeployerAgent:
    """Test cases for Staging Deployer Agent."""

    @pytest.fixture
    def agent(self):
        """Create agent instance with mocked LLM."""
        with patch('agents.base.create_llm_client') as mock_llm:
            mock_client = Mock()
            mock_client.get_provider_name.return_value = "mock"
            mock_client.model = "mock-model"
            mock_client.cost_tracker.get_report.return_value = {
                "provider": "mock",
                "model": "mock-model",
                "total_requests": 0,
                "total_tokens": 0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_cost_usd": 0.0
            }
            mock_llm.return_value = mock_client

            agent = StagingDeployerAgent()
            agent.llm = mock_client
            return agent

    @pytest.fixture
    def sample_migration_plan(self):
        """Sample migration plan."""
        return {
            "project_type": "nodejs",
            "dependencies": {
                "express": {
                    "current_version": "4.16.0",
                    "target_version": "4.19.2",
                    "action": "upgrade",
                    "risk": "low",
                    "breaking_changes": []
                },
                "body-parser": {
                    "current_version": "1.18.3",
                    "target_version": "N/A",
                    "action": "remove",
                    "risk": "low",
                    "reason": "Deprecated"
                }
            },
            "migration_strategy": {
                "total_phases": 1,
                "phases": [{"phase": 1, "name": "Low-risk updates"}]
            },
            "overall_risk": "low",
            "estimated_total_time": "1 hour",
            "recommendations": ["Test endpoints"]
        }

    @pytest.fixture
    def sample_validation_result(self):
        """Sample validation result."""
        return {
            "status": "success",
            "build_success": True,
            "install_success": True,
            "runtime_success": True,
            "health_check_success": True
        }

    def test_generate_branch_name_high_risk(self, agent, sample_migration_plan):
        """Test branch name generation with high-risk dependency."""
        sample_migration_plan["dependencies"]["express"]["risk"] = "high"
        branch = agent._generate_branch_name(sample_migration_plan)
        assert branch.startswith("upgrade/dependencies-")

    def test_generate_branch_name_first_upgrade(self, agent, sample_migration_plan):
        """Test branch name generation with first upgrade."""
        branch = agent._generate_branch_name(sample_migration_plan)
        assert branch.startswith("upgrade/dependencies-")

    def test_generate_branch_name_fallback(self, agent):
        """Test branch name generation with no upgrades."""
        empty_plan = {
            "dependencies": {
                "test": {"action": "keep"}
            }
        }
        branch = agent._generate_branch_name(empty_plan)
        assert branch.startswith("upgrade/dependencies-")

    def test_generate_commit_message_single_upgrade(self, agent, sample_migration_plan, sample_validation_result):
        """Test commit message generation for single upgrade."""
        message = agent._generate_commit_message(sample_migration_plan, sample_validation_result)

        # Updated format: "chore(deps): upgrade express 4.16.0 → 4.19.2"
        # Note: Since there's also a removal (body-parser), it uses the multi-dep format
        assert "chore(deps):" in message
        assert "Upgraded:" in message
        assert "express" in message
        assert "4.16.0 → 4.19.2" in message
        assert "Removed:" in message
        assert "body-parser" in message
        assert "Validation: ✓ Passed runtime tests in Docker" in message

    def test_generate_commit_message_multiple_upgrades(self, agent, sample_validation_result):
        """Test commit message generation for multiple upgrades."""
        plan = {
            "project_type": "nodejs",
            "dependencies": {
                "express": {"current_version": "4.16.0", "target_version": "5.0.0", "action": "upgrade", "risk": "high"},
                "cors": {"current_version": "2.8.4", "target_version": "2.8.5", "action": "upgrade", "risk": "low"},
            },
            "migration_strategy": {"total_phases": 2},
            "overall_risk": "medium"
        }

        message = agent._generate_commit_message(plan, sample_validation_result)
        assert "chore(deps): upgrade 2 dependencies" in message
        assert "express" in message
        assert "cors" in message

    def test_generate_pr_description(self, agent, sample_migration_plan, sample_validation_result):
        """Test PR description generation."""
        description = agent._generate_pr_description(sample_migration_plan, sample_validation_result)

        assert "Dependency Upgrade" in description
        assert "Upgraded Dependencies" in description
        assert "express" in description
        assert "4.16.0" in description
        assert "4.19.2" in description
        assert "Removed Dependencies" in description
        assert "body-parser" in description
        assert "Validation" in description
        assert "PASSED" in description
        assert "Migration Strategy" in description
        assert "Testing Instructions" in description
        assert "npm install" in description

    def test_update_package_json_upgrade(self, agent, sample_migration_plan, tmp_path):
        """Test package.json update with upgrade."""
        # Create test package.json
        package_json = tmp_path / "package.json"
        initial_data = {
            "name": "test-app",
            "dependencies": {
                "express": "4.16.0",
                "body-parser": "1.18.3"
            },
            "devDependencies": {
                "nodemon": "1.18.4"
            }
        }
        with open(package_json, 'w') as f:
            json.dump(initial_data, f)

        # Update
        agent._update_package_json(package_json, sample_migration_plan)

        # Verify
        with open(package_json, 'r') as f:
            updated_data = json.load(f)

        assert updated_data["dependencies"]["express"] == "4.19.2"
        assert "body-parser" not in updated_data["dependencies"]
        assert updated_data["devDependencies"]["nodemon"] == "1.18.4"  # Unchanged

    def test_update_package_json_remove(self, agent, sample_migration_plan, tmp_path):
        """Test package.json update with removal."""
        package_json = tmp_path / "package.json"
        initial_data = {
            "dependencies": {
                "express": "4.16.0",
                "body-parser": "1.18.3"
            }
        }
        with open(package_json, 'w') as f:
            json.dump(initial_data, f)

        agent._update_package_json(package_json, sample_migration_plan)

        with open(package_json, 'r') as f:
            updated_data = json.load(f)

        assert "body-parser" not in updated_data["dependencies"]

    def test_update_requirements_txt_upgrade(self, agent, tmp_path):
        """Test requirements.txt update with upgrade."""
        requirements_txt = tmp_path / "requirements.txt"
        requirements_txt.write_text("django==3.0.0\nrequests==2.25.0\n")

        plan = {
            "project_type": "python",
            "dependencies": {
                "django": {
                    "current_version": "3.0.0",
                    "target_version": "4.2.0",
                    "action": "upgrade"
                },
                "requests": {
                    "action": "keep"
                }
            }
        }

        agent._update_requirements_txt(requirements_txt, plan)

        content = requirements_txt.read_text()
        assert "django==4.2.0" in content
        assert "requests==2.25.0" in content

    def test_update_requirements_txt_remove(self, agent, tmp_path):
        """Test requirements.txt update with removal."""
        requirements_txt = tmp_path / "requirements.txt"
        requirements_txt.write_text("django==3.0.0\nold-package==1.0.0\n")

        plan = {
            "project_type": "python",
            "dependencies": {
                "old-package": {
                    "action": "remove"
                }
            }
        }

        agent._update_requirements_txt(requirements_txt, plan)

        content = requirements_txt.read_text()
        assert "django==3.0.0" in content
        assert "old-package" not in content

    def test_error_handling_no_project_path(self, agent, sample_migration_plan):
        """Test error handling when project_path not provided."""
        result = agent.execute({"migration_plan": sample_migration_plan})

        assert result["status"] == "error"
        assert "project_path is required" in result["error"]

    def test_error_handling_no_migration_plan(self, agent):
        """Test error handling when migration_plan not provided."""
        result = agent.execute({"project_path": "/tmp/test"})

        assert result["status"] == "error"
        assert "migration_plan is required" in result["error"]

    def test_error_handling_invalid_project_path(self, agent, sample_migration_plan):
        """Test error handling when project path doesn't exist."""
        result = agent.execute({
            "project_path": "/nonexistent/path",
            "migration_plan": sample_migration_plan
        })

        assert result["status"] == "error"
        assert "does not exist" in result["error"]

    @patch('subprocess.run')
    def test_create_branch_success(self, mock_run, agent, tmp_path):
        """Test successful branch creation."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        result = agent._create_branch(tmp_path, "test-branch", "main")

        assert result["status"] == "success"
        assert result["branch"] == "test-branch"
        assert mock_run.call_count == 3  # checkout, pull, checkout -b

    @patch('subprocess.run')
    def test_create_branch_failure(self, mock_run, agent, tmp_path):
        """Test branch creation failure."""
        import subprocess
        mock_run.side_effect = subprocess.CalledProcessError(1, 'git', stderr="Git error")

        result = agent._create_branch(tmp_path, "test-branch", "main")

        assert result["status"] == "error"
        assert "error" in result

    @patch('subprocess.run')
    def test_commit_changes_success(self, mock_run, agent, tmp_path):
        """Test successful commit."""
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="", stderr=""),  # git add
            MagicMock(returncode=0, stdout="", stderr=""),  # git commit
            MagicMock(returncode=0, stdout="abc123\n", stderr="")  # git rev-parse
        ]

        result = agent._commit_changes(tmp_path, "Test commit", ["file.txt"])

        assert result["status"] == "success"
        assert result["commit_sha"] == "abc123"

    @patch('subprocess.run')
    def test_push_branch_success(self, mock_run, agent, tmp_path):
        """Test successful branch push."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        result = agent._push_branch(tmp_path, "test-branch")

        assert result["status"] == "success"

    def test_update_dependency_files_nodejs(self, agent, sample_migration_plan, tmp_path):
        """Test dependency file update for Node.js project."""
        # Create package.json
        package_json = tmp_path / "package.json"
        package_json.write_text('{"dependencies": {"express": "4.16.0"}}')

        files = agent._update_dependency_files(tmp_path, sample_migration_plan)

        assert "package.json" in files
        assert len(files) == 1

    def test_update_dependency_files_python(self, agent, tmp_path):
        """Test dependency file update for Python project."""
        # Create requirements.txt
        requirements_txt = tmp_path / "requirements.txt"
        requirements_txt.write_text("django==3.0.0\n")

        plan = {
            "project_type": "python",
            "dependencies": {"django": {"action": "upgrade", "target_version": "4.0.0"}}
        }

        files = agent._update_dependency_files(tmp_path, plan)

        assert "requirements.txt" in files
        assert len(files) == 1


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
