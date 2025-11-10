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

            # Ensure project_type is set correctly if LLM didn't provide it
            if migration_plan.get("project_type") == "unknown":
                migration_plan["project_type"] = dependency_data["project_type"]

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
            # Check all possible variations: dependencies, dependenciesAnalysis, dependencyAnalysis, dependency_analysis
            if "dependencies" not in plan:
                if "dependenciesAnalysis" in plan:
                    plan["dependencies"] = plan["dependenciesAnalysis"]
                    del plan["dependenciesAnalysis"]
                elif "dependencyAnalysis" in plan:
                    plan["dependencies"] = plan["dependencyAnalysis"]
                    del plan["dependencyAnalysis"]
                elif "dependency_analysis" in plan:
                    plan["dependencies"] = plan["dependency_analysis"]
                    del plan["dependency_analysis"]

            if "dependencies" in plan:
                if isinstance(plan["dependencies"], list):
                    # Convert array format to object format
                    # Array format: [{"name": "pkg", ...}, ...]
                    # Object format: {"pkg": {...}, ...}
                    dependencies_obj = {}
                    for dep in plan["dependencies"]:
                        if "name" in dep:
                            pkg_name = dep.pop("name")  # Remove 'name' and use as key

                            # Normalize field names (different LLMs use different naming)
                            normalized_dep = {}
                            for key, value in dep.items():
                                # Convert camelCase to snake_case and map to standard fields
                                if key in ["currentVersion", "current_version"]:
                                    normalized_dep["current_version"] = value
                                elif key in ["latestVersion", "latest_version", "target_version", "targetVersion"]:
                                    normalized_dep["target_version"] = value
                                elif key in ["migrationRisk", "migration_risk", "risk"]:
                                    normalized_dep["risk"] = value.lower() if isinstance(value, str) else value
                                elif key in ["breakingChanges", "breaking_changes"]:
                                    # Handle both string and list formats
                                    if isinstance(value, str):
                                        normalized_dep["breaking_changes"] = [value] if value else []
                                    else:
                                        normalized_dep["breaking_changes"] = value
                                elif key == "action":
                                    normalized_dep["action"] = value
                                elif key in ["notes", "reason"]:
                                    normalized_dep["reason"] = value
                                else:
                                    # Keep other fields as-is
                                    normalized_dep[key] = value

                            dependencies_obj[pkg_name] = normalized_dep
                    plan["dependencies"] = dependencies_obj
                elif isinstance(plan["dependencies"], dict):
                    # Object format already, but normalize field names
                    dependencies_obj = {}
                    for pkg_name, dep in plan["dependencies"].items():
                        normalized_dep = {}
                        for key, value in dep.items():
                            # Convert camelCase to snake_case and map to standard fields
                            if key in ["currentVersion", "current_version"]:
                                normalized_dep["current_version"] = value
                            elif key in ["latestVersion", "latest_version", "target_version", "targetVersion"]:
                                normalized_dep["target_version"] = value
                            elif key in ["migrationRisk", "migration_risk", "risk"]:
                                normalized_dep["risk"] = value.lower() if isinstance(value, str) else value
                            elif key in ["breakingChanges", "breaking_changes"]:
                                # Handle both string and list formats
                                if isinstance(value, str):
                                    normalized_dep["breaking_changes"] = [value] if value else []
                                else:
                                    normalized_dep["breaking_changes"] = value
                            elif key == "action":
                                normalized_dep["action"] = value
                            elif key in ["notes", "reason"]:
                                normalized_dep["reason"] = value
                            else:
                                # Keep other fields as-is
                                normalized_dep[key] = value

                        dependencies_obj[pkg_name] = normalized_dep
                    plan["dependencies"] = dependencies_obj

            # Normalize migration strategy format
            # Check all possible variations: migration_strategy, migrationStrategy, migrationPlan, migration_plan
            if "migration_strategy" not in plan:
                if "migrationStrategy" in plan:
                    strategy = plan["migrationStrategy"]
                    del plan["migrationStrategy"]
                elif "migrationPlan" in plan:
                    strategy = plan["migrationPlan"]
                    del plan["migrationPlan"]
                elif "migration_plan" in plan:
                    strategy = plan["migration_plan"]
                    del plan["migration_plan"]
                else:
                    strategy = None
            else:
                strategy = plan["migration_strategy"]

            # Process strategy if found
            if strategy:
                # Check if strategy already has "phases" as an array (Gemini format)
                if "phases" in strategy and isinstance(strategy["phases"], list):
                    # Normalize each phase to ensure all fields are present
                    normalized_phases = []
                    for i, phase_data in enumerate(strategy["phases"], 1):
                        normalized_phase = {
                            "phase": phase_data.get("phase", i),  # Use index if phase number not provided
                            "name": phase_data.get("name", phase_data.get("description", f"Phase {i}")),
                            "dependencies": phase_data.get("dependencies", []),
                            "description": phase_data.get("description", phase_data.get("name", "")),
                            "estimated_time": phase_data.get("estimatedTime", phase_data.get("estimated_time", "unknown")),
                            "rollback_plan": phase_data.get("rollbackPlan", phase_data.get("rollback_plan", ""))
                        }
                        normalized_phases.append(normalized_phase)

                    plan["migration_strategy"] = {
                        "total_phases": len(normalized_phases),
                        "phases": normalized_phases
                    }
                # Convert phase1/phase2/phase3 or phase_1/phase_2/phase_3 format to phases array
                elif "phase1" in strategy or "phase2" in strategy or "phase3" in strategy or \
                   "phase_1" in strategy or "phase_2" in strategy or "phase_3" in strategy:
                    phases = []
                    phase_num = 1

                    # Try both formats: phase1 and phase_1
                    while f"phase{phase_num}" in strategy or f"phase_{phase_num}" in strategy:
                        phase_key = f"phase{phase_num}" if f"phase{phase_num}" in strategy else f"phase_{phase_num}"
                        phase_data = strategy[phase_key]
                        phases.append({
                            "phase": phase_num,
                            "name": phase_data.get("description", f"Phase {phase_num}"),
                            "dependencies": phase_data.get("dependencies", []),
                            "description": phase_data.get("description", ""),
                            "estimated_time": phase_data.get("estimatedTime", phase_data.get("estimated_time", "unknown")),
                            "rollback_plan": phase_data.get("rollbackPlan", phase_data.get("rollback_plan", ""))
                        })
                        phase_num += 1

                    plan["migration_strategy"] = {
                        "total_phases": len(phases),
                        "phases": phases
                    }
                else:
                    # Unknown format, keep as-is
                    plan["migration_strategy"] = strategy

            # Normalize top-level fields
            if "overallRiskAssessment" in plan and "overall_risk" not in plan:
                # Extract just the risk level (low/medium/high) from assessment text
                assessment = plan["overallRiskAssessment"]
                if isinstance(assessment, str):
                    assessment_lower = assessment.lower()
                    if "high" in assessment_lower:
                        plan["overall_risk"] = "high"
                    elif "medium" in assessment_lower:
                        plan["overall_risk"] = "medium"
                    elif "low" in assessment_lower:
                        plan["overall_risk"] = "low"
                    else:
                        plan["overall_risk"] = "medium"  # default
                del plan["overallRiskAssessment"]
            elif "overall_risk_assessment" in plan and "overall_risk" not in plan:
                # Handle snake_case version
                assessment = plan["overall_risk_assessment"]
                if isinstance(assessment, str):
                    assessment_lower = assessment.lower()
                    if "high" in assessment_lower:
                        plan["overall_risk"] = "high"
                    elif "medium" in assessment_lower:
                        plan["overall_risk"] = "medium"
                    elif "low" in assessment_lower:
                        plan["overall_risk"] = "low"
                    else:
                        plan["overall_risk"] = "medium"  # default
                del plan["overall_risk_assessment"]

            if "overallRecommendations" in plan and "recommendations" not in plan:
                recs = plan["overallRecommendations"]
                # Convert string to array if needed
                if isinstance(recs, str):
                    plan["recommendations"] = [recs]
                else:
                    plan["recommendations"] = recs
                del plan["overallRecommendations"]
            elif "overall_recommendations" in plan and "recommendations" not in plan:
                # Handle snake_case version
                recs = plan["overall_recommendations"]
                if isinstance(recs, str):
                    plan["recommendations"] = [recs]
                else:
                    plan["recommendations"] = recs
                del plan["overall_recommendations"]

            # Add missing fields with defaults
            if "project_type" not in plan:
                plan["project_type"] = "unknown"
            if "analysis_date" not in plan:
                from datetime import datetime
                plan["analysis_date"] = datetime.now().isoformat()
            if "overall_risk" not in plan:
                plan["overall_risk"] = "medium"
            if "estimated_total_time" not in plan:
                # Calculate from phases if available
                if "migration_strategy" in plan and "phases" in plan["migration_strategy"]:
                    plan["estimated_total_time"] = "See individual phases"
                else:
                    plan["estimated_total_time"] = "unknown"

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
