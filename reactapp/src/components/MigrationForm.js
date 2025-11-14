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

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
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
                <label htmlFor="githubToken">GitHub Token (optional for public repo)</label>
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
    </div>
  );
};

export default MigrationForm;