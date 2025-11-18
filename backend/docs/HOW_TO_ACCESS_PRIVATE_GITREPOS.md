✦ Private GitHub Repository Access - Prerequisites Documentation

  This document provides comprehensive instructions for setting up access to private GitHub repositories when using
  the AI Code Modernizer application.

  Table of Contents
   1. GitHub Personal Access Token (PAT) Creation (#github-personal-access-token-pat-creation)
   2. Required Token Permissions (#required-token-permissions)
   3. Organization SSO Authorization (#organization-sso-authorization)
   4. API Usage (#api-usage)
   5. Troubleshooting (#troubleshooting)

  GitHub Personal Access Token (PAT) Creation

  For Private Repository Access

  GitHub Personal Access Tokens (PATs) are required for authenticating with private repositories through the API and
  Git operations.

  Step-by-Step Creation:

   1. Navigate to GitHub Settings
      - Log in to your GitHub account
      - Click on your profile picture in the top-right corner
      - Select "Settings" from the dropdown menu

   2. Access Developer Settings
      - In the left sidebar, scroll down and click on "Developer settings"
      - Under "Personal access tokens", click on "Tokens (classic)" or "Fine-grained tokens" depending on your
        preference

   3. Generate New Token
      - Click on the "Generate new token" button (for classic) or "Generate new token (classic)"
      - Or click "Fine-grained tokens" → "Generate new token" for fine-grained approach

   4. Configure Token Details
      - Note/Description: Enter a descriptive name for the token (e.g., "AI Code Modernizer Access")
      - Expiration: Choose an appropriate expiration period (we recommend "No expiration" or a long period for
        development)
      - Note: Remember to save your token as it will only be shown once

  Required Token Permissions

  For Classic Personal Access Tokens (Recommended)

  Essential Scopes for Private Repositories:

   1. `repo` (Full control of private repositories) - REQUIRED
      - Grants full access to private repositories
      - Includes: repo:status, repo_deployment, public_repo, repo:invite, security_events
      - This is the key permission needed for private repository access

   2. `read:org` (Read organization membership) - Recommended if repository is in an organization
      - Required for repositories in organizations that require member visibility
      - Allows reading organization and team membership

   3. `read:user` (Read user profile data) - Optional but recommended
      - Allows reading user profile data
      - Useful for verification purposes

   4. `user:email` (Access user email addresses) - Optional but recommended
      - Allows access to user email addresses
      - Required for some Git operations

  How to Select Scopes (Step-by-step):

   1. On the token creation page, scroll down to the "Select scopes" section
   2. Check the following boxes:
      - [x] `repo` - Full control of private repositories
      - [x] `read:org` - Read organization membership (if applicable)
      - [x] `read:user` - Read user profile data (if applicable)
      - [x] `user:email` - Access user email addresses (if applicable)

   3. Click "Generate token"

   4. CRITICAL: Copy the generated token immediately, as it will not be shown again

  For Fine-grained Personal Access Tokens

  If you prefer fine-grained tokens (newer approach):

   1. Choose "Fine-grained tokens" when creating a new token
   2. Select the specific repository you want to access
   3. Grant these permissions:
      - Contents: Read access
      - Metadata: Read access
   4. Generate the token and copy it immediately

  Organization SSO Authorization

  If your repository is part of an organization that requires SSO (Single Sign-On):

  Authorization Steps:

   1. Complete Token Creation
      - First, create your PAT as described above
      - If the token is created successfully, continue to SSO authorization

   2. Enable SSO for the Token
      - Go back to your Personal Access Tokens page
      - Find the token you just created
      - Look for any organization names listed under the token that show "SSO: Required"
      - Click the "Enable SSO" button next to the organization name

   3. Follow SSO Flow
      - You'll be redirected to your organization's SSO provider (Azure AD, Okta, etc.)
      - Complete the authentication process
      - Authorize the personal access token for use with the organization
      - 

   4. Verify Authorization
      - Return to the GitHub token page
      - The status should now show "SSO: Authorized" instead of "SSO: Required"

  API Usage

  Using Your Token with the API

  When making API requests that access private repositories, include your token in the request:

   1 {
   2   "git_repo_url": "https://github.com/your-username/your-private-repo.git",
   3   "project_type": "nodejs",
   4   "git_branch": "main",
   5   "github_token": "your_personal_access_token_here",
   6   "max_retries": 3
   7 }

  Environment Variable (Alternative Method)

  You can also set the token in your .env file:

   1 GITHUB_TOKEN=your_personal_access_token_here

  Note: When both a token in the API request payload and in the .env file are provided, the payload token takes
  precedence.

  Troubleshooting

  Common Issues and Solutions:

  1. "Repository not found" Error
   - Cause: Token doesn't have required permissions or repository doesn't exist
   - Solution:
     - Verify the repository URL is correct
     - Ensure your PAT has the repo scope
     - Confirm you have access to the repository

  2. 401 Unauthorized Error
   - Cause: Invalid token or token has expired
   - Solution:
     - Verify the token is copied correctly (no extra spaces)
     - Check token expiration date
     - Generate a new token if needed

  3. 403 Forbidden Error
   - Cause: Token exists but lacks required permissions
   - Solution:
     - Regenerate token with proper scopes (repo scope is required)
     - If in organization, ensure SSO is authorized

  4. "Token lacks sufficient permissions"
   - Cause: Token doesn't have access to the specific repository
   - Solution:
     - Confirm you have read access to the repository
     - For organization repos, ensure you're a member with appropriate permissions
     - Regenerate token with proper scopes

  Verification Steps:

   1. Test Repository Access
      - Try to access the repository in a browser while logged in to verify access
      - Confirm you can see the repository contents

   2. Test Token
      - Use GitHub CLI to test: gh auth login with your token
      - Or test via API call: curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/user

   3. Check Token Permissions
      - Visit https://github.com/settings/tokens to review your tokens
      - Verify scopes and expiration dates

  Token Security Best Practices:

   - Never commit tokens to repositories
   - Don't share tokens in plain text
   - Use environment variables or secure vaults
   - Review token access regularly
   - Revoke unused tokens
   - Use the principle of least privilege (only grant required permissions)

  Additional Notes

   - Personal Access Tokens work with both HTTPS and Git operations
   - Tokens with proper scopes can be used for cloning, pulling, and accessing repository contents
   - For public repositories, tokens are not required but are safe to include
   - Always handle tokens securely and treat them like passwords
   - Consider using GitHub Apps instead of PATs for production applications with extensive permissions

  ---

  Important: Keep your Personal Access Token secure and never share it publicly. If you suspect a token has been
  compromised, regenerate it immediately.