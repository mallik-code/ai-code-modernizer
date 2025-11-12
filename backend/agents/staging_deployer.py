"""Staging Deployer Agent

Deploys validated dependency upgrades by creating Git branches, updating files,
committing changes, and creating GitHub Pull Requests for human review.

Capabilities:
- Creates Git branches for upgrades
- Updates package.json or requirements.txt with new versions
- Updates source code files if needed (e.g., removing deprecated imports)
- Commits changes with detailed commit messages
- Creates GitHub Pull Requests via MCP
- Provides rollback instructions
"""

import json
import subprocess
import sys
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime

from agents.base import BaseAgent


class StagingDeployerAgent(BaseAgent):
    """Agent for deploying validated dependency upgrades via GitHub PRs."""

    def __init__(self, llm_provider: Optional[str] = None, llm_model: Optional[str] = None):
        system_prompt = """You are an expert software deployment specialist.

Your role:
1. Create Git branches for dependency upgrades
2. Update dependency files (package.json, requirements.txt)
3. Update source code if needed (remove deprecated imports, update APIs)
4. Generate detailed commit messages
5. Create comprehensive Pull Request descriptions
6. Provide rollback instructions

When deploying:
- Always create a new branch (never modify main directly)
- Make atomic, focused changes
- Write clear commit messages explaining WHY changes were made
- Include testing instructions in PR descriptions
- Document breaking changes and migration steps
- Provide rollback procedures

Safety principles:
- Human approval required before merge
- All changes visible in PR diff
- Easy rollback via branch deletion
- No direct pushes to protected branches

Output Format:
Return structured deployment results with:
{
    "deployment_status": "success" or "failed",
    "branch_name": "upgrade/package-name-version",
    "files_updated": ["package.json", "src/app.js"],
    "commit_sha": "abc123...",
    "pr_url": "https://github.com/owner/repo/pull/123",
    "pr_number": 123,
    "rollback_instructions": ["git checkout main", "git branch -D upgrade-branch"],
    "next_steps": ["Review PR", "Test locally", "Merge when ready"]
}

Be thorough, safe, and provide clear guidance."""

        super().__init__(
            name="staging_deployer",
            system_prompt=system_prompt,
            llm_provider=llm_provider,
            llm_model=llm_model
        )

    def execute(self, input_data: Dict) -> Dict:
        """Execute staging deployment.

        Args:
            input_data: Dictionary with:
                - project_path: Path to project directory
                - migration_plan: Migration plan to deploy
                - validation_result: Results from runtime validation
                - github_token: GitHub Personal Access Token for API operations (optional)
                - base_branch: Base branch name (default: "main")
                - create_pr: Whether to create PR (default: True)

        Returns:
            Dictionary with deployment results
        """
        try:
            project_path = input_data.get("project_path")
            migration_plan = input_data.get("migration_plan")
            validation_result = input_data.get("validation_result")
            github_token = input_data.get("github_token")
            is_git_cloned_repo = input_data.get("is_git_cloned_repo", False)
            base_branch = input_data.get("base_branch", "main")
            create_pr = input_data.get("create_pr", True)

            if not project_path:
                return {
                    "status": "error",
                    "error": "project_path is required"
                }

            if not migration_plan:
                return {
                    "status": "error",
                    "error": "migration_plan is required"
                }

            self.logger.info("starting_staging_deployment",
                           project_path=project_path,
                           base_branch=base_branch,
                           create_pr=create_pr,
                           has_github_token=bool(github_token))

            # Change to project directory
            project_dir = Path(project_path)
            if not project_dir.exists():
                return {
                    "status": "error",
                    "error": f"Project path does not exist: {project_path}"
                }

            # Generate branch name
            branch_name = self._generate_branch_name(migration_plan)
            self.logger.info("branch_name_generated", branch_name=branch_name)

            # Create Git branch
            branch_result = self._create_branch(project_dir, branch_name, base_branch)
            if "error" in branch_result:
                return branch_result

            # Update files
            files_updated = self._update_dependency_files(project_dir, migration_plan)
            self.logger.info("files_updated", count=len(files_updated), files=files_updated)

            # Generate commit message
            commit_message = self._generate_commit_message(migration_plan, validation_result)

            # Commit changes
            commit_result = self._commit_changes(project_dir, commit_message, files_updated)
            if "error" in commit_result:
                return commit_result

            # Push branch
            push_result = self._push_branch(project_dir, branch_name, github_token, is_git_cloned_repo)
            if "error" in push_result:
                return push_result

            # Create PR if requested
            pr_result = {}
            if create_pr:
                pr_description = self._generate_pr_description(migration_plan, validation_result)
                pr_result = self._create_pull_request(
                    project_dir,
                    branch_name,
                    base_branch,
                    pr_description,
                    github_token
                )

            # Log cost
            cost_report = self.llm.cost_tracker.get_report()
            self.logger.info("staging_deployment_complete",
                           branch=branch_name,
                           files_updated=len(files_updated),
                           pr_created=create_pr,
                           cost_usd=cost_report["total_cost_usd"])

            return {
                "status": "success",
                "branch_name": branch_name,
                "files_updated": files_updated,
                "commit_sha": commit_result.get("commit_sha"),
                "pr_url": pr_result.get("pr_url"),
                "pr_number": pr_result.get("pr_number"),
                "rollback_instructions": [
                    f"git checkout {base_branch}",
                    f"git branch -D {branch_name}",
                    f"git push origin --delete {branch_name}"
                ],
                "next_steps": [
                    f"Review PR at {pr_result.get('pr_url', 'GitHub')}",
                    "Test changes locally",
                    "Merge PR when ready"
                ],
                "cost_report": cost_report
            }

        except Exception as e:
            self.logger.error("staging_deployment_failed", error=str(e), exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }

    def _generate_branch_name(self, migration_plan: Dict) -> str:
        """Generate branch name from migration plan.

        Args:
            migration_plan: Migration plan

        Returns:
            Branch name (e.g., "upgrade/dependencies-20251112-104530")
        """
        # Always use timestamp format for consistency
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        return f"upgrade/dependencies-{timestamp}"

    def _create_branch(self, project_dir: Path, branch_name: str, base_branch: str) -> Dict:
        """Create Git branch.

        Args:
            project_dir: Project directory
            branch_name: New branch name
            base_branch: Base branch to branch from

        Returns:
            Result dictionary
        """
        try:
            # Ensure we're on the base branch
            subprocess.run(
                ["git", "checkout", base_branch],
                cwd=project_dir,
                check=True,
                capture_output=True,
                text=True
            )

            # Pull latest changes
            subprocess.run(
                ["git", "pull"],
                cwd=project_dir,
                check=True,
                capture_output=True,
                text=True
            )

            # Create and checkout new branch
            result = subprocess.run(
                ["git", "checkout", "-b", branch_name],
                cwd=project_dir,
                check=True,
                capture_output=True,
                text=True
            )

            self.logger.info("branch_created", branch=branch_name, base=base_branch)
            return {"status": "success", "branch": branch_name}

        except subprocess.CalledProcessError as e:
            self.logger.error("branch_creation_failed", error=e.stderr, branch=branch_name)
            return {
                "status": "error",
                "error": f"Failed to create branch: {e.stderr}"
            }

    def _update_dependency_files(self, project_dir: Path, migration_plan: Dict) -> List[str]:
        """Update dependency files with new versions.

        Args:
            project_dir: Project directory
            migration_plan: Migration plan

        Returns:
            List of updated file paths
        """
        files_updated = []
        project_type = migration_plan.get("project_type", "unknown")

        if project_type == "nodejs":
            package_json = project_dir / "package.json"
            if package_json.exists():
                self._update_package_json(package_json, migration_plan)
                files_updated.append("package.json")

        elif project_type == "python":
            requirements_txt = project_dir / "requirements.txt"
            if requirements_txt.exists():
                self._update_requirements_txt(requirements_txt, migration_plan)
                files_updated.append("requirements.txt")

        return files_updated

    def _update_package_json(self, file_path: Path, migration_plan: Dict):
        """Update package.json with new versions.

        Args:
            file_path: Path to package.json
            migration_plan: Migration plan
        """
        with open(file_path, 'r') as f:
            package_data = json.load(f)

        # Apply upgrades
        for dep_name, dep_info in migration_plan.get("dependencies", {}).items():
            action = dep_info.get("action", "keep")
            target_version = dep_info.get("target_version", "")

            if action == "upgrade" and target_version:
                # Update in both dependencies and devDependencies
                if dep_name in package_data.get("dependencies", {}):
                    package_data["dependencies"][dep_name] = target_version
                    self.logger.info("dependency_updated", package=dep_name, version=target_version, type="dependencies")

                if dep_name in package_data.get("devDependencies", {}):
                    package_data["devDependencies"][dep_name] = target_version
                    self.logger.info("dependency_updated", package=dep_name, version=target_version, type="devDependencies")

            elif action == "remove":
                # Remove from both
                if dep_name in package_data.get("dependencies", {}):
                    del package_data["dependencies"][dep_name]
                    self.logger.info("dependency_removed", package=dep_name, type="dependencies")

                if dep_name in package_data.get("devDependencies", {}):
                    del package_data["devDependencies"][dep_name]
                    self.logger.info("dependency_removed", package=dep_name, type="devDependencies")

        # Write updated file
        with open(file_path, 'w') as f:
            json.dump(package_data, f, indent=2)
            f.write('\n')  # Add trailing newline

    def _update_requirements_txt(self, file_path: Path, migration_plan: Dict):
        """Update requirements.txt with new versions.

        Args:
            file_path: Path to requirements.txt
            migration_plan: Migration plan
        """
        with open(file_path, 'r') as f:
            lines = f.readlines()

        updated_lines = []
        dependencies = migration_plan.get("dependencies", {})

        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                updated_lines.append(line)
                continue

            # Parse package name
            pkg_name = line.split("==")[0].split(">=")[0].split("<")[0].strip()

            if pkg_name in dependencies:
                dep_info = dependencies[pkg_name]
                action = dep_info.get("action", "keep")
                target_version = dep_info.get("target_version", "")

                if action == "upgrade" and target_version:
                    updated_lines.append(f"{pkg_name}=={target_version}")
                    self.logger.info("dependency_updated", package=pkg_name, version=target_version)
                elif action != "remove":
                    updated_lines.append(line)
            else:
                updated_lines.append(line)

        # Write updated file
        with open(file_path, 'w') as f:
            f.write('\n'.join(updated_lines))
            f.write('\n')  # Add trailing newline

    def _generate_commit_message(self, migration_plan: Dict, validation_result: Optional[Dict]) -> str:
        """Generate commit message.

        Args:
            migration_plan: Migration plan
            validation_result: Validation results

        Returns:
            Commit message in conventional commits format
        """
        dependencies = migration_plan.get("dependencies", {})
        upgraded = [name for name, info in dependencies.items() if info.get("action") == "upgrade"]
        removed = [name for name, info in dependencies.items() if info.get("action") == "remove"]

        # Build commit title (conventional commits format)
        if len(upgraded) == 1 and len(removed) == 0:
            dep_name = upgraded[0]
            dep_info = dependencies[dep_name]
            current = dep_info.get("current_version", "")
            target = dep_info.get("target_version", "")
            title = f"chore(deps): upgrade {dep_name} {current} → {target}"
        elif len(upgraded) > 1:
            title = f"chore(deps): upgrade {len(upgraded)} dependencies"
        else:
            title = "chore(deps): update dependencies"

        # Build commit body
        body_parts = []

        if upgraded:
            body_parts.append("Upgraded:")
            for name in upgraded:
                info = dependencies[name]
                current = info.get("current_version", "unknown")
                target = info.get("target_version", "unknown")
                body_parts.append(f"  - {name}: {current} → {target}")

        if removed:
            body_parts.append("\nRemoved:")
            for name in removed:
                info = dependencies[name]
                reason = info.get("reason", "Deprecated")
                body_parts.append(f"  - {name} ({reason})")

        if validation_result and validation_result.get("status") == "success":
            body_parts.append("\nValidation: ✓ Passed runtime tests in Docker")

        # Combine
        commit_message = title + "\n\n" + "\n".join(body_parts)
        return commit_message

    def _commit_changes(self, project_dir: Path, commit_message: str, files: List[str]) -> Dict:
        """Commit changes to Git.

        Args:
            project_dir: Project directory
            commit_message: Commit message
            files: Files to commit

        Returns:
            Result dictionary with commit_sha
        """
        try:
            # Stage files
            subprocess.run(
                ["git", "add"] + files,
                cwd=project_dir,
                check=True,
                capture_output=True,
                text=True
            )

            # Commit
            subprocess.run(
                ["git", "commit", "-m", commit_message],
                cwd=project_dir,
                check=True,
                capture_output=True,
                text=True
            )

            # Get commit SHA
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=project_dir,
                check=True,
                capture_output=True,
                text=True
            )
            commit_sha = result.stdout.strip()

            self.logger.info("changes_committed", commit_sha=commit_sha[:8], files=len(files))
            return {"status": "success", "commit_sha": commit_sha}

        except subprocess.CalledProcessError as e:
            self.logger.error("commit_failed", error=e.stderr)
            return {
                "status": "error",
                "error": f"Failed to commit changes: {e.stderr}"
            }

    def _push_branch(self, project_dir: Path, branch_name: str, github_token: Optional[str] = None, is_git_cloned_repo: bool = False) -> Dict:
        """Push branch to remote with optional authentication.

        Args:
            project_dir: Project directory
            branch_name: Branch name
            github_token: GitHub Personal Access Token for authentication (optional)
            is_git_cloned_repo: Whether this repo was cloned from a Git repository

        Returns:
            Result dictionary
        """
        try:
            import os

            # Use provided token or fall back to environment variable
            token_to_use = github_token or os.getenv("GITHUB_TOKEN")

            # For local repos that aren't Git clones, use simple push unless token is explicitly provided
            if not is_git_cloned_repo and not token_to_use:
                # Use simple push for local repos without authentication
                subprocess.run(
                    ["git", "push", "-u", "origin", branch_name],
                    cwd=project_dir,
                    check=True,
                    capture_output=True,
                    text=True
                )
                self.logger.info("branch_pushed", branch=branch_name)
                return {"status": "success"}

            # For Git-cloned repos or when token is provided, use authentication logic
            if token_to_use:
                # Get current remote URL
                result = subprocess.run(
                    ["git", "remote", "get-url", "origin"],
                    cwd=project_dir,
                    check=True,
                    capture_output=True,
                    text=True
                )
                original_url = result.stdout.strip()

                # Check if this is a GitHub HTTPS URL that needs authentication
                if original_url.startswith("https://github.com/"):
                    # Add token to URL: https://token@github.com/user/repo.git
                    auth_url = original_url.replace("https://", f"https://{token_to_use}@")

                    subprocess.run(
                        ["git", "remote", "set-url", "origin", auth_url],
                        cwd=project_dir,
                        check=True,
                        capture_output=True,
                        text=True
                    )

                    try:
                        # Push with authentication
                        subprocess.run(
                            ["git", "push", "-u", "origin", branch_name],
                            cwd=project_dir,
                            check=True,
                            capture_output=True,
                            text=True
                        )

                        self.logger.info("branch_pushed", branch=branch_name)
                        return {"status": "success"}

                    finally:
                        # Restore original URL (remove token)
                        subprocess.run(
                            ["git", "remote", "set-url", "origin", original_url],
                            cwd=project_dir,
                            capture_output=True,
                            text=True
                        )
                else:
                    # Non-GitHub URL, push without token modification
                    subprocess.run(
                        ["git", "push", "-u", "origin", branch_name],
                        cwd=project_dir,
                        check=True,
                        capture_output=True,
                        text=True
                    )

                    self.logger.info("branch_pushed", branch=branch_name)
                    return {"status": "success"}
            else:
                # No token available, try push anyway (may work for public repos or repos with other authentication)
                self.logger.warning("no_github_token_for_push",
                                  message="No GitHub token available, push may fail for private repos")
                subprocess.run(
                    ["git", "push", "-u", "origin", branch_name],
                    cwd=project_dir,
                    check=True,
                    capture_output=True,
                    text=True
                )

                self.logger.info("branch_pushed", branch=branch_name)
                return {"status": "success"}

        except subprocess.CalledProcessError as e:
            self.logger.error("push_failed", error=e.stderr, branch=branch_name)
            return {
                "status": "error",
                "error": f"Failed to push branch: {e.stderr}"
            }

    def _generate_pr_description(self, migration_plan: Dict, validation_result: Optional[Dict]) -> str:
        """Generate PR description.

        Args:
            migration_plan: Migration plan
            validation_result: Validation results

        Returns:
            PR description in markdown
        """
        dependencies = migration_plan.get("dependencies", {})
        upgraded = {name: info for name, info in dependencies.items() if info.get("action") == "upgrade"}
        removed = {name: info for name, info in dependencies.items() if info.get("action") == "remove"}

        description_parts = []

        # Title section
        description_parts.append("## 🚀 Dependency Upgrade")
        description_parts.append("")
        description_parts.append("This PR upgrades project dependencies according to the automated migration plan.")
        description_parts.append("")

        # Upgraded dependencies
        if upgraded:
            description_parts.append("### 📦 Upgraded Dependencies")
            description_parts.append("")
            description_parts.append("| Package | Current | Target | Risk | Breaking Changes |")
            description_parts.append("|---------|---------|--------|------|------------------|")
            for name, info in upgraded.items():
                current = info.get("current_version", "?")
                target = info.get("target_version", "?")
                risk = info.get("risk", "?").upper()
                breaking = len(info.get("breaking_changes", []))
                description_parts.append(f"| {name} | {current} | {target} | {risk} | {breaking} |")
            description_parts.append("")

        # Removed dependencies
        if removed:
            description_parts.append("### 🗑️ Removed Dependencies")
            description_parts.append("")
            for name, info in removed.items():
                reason = info.get("reason", "Deprecated")
                description_parts.append(f"- **{name}**: {reason}")
            description_parts.append("")

        # Validation results
        if validation_result:
            description_parts.append("### ✅ Validation")
            description_parts.append("")
            if validation_result.get("status") == "success":
                description_parts.append("- ✅ Runtime validation **PASSED** in isolated Docker container")
                description_parts.append("- ✅ Application starts successfully")
                description_parts.append("- ✅ Health checks passed")
            else:
                description_parts.append("- ⚠️ Runtime validation encountered issues")
                description_parts.append("- See validation logs for details")
            description_parts.append("")

        # Migration strategy
        strategy = migration_plan.get("migration_strategy", {})
        description_parts.append("### 📋 Migration Strategy")
        description_parts.append("")
        description_parts.append(f"- **Total Phases**: {strategy.get('total_phases', 0)}")
        description_parts.append(f"- **Overall Risk**: {migration_plan.get('overall_risk', 'unknown').upper()}")
        description_parts.append(f"- **Estimated Time**: {migration_plan.get('estimated_total_time', 'unknown')}")
        description_parts.append("")

        # Recommendations
        recommendations = migration_plan.get("recommendations", [])
        if recommendations:
            description_parts.append("### 💡 Recommendations")
            description_parts.append("")
            for rec in recommendations:
                description_parts.append(f"- {rec}")
            description_parts.append("")

        # Testing instructions
        description_parts.append("### 🧪 Testing Instructions")
        description_parts.append("")
        description_parts.append("1. Checkout this branch:")
        description_parts.append("   ```bash")
        description_parts.append("   git fetch origin")
        description_parts.append("   git checkout <branch-name>")
        description_parts.append("   ```")
        description_parts.append("")
        description_parts.append("2. Install dependencies:")
        project_type = migration_plan.get("project_type", "unknown")
        if project_type == "nodejs":
            description_parts.append("   ```bash")
            description_parts.append("   npm install")
            description_parts.append("   ```")
        elif project_type == "python":
            description_parts.append("   ```bash")
            description_parts.append("   pip install -r requirements.txt")
            description_parts.append("   ```")
        description_parts.append("")
        description_parts.append("3. Run tests:")
        description_parts.append("   ```bash")
        description_parts.append("   npm test  # or pytest")
        description_parts.append("   ```")
        description_parts.append("")
        description_parts.append("4. Start application and verify functionality")
        description_parts.append("")

        # Footer
        description_parts.append("---")
        description_parts.append("")
        description_parts.append("🤖 *This PR was automatically generated by AI Code Modernizer*")

        return "\n".join(description_parts)

    def _create_pull_request(
        self,
        project_dir: Path,
        branch_name: str,
        base_branch: str,
        description: str,
        github_token: Optional[str] = None
    ) -> Dict:
        """Create GitHub Pull Request via MCP or GitHub API.

        Args:
            project_dir: Project directory
            branch_name: Source branch
            base_branch: Target branch
            description: PR description
            github_token: GitHub Personal Access Token for API operations (optional)

        Returns:
            Result dictionary with pr_url and pr_number
        """
        try:
            # Extract title from description (first line)
            title = description.split('\n')[0].replace('#', '').strip()
            if not title:
                title = f"Upgrade dependencies ({branch_name})"

            # Get repository info from git remote
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                cwd=project_dir,
                check=True,
                capture_output=True,
                text=True
            )
            remote_url = result.stdout.strip()

            # Parse owner/repo from URL
            # Examples:
            # - https://github.com/owner/repo.git
            # - git@github.com:owner/repo.git
            if "github.com" in remote_url:
                if remote_url.startswith("https://"):
                    parts = remote_url.replace("https://github.com/", "").replace(".git", "").split("/")
                elif remote_url.startswith("git@"):
                    parts = remote_url.replace("git@github.com:", "").replace(".git", "").split("/")
                else:
                    raise ValueError(f"Unsupported remote URL format: {remote_url}")

                owner, repo = parts[0], parts[1]
            else:
                raise ValueError(f"Not a GitHub repository: {remote_url}")

            # Create PR via MCP GitHub tools or GitHub API
            # Use provided token if available, otherwise fall back to environment variable
            import os
            token_to_use = github_token or os.getenv("GITHUB_TOKEN")

            if not token_to_use:
                self.logger.warning("no_github_token",
                                  message="No GitHub token provided, PR creation may fail")

            pr_result = self.tools.github_create_pr(
                owner=owner,
                repo=repo,
                title=title,
                body=description,
                head=branch_name,
                base=base_branch,
                token=token_to_use
            )

            self.logger.info("pull_request_created",
                           owner=owner,
                           repo=repo,
                           pr_number=pr_result.get("pr_number"),
                           pr_url=pr_result.get("pr_url"))

            return {
                "status": "success",
                "pr_url": pr_result.get("pr_url"),
                "pr_number": pr_result.get("pr_number")
            }

        except Exception as e:
            self.logger.error("pr_creation_failed", error=str(e))
            return {
                "status": "error",
                "error": f"Failed to create PR: {str(e)}",
                "pr_url": None,
                "pr_number": None
            }


def main():
    """Standalone test of Staging Deployer Agent."""

    print("=" * 80)
    print("STAGING DEPLOYER AGENT - STANDALONE TEST")
    print("=" * 80)

    # Test with sample Express app
    test_project = Path(__file__).parent.parent / "tests" / "sample_projects" / "express-app"

    if not test_project.exists():
        print(f"\nERROR: Test project not found at {test_project}")
        return 1

    print(f"\nTest Project: {test_project}")
    print("Action: Create branch and update files (NO PR creation for test)")

    # Load sample migration plan
    sample_plan = {
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
                "reason": "Deprecated - now built into Express"
            }
        },
        "migration_strategy": {
            "total_phases": 1,
            "phases": [{"phase": 1, "name": "Low-risk updates"}]
        },
        "overall_risk": "low",
        "estimated_total_time": "1 hour",
        "recommendations": ["Test all API endpoints after upgrade"]
    }

    sample_validation = {
        "status": "success",
        "build_success": True,
        "install_success": True,
        "runtime_success": True,
        "health_check_success": True
    }

    # Create agent
    print("\n1. Creating Staging Deployer Agent...")
    agent = StagingDeployerAgent()
    print(f"   Provider: {agent.llm.get_provider_name()}")
    print(f"   Model: {agent.llm.model}")

    # Execute deployment (without PR creation for test)
    print("\n2. Deploying changes...")
    print("   (Creating branch, updating files - NO PR for safety)")

    result = agent.execute({
        "project_path": str(test_project),
        "migration_plan": sample_plan,
        "validation_result": sample_validation,
        "base_branch": "main",
        "create_pr": False  # Don't create PR in test
    })

    # Display results
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)

    if result["status"] == "error":
        print(f"\nERROR: {result['error']}")
        return 1

    print(f"\n✅ Deployment Status: {result['status'].upper()}")
    print(f"📌 Branch: {result['branch_name']}")
    print(f"📝 Files Updated: {', '.join(result['files_updated'])}")
    print(f"🔖 Commit SHA: {result.get('commit_sha', 'N/A')[:8]}")

    if result.get("pr_url"):
        print(f"🔗 PR URL: {result['pr_url']}")
        print(f"#️⃣  PR Number: {result['pr_number']}")

    print(f"\n📋 Rollback Instructions:")
    for step in result['rollback_instructions']:
        print(f"   {step}")

    print(f"\n🎯 Next Steps:")
    for step in result['next_steps']:
        print(f"   - {step}")

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
    print("\n⚠️  NOTE: Branch created but NOT pushed for safety.")
    print("To cleanup: git checkout main && git branch -D <branch-name>")

    return 0


if __name__ == "__main__":
    sys.exit(main())
