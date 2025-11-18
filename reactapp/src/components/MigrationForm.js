import React, { useState } from 'react';
import './MigrationForm.css';

const MigrationForm = ({ onStartMigration }) => {
  const [formData, setFormData] = useState({
    sourceType: 'local', // 'local' or 'git'
    projectPath: 'target_repos/simple_express_app',
    gitRepoUrl: 'https://github.com/mallik-code/simple_express_app',
    projectType: 'nodejs',
    maxRetries: 3,
    gitBranch: 'main',
    githubToken: '',
    forceFreshClone: true
  });

  const [showHelpModal, setShowHelpModal] = useState(false);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const openGithubTokenHelp = () => {
    setShowHelpModal(true);
  };

  const closeGithubTokenHelp = () => {
    setShowHelpModal(false);
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    // Prepare the payload based on source type
    const payload = {
      project_type: formData.projectType,
      max_retries: formData.maxRetries,
      git_branch: formData.gitBranch,
      ...(formData.sourceType === 'local' && { project_path: formData.projectPath }),
      ...(formData.sourceType === 'git' && { git_repo_url: formData.gitRepoUrl }),
      ...(formData.sourceType === 'git' && formData.githubToken && { github_token: formData.githubToken }),
      ...(formData.sourceType === 'git' && { force_fresh_clone: formData.forceFreshClone })
    };

    onStartMigration(payload);
  };

  // GitHub token help content as an array for better rendering
  const githubTokenHelpContent = [
    {
      title: "Private GitHub Repository Access - Prerequisites Documentation",
      content: "This document provides comprehensive instructions for setting up access to private GitHub repositories when using the AI Code Modernizer application.",
      type: "header"
    },
    {
      title: "Table of Contents",
      content: [
        "1. GitHub Personal Access Token (PAT) Creation",
        "2. Required Token Permissions",
        "3. Organization SSO Authorization",
        "4. API Usage",
        "5. Troubleshooting"
      ],
      type: "toc"
    },
    {
      title: "GitHub Personal Access Token (PAT) Creation",
      content: "For Private Repository Access\n\nGitHub Personal Access Tokens (PATs) are required for authenticating with private repositories through the API and Git operations.",
      type: "section"
    },
    {
      title: "Step-by-Step Creation:",
      content: [
        "1. Navigate to GitHub Settings",
        "   - Log in to your GitHub account",
        "   - Click on your profile picture in the top-right corner",
        "   - Select \"Settings\" from the dropdown menu",
        "",
        "2. Access Developer Settings",
        "   - In the left sidebar, scroll down and click on \"Developer settings\"",
        "   - Under \"Personal access tokens\", click on \"Tokens (classic)\" or \"Fine-grained tokens\" depending on your preference",
        "",
        "3. Generate New Token",
        "   - Click on the \"Generate new token\" button (for classic) or \"Generate new token (classic)\"",
        "   - Or click \"Fine-grained tokens\" → \"Generate new token\" for fine-grained approach",
        "",
        "4. Configure Token Details",
        "   - Note/Description: Enter a descriptive name for the token (e.g., \"AI Code Modernizer Access\")",
        "   - Expiration: Choose an appropriate expiration period (we recommend \"No expiration\" or a long period for development)",
        "   - Note: Remember to save your token as it will only be shown once"
      ],
      type: "steps"
    },
    {
      title: "Required Token Permissions",
      content: "For Classic Personal Access Tokens (Recommended)\n\nEssential Scopes for Private Repositories:",
      type: "section"
    },
    {
      content: [
        "1. `repo` (Full control of private repositories) - REQUIRED",
        "   - Grants full access to private repositories",
        "   - Includes: repo:status, repo_deployment, public_repo, repo:invite, security_events",
        "   - This is the key permission needed for private repository access",
        "",
        "2. `read:org` (Read organization membership) - Recommended if repository is in an organization",
        "   - Required for repositories in organizations that require member visibility",
        "   - Allows reading organization and team membership",
        "",
        "3. `read:user` (Read user profile data) - Optional but recommended",
        "   - Allows reading user profile data",
        "   - Useful for verification purposes",
        "",
        "4. `user:email` (Access user email addresses) - Optional but recommended",
        "   - Allows access to user email addresses",
        "   - Required for some Git operations"
      ],
      type: "steps"
    },
    {
      title: "How to Select Scopes (Step-by-step):",
      content: [
        "1. On the token creation page, scroll down to the \"Select scopes\" section",
        "2. Check the following boxes:",
        "   - [x] `repo` - Full control of private repositories",
        "   - [x] `read:org` - Read organization membership (if applicable)",
        "   - [x] `read:user` - Read user profile data (if applicable)",
        "   - [x] `user:email` - Access user email addresses (if applicable)",
        "3. Click \"Generate token\"",
        "4. CRITICAL: Copy the generated token immediately, as it will not be shown again"
      ],
      type: "steps"
    },
    {
      title: "For Fine-grained Personal Access Tokens",
      content: "If you prefer fine-grained tokens (newer approach):\n\n1. Choose \"Fine-grained tokens\" when creating a new token\n2. Select the specific repository you want to access\n3. Grant these permissions:\n   - Contents: Read access\n   - Metadata: Read access\n4. Generate the token and copy it immediately",
      type: "section"
    },
    {
      title: "Organization SSO Authorization",
      content: "If your repository is part of an organization that requires SSO (Single Sign-On):",
      type: "section"
    },
    {
      title: "Authorization Steps:",
      content: [
        "1. Complete Token Creation",
        "   - First, create your PAT as described above",
        "   - If the token is created successfully, continue to SSO authorization",
        "",
        "2. Enable SSO for the Token",
        "   - Go back to your Personal Access Tokens page",
        "   - Find the token you just created",
        "   - Look for any organization names listed under the token that show \"SSO: Required\"",
        "   - Click the \"Enable SSO\" button next to the organization name",
        "",
        "3. Follow SSO Flow",
        "   - You'll be redirected to your organization's SSO provider (Azure AD, Okta, etc.)",
        "   - Complete the authentication process",
        "   - Authorize the personal access token for use with the organization",
        "",
        "4. Verify Authorization",
        "   - Return to the GitHub token page",
        "   - The status should now show \"SSO: Authorized\" instead of \"SSO: Required\""
      ],
      type: "steps"
    },
    {
      title: "API Usage",
      content: "Using Your Token with the API\n\nWhen making API requests that access private repositories, include your token in the request:",
      type: "section"
    },
    {
      content: [
        "{",
        "  \"git_repo_url\": \"https://github.com/your-username/your-private-repo.git\",",
        "  \"project_type\": \"nodejs\",",
        "  \"git_branch\": \"main\",",
        "  \"github_token\": \"your_personal_access_token_here\",",
        "  \"max_retries\": 3",
        "}"
      ],
      type: "code"
    },
    {
      title: "Environment Variable (Alternative Method)",
      content: "You can also set the token in your .env file:\n\nGITHUB_TOKEN=your_personal_access_token_here\n\nNote: When both a token in the API request payload and in the .env file are provided, the payload token takes precedence.",
      type: "section"
    },
    {
      title: "Troubleshooting",
      content: "Common Issues and Solutions:",
      type: "section"
    },
    {
      content: [
        "1. \"Repository not found\" Error",
        "   - Cause: Token doesn't have required permissions or repository doesn't exist",
        "   - Solution:",
        "     - Verify the repository URL is correct",
        "     - Ensure your PAT has the repo scope",
        "     - Confirm you have access to the repository",
        "",
        "2. 401 Unauthorized Error",
        "   - Cause: Invalid token or token has expired",
        "   - Solution:",
        "     - Verify the token is copied correctly (no extra spaces)",
        "     - Check token expiration date",
        "     - Generate a new token if needed",
        "",
        "3. 403 Forbidden Error",
        "   - Cause: Token exists but lacks required permissions",
        "   - Solution:",
        "     - Regenerate token with proper scopes (repo scope is required)",
        "     - If in organization, ensure SSO is authorized",
        "",
        "4. \"Token lacks sufficient permissions\"",
        "   - Cause: Token doesn't have access to the specific repository",
        "   - Solution:",
        "     - Confirm you have read access to the repository",
        "     - For organization repos, ensure you're a member with appropriate permissions",
        "     - Regenerate token with proper scopes"
      ],
      type: "steps"
    },
    {
      title: "Verification Steps:",
      content: [
        "1. Test Repository Access",
        "   - Try to access the repository in a browser while logged in to verify access",
        "   - Confirm you can see the repository contents",
        "",
        "2. Test Token",
        "   - Use GitHub CLI to test: gh auth login with your token",
        "   - Or test via API call: curl -H \"Authorization: token YOUR_TOKEN\" https://api.github.com/user",
        "",
        "3. Check Token Permissions",
        "   - Visit https://github.com/settings/tokens to review your tokens",
        "   - Verify scopes and expiration dates"
      ],
      type: "steps"
    },
    {
      title: "Token Security Best Practices:",
      content: [
        "- Never commit tokens to repositories",
        "- Don't share tokens in plain text",
        "- Use environment variables or secure vaults",
        "- Review token access regularly",
        "- Revoke unused tokens",
        "- Use the principle of least privilege (only grant required permissions)"
      ],
      type: "list"
    },
    {
      title: "Additional Notes",
      content: [
        "- Personal Access Tokens work with both HTTPS and Git operations",
        "- Tokens with proper scopes can be used for cloning, pulling, and accessing repository contents",
        "- For public repositories, tokens are not required but are safe to include",
        "- Always handle tokens securely and treat them like passwords",
        "- Consider using GitHub Apps instead of PATs for production applications with extensive permissions"
      ],
      type: "list"
    },
    {
      content: "Important: Keep your Personal Access Token secure and never share it publicly. If you suspect a token has been compromised, regenerate it immediately.",
      type: "important"
    }
  ];

  return (
    <div className="card">
      <h2 className="card-title">
        <i className="fas fa-cogs"></i>
        Start Migration
      </h2>
      <form onSubmit={handleSubmit}>
        <div className="form-grid">
          <div className="form-group">
            <label htmlFor="sourceType">Project Source Type</label>
            <select
              id="sourceType"
              name="sourceType"
              value={formData.sourceType}
              onChange={handleChange}
            >
              <option value="local">Local Project</option>
              <option value="git">Git Repository</option>
            </select>
          </div>

          {formData.sourceType === 'local' ? (
            <>
              <div className="form-group">
                <label htmlFor="projectPath">Local Project Path</label>
                <input
                  type="text"
                  id="projectPath"
                  name="projectPath"
                  value={formData.projectPath}
                  onChange={handleChange}
                  placeholder="Path to local project"
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="projectType">Project Type</label>
                <select
                  id="projectType"
                  name="projectType"
                  value={formData.projectType}
                  onChange={handleChange}
                  required
                >
                  <option value="nodejs">Node.js</option>
                  <option value="python">Python</option>
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="gitBranch">Git Branch</label>
                <input
                  type="text"
                  id="gitBranch"
                  name="gitBranch"
                  value={formData.gitBranch}
                  onChange={handleChange}
                  placeholder="main, master, etc."
                />
              </div>

              <div className="form-group">
                <label htmlFor="maxRetries">Max Retries</label>
                <input
                  type="number"
                  id="maxRetries"
                  name="maxRetries"
                  value={formData.maxRetries}
                  onChange={handleChange}
                  min="1"
                  max="10"
                />
              </div>
            </>
          ) : (
            <>
              <div className="form-group">
                <label htmlFor="gitRepoUrl">Git Repository URL</label>
                <input
                  type="text"
                  id="gitRepoUrl"
                  name="gitRepoUrl"
                  value={formData.gitRepoUrl}
                  onChange={handleChange}
                  placeholder="https://github.com/username/repo.git"
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="projectType">Project Type</label>
                <select
                  id="projectType"
                  name="projectType"
                  value={formData.projectType}
                  onChange={handleChange}
                  required
                >
                  <option value="nodejs">Node.js</option>
                  <option value="python">Python</option>
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="gitBranch">Git Branch</label>
                <input
                  type="text"
                  id="gitBranch"
                  name="gitBranch"
                  value={formData.gitBranch}
                  onChange={handleChange}
                  placeholder="main, master, etc."
                />
              </div>

              <div className="form-group">
                <label htmlFor="maxRetries">Max Retries</label>
                <input
                  type="number"
                  id="maxRetries"
                  name="maxRetries"
                  value={formData.maxRetries}
                  onChange={handleChange}
                  min="1"
                  max="10"
                />
              </div>

              <div className="form-group">
                <label htmlFor="githubToken">GitHub Token (Required for Private Repo) <i className="fas fa-question-circle help-icon" onClick={() => openGithubTokenHelp()}></i></label>
                <input
                  type="password"
                  id="githubToken"
                  name="githubToken"
                  value={formData.githubToken}
                  onChange={handleChange}
                  placeholder="Enter GitHub token for private repos"
                />
              </div>

              <div className="form-group">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    id="forceFreshClone"
                    name="forceFreshClone"
                    checked={formData.forceFreshClone}
                    onChange={handleChange}
                  />
                  Force Clone
                </label>
              </div>
            </>
          )}
        </div>

        <button type="submit" className="btn btn-primary">
          <i className="fas fa-play"></i> Start Migration
        </button>
      </form>

      {/* GitHub Token Help Modal */}
      {showHelpModal && (
        <div className="help-modal" onClick={closeGithubTokenHelp}>
          <div className="help-modal-content" onClick={e => e.stopPropagation()}>
            <div className="help-modal-header">
              <h3 className="help-modal-title">GitHub Token Help</h3>
              <button className="close-button" onClick={closeGithubTokenHelp}>
                &times;
              </button>
            </div>
            <div className="help-content">
              {githubTokenHelpContent.map((section, index) => (
                <div key={index} className={`help-section ${section.type}`}>
                  {section.title && <h3 className="help-section-title">{section.title}</h3>}
                  {section.type === 'toc' && Array.isArray(section.content) && (
                    <ul className="help-toc-list">
                      {section.content.map((item, i) => (
                        <li key={i}>{item}</li>
                      ))}
                    </ul>
                  )}
                  {section.type === 'steps' && Array.isArray(section.content) && (
                    <div className="help-steps">
                      {section.content.map((line, i) => (
                        <p key={i} className="help-step-line">{line}</p>
                      ))}
                    </div>
                  )}
                  {section.type === 'list' && Array.isArray(section.content) && (
                    <ul className="help-content-list">
                      {section.content.map((item, i) => (
                        <li key={i}>{item}</li>
                      ))}
                    </ul>
                  )}
                  {section.type === 'code' && Array.isArray(section.content) && (
                    <pre className="help-code-block">
                      {section.content.map((line, i) => (
                        <div key={i}>{line}</div>
                      ))}
                    </pre>
                  )}
                  {(section.type === 'section' || section.type === 'important') && typeof section.content === 'string' && (
                    <div className={`help-text ${section.type === 'important' ? 'help-important' : ''}`}>
                      {section.content.split('\n\n').map((paragraph, i) => (
                        <p key={i} className="help-paragraph">{paragraph}</p>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MigrationForm;