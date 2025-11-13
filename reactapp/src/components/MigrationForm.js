import React, { useState } from 'react';
import './MigrationForm.css';

const MigrationForm = ({ onStartMigration }) => {
  const [formData, setFormData] = useState({
    projectPath: 'target_repos/simple_express_app',
    projectType: 'nodejs',
    maxRetries: 3,
    gitBranch: 'main'
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
    onStartMigration(formData);
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
            <label htmlFor="projectPath">Project Path</label>
            <input 
              type="text" 
              id="projectPath" 
              name="projectPath"
              value={formData.projectPath}
              onChange={handleChange}
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
              <option value="">Select Project Type</option>
              <option value="nodejs">Node.js</option>
              <option value="python">Python</option>
            </select>
          </div>
          
          <div className="form-group">
            <label htmlFor="maxRetries">Max Retries</label>
            <input 
              type="number" 
              id="maxRetries" 
              name="maxRetries"
              min="0" 
              max="10" 
              value={formData.maxRetries}
              onChange={handleChange}
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="gitBranch">Git Branch</label>
            <input 
              type="text" 
              id="gitBranch" 
              name="gitBranch"
              value={formData.gitBranch}
              onChange={handleChange}
            />
          </div>
        </div>
        
        <button type="submit" className="btn btn-primary">
          <i className="fas fa-play"></i> Start Migration
        </button>
      </form>
    </div>
  );
};

export default MigrationForm;