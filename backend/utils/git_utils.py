"""Utility functions for Git operations including repository cloning."""

import os
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from utils.logger import setup_logger


logger = setup_logger(__name__)


def is_valid_git_repo_url(url: str) -> bool:
    """Check if the provided URL is a valid Git repository URL.
    
    Args:
        url: Git repository URL to validate
        
    Returns:
        True if valid Git URL, False otherwise
    """
    try:
        parsed = urlparse(url)
        # Check if it's a valid Git URL (supports https, ssh, and git protocols)
        return (
            parsed.scheme in ['http', 'https', 'git', 'ssh'] or
            # For SSH URLs like git@github.com:user/repo.git
            url.startswith('git@') or
            # Local paths
            Path(url).exists()
        )
    except Exception:
        return False


def clone_repository(
    repo_url: str,
    local_path: str,
    branch: str = None,
    github_token: Optional[str] = None,
    force_fresh_clone: bool = False
) -> bool:
    """Clone a Git repository to a local path.

    Args:
        repo_url: URL of the Git repository to clone
        local_path: Local path where repository should be cloned
        branch: Optional branch name to checkout
        github_token: Optional GitHub personal access token for private repos
        force_fresh_clone: If True, remove existing directory before cloning

    Returns:
        True if cloning was successful, False otherwise
    """
    try:
        repo_path = Path(local_path)

        # Handle existing directory
        if repo_path.exists():
            if force_fresh_clone:
                logger.info("removing_existing_directory", path=str(repo_path))
                shutil.rmtree(repo_path)
            else:
                # Check if it's already a git repo
                git_dir = repo_path / ".git"
                if git_dir.exists():
                    logger.info("directory_exists_is_git_repo", path=str(repo_path))
                    # Pull latest changes instead of cloning
                    try:
                        result = subprocess.run(
                            ["git", "pull"],
                            cwd=repo_path,
                            capture_output=True,
                            text=True,
                            timeout=60
                        )
                        if result.returncode != 0:
                            logger.warning("git_pull_failed",
                                         cwd=str(repo_path),
                                         stderr=result.stderr)
                        else:
                            logger.info("git_pull_success", cwd=str(repo_path))
                            return True
                    except subprocess.TimeoutExpired:
                        logger.warning("git_pull_timeout", cwd=str(repo_path))
                        return False
                else:
                    logger.error("path_exists_not_git_repo", path=str(repo_path))
                    return False

        # Prepare the clone command
        clone_cmd = ["git", "clone"]

        # Add branch if specified
        if branch:
            clone_cmd.extend(["--branch", branch])

        # For private repositories, use token if provided
        if github_token and ("github.com" in repo_url or "gitlab.com" in repo_url):
            # Insert token into HTTPS URL
            if repo_url.startswith("https://"):
                # For GitHub
                if "github.com" in repo_url:
                    parsed = urlparse(repo_url)
                    repo_url = f"https://oauth2:{github_token}@{parsed.netloc}{parsed.path}"
                # For GitLab
                elif "gitlab.com" in repo_url:
                    parsed = urlparse(repo_url)
                    repo_url = f"https://gitlab-ci-token:{github_token}@{parsed.netloc}{parsed.path}"
            # For SSH URLs, token won't work directly, but we'll log this
            elif repo_url.startswith("git@"):
                logger.info("ssh_authentication_note",
                           message="Using SSH key for authentication; ensure SSH key is configured")
        elif github_token and "bitbucket.org" in repo_url:
            # For Bitbucket
            parsed = urlparse(repo_url)
            repo_url = f"https://x-token-auth:{github_token}@{parsed.netloc}{parsed.path}"

        clone_cmd.extend([repo_url, str(repo_path)])

        logger.info("starting_git_clone",
                   command=" ".join(clone_cmd[:2] + ["***", str(repo_path)] if github_token else clone_cmd))

        # Execute the clone command
        result = subprocess.run(
            clone_cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout
        )

        if result.returncode != 0:
            logger.error("git_clone_failed",
                        stderr=result.stderr,
                        stdout=result.stdout,
                        repo_url=repo_url)
            # If we get a permission error, try alternative authentication methods
            if "Authentication failed" in result.stderr or "Permission denied" in result.stderr:
                logger.warning("auth_failed_trying_alternative", repo_url=repo_url)

                # For GitHub, try using credential helper with token
                if github_token and "github.com" in repo_url:
                    return _clone_with_github_token_auth(repo_url, repo_path, branch, github_token)

            return False

        # Double-check that files were actually cloned (not just .git folder)
        files_after_clone = list(repo_path.iterdir())
        if len(files_after_clone) == 1 and files_after_clone[0].name == '.git':
            logger.error("git_clone_incomplete_only_git_folder",
                        repo_url=repo_url,
                        local_path=str(repo_path))
            return False

        logger.info("git_clone_success",
                   repo_url=repo_url,
                   local_path=str(repo_path),
                   files_count=len(files_after_clone))

        # If a specific branch was requested and different from default, checkout that branch
        if branch:
            # First, fetch all branches to make sure the requested branch exists
            fetch_result = subprocess.run(
                ["git", "fetch", "origin"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )

            if fetch_result.returncode == 0:
                # Check if the branch exists locally or remotely
                branch_check = subprocess.run(
                    ["git", "show-ref", "--verify", f"refs/heads/{branch}"],
                    cwd=repo_path,
                    capture_output=True,
                    text=True
                )

                # If branch doesn't exist locally, check if it exists on remote
                if branch_check.returncode != 0:
                    remote_branch_check = subprocess.run(
                        ["git", "ls-remote", "--heads", "origin", branch],
                        cwd=repo_path,
                        capture_output=True,
                        text=True
                    )

                    if remote_branch_check.returncode == 0 and remote_branch_check.stdout.strip():
                        # Branch exists on remote, so we can checkout and track it
                        checkout_result = subprocess.run(
                            ["git", "checkout", "-b", branch, f"origin/{branch}"],
                            cwd=repo_path,
                            capture_output=True,
                            text=True,
                            timeout=30
                        )

                        if checkout_result.returncode != 0:
                            logger.warning("branch_checkout_failed",
                                         branch=branch,
                                         cwd=str(repo_path),
                                         stderr=checkout_result.stderr)
                            # Continue anyway as the clone was successful
                    else:
                        # Branch doesn't exist, just continue with whatever is checked out
                        logger.warning("branch_does_not_exist",
                                     branch=branch,
                                     repo_url=repo_url)
                        return True
                else:
                    # Branch exists locally, just checkout
                    checkout_result = subprocess.run(
                        ["git", "checkout", branch],
                        cwd=repo_path,
                        capture_output=True,
                        text=True,
                        timeout=30
                    )

                    if checkout_result.returncode != 0:
                        logger.warning("branch_checkout_failed",
                                     branch=branch,
                                     cwd=str(repo_path),
                                     stderr=checkout_result.stderr)
                        # Continue anyway as the clone was successful
            else:
                logger.warning("fetch_failed_for_branch",
                              branch=branch,
                              cwd=str(repo_path),
                              stderr=fetch_result.stderr)

        # Verify files exist after branch operations
        files_after_checkout = list(repo_path.iterdir())
        if len(files_after_checkout) == 1 and files_after_checkout[0].name == '.git':
            logger.error("git_checkout_resulted_in_only_git_folder",
                        repo_url=repo_url,
                        local_path=str(repo_path),
                        requested_branch=branch)
            return False

        return True

    except subprocess.TimeoutExpired:
        logger.error("git_operation_timeout", repo_url=repo_url)
        return False
    except Exception as e:
        logger.error("git_clone_error",
                    repo_url=repo_url,
                    error=str(e))
        return False


def _clone_with_github_token_auth(repo_url: str, repo_path: Path, branch: str = None, github_token: str = None) -> bool:
    """Clone using GitHub token with credential helper as an alternative authentication method.

    Args:
        repo_url: GitHub repository URL
        repo_path: Local path to clone to
        branch: Optional branch to checkout
        github_token: GitHub personal access token

    Returns:
        True if cloning was successful, False otherwise
    """
    try:
        # Set up temporary credential helper to use the token
        env = os.environ.copy()
        env['GIT_ASKPASS'] = ''  # Disable interactive prompts
        env['GIT_TERMINAL_PROMPT'] = '0'  # Disable terminal prompts

        # Create a temporary credential script to provide the token
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sh', prefix='git_creds_') as cred_script:
            # Create a temporary credentials file that git can use
            parsed = urlparse(repo_url)
            cred_script.write(f"#!/bin/sh\necho username=oauth2\necho password={github_token}\n")
            cred_script.flush()
            os.chmod(cred_script.name, 0o755)  # Make executable

            try:
                # Clone with custom credential helper
                clone_cmd = ["git", "-c", f"credential.helper={cred_script.name}"] + ["clone"]

                if branch:
                    clone_cmd.extend(["--branch", branch])

                clone_cmd.extend([repo_url, str(repo_path)])

                result = subprocess.run(
                    clone_cmd,
                    capture_output=True,
                    text=True,
                    timeout=300,
                    env=env
                )

                if result.returncode != 0:
                    logger.error("git_clone_with_token_auth_failed",
                                stderr=result.stderr,
                                stdout=result.stdout,
                                repo_url=repo_url)
                    return False

                logger.info("git_clone_with_token_auth_success",
                           repo_url=repo_url,
                           local_path=str(repo_path))

                return True
            finally:
                # Clean up the temporary script
                os.unlink(cred_script.name)

    except subprocess.TimeoutExpired:
        logger.error("git_clone_with_token_auth_timeout", repo_url=repo_url)
        return False
    except Exception as e:
        logger.error("git_clone_with_token_auth_error",
                    repo_url=repo_url,
                    error=str(e))
        return False


def handle_git_permission_errors(repo_url: str, github_token: Optional[str] = None) -> str:
    """Provide guidance on resolving Git permission errors for private repositories.

    Args:
        repo_url: Repository URL
        github_token: GitHub token if available

    Returns:
        Formatted string with resolution steps
    """
    guidance = []

    if repo_url.startswith("https://github.com/") or repo_url.startswith("git@github.com:"):
        guidance.append("GitHub Private Repository Access Issues:")
        guidance.append("1. Verify your GitHub Personal Access Token has the correct permissions")
        guidance.append("   - Required scopes: 'repo' for private repositories")
        guidance.append("   - For organization repos: ensure SSO is authorized")
        guidance.append("")

        if github_token:
            guidance.append("2. Token is provided - verify it's valid and has correct permissions:")
            guidance.append("   - Check that it hasn't expired")
            guidance.append("   - Ensure it has 'repo' scope for private repositories")
        else:
            guidance.append("2. No GitHub token provided - you'll need to supply a Personal Access Token")
            guidance.append("   - Create one at: https://github.com/settings/tokens")
            guidance.append("   - Use 'repo' scope for private repository access")

        guidance.append("")
        guidance.append("3. Alternative authentication methods:")
        guidance.append("   - SSH keys: Ensure your SSH key is added to GitHub")
        guidance.append("   - For SSH URLs like 'git@github.com:user/repo.git'")
        guidance.append("")
        guidance.append("4. Check repository visibility settings:")
        guidance.append("   - Confirm you have read access to the repository")
        guidance.append("   - For organization repos, ensure you're a member with appropriate permissions")

    elif repo_url.startswith("https://gitlab.com/") or repo_url.startswith("git@gitlab.com:"):
        guidance.append("GitLab Private Repository Access Issues:")
        guidance.append("1. Verify your GitLab Personal Access Token has the correct permissions")
        guidance.append("   - Required scope: 'read_repository' for cloning")
        guidance.append("")

        if github_token:
            guidance.append("2. Token is provided - verify it's valid and has correct permissions:")
            guidance.append("   - Check that it hasn't expired")
            guidance.append("   - Ensure it has 'read_repository' scope")
        else:
            guidance.append("2. No GitLab token provided - you'll need to supply a Personal Access Token")
            guidance.append("   - Create one at: https://gitlab.com/-/profile/personal_access_tokens")
            guidance.append("   - Use 'read_repository' scope for private repository access")

    elif repo_url.startswith("https://bitbucket.org/") or repo_url.startswith("git@bitbucket.org:"):
        guidance.append("Bitbucket Private Repository Access Issues:")
        guidance.append("1. Verify your Bitbucket App Password or Personal Access Token")
        guidance.append("   - For App Passwords: ensure it has 'Repository' read permissions")
        guidance.append("   - For Personal Access Tokens: ensure it has 'repository' read scope")
        guidance.append("")

        if github_token:
            guidance.append("2. Token is provided - verify it's valid and has correct permissions:")
            guidance.append("   - For App Passwords: ensure it's correctly configured for repository read access")
            guidance.append("   - Check that it hasn't been revoked")
        else:
            guidance.append("2. No token provided - you'll need to supply either an App Password or Personal Access Token")
            guidance.append("   - App Passwords: https://support.atlassian.com/bitbucket-cloud/docs/app-passwords/")
            guidance.append("   - Personal Access Tokens: https://bitbucket.org/account/settings/app-passwords/")

    else:
        guidance.append("Private Repository Access Issues:")
        guidance.append("1. Verify your authentication credentials are correct and have appropriate permissions")
        guidance.append("2. Check that the repository URL is correct")
        guidance.append("3. Confirm you have read access to the repository")
        guidance.append("4. For SSH URLs, ensure your SSH key is properly configured")

    return "\n".join(guidance)


def get_repo_name_from_url(repo_url: str) -> str:
    """Extract repository name from Git URL.
    
    Args:
        repo_url: Git repository URL
        
    Returns:
        Repository name (e.g., "my-repo" from "https://github.com/user/my-repo.git")
    """
    try:
        parsed = urlparse(repo_url)
        if parsed.path:
            # Extract the last part after splitting by '/'
            repo_name = parsed.path.split('/')[-1]
            # Remove .git suffix if present
            if repo_name.endswith('.git'):
                repo_name = repo_name[:-4]
            return repo_name
    except Exception:
        # Handle SSH URLs like git@github.com:user/repo.git
        if repo_url.startswith('git@'):
            parts = repo_url.split(':')[-1].split('/')
            repo_name = parts[-1]
            if repo_name.endswith('.git'):
                repo_name = repo_name[:-4]
            return repo_name
    
    return "unknown_repo"


def clone_to_temp_directory(
    repo_url: str,
    branch: str = None,
    github_token: Optional[str] = None
) -> Optional[str]:
    """Clone repository to a temporary directory.
    
    Args:
        repo_url: URL of the Git repository to clone
        branch: Optional branch name to checkout
        github_token: Optional GitHub personal access token for private repos
        
    Returns:
        Path to temporary directory if successful, None otherwise
    """
    try:
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp(prefix="migration_repo_")
        logger.info("created_temp_directory", path=temp_dir)
        
        # Clone the repository
        success = clone_repository(
            repo_url=repo_url,
            local_path=temp_dir,
            branch=branch,
            github_token=github_token,
            force_fresh_clone=False
        )
        
        if success:
            return temp_dir
        else:
            # Clean up on failure
            shutil.rmtree(temp_dir, ignore_errors=True)
            return None
            
    except Exception as e:
        logger.error("temp_clone_error", error=str(e))
        return None