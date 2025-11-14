"""Runtime Validator Agent

Tests dependency upgrades in isolated Docker containers to verify they work correctly.

Capabilities:
- Creates Docker containers with project code
- Applies dependency upgrades from migration plan
- Installs upgraded dependencies
- Runs application and performs health checks
- Collects logs and error information
- Returns validation results
"""

import sys
import json
from typing import Dict, Optional

from agents.base import BaseAgent
from tools.docker_tools import DockerValidator


class RuntimeValidatorAgent(BaseAgent):
    """Agent for validating dependency upgrades in Docker containers."""

    def __init__(self, llm_provider: Optional[str] = None, llm_model: Optional[str] = None, broadcaster=None):
        system_prompt = """You are an expert runtime validation specialist.

Your role:
1. Test dependency upgrades in isolated Docker containers
2. Verify applications start successfully with new dependencies
3. Analyze runtime errors and failures
4. Determine if upgrades are safe to apply
5. Provide detailed validation reports

When validating:
- Test in clean Docker containers (no side effects)
- Check for runtime errors during startup
- Verify key processes are running
- Analyze error logs if validation fails
- Determine root cause of failures

Output Format:
Return structured validation results with:
{
    "validation_status": "success" or "failed",
    "validation_details": {
        "container_created": bool,
        "dependencies_installed": bool,
        "application_started": bool,
        "health_checks_passed": bool
    },
    "errors": ["list of errors if any"],
    "logs": {
        "install": "npm install output",
        "startup": "application startup output",
        "health_check": "health check results"
    },
    "recommendation": "proceed" or "fix_required" or "rollback",
    "next_steps": ["what to do next"]
}

Be thorough and prioritize correctness."""

        super().__init__(
            name="runtime_validator",
            system_prompt=system_prompt,
            llm_provider=llm_provider,
            llm_model=llm_model,
            broadcaster=broadcaster
        )

    def execute(self, input_data: Dict) -> Dict:
        """Execute runtime validation.

        Args:
            input_data: Dictionary with:
                - project_path: Path to project directory
                - project_type: "nodejs" or "python"
                - migration_plan: Optional migration plan to test
                - timeout: Optional Docker timeout (default: 300)

        Returns:
            Dictionary with validation results and analysis
        """
        try:
            project_path = input_data.get("project_path")
            project_type = input_data.get("project_type")
            migration_plan = input_data.get("migration_plan")
            timeout = input_data.get("timeout", 300)

            if not project_path:
                return {
                    "status": "error",
                    "error": "project_path is required"
                }

            if not project_type:
                return {
                    "status": "error",
                    "error": "project_type is required"
                }

            self.logger.info("starting_runtime_validation",
                           project_path=project_path,
                           project_type=project_type,
                           has_migration_plan=migration_plan is not None)

            # Create Docker validator with forced cleanup enabled
            validator = DockerValidator(timeout=timeout, cleanup_containers=True)

            # Send initial update about validation start
            self.send_update(
                message=f"Starting runtime validation for {project_type} project",
                message_type="agent_start",
                extra_data={
                    "project_path": project_path,
                    "project_type": project_type
                }
            )

            # Send update about migration plan if available
            if migration_plan:
                # Send update about dependencies being tested
                dependencies = migration_plan.get("dependencies", {})
                dep_list = []
                for pkg_name, dep_info in dependencies.items():
                    current = dep_info.get("current_version", "unknown")
                    target = dep_info.get("target_version", "unknown")
                    dep_list.append(f"{pkg_name}: {current} → {target}")

                self.send_update(
                    message=f"Testing {len(dependencies)} dependency upgrades",
                    message_type="validation_info",
                    extra_data={
                        "dependencies": dep_list,
                        "total_dependencies": len(dependencies)
                    }
                )

            self.send_update(
                message="Creating Docker container for validation",
                message_type="validation_info",
                extra_data={"status": "creating_container"}
            )

            # Run validation
            validation_result = validator.validate_project(
                project_path=project_path,
                project_type=project_type,
                migration_plan=migration_plan
            )

            self.logger.info("docker_validation_complete",
                           status=validation_result["status"],
                           build=validation_result["build_success"],
                           install=validation_result["install_success"],
                           runtime=validation_result["runtime_success"],
                           health_check=validation_result["health_check_success"],
                           tests_run=validation_result["tests_run"],
                           tests_passed=validation_result["tests_passed"])

            # Send updates about validation results
            self.send_update(
                message="Docker validation completed",
                message_type="validation_result",
                extra_data={
                    "build_success": validation_result["build_success"],
                    "install_success": validation_result["install_success"],
                    "runtime_success": validation_result["runtime_success"],
                    "health_check_success": validation_result["health_check_success"],
                    "tests_run": validation_result["tests_run"],
                    "tests_passed": validation_result["tests_passed"]
                }
            )

            # Analyze results with LLM
            # Skip LLM analysis if validation was clearly successful
            if (validation_result["status"] == "success" and
                validation_result["build_success"] and
                validation_result["install_success"] and
                validation_result["runtime_success"] and
                validation_result["health_check_success"]):

                # Direct success - no need for LLM analysis
                analysis = {
                    "validation_status": "success",
                    "validation_details": {
                        "container_created": True,
                        "dependencies_installed": validation_result["install_success"],
                        "application_started": validation_result["runtime_success"],
                        "health_checks_passed": validation_result["health_check_success"],
                        "tests_run": validation_result["tests_run"],
                        "tests_passed": validation_result["tests_passed"]
                    },
                    "errors": [],
                    "recommendation": "proceed",
                    "next_steps": ["Deploy to staging environment", "Create pull request"],
                    "confidence": "high"
                }
                self.logger.info("validation_success_without_llm",
                               tests_configured=validation_result["tests_run"])
                
                # Send success update
                self.send_update(
                    message="All validation checks passed successfully",
                    message_type="validation_success"
                )
            else:
                # Validation had issues - use LLM for analysis
                self.send_update(
                    message="Validation issues detected, analyzing with LLM",
                    message_type="validation_analysis"
                )
                analysis = self._analyze_validation_results(validation_result, migration_plan)

            # Cleanup
            validator.cleanup_all()

            # Log cost
            cost_report = self.llm.cost_tracker.get_report()
            self.logger.info("runtime_validation_complete",
                           validation_status=analysis.get("validation_status", "unknown"),
                           recommendation=analysis.get("recommendation", "unknown"),
                           cost_usd=cost_report["total_cost_usd"])

            return {
                "status": "success",
                "validation_result": validation_result,
                "analysis": analysis,
                "cost_report": cost_report
            }

        except Exception as e:
            self.logger.error("runtime_validation_failed", error=str(e), exc_info=True)
            # Ensure cleanup happens even when there's an exception
            try:
                validator.cleanup_all()
            except Exception as cleanup_error:
                self.logger.warning("cleanup_failed_in_exception", error=str(cleanup_error))
            return {
                "status": "error",
                "error": str(e)
            }

    def _analyze_validation_results(self, validation_result: Dict, migration_plan: Optional[Dict]) -> Dict:
        """Analyze validation results with LLM.

        Args:
            validation_result: Raw validation results from Docker
            migration_plan: Migration plan that was tested (if any)

        Returns:
            Analysis dictionary with recommendations
        """
        # Build analysis prompt
        prompt = self._build_analysis_prompt(validation_result, migration_plan)

        self.logger.info("analyzing_validation_results", prompt_length=len(prompt))

        # Get LLM analysis
        llm_response = self.think(prompt, max_tokens=2000)

        self.logger.info("llm_analysis_received", response_length=len(llm_response))

        # Parse response
        try:
            # Remove markdown code blocks if present
            cleaned = llm_response.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                cleaned = "\n".join(lines[1:-1]) if len(lines) > 2 else cleaned

            analysis = json.loads(cleaned)
            
            # Send update about analysis results
            self.send_update(
                message="LLM analysis complete",
                message_type="analysis_complete",
                extra_data={
                    "validation_status": analysis.get("validation_status", "unknown"),
                    "recommendation": analysis.get("recommendation", "unknown"),
                    "confidence": analysis.get("confidence", "unknown")
                }
            )
            
            return analysis

        except json.JSONDecodeError as e:
            self.logger.error("json_parse_error", error=str(e), response=llm_response[:500])

            # Send error update
            self.send_update(
                message="Error parsing LLM analysis, using fallback",
                message_type="analysis_error",
                extra_data={"error": str(e)}
            )

            # Return fallback analysis based on validation result
            return self._fallback_analysis(validation_result)

    def _build_analysis_prompt(self, validation_result: Dict, migration_plan: Optional[Dict]) -> str:
        """Build prompt for LLM analysis.

        Args:
            validation_result: Validation results
            migration_plan: Migration plan (if any)

        Returns:
            Formatted prompt string
        """
        prompt = f"""Analyze these runtime validation results and provide recommendations.

VALIDATION RESULTS:
{json.dumps(validation_result, indent=2)}
"""

        if migration_plan:
            prompt += f"""
MIGRATION PLAN TESTED:
- Dependencies upgraded: {len(migration_plan.get('dependencies', {}))}
- Overall risk: {migration_plan.get('overall_risk', 'unknown')}
"""

        prompt += """
TASKS:
1. Determine validation status: "success" or "failed"
2. Analyze what worked and what didn't:
   - Container creation
   - Dependency installation
   - Application startup
   - Health checks
   - Test execution (if tests were found)

3. If validation failed:
   - Identify root cause from error messages
   - Determine which dependency likely caused the issue
   - Suggest fixes

4. Provide recommendation:
   - "proceed" - Validation passed, safe to deploy
   - "fix_required" - Failed but fixable, provide steps
   - "rollback" - Failed critically, recommend rollback

5. List next steps

OUTPUT FORMAT: Return ONLY valid JSON matching this schema:
{
    "validation_status": "success" or "failed",
    "validation_details": {
        "container_created": bool,
        "dependencies_installed": bool,
        "application_started": bool,
        "health_checks_passed": bool,
        "tests_run": bool,
        "tests_passed": bool
    },
    "errors": ["list of errors if any"],
    "root_cause": "explanation if failed",
    "problematic_dependencies": ["list of packages that likely caused issues"],
    "recommendation": "proceed" or "fix_required" or "rollback",
    "next_steps": ["what to do next"],
    "confidence": "high" or "medium" or "low"
}

No markdown, no explanations outside JSON."""

        return prompt

    def _fallback_analysis(self, validation_result: Dict) -> Dict:
        """Generate fallback analysis when LLM parsing fails.

        Args:
            validation_result: Validation results

        Returns:
            Basic analysis dict
        """
        validation_success = validation_result.get("status") == "success"

        # Send update about fallback analysis
        self.send_update(
            message="Using fallback analysis due to LLM parsing error",
            message_type="fallback_analysis",
            extra_data={
                "validation_success": validation_success,
                "errors_count": len(validation_result.get("errors", []))
            }
        )

        return {
            "validation_status": "success" if validation_success else "failed",
            "validation_details": {
                "container_created": validation_result.get("build_success", False),
                "dependencies_installed": validation_result.get("install_success", False),
                "application_started": validation_result.get("runtime_success", False),
                "health_checks_passed": validation_result.get("health_check_success", False),
                "tests_run": validation_result.get("tests_run", False),
                "tests_passed": validation_result.get("tests_passed", False)
            },
            "errors": validation_result.get("errors", []),
            "root_cause": "See errors list" if not validation_success else "N/A",
            "problematic_dependencies": [],
            "recommendation": "proceed" if validation_success else "fix_required",
            "next_steps": [
                "Deploy to staging" if validation_success else "Review error logs",
                "Run integration tests" if validation_success else "Fix identified issues"
            ],
            "confidence": "medium"
        }


def main():
    """Standalone test of Runtime Validator Agent."""
    from pathlib import Path

    print("=" * 80)
    print("RUNTIME VALIDATOR AGENT - STANDALONE TEST")
    print("=" * 80)

    # Test with sample Express app
    test_project = Path(__file__).parent.parent / "tests" / "sample_projects" / "express-app"

    if not test_project.exists():
        print(f"\nERROR: Test project not found at {test_project}")
        return 1

    print(f"\nTest Project: {test_project}")
    print("Project Type: nodejs")
    print("Testing: Baseline (no migration)\n")

    # Create agent
    print("1. Creating Runtime Validator Agent...")
    agent = RuntimeValidatorAgent()
    print(f"   Provider: {agent.llm.get_provider_name()}")
    print(f"   Model: {agent.llm.model}")

    # Execute validation
    print("\n2. Running runtime validation...")
    print("   (This will create Docker container, install deps, start app)")
    result = agent.execute({
        "project_path": str(test_project),
        "project_type": "nodejs",
        "migration_plan": None
    })

    # Display results
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)

    if result["status"] == "error":
        print(f"\nERROR: {result['error']}")
        return 1

    validation = result["validation_result"]
    analysis = result["analysis"]

    print(f"\nDocker Validation:")
    print(f"  Container ID: {validation['container_id']}")
    print(f"  Status: {validation['status'].upper()}")
    print(f"  Build: {'SUCCESS' if validation['build_success'] else 'FAILED'}")
    print(f"  Install: {'SUCCESS' if validation['install_success'] else 'FAILED'}")
    print(f"  Runtime: {'SUCCESS' if validation['runtime_success'] else 'FAILED'}")
    print(f"  Health Check: {'SUCCESS' if validation['health_check_success'] else 'FAILED'}")

    if validation.get('errors'):
        print(f"\n  Errors: {len(validation['errors'])}")
        for error in validation['errors']:
            print(f"    - {error}")

    print(f"\nLLM Analysis:")
    print(f"  Validation Status: {analysis.get('validation_status', 'unknown').upper()}")
    print(f"  Recommendation: {analysis.get('recommendation', 'unknown').upper()}")
    print(f"  Confidence: {analysis.get('confidence', 'unknown').upper()}")

    if analysis.get('root_cause'):
        print(f"  Root Cause: {analysis['root_cause']}")

    if analysis.get('problematic_dependencies'):
        print(f"  Problematic Deps: {', '.join(analysis['problematic_dependencies'])}")

    next_steps = analysis.get('next_steps', [])
    if next_steps:
        print(f"\n  Next Steps:")
        for i, step in enumerate(next_steps, 1):
            print(f"    {i}. {step}")

    # Cost Report
    print("\n" + "=" * 80)
    print("COST REPORT")
    print("=" * 80)
    cost_report = result["cost_report"]
    print(f"Provider: {cost_report['provider']}")
    print(f"Model: {cost_report['model']}")
    print(f"Total Requests: {cost_report['total_requests']}")
    print(f"Total Tokens: {cost_report['total_tokens']:,}")
    print(f"Total Cost: ${cost_report['total_cost_usd']:.4f}")

    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

    return 0 if result['status'] == 'success' else 1


if __name__ == "__main__":
    sys.exit(main())
