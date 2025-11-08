"""Unit tests for Error Analyzer Agent."""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.error_analyzer import ErrorAnalyzerAgent


class TestErrorAnalyzerAgent:
    """Test cases for Error Analyzer Agent."""

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

            agent = ErrorAnalyzerAgent()
            agent.llm = mock_client
            return agent

    @pytest.fixture
    def sample_validation_failure(self):
        """Sample validation failure result."""
        return {
            "status": "failed",
            "build_success": True,
            "install_success": False,
            "runtime_success": False,
            "health_check_success": False,
            "errors": [
                "npm ERR! peer dep missing: express@^5.0.0",
                "Cannot find module 'body-parser'"
            ],
            "install_logs": "npm WARN ERESOLVE peer dependency",
            "runtime_logs": "Error: Cannot find module 'body-parser'",
            "health_check_logs": ""
        }

    @pytest.fixture
    def sample_migration_plan(self):
        """Sample migration plan."""
        return {
            "project_type": "nodejs",
            "dependencies": {
                "express": {
                    "current_version": "4.16.0",
                    "target_version": "5.0.0",
                    "action": "upgrade",
                    "risk": "high"
                }
            }
        }

    def test_extract_error_info(self, agent, sample_validation_failure):
        """Test error information extraction."""
        error_info = agent._extract_error_info(sample_validation_failure)

        assert error_info["status"] == "failed"
        assert error_info["build_success"] is True
        assert error_info["install_success"] is False
        assert len(error_info["errors"]) == 2
        assert "key_errors" in error_info

    def test_extract_npm_errors(self, agent):
        """Test npm error extraction."""
        logs = """
npm WARN ERESOLVE peer dep missing: express@^5.0.0, required by body-parser@2.0.0
npm ERR! code ERESOLVE
npm ERR! ERESOLVE unable to resolve dependency tree
npm ERR! peer express@"^5.0.0" from body-parser@2.0.0
        """

        errors = agent._extract_npm_errors(logs)

        assert len(errors) > 0
        assert any("peer" in e.lower() for e in errors)

    def test_extract_pip_errors(self, agent):
        """Test pip error extraction."""
        logs = """
ERROR: Could not find a version that satisfies the requirement django==5.0.0
ERROR: No matching distribution found for django==5.0.0
        """

        errors = agent._extract_pip_errors(logs)

        assert len(errors) > 0
        assert any("pip error" in e for e in errors)

    def test_extract_runtime_errors_javascript(self, agent):
        """Test JavaScript runtime error extraction."""
        logs = """
TypeError: app.use is not a function
    at Object.<anonymous> (/app/src/server.js:15:5)
ReferenceError: bodyParser is not defined
    at initApp (/app/src/app.js:10:3)
        """

        errors = agent._extract_runtime_errors(logs)

        assert len(errors) > 0
        assert any("TypeError" in e for e in errors)
        assert any("ReferenceError" in e for e in errors)

    def test_extract_runtime_errors_python(self, agent):
        """Test Python runtime error extraction."""
        logs = """
ImportError: cannot import name 'OldClass' from 'django.contrib.auth'
AttributeError: module 'requests' has no attribute 'get_legacy'
        """

        errors = agent._extract_runtime_errors(logs)

        assert len(errors) > 0
        assert any("ImportError" in e for e in errors)
        assert any("AttributeError" in e for e in errors)

    def test_fallback_analysis_missing_dependency(self, agent):
        """Test fallback analysis categorization for missing dependency."""
        error_info = {
            "key_errors": [
                "peer dep missing: express@^5.0.0",
                "Cannot find module 'body-parser'"
            ],
            "build_success": True,
            "install_success": False,
            "runtime_success": False,
            "health_check_success": False
        }

        analysis = agent._fallback_analysis(error_info)

        assert analysis["analysis_status"] == "success"
        assert analysis["error_category"] == "missing_dependency"
        assert analysis["confidence"] == "low"
        assert len(analysis["fix_suggestions"]) > 0

    def test_fallback_analysis_api_change(self, agent):
        """Test fallback analysis categorization for API change."""
        error_info = {
            "key_errors": [
                "TypeError: app.use is not a function",
                "not a function error at server.js"
            ],
            "build_success": True,
            "install_success": True,
            "runtime_success": False,
            "health_check_success": False
        }

        analysis = agent._fallback_analysis(error_info)

        # Should detect as api_change due to "not a function"
        assert analysis["error_category"] in ["api_change", "unknown"]

    def test_fallback_analysis_version_conflict(self, agent):
        """Test fallback analysis categorization for version conflict."""
        error_info = {
            "key_errors": [
                "Conflict: package A requires B@2.0, but found B@1.0"
            ],
            "build_success": True,
            "install_success": False,
            "runtime_success": False,
            "health_check_success": False
        }

        analysis = agent._fallback_analysis(error_info)

        assert analysis["error_category"] == "version_conflict"

    def test_build_analysis_prompt(self, agent, sample_validation_failure, sample_migration_plan):
        """Test analysis prompt building."""
        error_info = agent._extract_error_info(sample_validation_failure)
        prompt = agent._build_analysis_prompt(error_info, sample_migration_plan)

        assert "VALIDATION RESULTS" in prompt
        assert "Build Success" in prompt
        assert "MIGRATION PLAN BEING TESTED" in prompt
        assert "express" in prompt
        assert "TASKS:" in prompt
        assert "OUTPUT FORMAT" in prompt

    def test_analyze_with_llm_success(self, agent, sample_validation_failure):
        """Test LLM analysis with valid response."""
        error_info = agent._extract_error_info(sample_validation_failure)

        # Mock LLM response
        mock_analysis = {
            "analysis_status": "success",
            "error_category": "missing_dependency",
            "root_cause": "body-parser was removed but code still imports it",
            "problematic_dependencies": ["body-parser"],
            "fix_suggestions": [
                {
                    "priority": 1,
                    "type": "update_code",
                    "description": "Remove body-parser import",
                    "commands": [],
                    "code_changes": {
                        "file": "src/server.js",
                        "old_code": "const bodyParser = require('body-parser')",
                        "new_code": "// body-parser is now built into Express"
                    }
                }
            ],
            "confidence": "high",
            "next_steps": ["Update code", "Re-run validation"]
        }

        agent.llm.generate = Mock(return_value=json.dumps(mock_analysis))

        result = agent._analyze_with_llm(error_info, None)

        assert result["analysis_status"] == "success"
        assert result["error_category"] == "missing_dependency"
        assert len(result["fix_suggestions"]) == 1

    def test_analyze_with_llm_json_error(self, agent, sample_validation_failure):
        """Test LLM analysis with invalid JSON response."""
        error_info = agent._extract_error_info(sample_validation_failure)

        # Mock invalid JSON response
        agent.llm.generate = Mock(return_value="This is not JSON")

        result = agent._analyze_with_llm(error_info, None)

        # Should fall back to basic analysis
        assert result["analysis_status"] == "success"
        assert "error_category" in result
        assert result["confidence"] == "low"

    def test_execute_success(self, agent, sample_validation_failure, sample_migration_plan):
        """Test full execution with mocked LLM."""
        # Mock LLM response
        mock_analysis = {
            "analysis_status": "success",
            "error_category": "api_change",
            "root_cause": "Breaking API changes in Express 5",
            "problematic_dependencies": ["express"],
            "fix_suggestions": [],
            "confidence": "medium",
            "next_steps": []
        }

        agent.llm.generate = Mock(return_value=json.dumps(mock_analysis))

        result = agent.execute({
            "validation_result": sample_validation_failure,
            "migration_plan": sample_migration_plan
        })

        assert result["status"] == "success"
        assert "analysis" in result
        assert "error_info" in result
        assert "cost_report" in result

    def test_execute_no_validation_result(self, agent):
        """Test error handling when validation_result not provided."""
        result = agent.execute({})

        assert result["status"] == "error"
        assert "validation_result is required" in result["error"]

    def test_get_code_context(self, agent, tmp_path):
        """Test code context extraction."""
        # Create test file
        test_file = tmp_path / "server.js"
        test_file.write_text("""const express = require('express');
const bodyParser = require('body-parser');

const app = express();

app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

app.get('/', (req, res) => {
    res.send('Hello World');
});

app.listen(3000);
""")

        error_location = {
            "file": "server.js",
            "line": 6
        }

        context = agent._get_code_context(str(tmp_path), error_location)

        assert context is not None
        assert context["file"] == "server.js"
        assert context["line"] == 6
        assert ">>>" in context["context"]
        assert "bodyParser.json()" in context["context"]

    def test_get_code_context_file_not_found(self, agent, tmp_path):
        """Test code context when file doesn't exist."""
        error_location = {
            "file": "nonexistent.js",
            "line": 10
        }

        context = agent._get_code_context(str(tmp_path), error_location)

        assert context is None

    def test_get_code_context_no_location(self, agent, tmp_path):
        """Test code context with incomplete location info."""
        error_location = {
            "file": "server.js"
            # Missing line number
        }

        context = agent._get_code_context(str(tmp_path), error_location)

        assert context is None

    def test_extract_error_info_all_success(self, agent):
        """Test error info extraction when validation succeeded."""
        validation_result = {
            "status": "success",
            "build_success": True,
            "install_success": True,
            "runtime_success": True,
            "health_check_success": True,
            "errors": [],
            "install_logs": "",
            "runtime_logs": "",
            "health_check_logs": ""
        }

        error_info = agent._extract_error_info(validation_result)

        assert error_info["status"] == "success"
        assert error_info["build_success"] is True
        assert len(error_info["errors"]) == 0
        assert len(error_info.get("key_errors", [])) == 0

    def test_extract_npm_errors_peer_dependency(self, agent):
        """Test specific npm peer dependency error pattern."""
        logs = """
npm WARN ERESOLVE overriding peer dependency
npm WARN ERESOLVE peer dep missing: react@^18.0.0, required by react-dom@18.2.0 from react@17.0.0
npm ERR! peer react@"^18.0.0" from react-dom@18.2.0
        """

        errors = agent._extract_npm_errors(logs)

        assert len(errors) > 0
        assert any("peer" in e.lower() or "react" in e.lower() for e in errors)

    def test_extract_runtime_errors_stack_trace(self, agent):
        """Test runtime error extraction with stack trace."""
        logs = """
Error: Something went wrong
    at performAction (/app/src/utils.js:42:11)
    at handleRequest (/app/src/server.js:100:7)
    at Layer.handle [as handle_request] (/app/node_modules/express/lib/router/layer.js:95:5)
        """

        errors = agent._extract_runtime_errors(logs)

        assert len(errors) > 0
        # Should extract both the Error and stack trace locations
        assert any("utils.js:42" in e for e in errors)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
