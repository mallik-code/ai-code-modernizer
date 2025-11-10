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
        base_name = f"{project_name}_migration_report_{timestamp}"

        reports = {}

        # Generate JSON report
        json_path = self.output_dir / f"{base_name}.json"
        self.generate_json_report(workflow_state, json_path)
        reports['json'] = str(json_path)

        # Generate Markdown report
        md_path = self.output_dir / f"{base_name}.md"
        self.generate_markdown_report(workflow_state, md_path)
        reports['markdown'] = str(md_path)

        # Generate HTML report
        html_path = self.output_dir / f"{base_name}.html"
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
        pr_url = state.get('pr_url')
        branch_name = state.get('branch_name')

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
            md += f"| Health Check | {'✅ SUCCESS' if val_data.get('health_check_success') else '❌ FAILED'} |\n\n"

            # Errors
            errors = val_data.get('errors', [])
            if errors:
                md += "### Errors\n\n"
                for i, error in enumerate(errors, 1):
                    md += f"{i}. {error}\n"
                md += "\n"
        else:
            md += "*Validation not performed*\n\n"

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

        # Footer
        md += "---\n\n"
        md += "*Report generated by AI Code Modernizer*\n"

        return md

    def _build_html_content(self, state: Dict[str, Any]) -> str:
        """Build HTML report content."""

        migration_plan = state.get('migration_plan', {})
        validation_result = state.get('validation_result', {})
        pr_url = state.get('pr_url')
        branch_name = state.get('branch_name')

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
            </div>
        </div>
"""

        # Dependencies Table
        dependencies = migration_plan.get('dependencies', {})
        if dependencies:
            html += """
        <h2>Dependencies Analysis</h2>
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
            </tbody>
        </table>
"""

        # Cost Report
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
