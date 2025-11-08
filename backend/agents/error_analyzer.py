"""Error Analyzer Agent

Analyzes runtime validation failures, identifies root causes, and generates
fix suggestions to resolve dependency upgrade issues.

Capabilities:
- Parses error logs from Docker validation failures
- Identifies root causes (missing dependencies, API changes, configuration issues)
- Determines which dependency caused the failure
- Generates specific fix suggestions
- Proposes alternative upgrade strategies
- Creates updated migration plans
"""

import json
import re
import sys
from typing import Dict, List, Optional
from pathlib import Path

from agents.base import BaseAgent


class ErrorAnalyzerAgent(BaseAgent):
    """Agent for analyzing validation errors and generating fixes."""

    def __init__(self, llm_provider: Optional[str] = None, llm_model: Optional[str] = None):
        system_prompt = """You are an expert software error analyst and debugger.

Your role:
1. Analyze runtime validation errors from Docker containers
2. Identify root causes of failures
3. Determine which dependency or code change caused the issue
4. Generate specific, actionable fix suggestions
5. Propose alternative upgrade strategies if needed

When analyzing errors:
- Read error messages carefully (stack traces, npm errors, Python exceptions)
- Identify the exact line or module that failed
- Look for common patterns:
  - Missing dependencies
  - Breaking API changes
  - Deprecated methods
  - Configuration issues
  - Version incompatibilities
  - Import errors
- Consider the context of the migration plan
- Prioritize fixes by likelihood of success

Common Error Patterns:
- **Missing Peer Dependency**: "WARN ERESOLVE peer dependency" → Install missing peer dependency
- **Breaking API Change**: "TypeError: X is not a function" → API changed, update code
- **Deprecated Method**: "DeprecationWarning" → Use new API
- **Import Error**: "Cannot find module 'X'" → Package renamed or removed
- **Version Conflict**: "Conflicting peer dependency" → Adjust version constraints

Output Format:
Return structured analysis with:
{
    "analysis_status": "success",
    "error_category": "missing_dependency" | "api_change" | "config_issue" | "version_conflict" | "unknown",
    "root_cause": "Detailed explanation of what went wrong",
    "problematic_dependencies": ["package1", "package2"],
    "error_location": {
        "file": "src/app.js",
        "line": 42,
        "function": "initializeApp"
    },
    "fix_suggestions": [
        {
            "priority": 1,
            "type": "add_dependency" | "update_code" | "adjust_version" | "remove_dependency",
            "description": "What to do",
            "commands": ["npm install peer-dep@version"],
            "code_changes": {
                "file": "src/app.js",
                "old_code": "app.use(bodyParser.json())",
                "new_code": "app.use(express.json())"
            }
        }
    ],
    "alternative_strategy": {
        "description": "If fixes don't work, try this",
        "dependencies_to_skip": ["package1"],
        "dependencies_to_downgrade": {"package2": "older-version"}
    },
    "confidence": "high" | "medium" | "low",
    "next_steps": ["Apply fix 1", "Re-run validation", "If still fails, try alternative"]
}

Be thorough, specific, and provide actionable fixes."""

        super().__init__(
            name="error_analyzer",
            system_prompt=system_prompt,
            llm_provider=llm_provider,
            llm_model=llm_model
        )

    def execute(self, input_data: Dict) -> Dict:
        """Execute error analysis.

        Args:
            input_data: Dictionary with:
                - validation_result: Failed validation result from RuntimeValidator
                - migration_plan: Migration plan that was being tested
                - project_path: Path to project (optional, for code inspection)

        Returns:
            Dictionary with error analysis and fix suggestions
        """
        try:
            validation_result = input_data.get("validation_result")
            migration_plan = input_data.get("migration_plan")
            project_path = input_data.get("project_path")

            if not validation_result:
                return {
                    "status": "error",
                    "error": "validation_result is required"
                }

            self.logger.info("starting_error_analysis",
                           has_migration_plan=migration_plan is not None,
                           has_project_path=project_path is not None)

            # Extract error information
            error_info = self._extract_error_info(validation_result)
            self.logger.info("error_info_extracted",
                           error_count=len(error_info.get("errors", [])),
                           has_install_logs=bool(error_info.get("install_logs")),
                           has_runtime_logs=bool(error_info.get("runtime_logs")))

            # Analyze with LLM
            analysis = self._analyze_with_llm(error_info, migration_plan)

            # Enhance with code inspection if project path provided
            if project_path and analysis.get("error_location"):
                code_context = self._get_code_context(project_path, analysis["error_location"])
                if code_context:
                    analysis["code_context"] = code_context

            # Log cost
            cost_report = self.llm.cost_tracker.get_report()
            self.logger.info("error_analysis_complete",
                           error_category=analysis.get("error_category", "unknown"),
                           fix_count=len(analysis.get("fix_suggestions", [])),
                           confidence=analysis.get("confidence", "unknown"),
                           cost_usd=cost_report["total_cost_usd"])

            return {
                "status": "success",
                "analysis": analysis,
                "error_info": error_info,
                "cost_report": cost_report
            }

        except Exception as e:
            self.logger.error("error_analysis_failed", error=str(e), exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }

    def _extract_error_info(self, validation_result: Dict) -> Dict:
        """Extract error information from validation result.

        Args:
            validation_result: Validation result dictionary

        Returns:
            Extracted error information
        """
        error_info = {
            "status": validation_result.get("status"),
            "errors": validation_result.get("errors", []),
            "install_logs": validation_result.get("install_logs", ""),
            "runtime_logs": validation_result.get("runtime_logs", ""),
            "health_check_logs": validation_result.get("health_check_logs", ""),
            "build_success": validation_result.get("build_success", False),
            "install_success": validation_result.get("install_success", False),
            "runtime_success": validation_result.get("runtime_success", False),
            "health_check_success": validation_result.get("health_check_success", False)
        }

        # Extract key error messages
        key_errors = []

        # From install logs
        if not error_info["install_success"] and error_info["install_logs"]:
            key_errors.extend(self._extract_npm_errors(error_info["install_logs"]))
            key_errors.extend(self._extract_pip_errors(error_info["install_logs"]))

        # From runtime logs
        if not error_info["runtime_success"] and error_info["runtime_logs"]:
            key_errors.extend(self._extract_runtime_errors(error_info["runtime_logs"]))

        error_info["key_errors"] = key_errors

        return error_info

    def _extract_npm_errors(self, logs: str) -> List[str]:
        """Extract npm-specific errors from logs.

        Args:
            logs: npm install logs

        Returns:
            List of error messages
        """
        errors = []

        # ERESOLVE peer dependency warnings
        peer_dep_pattern = r"ERESOLVE.*?peer (.*?)@(.*?) from (.*?)@(.*?)\n"
        for match in re.finditer(peer_dep_pattern, logs):
            errors.append(f"Peer dependency issue: {match.group(1)} required by {match.group(3)}")

        # npm ERR! messages
        err_pattern = r"npm ERR! (.*?)\n"
        for match in re.finditer(err_pattern, logs):
            error_msg = match.group(1).strip()
            if error_msg and not error_msg.startswith("code "):
                errors.append(f"npm error: {error_msg}")

        # Missing package errors
        missing_pattern = r"Cannot find module ['\"](.*?)['\"]"
        for match in re.finditer(missing_pattern, logs):
            errors.append(f"Missing module: {match.group(1)}")

        return errors[:10]  # Limit to 10 most relevant

    def _extract_pip_errors(self, logs: str) -> List[str]:
        """Extract pip-specific errors from logs.

        Args:
            logs: pip install logs

        Returns:
            List of error messages
        """
        errors = []

        # ERROR: messages
        err_pattern = r"ERROR: (.*?)\n"
        for match in re.finditer(err_pattern, logs):
            errors.append(f"pip error: {match.group(1).strip()}")

        # No matching distribution
        no_match_pattern = r"No matching distribution found for (.*?)\n"
        for match in re.finditer(no_match_pattern, logs):
            errors.append(f"Package not found: {match.group(1).strip()}")

        # Incompatible versions
        incompatible_pattern = r"has requirement (.*?), but (.*?) which is incompatible"
        for match in re.finditer(incompatible_pattern, logs):
            errors.append(f"Version conflict: {match.group(1)}")

        return errors[:10]

    def _extract_runtime_errors(self, logs: str) -> List[str]:
        """Extract runtime errors from application logs.

        Args:
            logs: Runtime logs

        Returns:
            List of error messages
        """
        errors = []

        # JavaScript/Node.js errors
        # TypeError, ReferenceError, etc.
        js_error_pattern = r"(TypeError|ReferenceError|SyntaxError|Error): (.*?)\n"
        for match in re.finditer(js_error_pattern, logs):
            errors.append(f"{match.group(1)}: {match.group(2).strip()}")

        # Python exceptions
        py_error_pattern = r"(.*?Error): (.*?)\n"
        for match in re.finditer(py_error_pattern, logs):
            error_type, message = match.groups()
            if error_type.endswith("Error"):
                errors.append(f"{error_type}: {message.strip()}")

        # Stack trace file locations
        stack_pattern = r"at (.*?) \((.*?):(\d+):(\d+)\)"
        for match in re.finditer(stack_pattern, logs):
            function, file, line, col = match.groups()
            errors.append(f"Error at {file}:{line} in {function}")

        return errors[:10]

    def _analyze_with_llm(self, error_info: Dict, migration_plan: Optional[Dict]) -> Dict:
        """Analyze errors with LLM.

        Args:
            error_info: Extracted error information
            migration_plan: Migration plan (optional)

        Returns:
            Analysis results
        """
        # Build analysis prompt
        prompt = self._build_analysis_prompt(error_info, migration_plan)

        self.logger.info("sending_to_llm", prompt_length=len(prompt))

        # Get LLM analysis
        llm_response = self.think(prompt, max_tokens=3000)

        self.logger.info("llm_response_received", response_length=len(llm_response))

        # Parse response
        try:
            # Remove markdown code blocks if present
            cleaned = llm_response.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                cleaned = "\n".join(lines[1:-1]) if len(lines) > 2 else cleaned

            analysis = json.loads(cleaned)
            return analysis

        except json.JSONDecodeError as e:
            self.logger.error("json_parse_error", error=str(e), response=llm_response[:500])

            # Return fallback analysis
            return self._fallback_analysis(error_info)

    def _build_analysis_prompt(self, error_info: Dict, migration_plan: Optional[Dict]) -> str:
        """Build analysis prompt for LLM.

        Args:
            error_info: Error information
            migration_plan: Migration plan (optional)

        Returns:
            Prompt string
        """
        prompt_parts = []

        prompt_parts.append("Analyze these validation errors and provide fix suggestions.\n")

        # Validation results
        prompt_parts.append("VALIDATION RESULTS:")
        prompt_parts.append(f"- Build Success: {error_info['build_success']}")
        prompt_parts.append(f"- Install Success: {error_info['install_success']}")
        prompt_parts.append(f"- Runtime Success: {error_info['runtime_success']}")
        prompt_parts.append(f"- Health Check Success: {error_info['health_check_success']}")
        prompt_parts.append("")

        # Key errors
        if error_info.get("key_errors"):
            prompt_parts.append("KEY ERRORS:")
            for error in error_info["key_errors"]:
                prompt_parts.append(f"- {error}")
            prompt_parts.append("")

        # Full error list
        if error_info.get("errors"):
            prompt_parts.append("ALL ERRORS:")
            for error in error_info["errors"][:20]:  # Limit to 20
                prompt_parts.append(f"- {error}")
            prompt_parts.append("")

        # Install logs (excerpt)
        if error_info.get("install_logs"):
            logs = error_info["install_logs"]
            if len(logs) > 2000:
                logs = logs[-2000:]  # Last 2000 chars
            prompt_parts.append("INSTALL LOGS (excerpt):")
            prompt_parts.append(logs)
            prompt_parts.append("")

        # Runtime logs (excerpt)
        if error_info.get("runtime_logs"):
            logs = error_info["runtime_logs"]
            if len(logs) > 2000:
                logs = logs[-2000:]
            prompt_parts.append("RUNTIME LOGS (excerpt):")
            prompt_parts.append(logs)
            prompt_parts.append("")

        # Migration plan context
        if migration_plan:
            prompt_parts.append("MIGRATION PLAN BEING TESTED:")
            dependencies = migration_plan.get("dependencies", {})
            for name, info in dependencies.items():
                if info.get("action") == "upgrade":
                    current = info.get("current_version", "?")
                    target = info.get("target_version", "?")
                    prompt_parts.append(f"- {name}: {current} → {target} (risk: {info.get('risk', '?')})")
                elif info.get("action") == "remove":
                    prompt_parts.append(f"- {name}: REMOVED ({info.get('reason', 'deprecated')})")
            prompt_parts.append("")

        prompt_parts.append("TASKS:")
        prompt_parts.append("1. Identify the error category (missing_dependency, api_change, config_issue, version_conflict, unknown)")
        prompt_parts.append("2. Determine root cause - what exactly went wrong?")
        prompt_parts.append("3. Identify which dependency(ies) caused the issue")
        prompt_parts.append("4. Generate specific fix suggestions with commands and code changes")
        prompt_parts.append("5. Provide alternative strategy if fixes might not work")
        prompt_parts.append("6. Rate your confidence level (high/medium/low)")
        prompt_parts.append("")
        prompt_parts.append("OUTPUT FORMAT: Return ONLY valid JSON matching the specified schema. No markdown, no explanations outside JSON.")

        return "\n".join(prompt_parts)

    def _fallback_analysis(self, error_info: Dict) -> Dict:
        """Generate fallback analysis when LLM parsing fails.

        Args:
            error_info: Error information

        Returns:
            Basic analysis
        """
        # Determine error category from key errors
        error_category = "unknown"
        key_errors = error_info.get("key_errors", [])

        # Check for API changes first (more specific)
        if any("typeerror" in e.lower() or "not a function" in e.lower() or "is not defined" in e.lower() for e in key_errors):
            error_category = "api_change"
        # Check for missing dependencies (use word boundaries to avoid false positives)
        elif any("peer dep" in e.lower() or "cannot find module" in e.lower() or "missing:" in e.lower() for e in key_errors):
            error_category = "missing_dependency"
        elif any("conflict" in e.lower() for e in key_errors):
            error_category = "version_conflict"

        return {
            "analysis_status": "success",
            "error_category": error_category,
            "root_cause": "See error logs for details",
            "problematic_dependencies": [],
            "error_location": None,
            "fix_suggestions": [
                {
                    "priority": 1,
                    "type": "review_logs",
                    "description": "Review error logs manually to identify the issue",
                    "commands": [],
                    "code_changes": None
                }
            ],
            "alternative_strategy": {
                "description": "Rollback to previous versions",
                "dependencies_to_skip": [],
                "dependencies_to_downgrade": {}
            },
            "confidence": "low",
            "next_steps": [
                "Review error logs",
                "Check dependency documentation",
                "Consider rolling back changes"
            ]
        }

    def _get_code_context(self, project_path: str, error_location: Dict) -> Optional[Dict]:
        """Get code context around error location.

        Args:
            project_path: Path to project
            error_location: Error location info with file and line

        Returns:
            Code context dictionary or None
        """
        try:
            file_path = error_location.get("file")
            line_number = error_location.get("line")

            if not file_path or not line_number:
                return None

            full_path = Path(project_path) / file_path

            if not full_path.exists():
                return None

            # Read file
            with open(full_path, 'r') as f:
                lines = f.readlines()

            # Get context (5 lines before and after)
            start = max(0, line_number - 6)
            end = min(len(lines), line_number + 5)

            context_lines = []
            for i in range(start, end):
                prefix = ">>>" if i == line_number - 1 else "   "
                context_lines.append(f"{prefix} {i+1:4d} | {lines[i].rstrip()}")

            return {
                "file": file_path,
                "line": line_number,
                "context": "\n".join(context_lines)
            }

        except Exception as e:
            self.logger.warning("code_context_failed", error=str(e), file=file_path)
            return None


def main():
    """Standalone test of Error Analyzer Agent."""

    print("=" * 80)
    print("ERROR ANALYZER AGENT - STANDALONE TEST")
    print("=" * 80)

    # Sample validation failure
    sample_validation_failure = {
        "status": "failed",
        "build_success": True,
        "install_success": False,
        "runtime_success": False,
        "health_check_success": False,
        "errors": [
            "npm ERR! peer dep missing: express@^5.0.0, required by body-parser@2.0.0",
            "Error: Cannot find module 'body-parser'",
            "TypeError: app.use is not a function at /app/src/server.js:15:5"
        ],
        "install_logs": """
npm WARN ERESOLVE overriding peer dependency
npm WARN ERESOLVE peer dep missing: express@^5.0.0, required by body-parser@2.0.0
npm ERR! code ERESOLVE
npm ERR! ERESOLVE unable to resolve dependency tree
npm ERR!
npm ERR! While resolving: test-app@1.0.0
npm ERR! Found: express@4.19.2
npm ERR! node_modules/express
npm ERR!   express@"4.19.2" from the root project
npm ERR!
npm ERR! Could not resolve dependency:
npm ERR! peer express@"^5.0.0" from body-parser@2.0.0
        """,
        "runtime_logs": """
Error: Cannot find module 'body-parser'
Require stack:
- /app/src/server.js
- /app/src/app.js
    at Module._resolveFilename (node:internal/modules/cjs/loader:1145:15)
    at Module._load (node:internal/modules/cjs/loader:986:27)
TypeError: app.use is not a function
    at Object.<anonymous> (/app/src/server.js:15:5)
    at Module._compile (node:internal/modules/cjs/loader:1469:14)
        """,
        "health_check_logs": "Process not running"
    }

    sample_migration_plan = {
        "project_type": "nodejs",
        "dependencies": {
            "express": {
                "current_version": "4.16.0",
                "target_version": "4.19.2",
                "action": "upgrade",
                "risk": "low"
            },
            "body-parser": {
                "current_version": "1.18.3",
                "target_version": "N/A",
                "action": "remove",
                "risk": "low",
                "reason": "Deprecated - built into Express 4.16+"
            }
        },
        "overall_risk": "low"
    }

    # Create agent
    print("\n1. Creating Error Analyzer Agent...")
    agent = ErrorAnalyzerAgent()
    print(f"   Provider: {agent.llm.get_provider_name()}")
    print(f"   Model: {agent.llm.model}")

    # Execute analysis
    print("\n2. Analyzing validation failure...")
    result = agent.execute({
        "validation_result": sample_validation_failure,
        "migration_plan": sample_migration_plan
    })

    # Display results
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)

    if result["status"] == "error":
        print(f"\nERROR: {result['error']}")
        return 1

    analysis = result["analysis"]

    print(f"\n📊 Analysis Status: {analysis.get('analysis_status', 'unknown').upper()}")
    print(f"📁 Error Category: {analysis.get('error_category', 'unknown').upper()}")
    print(f"🎯 Confidence: {analysis.get('confidence', 'unknown').upper()}")

    print(f"\n🔍 Root Cause:")
    print(f"   {analysis.get('root_cause', 'Unknown')}")

    problematic = analysis.get('problematic_dependencies', [])
    if problematic:
        print(f"\n⚠️  Problematic Dependencies:")
        for dep in problematic:
            print(f"   - {dep}")

    fix_suggestions = analysis.get('fix_suggestions', [])
    if fix_suggestions:
        print(f"\n🔧 Fix Suggestions ({len(fix_suggestions)}):")
        for i, fix in enumerate(fix_suggestions, 1):
            print(f"\n   Fix {i} (Priority {fix.get('priority', '?')}):")
            print(f"   Type: {fix.get('type', 'unknown')}")
            print(f"   Description: {fix.get('description', 'N/A')}")

            commands = fix.get('commands', [])
            if commands:
                print(f"   Commands:")
                for cmd in commands:
                    print(f"      $ {cmd}")

            code_changes = fix.get('code_changes')
            if code_changes:
                print(f"   Code Changes:")
                print(f"      File: {code_changes.get('file', 'N/A')}")
                print(f"      Old: {code_changes.get('old_code', 'N/A')}")
                print(f"      New: {code_changes.get('new_code', 'N/A')}")

    alt_strategy = analysis.get('alternative_strategy')
    if alt_strategy:
        print(f"\n🔄 Alternative Strategy:")
        print(f"   {alt_strategy.get('description', 'N/A')}")

        skip = alt_strategy.get('dependencies_to_skip', [])
        if skip:
            print(f"   Skip: {', '.join(skip)}")

        downgrade = alt_strategy.get('dependencies_to_downgrade', {})
        if downgrade:
            print(f"   Downgrade:")
            for pkg, version in downgrade.items():
                print(f"      {pkg} → {version}")

    next_steps = analysis.get('next_steps', [])
    if next_steps:
        print(f"\n📋 Next Steps:")
        for i, step in enumerate(next_steps, 1):
            print(f"   {i}. {step}")

    # Cost Report
    print("\n" + "=" * 80)
    print("COST REPORT")
    print("=" * 80)
    cost_report = result["cost_report"]
    print(f"Provider: {cost_report['provider']}")
    print(f"Model: {cost_report['model']}")
    print(f"Total Tokens: {cost_report['total_tokens']:,}")
    print(f"Total Cost: ${cost_report['total_cost_usd']:.4f}")

    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())
