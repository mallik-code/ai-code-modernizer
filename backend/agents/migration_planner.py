"""Migration Planner Agent

Analyzes project dependencies, identifies outdated packages, researches breaking changes,
and creates phased migration strategies for safe upgrades.

Capabilities:
- Parses package.json (Node.js) and requirements.txt (Python)
- Identifies outdated dependencies and their latest versions
- Researches breaking changes and security vulnerabilities
- Assesses migration risk (low/medium/high)
- Creates phased migration plans with rollback strategies
"""

import json
import re
import sys
from typing import Dict, List, Optional
from pathlib import Path

from agents.base import BaseAgent


class MigrationPlannerAgent(BaseAgent):
    """Agent for analyzing dependencies and planning migration strategies."""

    def __init__(self, llm_provider: Optional[str] = None, llm_model: Optional[str] = None):
        system_prompt = """You are an expert software dependency migration planner.

Your role:
1. Analyze project dependencies (package.json or requirements.txt)
2. Identify outdated packages and their latest stable versions
3. Research breaking changes between versions
4. Assess migration risk (low/medium/high)
5. Create phased migration strategies
6. Identify packages that should be removed (deprecated)

When analyzing dependencies:
- Consider semantic versioning (major.minor.patch)
- Major version changes = potential breaking changes
- Identify deprecated packages (e.g., body-parser in Express 5+)
- Check for security vulnerabilities
- Consider dependency conflicts

Output Format:
Return a structured JSON migration plan with:
{
    "project_type": "nodejs" or "python",
    "analysis_date": "ISO timestamp",
    "dependencies": {
        "package_name": {
            "current_version": "x.y.z",
            "target_version": "a.b.c",
            "action": "upgrade" or "remove" or "keep",
            "breaking_changes": ["list of breaking changes"],
            "risk": "low" or "medium" or "high",
            "reason": "explanation"
        }
    },
    "migration_strategy": {
        "total_phases": 3,
        "phases": [
            {
                "phase": 1,
                "name": "Low-risk updates",
                "dependencies": ["pkg1", "pkg2"],
                "description": "Patch and minor version updates",
                "estimated_time": "1 hour",
                "rollback_plan": "revert to previous package.json"
            }
        ]
    },
    "recommendations": ["list of recommendations"],
    "estimated_total_time": "X hours",
    "overall_risk": "low/medium/high"
}

Be thorough, accurate, and prioritize safety."""

        super().__init__(
            name="migration_planner",
            system_prompt=system_prompt,
            llm_provider=llm_provider,
            llm_model=llm_model
        )

    def execute(self, input_data: Dict) -> Dict:
        """Execute migration planning.

        Args:
            input_data: Dictionary with:
                - project_path: Path to project directory
                - dependency_file: Optional specific file (package.json or requirements.txt)

        Returns:
            Dictionary with migration plan and analysis
        """
        try:
            project_path = input_data.get("project_path")
            if not project_path:
                return {
                    "status": "error",
                    "error": "project_path is required"
                }

            self.logger.info("starting_migration_analysis", project_path=project_path)

            # Detect project type and read dependency file
            dependency_data = self._read_dependencies(project_path, input_data.get("dependency_file"))
            if "error" in dependency_data:
                return dependency_data

            self.logger.info("dependencies_detected",
                           project_type=dependency_data["project_type"],
                           file=dependency_data["file_path"],
                           dependency_count=len(dependency_data.get("dependencies", {})))

            # Analyze dependencies with LLM
            analysis_prompt = self._build_analysis_prompt(dependency_data)
            self.logger.info("sending_to_llm", prompt_length=len(analysis_prompt))

            print("PROMPT SENT TO LLM:")
            print(analysis_prompt)
            print("="*50)

            llm_response = self.think(analysis_prompt, max_tokens=4000)

            print("RESPONSE RECEIVED FROM LLM:")
            print(llm_response)
            print("="*50)

            self.logger.info("llm_response_received", response_length=len(llm_response))

            # Parse LLM response
            migration_plan = self._parse_migration_plan(llm_response)
            if "error" in migration_plan:
                return migration_plan

            # Add metadata
            migration_plan["project_path"] = project_path
            migration_plan["dependency_file"] = dependency_data["file_path"]
            migration_plan["raw_dependencies"] = dependency_data["raw_content"]

            # Log cost
            cost_report = self.llm.cost_tracker.get_report()
            self.logger.info("migration_plan_complete",
                           total_dependencies=len(migration_plan.get("dependencies", {})),
                           phases=migration_plan.get("migration_strategy", {}).get("total_phases", 0),
                           overall_risk=migration_plan.get("overall_risk", "unknown"),
                           cost_usd=cost_report["total_cost_usd"])

            return {
                "status": "success",
                "migration_plan": migration_plan,
                "cost_report": cost_report
            }

        except Exception as e:
            self.logger.error("migration_planning_failed", error=str(e), exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }

    def _read_dependencies(self, project_path: str, dependency_file: Optional[str] = None) -> Dict:
        """Read and parse dependency file from project.

        Args:
            project_path: Path to project directory
            dependency_file: Optional specific file to read

        Returns:
            Dictionary with project_type, file_path, dependencies, and raw_content
        """
        project_dir = Path(project_path)

        # Determine which file to read
        if dependency_file:
            file_path = project_dir / dependency_file
            if not file_path.exists():
                return {
                    "status": "error",
                    "error": f"Specified dependency file not found: {dependency_file}"
                }
        else:
            # Auto-detect
            package_json = project_dir / "package.json"
            requirements_txt = project_dir / "requirements.txt"

            if package_json.exists():
                file_path = package_json
            elif requirements_txt.exists():
                file_path = requirements_txt
            else:
                return {
                    "status": "error",
                    "error": "No package.json or requirements.txt found in project"
                }

        # Read file
        try:
            content = self.tools.read_file(str(file_path))
            self.logger.info("dependency_file_read", file=str(file_path), size=len(content))
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to read dependency file: {str(e)}"
            }

        # Parse based on file type
        project_type = "nodejs" if file_path.name == "package.json" else "python"

        if project_type == "nodejs":
            try:
                parsed = json.loads(content)
                dependencies = {
                    **parsed.get("dependencies", {}),
                    **parsed.get("devDependencies", {})
                }
            except json.JSONDecodeError as e:
                return {
                    "status": "error",
                    "error": f"Invalid JSON in package.json: {str(e)}"
                }
        else:  # Python
            # Simple requirements.txt parsing (package==version or package>=version)
            dependencies = {}
            for line in content.split("\n"):
                line = line.strip()
                if line and not line.startswith("#"):
                    # Match package==version or package>=version
                    match = re.match(r"([a-zA-Z0-9-_.]+)\s*([>=<~!]+)\s*([0-9.]+)", line)
                    if match:
                        pkg_name, operator, version = match.groups()
                        dependencies[pkg_name] = f"{operator}{version}"
                    else:
                        # Package without version
                        dependencies[line] = "latest"

        return {
            "project_type": project_type,
            "file_path": str(file_path),
            "dependencies": dependencies,
            "raw_content": content
        }

    def _build_analysis_prompt(self, dependency_data: Dict) -> str:
        """Build prompt for LLM analysis.

        Args:
            dependency_data: Parsed dependency information

        Returns:
            Formatted prompt string
        """
        project_type = dependency_data["project_type"]
        dependencies = dependency_data["dependencies"]

        prompt = f"""Analyze these {project_type.upper()} dependencies and create a migration plan.

PROJECT TYPE: {project_type}
DEPENDENCY FILE: {dependency_data['file_path']}

CURRENT DEPENDENCIES:
{json.dumps(dependencies, indent=2)}

TASKS:
1. For each dependency:
   - Determine if it's outdated (check major/minor versions)
   - Identify the latest stable version
   - Research known breaking changes between current and target version
   - Assess migration risk (low/medium/high)
   - Determine action: upgrade, remove (if deprecated), or keep

2. Create a phased migration strategy:
   - Phase 1: Low-risk updates (patch versions, minor updates with no breaking changes)
   - Phase 2: Medium-risk updates (minor updates with small breaking changes)
   - Phase 3: High-risk updates (major version changes, deprecated package removal)

3. Provide:
   - Rollback plan for each phase
   - Estimated time per phase
   - Overall recommendations
   - Overall risk assessment

IMPORTANT:
- For Node.js: Check if body-parser is used (deprecated in Express 5+)
- For Python: Check for packages with known security vulnerabilities
- Consider dependency conflicts (e.g., package A requires old version of package B)
- Be specific about breaking changes

OUTPUT FORMAT: Return ONLY valid JSON matching the specified schema. No markdown, no explanations outside JSON."""

        return prompt

    def _parse_migration_plan(self, llm_response: str) -> Dict:
        """Parse LLM response into structured migration plan.

        Args:
            llm_response: Raw LLM response

        Returns:
            Parsed migration plan dictionary
        """
        try:
            # Remove markdown code blocks if present
            cleaned = llm_response.strip()
            if cleaned.startswith("```"):
                # Remove ```json and ``` markers
                lines = cleaned.split("\n")
                cleaned = "\n".join(lines[1:-1]) if len(lines) > 2 else cleaned

            # Parse JSON
            plan = json.loads(cleaned)

            # Handle different formats for dependencies (some LLMs return array format)
            # Handle different field names that different LLMs might use
            if "dependencies" not in plan and "dependenciesAnalysis" in plan:
                # Some LLMs return dependencies in a differently named field
                plan["dependencies"] = plan["dependenciesAnalysis"]
                del plan["dependenciesAnalysis"]
            
            if "dependencies" in plan:
                if isinstance(plan["dependencies"], list):
                    # Convert array format to object format
                    # Array format: [{"name": "pkg", ...}, ...]
                    # Object format: {"pkg": {...}, ...}
                    dependencies_obj = {}
                    for dep in plan["dependencies"]:
                        if "name" in dep:
                            pkg_name = dep.pop("name")  # Remove 'name' and use as key
                            dependencies_obj[pkg_name] = dep
                    plan["dependencies"] = dependencies_obj

            # Validate required fields
            required_fields = ["dependencies", "migration_strategy"]
            for field in required_fields:
                if field not in plan:
                    self.logger.warning("missing_field_in_plan", field=field)

            return plan

        except json.JSONDecodeError as e:
            self.logger.error("json_parse_error", error=str(e), response=llm_response[:500])
            return {
                "status": "error",
                "error": f"Failed to parse LLM response as JSON: {str(e)}",
                "raw_response": llm_response
            }


def main():
    """Standalone test of Migration Planner Agent."""

    print("=" * 80)
    print("MIGRATION PLANNER AGENT - STANDALONE TEST")
    print("=" * 80)

    # Test with sample Express app
    test_project = Path(__file__).parent.parent / "tests" / "sample_projects" / "express-app"

    if not test_project.exists():
        print(f"ERROR: Test project not found at {test_project}")
        print("Please create the sample project first.")
        return 1

    print(f"\nTest Project: {test_project}")
    print(f"Testing with: package.json")

    # Create agent
    print("\n1. Creating Migration Planner Agent...")
    agent = MigrationPlannerAgent()
    print(f"   Provider: {agent.llm.get_provider_name()}")
    print(f"   Model: {agent.llm.model}")

    # Execute analysis
    print("\n2. Analyzing dependencies...")
    result = agent.execute({
        "project_path": str(test_project)
    })

    # Display results
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)

    if result["status"] == "error":
        print(f"\nERROR: {result['error']}")
        return 1

    plan = result["migration_plan"]

    print(f"\nProject Type: {plan.get('project_type', 'unknown').upper()}")
    print(f"Analysis Date: {plan.get('analysis_date', 'N/A')}")
    print(f"Overall Risk: {plan.get('overall_risk', 'unknown').upper()}")
    print(f"Estimated Time: {plan.get('estimated_total_time', 'unknown')}")

    # Dependencies
    print(f"\n--- DEPENDENCIES ({len(plan.get('dependencies', {}))}) ---")
    for pkg_name, pkg_info in plan.get("dependencies", {}).items():
        action = pkg_info.get("action", "unknown")
        risk = pkg_info.get("risk", "?")
        current = pkg_info.get("current_version", "?")
        target = pkg_info.get("target_version", "?")

        print(f"\n{pkg_name}:")
        print(f"  Action: {action.upper()}")
        print(f"  Current: {current} -> Target: {target}")
        print(f"  Risk: {risk.upper()}")
        if pkg_info.get("breaking_changes"):
            print(f"  Breaking Changes: {len(pkg_info['breaking_changes'])}")

    # Migration Strategy
    strategy = plan.get("migration_strategy", {})
    phases = strategy.get("phases", [])
    print(f"\n--- MIGRATION STRATEGY ({len(phases)} phases) ---")
    for phase in phases:
        print(f"\nPhase {phase.get('phase', '?')}: {phase.get('name', 'Unknown')}")
        print(f"  Dependencies: {', '.join(phase.get('dependencies', []))}")
        print(f"  Time: {phase.get('estimated_time', 'unknown')}")
        print(f"  Description: {phase.get('description', 'N/A')}")

    # Recommendations
    recommendations = plan.get("recommendations", [])
    if recommendations:
        print(f"\n--- RECOMMENDATIONS ({len(recommendations)}) ---")
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec}")

    # Cost Report
    print("\n" + "=" * 80)
    print("COST REPORT")
    print("=" * 80)
    cost_report = result["cost_report"]
    print(f"Provider: {agent.llm.get_provider_name()}")
    print(f"Model: {agent.llm.model}")
    print(f"Total Tokens: {cost_report['total_input_tokens'] + cost_report['total_output_tokens']:,}")
    print(f"  Input: {cost_report['total_input_tokens']:,}")
    print(f"  Output: {cost_report['total_output_tokens']:,}")
    print(f"Total Cost: ${cost_report['total_cost_usd']:.4f}")

    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())
