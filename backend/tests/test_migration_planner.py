"""Unit tests for Migration Planner Agent."""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.migration_planner import MigrationPlannerAgent


class TestMigrationPlannerAgent:
    """Test cases for Migration Planner Agent."""

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
                "total_requests": 1,
                "total_tokens": 100,
                "total_input_tokens": 50,
                "total_output_tokens": 50,
                "total_cost_usd": 0.001
            }
            mock_llm.return_value = mock_client

            agent = MigrationPlannerAgent()
            agent.llm = mock_client
            return agent

    @pytest.fixture
    def sample_project_path(self):
        """Path to sample Express.js project."""
        return str(Path(__file__).parent / "sample_projects" / "express-app")

    def test_read_package_json(self, agent, sample_project_path):
        """Test reading and parsing package.json."""
        result = agent._read_dependencies(sample_project_path)

        assert result["project_type"] == "nodejs"
        assert "express" in result["dependencies"]
        assert result["dependencies"]["express"] == "4.16.0"
        assert "body-parser" in result["dependencies"]
        assert result["dependencies"]["body-parser"] == "1.18.3"

    def test_build_analysis_prompt(self, agent, sample_project_path):
        """Test prompt building for LLM analysis."""
        dependency_data = agent._read_dependencies(sample_project_path)
        prompt = agent._build_analysis_prompt(dependency_data)

        assert "NODEJS" in prompt
        assert "express" in prompt
        assert "4.16.0" in prompt
        assert "body-parser" in prompt
        assert "OUTPUT FORMAT" in prompt
        assert "JSON" in prompt

    def test_parse_valid_migration_plan(self, agent):
        """Test parsing valid LLM response."""
        mock_response = json.dumps({
            "project_type": "nodejs",
            "dependencies": {
                "express": {
                    "current_version": "4.16.0",
                    "target_version": "5.0.0",
                    "action": "upgrade",
                    "risk": "medium"
                }
            },
            "migration_strategy": {
                "total_phases": 1,
                "phases": []
            }
        })

        plan = agent._parse_migration_plan(mock_response)

        assert "dependencies" in plan
        assert "migration_strategy" in plan
        assert plan["dependencies"]["express"]["current_version"] == "4.16.0"

    def test_parse_migration_plan_with_markdown(self, agent):
        """Test parsing LLM response with markdown code blocks."""
        mock_response = """```json
{
    "project_type": "nodejs",
    "dependencies": {},
    "migration_strategy": {"total_phases": 0, "phases": []}
}
```"""

        plan = agent._parse_migration_plan(mock_response)

        assert "dependencies" in plan
        assert "migration_strategy" in plan

    def test_execute_with_mock_llm(self, agent, sample_project_path):
        """Test full execution with mocked LLM response."""
        # Mock LLM response
        mock_plan = {
            "project_type": "nodejs",
            "analysis_date": "2025-11-07",
            "dependencies": {
                "express": {
                    "current_version": "4.16.0",
                    "target_version": "5.0.0",
                    "action": "upgrade",
                    "breaking_changes": [
                        "body-parser now built-in",
                        "Promise-based error handling"
                    ],
                    "risk": "medium",
                    "reason": "Major version upgrade with breaking changes"
                },
                "body-parser": {
                    "current_version": "1.18.3",
                    "target_version": "N/A",
                    "action": "remove",
                    "breaking_changes": [],
                    "risk": "low",
                    "reason": "Deprecated - now built into Express 5.0"
                },
                "cors": {
                    "current_version": "2.8.4",
                    "target_version": "2.8.5",
                    "action": "upgrade",
                    "breaking_changes": [],
                    "risk": "low",
                    "reason": "Patch update for bug fixes"
                },
                "dotenv": {
                    "current_version": "6.0.0",
                    "target_version": "16.4.5",
                    "action": "upgrade",
                    "breaking_changes": ["TypeScript types improved", "Node 12+ required"],
                    "risk": "low",
                    "reason": "Many versions behind, but no breaking API changes"
                },
                "morgan": {
                    "current_version": "1.9.1",
                    "target_version": "1.10.0",
                    "action": "upgrade",
                    "breaking_changes": [],
                    "risk": "low",
                    "reason": "Minor version upgrade"
                },
                "nodemon": {
                    "current_version": "1.18.4",
                    "target_version": "3.1.0",
                    "action": "upgrade",
                    "breaking_changes": ["Node 14+ required"],
                    "risk": "low",
                    "reason": "Dev dependency, no production impact"
                }
            },
            "migration_strategy": {
                "total_phases": 3,
                "phases": [
                    {
                        "phase": 1,
                        "name": "Low-risk updates",
                        "dependencies": ["cors", "morgan", "nodemon", "dotenv"],
                        "description": "Update packages with no breaking changes or dev-only dependencies",
                        "estimated_time": "30 minutes",
                        "rollback_plan": "Revert package.json and run npm install"
                    },
                    {
                        "phase": 2,
                        "name": "Express 5.0 upgrade",
                        "dependencies": ["express"],
                        "description": "Upgrade Express to 5.0 and update middleware configuration",
                        "estimated_time": "2 hours",
                        "rollback_plan": "Revert package.json, restore body-parser imports, run npm install"
                    },
                    {
                        "phase": 3,
                        "name": "Remove deprecated packages",
                        "dependencies": ["body-parser"],
                        "description": "Remove body-parser imports and use Express built-in parsing",
                        "estimated_time": "1 hour",
                        "rollback_plan": "Restore body-parser in package.json and code"
                    }
                ]
            },
            "recommendations": [
                "Test all API endpoints after Express 5.0 upgrade",
                "Update error handling to use async/await with try/catch",
                "Consider adding TypeScript for better type safety",
                "Add integration tests before proceeding with upgrades",
                "Update Node.js version to 18+ for best compatibility"
            ],
            "estimated_total_time": "3.5 hours",
            "overall_risk": "medium"
        }

        agent.llm.generate = Mock(return_value=json.dumps(mock_plan))

        result = agent.execute({"project_path": sample_project_path})

        assert result["status"] == "success"
        assert "migration_plan" in result
        assert "cost_report" in result

        plan = result["migration_plan"]
        assert plan["project_type"] == "nodejs"
        assert len(plan["dependencies"]) == 6
        assert plan["dependencies"]["express"]["action"] == "upgrade"
        assert plan["dependencies"]["body-parser"]["action"] == "remove"
        assert plan["migration_strategy"]["total_phases"] == 3
        assert plan["overall_risk"] == "medium"

    def test_error_handling_no_project_path(self, agent):
        """Test error handling when project_path not provided."""
        result = agent.execute({})

        assert result["status"] == "error"
        assert "project_path is required" in result["error"]

    def test_error_handling_missing_dependency_file(self, agent):
        """Test error handling when no dependency file found."""
        result = agent.execute({"project_path": "/nonexistent/path"})

        assert result["status"] == "error"
        assert "package.json" in result["error"].lower() or "requirements.txt" in result["error"].lower()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
