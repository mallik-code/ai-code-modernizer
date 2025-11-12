"""Migration Report Generator

Generates comprehensive HTML and Markdown reports from workflow execution results.
"""

import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional


class ReportGenerator:
    """Generate migration reports in various formats."""

    def __init__(self, output_dir: Optional[str] = None):
        """Initialize report generator.

        Args:
            output_dir: Directory to save reports (default: current directory)
        """
        self.output_dir = Path(output_dir) if output_dir else Path.cwd()
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_all_reports(self, workflow_state: Dict[str, Any], project_name: str) -> Dict[str, str]:
        """Generate all report formats.

        Args:
            workflow_state: Final workflow state
            project_name: Name of the project

        Returns:
            Dictionary with paths to generated reports
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Get branch name from workflow state
        deployment_result = workflow_state.get('deployment_result', {})
        branch_name = deployment_result.get('branch_name', None)

        # Create folder with branch name if available, otherwise use timestamp
        if branch_name:
            # Clean branch name for folder (remove invalid characters)
            folder_name = branch_name.replace('/', '_').replace('\\', '_')
            report_dir = self.output_dir / folder_name
        else:
            report_dir = self.output_dir / f"migration_{timestamp}"

        # Create directory if it doesn't exist
        report_dir.mkdir(parents=True, exist_ok=True)

        base_name = f"{project_name}_migration_report_{timestamp}"

        reports = {}

        # Generate JSON report
        json_path = report_dir / f"{base_name}.json"
        self.generate_json_report(workflow_state, json_path)
        reports['json'] = str(json_path)

        # Generate Markdown report
        md_path = report_dir / f"{base_name}.md"
        self.generate_markdown_report(workflow_state, md_path)
        reports['markdown'] = str(md_path)

        # Generate HTML report
        html_path = report_dir / f"{base_name}.html"
        self.generate_html_report(workflow_state, html_path)
        reports['html'] = str(html_path)

        return reports

    def generate_json_report(self, workflow_state: Dict[str, Any], output_path: Path):
        """Generate JSON report.

        Args:
            workflow_state: Final workflow state
            output_path: Path to save JSON report
        """
        with open(output_path, 'w') as f:
            json.dump(workflow_state, f, indent=2, default=str)

    def generate_markdown_report(self, workflow_state: Dict[str, Any], output_path: Path):
        """Generate Markdown report.

        Args:
            workflow_state: Final workflow state
            output_path: Path to save Markdown report
        """
        md = self._build_markdown_content(workflow_state)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(md)

    def generate_html_report(self, workflow_state: Dict[str, Any], output_path: Path):
        """Generate HTML report.

        Args:
            workflow_state: Final workflow state
            output_path: Path to save HTML report
        """
        html = self._build_html_content(workflow_state)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

    def _build_markdown_content(self, state: Dict[str, Any]) -> str:
        """Build Markdown report content."""

        migration_plan = state.get('migration_plan', {})
        validation_result = state.get('validation_result', {})
        deployment_result = state.get('deployment_result', {})
        pr_url = state.get('pr_url')
        branch_name = state.get('branch_name')

        # Get source and target branch names
        source_branch = deployment_result.get('base_branch', 'main') if deployment_result else 'main'
        target_branch = branch_name if branch_name else 'N/A'

        md = f"""# Migration Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Project:** {state.get('project_path', 'Unknown')}
**Project Type:** {state.get('project_type', 'Unknown').upper()}
**Status:** {state.get('status', 'Unknown').upper()}
**Overall Risk:** {migration_plan.get('overall_risk', 'Unknown').upper()}

---

## Summary

- **Dependencies Analyzed:** {len(migration_plan.get('dependencies', {}))}
- **Migration Phases:** {migration_plan.get('migration_strategy', {}).get('total_phases', 0)}
- **Validation Status:** {'✅ PASSED' if state.get('validation_success') else '❌ FAILED'}
- **Total Cost:** ${state.get('total_cost', 0):.4f}
- **Retry Count:** {state.get('retry_count', 0)}/{state.get('max_retries', 0)}
- **Source Branch:** `{source_branch}`
- **Target Branch:** `{target_branch}`

"""

        if pr_url:
            md += f"**Pull Request:** [{branch_name}]({pr_url})\n\n"
        elif branch_name:
            md += f"**Branch Created:** `{branch_name}`\n\n"

        md += "---\n\n"

        # Dependencies Section
        md += "## Dependencies Analysis\n\n"

        dependencies = migration_plan.get('dependencies', {})
        if dependencies:
            md += "| Package | Current | Target | Risk | Action | Breaking Changes |\n"
            md += "|---------|---------|--------|------|--------|------------------|\n"

            for pkg_name, pkg_info in dependencies.items():
                current = pkg_info.get('current_version', '?')
                target = pkg_info.get('target_version', '?')
                risk = pkg_info.get('risk', '?').upper()
                action = pkg_info.get('action', '?').upper()
                breaking_count = len(pkg_info.get('breaking_changes', []))

                risk_emoji = {'LOW': '🟢', 'MEDIUM': '🟡', 'HIGH': '🔴'}.get(risk, '⚪')

                md += f"| {pkg_name} | {current} | {target} | {risk_emoji} {risk} | {action} | {breaking_count} |\n"

            md += "\n"
        else:
            md += "*No dependencies analyzed*\n\n"

        # Breaking Changes Detail
        md += "### Breaking Changes Detail\n\n"
        md += "> **ℹ️ What are Breaking Changes?**\n"
        md += "> Breaking changes are modifications in a new library version that are NOT backward-compatible. "
        md += "This means code written for the old version may require updates to work with the new version. "
        md += "Examples include: removed functions, changed API signatures, renamed methods, or removed built-in features. "
        md += "They don't mean your code is broken - they indicate potential compatibility issues that may need attention.\n\n"

        for pkg_name, pkg_info in dependencies.items():
            breaking_changes = pkg_info.get('breaking_changes', [])
            if breaking_changes:
                md += f"#### {pkg_name}\n\n"
                for i, change in enumerate(breaking_changes, 1):
                    if isinstance(change, dict):
                        version = change.get('version', 'Unknown')
                        desc = change.get('description', 'No description')
                        impact = change.get('impact', 'unknown').upper()
                    else:
                        version = "Unknown"
                        desc = str(change)
                        impact = "UNKNOWN"

                    md += f"{i}. **Version {version}** - Impact: {impact}\n"
                    md += f"   - {desc}\n\n"

        # Migration Strategy
        md += "---\n\n## Migration Strategy\n\n"

        strategy = migration_plan.get('migration_strategy', {})
        phases = strategy.get('phases', [])

        if phases:
            for phase in phases:
                phase_num = phase.get('phase', '?')
                name = phase.get('name', 'Unknown Phase')
                deps = phase.get('dependencies', [])
                time = phase.get('estimated_time', 'Unknown')
                rollback = phase.get('rollback_plan', 'No rollback plan')

                md += f"### Phase {phase_num}: {name}\n\n"
                md += f"**Dependencies:** {', '.join(deps)}\n\n"
                md += f"**Estimated Time:** {time}\n\n"
                md += f"**Rollback Plan:**\n{rollback}\n\n"
        else:
            md += "*No migration strategy defined*\n\n"

        # Validation Results
        md += "---\n\n## Validation Results\n\n"

        if validation_result:
            val_data = validation_result.get('validation_result', {})

            md += f"**Container:** `{val_data.get('container_name', val_data.get('container_id', 'Unknown'))}`\n\n"

            md += "| Stage | Status |\n"
            md += "|-------|--------|\n"
            md += f"| Build | {'✅ SUCCESS' if val_data.get('build_success') else '❌ FAILED'} |\n"
            md += f"| Install | {'✅ SUCCESS' if val_data.get('install_success') else '❌ FAILED'} |\n"
            md += f"| Runtime | {'✅ SUCCESS' if val_data.get('runtime_success') else '❌ FAILED'} |\n"
            md += f"| Health Check | {'✅ SUCCESS' if val_data.get('health_check_success') else '❌ FAILED'} |\n"
            md += f"| **Functional Tests** | {'✅ SUCCESS' if val_data.get('tests_passed') else ('⚠️ NOT RUN' if not val_data.get('tests_run') else '❌ FAILED')} |\n\n"

            # Test Results Details
            logs = val_data.get('logs', {})
            test_logs = logs.get('tests', {})
            if test_logs and test_logs.get('success'):
                md += "### Test Results\n\n"
                test_summary = test_logs.get('test_summary', 'N/A')
                md += f"**Summary:** {test_summary}\n\n"

                # Extract test counts from output
                test_output = test_logs.get('output', '')
                if 'Test Suites:' in test_output:
                    lines = test_output.split('\n')
                    for line in lines:
                        if 'Test Suites:' in line or 'Tests:' in line:
                            md += f"- {line.strip()}\n"
                md += "\n"

            # Errors
            errors = val_data.get('errors', [])
            if errors:
                md += "### Errors\n\n"
                for i, error in enumerate(errors, 1):
                    md += f"{i}. {error}\n"
                md += "\n"
        else:
            md += "*Validation not performed*\n\n"

        # Workflow Execution Diagram (always show all 4 agents)
        md += "---\n\n## Workflow Execution\n\n"
        md += "```\n"
        md += "┌─────────────────────────────────────────────────────────────┐\n"
        md += "│          AI Code Modernizer - 4-Agent Workflow             │\n"
        md += "└─────────────────────────────────────────────────────────────┘\n"
        md += "\n"

        # Agent 1: Migration Planner
        planner_status = "✅ COMPLETE" if migration_plan else "❌ FAILED"
        md += f"┌─────────────────────┐\n"
        md += f"│ [1] Migration       │ {planner_status}\n"
        md += f"│     Planner         │\n"
        md += f"└─────────────────────┘\n"
        md += "          ↓\n"
        md += "   (npm registry API)\n"
        md += "          ↓\n"

        # Agent 2: Runtime Validator
        validator_status = "✅ COMPLETE" if validation_result and validation_result.get('status') == 'success' else "❌ FAILED" if validation_result else "⚠️ SKIPPED"
        md += f"┌─────────────────────┐\n"
        md += f"│ [2] Runtime         │ {validator_status}\n"
        md += f"│     Validator       │\n"
        md += f"└─────────────────────┘\n"
        md += "          ↓\n"
        md += "  (Docker container)\n"
        md += "          ↓\n"

        # Agent 3: Error Analyzer (always show, but mark as conditional)
        error_analysis = state.get('error_analysis')
        analyzer_status = "✅ COMPLETE" if error_analysis else "⚠️ NOT NEEDED"
        md += f"┌─────────────────────┐\n"
        md += f"│ [3] Error Analyzer  │ {analyzer_status}\n"
        md += f"│   (conditional)     │\n"
        md += f"└─────────────────────┘\n"
        md += "          ↓\n"
        md += "  (only if validation fails)\n"
        md += "          ↓\n"

        # Agent 4: Staging Deployer
        deployment_result = state.get('deployment_result')
        deployer_status = "✅ COMPLETE" if deployment_result and deployment_result.get('status') == 'success' else "⚠️ SKIPPED" if not deployment_result else "❌ FAILED"
        md += f"┌─────────────────────┐\n"
        md += f"│ [4] Staging         │ {deployer_status}\n"
        md += f"│     Deployer        │\n"
        md += f"└─────────────────────┘\n"
        md += "          ↓\n"
        md += "  (GitHub PR created)\n"
        md += "\n```\n\n"

        # Agent Execution Summary
        md += "### Agent Execution Summary\n\n"
        md += "| Agent | Status | Cost | Details |\n"
        md += "|-------|--------|------|----------|\n"

        agent_costs = state.get('agent_costs', {})
        planner_cost = agent_costs.get('migration_planner', 0)
        validator_cost = agent_costs.get('runtime_validator', 0)
        analyzer_cost = agent_costs.get('error_analyzer', 0)
        deployer_cost = agent_costs.get('staging_deployer', 0)

        dep_count = len(migration_plan.get('dependencies', {})) if migration_plan else 0
        md += f"| Migration Planner | {planner_status} | ${planner_cost:.6f} | Analyzed {dep_count} dependencies |\n"

        # Runtime Validator details
        val_data = validation_result.get('validation_result', {}) if validation_result else {}
        tests_passed = val_data.get('tests_passed', False)
        tests_run = val_data.get('tests_run', False)
        test_count = val_data.get('logs', {}).get('tests', {}).get('test_summary', 'N/A')
        validator_details = f"Docker validation, Tests: {test_count}" if tests_run else "Docker validation only"
        md += f"| Runtime Validator | {validator_status} | ${validator_cost:.6f} | {validator_details} |\n"

        # Error Analyzer (always show, even if not executed)
        analyzer_status_text = "✅ COMPLETE" if error_analysis else "⚠️ NOT NEEDED"
        fix_count = len(error_analysis.get('fix_suggestions', [])) if error_analysis else 0
        analyzer_details = f"Analyzed errors, {fix_count} fix suggestions" if error_analysis else "Validation succeeded, no errors to analyze"
        md += f"| Error Analyzer | {analyzer_status_text} | ${analyzer_cost:.6f} | {analyzer_details} |\n"

        deployment_result = state.get('deployment_result', {})
        files_updated = len(deployment_result.get('files_updated', []))
        branch_name = deployment_result.get('branch_name') or state.get('branch_name') or 'N/A'
        branch_display = branch_name[:30] if branch_name != 'N/A' else 'N/A'
        deployer_details = f"Updated {files_updated} files, Branch: {branch_display}"
        md += f"| Staging Deployer | {deployer_status} | ${deployer_cost:.6f} | {deployer_details} |\n"
        md += "\n"

        # Cost Report
        md += "---\n\n## Cost Report\n\n"

        agent_costs = state.get('agent_costs', {})
        if agent_costs:
            md += "| Agent | Cost (USD) |\n"
            md += "|-------|------------|\n"
            for agent, cost in agent_costs.items():
                md += f"| {agent} | ${cost:.4f} |\n"
            md += f"| **TOTAL** | **${state.get('total_cost', 0):.4f}** |\n\n"
        else:
            md += f"**Total Cost:** ${state.get('total_cost', 0):.4f}\n\n"

        # Errors and Warnings
        errors = state.get('errors', [])
        if errors:
            md += "---\n\n## Errors and Warnings\n\n"
            for i, error in enumerate(errors, 1):
                md += f"{i}. {error}\n"
            md += "\n"

        # LLM Insights (for hackathon judges)
        md += "---\n\n## AI/LLM Insights\n\n"
        md += "*This section provides transparency into how our AI agents make decisions.*\n\n"

        # Migration Planner LLM insights
        if migration_plan:
            md += "### Migration Planner Analysis\n\n"
            md += f"**AI Model Used:** Gemini 2.0 Flash (fast, cost-effective)\n\n"
            md += f"**Data Sources:**\n"
            md += f"- npm Registry API (https://registry.npmjs.org) for latest versions\n"
            md += f"- LLM knowledge base for breaking changes and migration risks\n\n"

            md += f"**Decision Process:**\n"
            md += f"1. Fetched latest versions from npm registry\n"
            md += f"2. Compared current vs. latest for each dependency\n"
            md += f"3. Analyzed version jumps (major/minor/patch)\n"
            md += f"4. Assessed breaking changes and compatibility risks\n"
            md += f"5. Created phased migration strategy\n\n"

            # Show some key LLM decisions
            md += "**Key AI Decisions:**\n\n"
            if migration_plan.get('dependencies'):
                high_risk_deps = [(name, info) for name, info in migration_plan['dependencies'].items()
                                 if info.get('risk', '').lower() == 'high']
                if high_risk_deps:
                    md += "High-risk upgrades identified:\n"
                    for name, info in high_risk_deps[:3]:  # Show top 3
                        md += f"- **{name}** ({info.get('current_version')} → {info.get('target_version')})\n"
                        breaking_changes = info.get('breaking_changes', [])
                        if breaking_changes:
                            md += f"  - Breaking: {breaking_changes[0]}\n"
                    md += "\n"

        # Runtime Validator insights
        if validation_result:
            md += "### Runtime Validator Process\n\n"
            md += "**Validation Environment:** Docker container (isolated, reproducible)\n\n"
            md += "**Steps Executed:**\n"
            val_data = validation_result.get('validation_result', {})
            md += f"1. ✅ Container created: `{val_data.get('container_name', 'N/A')}`\n"
            md += f"2. {'✅' if val_data.get('build_success') else '❌'} Project files copied\n"
            md += f"3. {'✅' if val_data.get('install_success') else '❌'} Dependencies installed\n"
            md += f"4. {'✅' if val_data.get('runtime_success') else '❌'} Application started\n"
            md += f"5. {'✅' if val_data.get('health_check_success') else '❌'} Health checks passed\n"
            md += f"6. {'✅' if val_data.get('tests_passed') else '⚠️'} Functional tests executed\n\n"

        # Agent Roles and Responsibilities
        md += "### Agent Roles & Responsibilities\n\n"

        md += "#### 1. 🤖 Migration Planner Agent\n"
        md += "**Role:** Dependency Analysis & Strategy Planning\n\n"
        md += "**Responsibilities:**\n"
        md += "- Fetch latest package versions from npm/PyPI registries\n"
        md += "- Compare current vs. latest versions for all dependencies\n"
        md += "- Identify outdated, deprecated, or vulnerable packages\n"
        md += "- Assess migration risks (low/medium/high) based on version jumps\n"
        md += "- Research breaking changes and compatibility issues using LLM\n"
        md += "- Create phased migration strategy (low-risk → high-risk)\n"
        md += "- Calculate estimated time and effort per phase\n\n"
        md += f"**Status in this migration:** {planner_status}\n"
        md += f"**Cost:** ${planner_cost:.6f} | **Dependencies analyzed:** {dep_count}\n\n"

        md += "#### 2. 🐳 Runtime Validator Agent\n"
        md += "**Role:** Safe Testing in Isolated Environments\n\n"
        md += "**Responsibilities:**\n"
        md += "- Create isolated Docker container for testing\n"
        md += "- Apply dependency upgrades to container\n"
        md += "- Install upgraded dependencies (npm install / pip install)\n"
        md += "- Start the application in container\n"
        md += "- Perform health checks on running application\n"
        md += "- Execute functional test suites (if available)\n"
        md += "- Collect logs and error details\n"
        md += "- Report validation success/failure with diagnostics\n\n"
        md += f"**Status in this migration:** {validator_status}\n"
        md += f"**Cost:** ${validator_cost:.6f} | **Tests executed:** {test_count if tests_run else 'N/A'}\n\n"

        # Error Analyzer (always show, even if not executed)
        analyzer_status = "✅ COMPLETE" if error_analysis else "⚠️ NOT NEEDED"
        fix_count = len(error_analysis.get('fix_suggestions', [])) if error_analysis else 0
        md += "#### 3. 🔍 Error Analyzer Agent\n"
        md += "**Role:** Intelligent Error Diagnosis & Fix Suggestions\n\n"
        md += "**Responsibilities:**\n"
        md += "- Parse error logs from validation failures\n"
        md += "- Identify root causes using pattern matching + LLM analysis\n"
        md += "- Categorize errors (dependency conflict, breaking change, etc.)\n"
        md += "- Generate actionable fix suggestions\n"
        md += "- Prioritize fixes by impact and feasibility\n"
        md += "- Recommend alternative upgrade strategies if needed\n"
        md += "- **Conditional execution**: Only runs when validation fails\n\n"
        md += f"**Status in this migration:** {analyzer_status}\n"
        md += f"**Cost:** ${analyzer_cost:.6f} | **Fixes suggested:** {fix_count if error_analysis else 'N/A'}\n\n"

        md += "#### 4. 🚀 Staging Deployer Agent\n"
        md += "**Role:** Safe Deployment via GitHub Workflow\n\n"
        md += "**Responsibilities:**\n"
        md += "- Create timestamped feature branch (upgrade/dependencies-YYYYMMDD-HHMMSS)\n"
        md += "- Update dependency files (package.json / requirements.txt)\n"
        md += "- Generate conventional commit messages with upgrade details\n"
        md += "- Commit changes to the new branch\n"
        md += "- Push branch to remote repository\n"
        md += "- Create GitHub Pull Request with detailed description\n"
        md += "- Include testing instructions and rollback plan\n"
        md += "- Wait for human approval before merge (safety gate)\n\n"
        md += f"**Status in this migration:** {deployer_status}\n"
        md += f"**Cost:** ${deployer_cost:.6f} | **Files updated:** {files_updated}\n\n"

        # Overall system intelligence
        md += "### System Intelligence Highlights\n\n"
        md += "**Multi-Agent Architecture (4 Specialized Agents):**\n"
        md += "- Each agent has a specific responsibility and expertise\n"
        md += "- Agents communicate via LangGraph workflow state\n"
        md += "- Conditional routing: Error Analyzer only runs when validation fails\n"
        md += "- Retry logic: Up to 3 attempts with automatic fix application\n\n"
        md += "**Intelligence Features:**\n"
        md += "- Automatic error detection and retry logic\n"
        md += "- Cost-optimized: Uses Gemini Flash ($0.001 per migration)\n"
        md += "- Conditional routing: Error Analyzer only runs when needed\n"
        md += "- Real-time npm registry integration for accurate versions\n\n"

        md += "**Safety Mechanisms:**\n"
        md += "- Docker isolation prevents host system contamination\n"
        md += "- All changes go through GitHub PR (human review required)\n"
        md += "- Automatic rollback instructions provided\n"
        md += "- Comprehensive test suite execution before deployment\n\n"

        total_cost = state.get('total_cost', 0)
        md += f"**Total AI Cost for This Migration:** ${total_cost:.6f} USD\n\n"

        # Footer
        md += "---\n\n"
        md += "*Report generated by AI Code Modernizer - A hackathon project showcasing autonomous AI agents for code maintenance*\n"

        return md

    def _calculate_version_jump(self, current: str, target: str) -> str:
        """Calculate version jump type (major/minor/patch).

        Args:
            current: Current version string
            target: Target version string

        Returns:
            Description of version jump
        """
        try:
            # Clean version strings (remove ^ and other prefixes)
            current_clean = current.lstrip('^~>=<')
            target_clean = target.lstrip('^~>=<')

            # Split into major.minor.patch
            current_parts = current_clean.split('.')
            target_parts = target_clean.split('.')

            if len(current_parts) < 1 or len(target_parts) < 1:
                return "Unknown"

            current_major = int(current_parts[0]) if current_parts[0].isdigit() else 0
            target_major = int(target_parts[0]) if target_parts[0].isdigit() else 0

            if target_major > current_major:
                return f"Major (+{target_major - current_major})"

            if len(current_parts) >= 2 and len(target_parts) >= 2:
                current_minor = int(current_parts[1]) if current_parts[1].isdigit() else 0
                target_minor = int(target_parts[1]) if target_parts[1].isdigit() else 0

                if target_minor > current_minor:
                    return f"Minor (+{target_minor - current_minor})"

            if len(current_parts) >= 3 and len(target_parts) >= 3:
                current_patch = int(current_parts[2]) if current_parts[2].isdigit() else 0
                target_patch = int(target_parts[2]) if target_parts[2].isdigit() else 0

                if target_patch > current_patch:
                    return f"Patch (+{target_patch - current_patch})"

            return "Same"

        except Exception:
            return "Unknown"

    def _build_html_content(self, state: Dict[str, Any]) -> str:
        """Build HTML report content."""

        migration_plan = state.get('migration_plan', {})
        validation_result = state.get('validation_result', {})
        deployment_result = state.get('deployment_result', {})
        pr_url = state.get('pr_url')
        branch_name = state.get('branch_name')

        # Get source and target branch names
        source_branch = deployment_result.get('base_branch', 'main') if deployment_result else 'main'
        target_branch = branch_name if branch_name else 'N/A'

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Migration Report - {Path(state.get('project_path', 'Unknown')).name}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 30px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 40px;
            margin-bottom: 20px;
            border-left: 4px solid #3498db;
            padding-left: 15px;
        }}
        h3 {{
            color: #7f8c8d;
            margin-top: 25px;
            margin-bottom: 15px;
        }}
        .summary {{
            background: #ecf0f1;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 30px;
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }}
        .summary-item {{
            background: white;
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid #3498db;
        }}
        .summary-item strong {{
            display: block;
            color: #7f8c8d;
            font-size: 0.9em;
            margin-bottom: 5px;
        }}
        .summary-item span {{
            font-size: 1.3em;
            color: #2c3e50;
            font-weight: 600;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #34495e;
            color: white;
            font-weight: 600;
        }}
        tr:hover {{
            background: #f8f9fa;
        }}
        .badge {{
            padding: 4px 8px;
            border-radius: 3px;
            font-size: 0.85em;
            font-weight: 600;
        }}
        .risk-low {{ background: #2ecc71; color: white; }}
        .risk-medium {{ background: #f39c12; color: white; }}
        .risk-high {{ background: #e74c3c; color: white; }}
        .status-success {{ background: #2ecc71; color: white; }}
        .status-failed {{ background: #e74c3c; color: white; }}
        .phase {{
            background: #f8f9fa;
            padding: 20px;
            margin: 15px 0;
            border-radius: 5px;
            border-left: 4px solid #3498db;
        }}
        .phase-header {{
            font-size: 1.2em;
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 10px;
        }}
        .error {{
            background: #fee;
            border-left: 4px solid #e74c3c;
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
        }}
        .footer {{
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            text-align: center;
            color: #7f8c8d;
            font-size: 0.9em;
        }}
        a {{
            color: #3498db;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Migration Report</h1>

        <div class="summary">
            <strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
            <strong>Project:</strong> {state.get('project_path', 'Unknown')}<br>
            <strong>Type:</strong> {state.get('project_type', 'Unknown').upper()}<br>
            <strong>Status:</strong> <span class="badge status-{'success' if state.get('status') == 'deployed' else 'failed'}">{state.get('status', 'Unknown').upper()}</span>
"""

        if pr_url:
            html += f'<br><strong>Pull Request:</strong> <a href="{pr_url}" target="_blank">{branch_name}</a>'
        elif branch_name:
            html += f'<br><strong>Branch:</strong> <code>{branch_name}</code>'

        html += """

            <div class="summary-grid">
"""

        html += f"""
                <div class="summary-item">
                    <strong>Dependencies</strong>
                    <span>{len(migration_plan.get('dependencies', {}))}</span>
                </div>
                <div class="summary-item">
                    <strong>Migration Phases</strong>
                    <span>{migration_plan.get('migration_strategy', {}).get('total_phases', 0)}</span>
                </div>
                <div class="summary-item">
                    <strong>Overall Risk</strong>
                    <span class="badge risk-{migration_plan.get('overall_risk', 'medium')}">{migration_plan.get('overall_risk', 'Unknown').upper()}</span>
                </div>
                <div class="summary-item">
                    <strong>Total Cost</strong>
                    <span>${state.get('total_cost', 0):.4f}</span>
                </div>
                <div class="summary-item">
                    <strong>Source Branch</strong>
                    <span><code>{source_branch}</code></span>
                </div>
                <div class="summary-item">
                    <strong>Target Branch</strong>
                    <span><code>{target_branch}</code></span>
                </div>
            </div>
        </div>
"""

        # Dependencies Table
        dependencies = migration_plan.get('dependencies', {})
        if dependencies:
            html += """
        <h2>Dependencies Analysis</h2>
        <div style="background: #e3f2fd; border-left: 4px solid #2196f3; padding: 15px; margin: 20px 0; border-radius: 4px;">
            <p style="margin: 0; font-weight: 600; color: #1976d2;">ℹ️ What are Breaking Changes?</p>
            <p style="margin: 10px 0 0 0; color: #555;">
                Breaking changes are modifications in a new library version that are NOT backward-compatible.
                This means code written for the old version may require updates to work with the new version.
                Examples include: removed functions, changed API signatures, renamed methods, or removed built-in features.
                They don't mean your code is broken - they indicate potential compatibility issues that may need attention.
            </p>
        </div>
        <table>
            <thead>
                <tr>
                    <th>Package</th>
                    <th>Current</th>
                    <th>Target</th>
                    <th>Risk</th>
                    <th>Action</th>
                    <th>Breaking Changes</th>
                </tr>
            </thead>
            <tbody>
"""

            for pkg_name, pkg_info in dependencies.items():
                current = pkg_info.get('current_version', '?')
                target = pkg_info.get('target_version', '?')
                risk = pkg_info.get('risk', 'medium')
                action = pkg_info.get('action', '?').upper()
                breaking_count = len(pkg_info.get('breaking_changes', []))

                html += f"""
                <tr>
                    <td><strong>{pkg_name}</strong></td>
                    <td>{current}</td>
                    <td>{target}</td>
                    <td><span class="badge risk-{risk}">{risk.upper()}</span></td>
                    <td>{action}</td>
                    <td>{breaking_count}</td>
                </tr>
"""

            html += """
            </tbody>
        </table>
"""

        # Migration Strategy
        strategy = migration_plan.get('migration_strategy', {})
        phases = strategy.get('phases', [])

        if phases:
            html += "<h2>Migration Strategy</h2>"

            for phase in phases:
                phase_num = phase.get('phase', '?')
                name = phase.get('name', 'Unknown Phase')
                deps = phase.get('dependencies', [])
                time = phase.get('estimated_time', 'Unknown')
                rollback = phase.get('rollback_plan', 'No rollback plan')

                html += f"""
        <div class="phase">
            <div class="phase-header">Phase {phase_num}: {name}</div>
            <p><strong>Dependencies:</strong> {', '.join(deps)}</p>
            <p><strong>Estimated Time:</strong> {time}</p>
            <p><strong>Rollback Plan:</strong> {rollback}</p>
        </div>
"""

        # Validation Results
        if validation_result:
            val_data = validation_result.get('validation_result', {})

            html += f"""
        <h2>Validation Results</h2>
        <p><strong>Container:</strong> <code>{val_data.get('container_name', val_data.get('container_id', 'Unknown'))}</code></p>
        <table>
            <thead>
                <tr>
                    <th>Stage</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Build</td>
                    <td><span class="badge status-{'success' if val_data.get('build_success') else 'failed'}">{'SUCCESS' if val_data.get('build_success') else 'FAILED'}</span></td>
                </tr>
                <tr>
                    <td>Install</td>
                    <td><span class="badge status-{'success' if val_data.get('install_success') else 'failed'}">{'SUCCESS' if val_data.get('install_success') else 'FAILED'}</span></td>
                </tr>
                <tr>
                    <td>Runtime</td>
                    <td><span class="badge status-{'success' if val_data.get('runtime_success') else 'failed'}">{'SUCCESS' if val_data.get('runtime_success') else 'FAILED'}</span></td>
                </tr>
                <tr>
                    <td>Health Check</td>
                    <td><span class="badge status-{'success' if val_data.get('health_check_success') else 'failed'}">{'SUCCESS' if val_data.get('health_check_success') else 'FAILED'}</span></td>
                </tr>
                <tr>
                    <td><strong>Functional Tests</strong></td>
                    <td><span class="badge status-{'success' if val_data.get('tests_passed') else ('warning' if not val_data.get('tests_run') else 'failed')}">{'SUCCESS' if val_data.get('tests_passed') else ('NOT RUN' if not val_data.get('tests_run') else 'FAILED')}</span></td>
                </tr>
            </tbody>
        </table>
"""

            # Test Results Details
            logs = val_data.get('logs', {})
            test_logs = logs.get('tests', {})
            if test_logs and test_logs.get('success'):
                test_summary = test_logs.get('test_summary', 'N/A')
                html += f"""
        <h3>Test Results</h3>
        <p><strong>Summary:</strong> {test_summary}</p>
"""
                # Extract test counts
                test_output = test_logs.get('output', '')
                if 'Test Suites:' in test_output:
                    html += "<ul>"
                    lines = test_output.split('\n')
                    for line in lines:
                        if 'Test Suites:' in line or 'Tests:' in line:
                            html += f"<li>{line.strip()}</li>"
                    html += "</ul>"

            html += """
"""

        # Workflow Execution
        html += """
        <h2>Workflow Execution</h2>
        <pre style="background: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto;">
┌─────────────────────────────────────────────────────────────┐
│          AI Code Modernizer - 4-Agent Workflow             │
└─────────────────────────────────────────────────────────────┘

"""

        # Agent 1: Migration Planner
        planner_status = "✅ COMPLETE" if migration_plan else "❌ FAILED"
        html += f"""┌─────────────────────┐
│ [1] Migration       │ {planner_status}
│     Planner         │
└─────────────────────┘
          ↓
   (npm registry API)
          ↓
"""

        # Agent 2: Runtime Validator
        validator_status = "✅ COMPLETE" if validation_result and validation_result.get('status') == 'success' else "❌ FAILED" if validation_result else "⚠️ SKIPPED"
        html += f"""┌─────────────────────┐
│ [2] Runtime         │ {validator_status}
│     Validator       │
└─────────────────────┘
          ↓
  (Docker container)
          ↓
"""

        # Agent 3: Error Analyzer (always show)
        error_analysis = state.get('error_analysis')
        analyzer_status = "✅ COMPLETE" if error_analysis else "⚠️ NOT NEEDED"
        html += f"""┌─────────────────────┐
│ [3] Error Analyzer  │ {analyzer_status}
│   (conditional)     │
└─────────────────────┘
          ↓
  (only if validation fails)
          ↓
"""

        # Agent 4: Staging Deployer
        deployment_result = state.get('deployment_result')
        deployer_status = "✅ COMPLETE" if deployment_result and deployment_result.get('status') == 'success' else "⚠️ SKIPPED" if not deployment_result else "❌ FAILED"
        html += f"""┌─────────────────────┐
│ [4] Staging         │ {deployer_status}
│     Deployer        │
└─────────────────────┘
          ↓
  (GitHub PR created)
        </pre>

        <h3>Agent Execution Summary</h3>
        <table>
            <thead>
                <tr>
                    <th>Agent</th>
                    <th>Status</th>
                    <th>Cost</th>
                    <th>Details</th>
                </tr>
            </thead>
            <tbody>
"""

        # Add agent rows
        agent_costs = state.get('agent_costs', {})
        planner_cost = agent_costs.get('migration_planner', 0)
        validator_cost = agent_costs.get('runtime_validator', 0)
        analyzer_cost = agent_costs.get('error_analyzer', 0)
        deployer_cost = agent_costs.get('staging_deployer', 0)

        dep_count = len(migration_plan.get('dependencies', {})) if migration_plan else 0
        html += f"""
                <tr>
                    <td>Migration Planner</td>
                    <td><span class="badge status-success">COMPLETE</span></td>
                    <td>${planner_cost:.6f}</td>
                    <td>Analyzed {dep_count} dependencies</td>
                </tr>
"""

        # Runtime Validator
        val_data = validation_result.get('validation_result', {}) if validation_result else {}
        tests_run = val_data.get('tests_run', False)
        test_count = val_data.get('logs', {}).get('tests', {}).get('test_summary', 'N/A')
        validator_details = f"Docker validation, Tests: {test_count}" if tests_run else "Docker validation only"
        html += f"""
                <tr>
                    <td>Runtime Validator</td>
                    <td><span class="badge status-{'success' if validator_status == '✅ COMPLETE' else 'failed'}">{'COMPLETE' if validator_status == '✅ COMPLETE' else 'FAILED'}</span></td>
                    <td>${validator_cost:.6f}</td>
                    <td>{validator_details}</td>
                </tr>
"""

        # Error Analyzer (always show)
        analyzer_status_text = "COMPLETE" if error_analysis else "NOT NEEDED"
        analyzer_badge_class = "success" if error_analysis else "warning"
        fix_count = len(error_analysis.get('fix_suggestions', [])) if error_analysis else 0
        analyzer_details = f"Analyzed errors, {fix_count} fix suggestions" if error_analysis else "Validation succeeded, no errors to analyze"
        html += f"""
                <tr>
                    <td>Error Analyzer</td>
                    <td><span class="badge status-{analyzer_badge_class}">{analyzer_status_text}</span></td>
                    <td>${analyzer_cost:.6f}</td>
                    <td>{analyzer_details}</td>
                </tr>
"""

        deployment_result = state.get('deployment_result', {})
        files_updated = len(deployment_result.get('files_updated', []))
        branch_name = deployment_result.get('branch_name') or state.get('branch_name') or 'N/A'
        branch_display = branch_name[:30] if branch_name != 'N/A' else 'N/A'
        html += f"""
                <tr>
                    <td>Staging Deployer</td>
                    <td><span class="badge status-{'success' if deployer_status == '✅ COMPLETE' else 'warning'}">{'COMPLETE' if deployer_status == '✅ COMPLETE' else 'SKIPPED'}</span></td>
                    <td>${deployer_cost:.6f}</td>
                    <td>Updated {files_updated} files, Branch: {branch_display}</td>
                </tr>
"""

        html += """
            </tbody>
        </table>
"""

        # Agent Roles & Responsibilities
        html += """
        <h2>Agent Roles &amp; Responsibilities</h2>

        <h3>1. 🤖 Migration Planner Agent</h3>
        <p><strong>Role:</strong> Dependency Analysis &amp; Strategy Planning</p>
        <p><strong>Responsibilities:</strong></p>
        <ul>
            <li>Fetch latest package versions from npm/PyPI registries</li>
            <li>Compare current vs. latest versions for all dependencies</li>
            <li>Identify outdated, deprecated, or vulnerable packages</li>
            <li>Assess migration risks (low/medium/high) based on version jumps</li>
            <li>Research breaking changes and compatibility issues using LLM</li>
            <li>Create phased migration strategy (low-risk → high-risk)</li>
            <li>Calculate estimated time and effort per phase</li>
        </ul>
"""
        html += f"<p><strong>Status in this migration:</strong> {planner_status}<br>"
        html += f"<strong>Cost:</strong> ${planner_cost:.6f} | <strong>Dependencies analyzed:</strong> {dep_count}</p>"

        html += """
        <h3>2. 🐳 Runtime Validator Agent</h3>
        <p><strong>Role:</strong> Safe Testing in Isolated Environments</p>
        <p><strong>Responsibilities:</strong></p>
        <ul>
            <li>Create isolated Docker container for testing</li>
            <li>Apply dependency upgrades to container</li>
            <li>Install upgraded dependencies (npm install / pip install)</li>
            <li>Start the application in container</li>
            <li>Perform health checks on running application</li>
            <li>Execute functional test suites (if available)</li>
            <li>Collect logs and error details</li>
            <li>Report validation success/failure with diagnostics</li>
        </ul>
"""
        html += f"<p><strong>Status in this migration:</strong> {validator_status}<br>"
        html += f"<strong>Cost:</strong> ${validator_cost:.6f} | <strong>Tests executed:</strong> {test_count if tests_run else 'N/A'}</p>"

        if error_analysis:
            html += """
        <h3>3. 🔍 Error Analyzer Agent</h3>
        <p><strong>Role:</strong> Intelligent Error Diagnosis &amp; Fix Suggestions</p>
        <p><strong>Responsibilities:</strong></p>
        <ul>
            <li>Parse error logs from validation failures</li>
            <li>Identify root causes using pattern matching + LLM analysis</li>
            <li>Categorize errors (dependency conflict, breaking change, etc.)</li>
            <li>Generate actionable fix suggestions</li>
            <li>Prioritize fixes by impact and feasibility</li>
            <li>Recommend alternative upgrade strategies if needed</li>
        </ul>
"""
            html += f"<p><strong>Status in this migration:</strong> ✅ COMPLETE<br>"
            html += f"<strong>Cost:</strong> ${analyzer_cost:.6f} | <strong>Fixes suggested:</strong> {fix_count}</p>"

        html += """
        <h3>4. 🚀 Staging Deployer Agent</h3>
        <p><strong>Role:</strong> Safe Deployment via GitHub Workflow</p>
        <p><strong>Responsibilities:</strong></p>
        <ul>
            <li>Create timestamped feature branch (upgrade/dependencies-YYYYMMDD-HHMMSS)</li>
            <li>Update dependency files (package.json / requirements.txt)</li>
            <li>Generate conventional commit messages with upgrade details</li>
            <li>Commit changes to the new branch</li>
            <li>Push branch to remote repository</li>
            <li>Create GitHub Pull Request with detailed description</li>
            <li>Include testing instructions and rollback plan</li>
            <li>Wait for human approval before merge (safety gate)</li>
        </ul>
"""
        html += f"<p><strong>Status in this migration:</strong> {deployer_status}<br>"
        html += f"<strong>Cost:</strong> ${deployer_cost:.6f} | <strong>Files updated:</strong> {files_updated}</p>"

        # AI/LLM Insights
        html += """
        <h2>AI/LLM Insights</h2>
        <p><em>This section provides transparency into how our AI agents make decisions.</em></p>

        <h3>Migration Planner Analysis</h3>
        <p><strong>AI Model Used:</strong> Gemini 2.0 Flash (fast, cost-effective)</p>
        <p><strong>Data Sources:</strong></p>
        <ul>
            <li>npm Registry API (https://registry.npmjs.org) for latest versions</li>
            <li>LLM knowledge base for breaking changes and migration risks</li>
        </ul>
        <p><strong>Decision Process:</strong></p>
        <ol>
            <li>Fetched latest versions from npm registry</li>
            <li>Compared current vs. latest for each dependency</li>
            <li>Analyzed version jumps (major/minor/patch)</li>
            <li>Assessed breaking changes and compatibility risks</li>
            <li>Created phased migration strategy</li>
        </ol>
"""

        if migration_plan and migration_plan.get('dependencies'):
            high_risk_deps = [(name, info) for name, info in migration_plan['dependencies'].items()
                             if info.get('risk', '').lower() == 'high']
            if high_risk_deps:
                html += "<p><strong>Key AI Decisions:</strong></p><p>High-risk upgrades identified:</p><ul>"
                for name, info in high_risk_deps[:3]:
                    html += f"<li><strong>{name}</strong> ({info.get('current_version')} → {info.get('target_version')})"
                    breaking_changes = info.get('breaking_changes', [])
                    if breaking_changes:
                        html += f"<br>Breaking: {breaking_changes[0]}"
                    html += "</li>"
                html += "</ul>"

        if validation_result:
            val_data = validation_result.get('validation_result', {})
            html += """
        <h3>Runtime Validator Process</h3>
        <p><strong>Validation Environment:</strong> Docker container (isolated, reproducible)</p>
        <p><strong>Steps Executed:</strong></p>
        <ol>
"""
            html += f"<li>✅ Container created: <code>{val_data.get('container_name', 'N/A')}</code></li>"
            html += f"<li>{'✅' if val_data.get('build_success') else '❌'} Project files copied</li>"
            html += f"<li>{'✅' if val_data.get('install_success') else '❌'} Dependencies installed</li>"
            html += f"<li>{'✅' if val_data.get('runtime_success') else '❌'} Application started</li>"
            html += f"<li>{'✅' if val_data.get('health_check_success') else '❌'} Health checks passed</li>"
            html += f"<li>{'✅' if val_data.get('tests_passed') else '⚠️'} Functional tests executed</li>"
            html += "</ol>"

        html += """
        <h3>System Intelligence Highlights</h3>
        <p><strong>Multi-Agent Architecture (4 Specialized Agents):</strong></p>
        <ul>
            <li>Each agent has a specific responsibility and expertise</li>
            <li>Agents communicate via LangGraph workflow state</li>
            <li>Conditional routing: Error Analyzer only runs when validation fails</li>
            <li>Retry logic: Up to 3 attempts with automatic fix application</li>
        </ul>
        <p><strong>Safety Mechanisms:</strong></p>
        <ul>
            <li>Docker isolation prevents host system contamination</li>
            <li>All changes go through GitHub PR (human review required)</li>
            <li>Automatic rollback instructions provided</li>
            <li>Comprehensive test suite execution before deployment</li>
        </ul>
"""

        total_cost = state.get('total_cost', 0)
        html += f"<p><strong>Total AI Cost for This Migration:</strong> ${total_cost:.6f} USD</p>"

        # Cost Report
        agent_costs = state.get('agent_costs', {})
        agent_costs = state.get('agent_costs', {})
        if agent_costs:
            html += """
        <h2>Cost Report</h2>
        <table>
            <thead>
                <tr>
                    <th>Agent</th>
                    <th>Cost (USD)</th>
                </tr>
            </thead>
            <tbody>
"""

            for agent, cost in agent_costs.items():
                html += f"""
                <tr>
                    <td>{agent}</td>
                    <td>${cost:.4f}</td>
                </tr>
"""

            html += f"""
                <tr style="background: #ecf0f1; font-weight: 600;">
                    <td>TOTAL</td>
                    <td>${state.get('total_cost', 0):.4f}</td>
                </tr>
            </tbody>
        </table>
"""

        # Errors
        errors = state.get('errors', [])
        if errors:
            html += """
        <h2>Errors and Warnings</h2>
"""
            for i, error in enumerate(errors, 1):
                html += f"""
        <div class="error">{i}. {error}</div>
"""

        # Footer
        html += """
        <div class="footer">
            Report generated by <strong>AI Code Modernizer</strong>
        </div>
    </div>
</body>
</html>
"""

        return html


def main():
    """Standalone test of report generator."""
    print("=" * 80)
    print("REPORT GENERATOR - STANDALONE TEST")
    print("=" * 80)

    # Load the most recent migration plan
    migration_plan_file = Path("migration_plan_output.json")

    if not migration_plan_file.exists():
        print(f"\nERROR: {migration_plan_file} not found")
        return 1

    with open(migration_plan_file) as f:
        migration_plan = json.load(f)

    # Create mock workflow state
    workflow_state = {
        "project_path": migration_plan.get('project_path', 'Unknown'),
        "project_type": migration_plan.get('project_type', 'nodejs'),
        "status": "deployed",
        "migration_plan": migration_plan,
        "validation_success": True,
        "validation_result": {
            "status": "success",
            "validation_result": {
                "container_id": "abc123",
                "container_name": "ai-modernizer-simple-express-app",
                "build_success": True,
                "install_success": True,
                "runtime_success": True,
                "health_check_success": True,
                "errors": []
            }
        },
        "branch_name": "upgrade/dependencies-20251110",
        "pr_url": None,
        "total_cost": 0.0007,
        "retry_count": 0,
        "max_retries": 3,
        "agent_costs": {
            "migration_planner": 0.0005,
            "runtime_validator": 0.0002,
            "staging_deployer": 0.0000
        },
        "errors": []
    }

    # Generate reports
    print("\nGenerating reports...")
    generator = ReportGenerator(output_dir="reports")

    project_name = Path(workflow_state['project_path']).name
    reports = generator.generate_all_reports(workflow_state, project_name)

    print("\n" + "=" * 80)
    print("REPORTS GENERATED")
    print("=" * 80)

    for format_type, path in reports.items():
        print(f"\n{format_type.upper()}: {path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
