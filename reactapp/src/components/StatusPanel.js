import React from 'react';
import './StatusPanel.css';

const StatusPanel = ({ migrationStatus, migrationDetails, progress }) => {
  const { status, migrationId, projectPath } = migrationDetails;

  return (
    <div className="card">
      <h2 className="card-title">
        <i className="fas fa-bolt"></i>
        Migration Status
      </h2>
      
      <div className={`status-indicator ${status === 'deployed' ? 'success' : status === 'error' ? 'error' : status ? 'active' : ''}`}>
        <i className={`fas fa-${status === 'deployed' ? 'check-circle' : status === 'error' ? 'exclamation-circle' : 'info-circle'} status-icon`}></i>
        <span>{status ? status.charAt(0).toUpperCase() + status.slice(1) : 'Waiting to start...'}</span>
      </div>
      
      <div className="progress-container">
        <div className="progress-bar">
          <div className="progress" style={{ width: `${progress}%` }}></div>
        </div>
      </div>
      
      {migrationId && (
        <div className="migration-details">
          <p><strong>Migration ID:</strong> <span>{migrationId}</span></p>
          <p><strong>Project Path:</strong> <span>{projectPath}</span></p>
          <p><strong>Status:</strong> <span>{status}</span></p>
        </div>
      )}
    </div>
  );
};

export default StatusPanel;