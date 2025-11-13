import React, { useState } from 'react';
import './ReportSection.css';

const ReportSection = ({ reportUrl, reportLinks, onViewReport, onDownloadReport }) => {
  const [showDropdown, setShowDropdown] = useState(false);

  const handleDownload = (format) => {
    onDownloadReport(format);
    setShowDropdown(false);
  };

  return (
    <div className="card">
      <h2 className="card-title">
        <i className="fas fa-file-alt"></i>
        Migration Report
      </h2>

      {reportLinks && (
        <div className="report-actions">
          <button className="btn btn-primary" onClick={onViewReport}>
            <i className="fas fa-eye"></i> View Report
          </button>

          <div className="dropdown-container">
            <button
              className="btn btn-secondary dropdown-toggle"
              onClick={() => setShowDropdown(!showDropdown)}
            >
              <i className="fas fa-download"></i> Download Report
              <i className={`fas fa-chevron-${showDropdown ? 'up' : 'down'} dropdown-icon`}></i>
            </button>

            {showDropdown && (
              <div className="dropdown-menu">
                <button
                  className="dropdown-item"
                  onClick={() => handleDownload('html')}
                >
                  <i className="fas fa-file-code"></i> HTML
                </button>
                <button
                  className="dropdown-item"
                  onClick={() => handleDownload('markdown')}
                >
                  <i className="fab fa-markdown"></i> Markdown
                </button>
                <button
                  className="dropdown-item"
                  onClick={() => handleDownload('json')}
                >
                  <i className="fas fa-file-code"></i> JSON
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      <div className="report-container" id="reportContainer" style={{ display: reportUrl ? 'block' : 'none' }}>
        <iframe className="report-iframe" id="reportIframe" src={reportUrl} title="Migration Report"></iframe>
      </div>
    </div>
  );
};

export default ReportSection;