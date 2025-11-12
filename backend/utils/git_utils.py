"""Git utilities for cloning and managing repositories.

Provides functions to clone Git repositories with authentication support.
"""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Tuple
from utils.logger import setup_logger

logger = setup_logger(__name__)


class GitCloner:
    """Clone and manage Git repositories."""

    def __init__(self, workspace_dir: Optional[str] = None):
        """Initialize Git cloner.

        Args:
            workspace_dir: Directory to clone repositories into (default: temp directory)
        """
        if workspace_dir:
            self.workspace_dir = Path(workspace_dir)
            self.workspace_dir.mkdir(parents=True, exist_ok=True)
        else:
            self.workspace_dir = Path(tempfile.gettempdir()) / "ai-code-modernizer"
            self.workspace_dir.mkdir(parents=True, exist_ok=True)

        logger.info("git_cloner_initialized", workspace_dir=str(self.workspace_dir))

    def clone_repository(
        self,
        repo_url: str,
        branch: str = "main",
        github_token: Optional[str] = None,
        force_fresh_clone: bool = False
    ) -> Tuple[bool, str, str]:
        """Clone a Git repository with intelligent branch handling.

        Behavior:
        - If repository doesn't exist: Clones the specified branch
        - If repository exists and force_fresh_clone=False:
          * If already on correct branch: Pulls latest changes
          * If on different branch: Fetches and checks out the requested branch
          * If branch doesn't exist in cached repo: Automatically does a fresh clone
        - If force_fresh_clone=True: Deletes existing and clones fresh

        This ensures you always get the correct branch with the latest code,
        while utilizing caching when possible for better performance.

        Args:
            repo_url: Git repository URL (https or git protocol)
            branch: Branch to clone/checkout (default: main)
            github_token: GitHub personal access token for private repos
            force_fresh_clone: If True, delete existing clone and re-clone (default: False)

        Returns:
            Tuple of (success, local_path, error_message)
        """
        try:
            # Extract repository name from URL
            repo_name = self._extract_repo_name(repo_url)
            target_path = self.workspace_dir / repo_name

            logger.info("cloning_repository",
                       repo_url=repo_url,
                       branch=branch,
                       target_path=str(target_path),
                       force_fresh=force_fresh_clone)

            # Check if already cloned
            if target_path.exists() and not force_fresh_clone:
                logger.info("using_cached_clone",
                           path=str(target_path),
                           repo_url=repo_url,
                           branch=branch)

                # Ensure we're on the correct branch
                checkout_success, error = self._checkout_branch(target_path, branch)
                if not checkout_success:
                    logger.warning("branch_checkout_failed_fallback_to_fresh_clone",
                                 path=str(target_path),
                                 branch=branch,
                                 error=error)
                    # Fallback: do a fresh clone by setting force_fresh_clone=True
                    # This handles the case where the cached repo doesn't have the requested branch
                    return self.clone_repository(repo_url, branch, github_token, force_fresh_clone=True)
                else:
                    return True, str(target_path), ""

            # Remove existing directory if present and force_fresh_clone is True
            if target_path.exists() and force_fresh_clone:
                logger.info("removing_existing_clone_for_fresh_copy", path=str(target_path))
                import shutil
                import stat

                # Handle Windows permission issues
                def handle_remove_readonly(func, path, exc_info):
                    """Error handler for Windows readonly files"""
                    if not os.access(path, os.W_OK):
                        os.chmod(path, stat.S_IWUSR)
                        func(path)
                    else:
                        raise

                shutil.rmtree(target_path, onerror=handle_remove_readonly)

            # Prepare clone URL with authentication if token provided
            clone_url = self._prepare_clone_url(repo_url, github_token)

            # Clone repository
            cmd = ["git", "clone", "--branch", branch, "--depth", "1", clone_url, str(target_path)]

            # Run git clone
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )

            if result.returncode != 0:
                error_msg = result.stderr or "Unknown git clone error"
                logger.error("git_clone_failed",
                           repo_url=repo_url,
                           error=error_msg)
                return False, "", error_msg

            logger.info("repository_cloned_successfully",
                       repo_url=repo_url,
                       path=str(target_path))

            return True, str(target_path), ""

        except subprocess.TimeoutExpired:
            error_msg = "Git clone timeout (exceeded 5 minutes)"
            logger.error("git_clone_timeout", repo_url=repo_url)
            return False, "", error_msg

        except Exception as e:
            error_msg = f"Git clone error: {str(e)}"
            logger.error("git_clone_exception",
                        repo_url=repo_url,
                        error=str(e),
                        exc_info=True)
            return False, "", error_msg

    def _checkout_branch(self, repo_path: Path, branch: str) -> Tuple[bool, str]:
        """Checkout a specific branch in an existing repository.

        Args:
            repo_path: Path to the repository
            branch: Branch name to checkout

        Returns:
            Tuple of (success, error_message)
        """
        try:
            # First, check current branch
            current_branch_result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=str(repo_path),
                capture_output=True,
                text=True,
                timeout=10
            )

            current_branch = current_branch_result.stdout.strip()

            # If already on the correct branch, just pull latest
            if current_branch == branch:
                logger.info("already_on_correct_branch",
                           path=str(repo_path),
                           branch=branch)

                # Pull latest changes
                pull_result = subprocess.run(
                    ["git", "pull", "origin", branch],
                    cwd=str(repo_path),
                    capture_output=True,
                    text=True,
                    timeout=60
                )

                if pull_result.returncode != 0:
                    # Pull might fail for shallow clones, try fetch + reset instead
                    fetch_result = subprocess.run(
                        ["git", "fetch", "origin", branch],
                        cwd=str(repo_path),
                        capture_output=True,
                        text=True,
                        timeout=60
                    )

                    if fetch_result.returncode == 0:
                        reset_result = subprocess.run(
                            ["git", "reset", "--hard", f"origin/{branch}"],
                            cwd=str(repo_path),
                            capture_output=True,
                            text=True,
                            timeout=30
                        )

                        if reset_result.returncode != 0:
                            logger.warning("git_reset_failed_but_continuing",
                                         path=str(repo_path),
                                         branch=branch)

                logger.info("branch_up_to_date",
                           path=str(repo_path),
                           branch=branch)
                return True, ""

            # Different branch needed - fetch and checkout
            fetch_result = subprocess.run(
                ["git", "fetch", "origin", branch],
                cwd=str(repo_path),
                capture_output=True,
                text=True,
                timeout=60
            )

            if fetch_result.returncode != 0:
                error_msg = f"Git fetch failed: {fetch_result.stderr}"
                logger.error("git_fetch_failed",
                           path=str(repo_path),
                           branch=branch,
                           error=error_msg)
                return False, error_msg

            # Checkout the branch
            checkout_result = subprocess.run(
                ["git", "checkout", "-B", branch, f"origin/{branch}"],
                cwd=str(repo_path),
                capture_output=True,
                text=True,
                timeout=30
            )

            if checkout_result.returncode != 0:
                error_msg = f"Git checkout failed: {checkout_result.stderr}"
                logger.error("git_checkout_failed",
                           path=str(repo_path),
                           branch=branch,
                           error=error_msg)
                return False, error_msg

            logger.info("branch_checkout_successful",
                       path=str(repo_path),
                       branch=branch)
            return True, ""

        except subprocess.TimeoutExpired:
            error_msg = "Git operation timeout"
            logger.error("git_operation_timeout",
                       path=str(repo_path),
                       branch=branch)
            return False, error_msg
        except Exception as e:
            error_msg = f"Git checkout error: {str(e)}"
            logger.error("git_checkout_exception",
                       path=str(repo_path),
                       branch=branch,
                       error=str(e))
            return False, error_msg

    def _extract_repo_name(self, repo_url: str) -> str:
        """Extract repository name from URL.

        Args:
            repo_url: Git repository URL

        Returns:
            Repository name
        """
        # Remove .git suffix if present
        url = repo_url.rstrip('/')
        if url.endswith('.git'):
            url = url[:-4]

        # Extract last part of URL
        parts = url.split('/')
        return parts[-1]

    def _prepare_clone_url(self, repo_url: str, github_token: Optional[str]) -> str:
        """Prepare clone URL with authentication if needed.

        Args:
            repo_url: Original repository URL
            github_token: GitHub personal access token

        Returns:
            Clone URL with authentication
        """
        if not github_token:
            return repo_url

        # Convert to HTTPS URL with token
        if repo_url.startswith('https://github.com/'):
            # Format: https://token@github.com/user/repo.git
            url_without_protocol = repo_url.replace('https://', '')
            return f"https://{github_token}@{url_without_protocol}"
        elif repo_url.startswith('git@github.com:'):
            # Convert SSH to HTTPS with token
            # git@github.com:user/repo.git -> https://token@github.com/user/repo.git
            path = repo_url.replace('git@github.com:', '')
            return f"https://{github_token}@github.com/{path}"
        else:
            # Return as-is for other Git providers
            return repo_url

    def cleanup(self, repo_path: str) -> bool:
        """Clean up cloned repository.

        Args:
            repo_path: Path to cloned repository

        Returns:
            True if cleanup successful
        """
        try:
            path = Path(repo_path)
            if path.exists() and path.is_dir():
                import shutil
                shutil.rmtree(path)
                logger.info("repository_cleaned_up", path=str(path))
                return True
            return False
        except Exception as e:
            logger.error("cleanup_failed", path=repo_path, error=str(e))
            return False


if __name__ == "__main__":
    """Standalone test of Git cloner."""
    print("=" * 80)
    print("GIT CLONER TEST")
    print("=" * 80)

    # Test with a public repository
    cloner = GitCloner()

    test_repo = "https://github.com/expressjs/express.git"
    test_branch = "master"

    print(f"\n[INFO] Testing with public repository: {test_repo}")
    print(f"[INFO] Branch: {test_branch}")
    print("[INFO] Cloning...")

    success, path, error = cloner.clone_repository(test_repo, test_branch)

    if success:
        print(f"\n[SUCCESS] Repository cloned to: {path}")
        print(f"[INFO] Directory contents:")

        # List files
        repo_path = Path(path)
        if repo_path.exists():
            files = list(repo_path.iterdir())[:10]  # First 10 files
            for file in files:
                print(f"  - {file.name}")

        # Cleanup
        print(f"\n[INFO] Cleaning up...")
        if cloner.cleanup(path):
            print("[SUCCESS] Cleanup complete")
    else:
        print(f"\n[ERROR] Clone failed: {error}")

    print("\n" + "=" * 80)
