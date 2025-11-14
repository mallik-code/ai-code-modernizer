import React, { useState, useEffect } from 'react';
import './App.css';
import MigrationForm from './components/MigrationForm';
import StatusPanel from './components/StatusPanel';
import WebSocketLogs from './components/WebSocketLogs';
import ReportSection from './components/ReportSection';

function App() {
  // State management
  const [migrationStatus, setMigrationStatus] = useState('');
  const [migrationDetails, setMigrationDetails] = useState({
    status: '',
    migrationId: null,
    projectPath: ''
  });
  const [progress, setProgress] = useState(0);
  const [logs, setLogs] = useState([]);
  const [reportUrl, setReportUrl] = useState('');
  const [reportLinks, setReportLinks] = useState(null);
  const [isMigrationRunning, setIsMigrationRunning] = useState(false);
  const [ws, setWs] = useState(null);
  const [currentMigrationId, setCurrentMigrationId] = useState(null);

  // Base URL for API calls
  const BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  // Add log entry
  const addLogEntry = (message, type = 'info', agent = null, timestamp = new Date()) => {
    const logEntry = {
      message,
      type,
      agent,
      timestamp: timestamp.toISOString()
    };
    setLogs(prevLogs => [...prevLogs, logEntry]);
  };

  // Start migration
  const startMigration = async (formData) => {
    if (isMigrationRunning) {
      addLogEntry('Migration is already running!', 'error');
      return;
    }

    setIsMigrationRunning(true);
    setMigrationStatus('starting');
    setMigrationDetails(prev => ({
      ...prev,
      status: 'starting'
    }));
    addLogEntry('Starting new migration...', 'info');

    try {
      const response = await fetch(`${BASE_URL}/api/migrations/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      console.log("Migration start response received:", result);
      const migrationId = result.migration_id;
      console.log("Extracted migration ID:", migrationId);

      if (!migrationId) {
        throw new Error('Migration ID not returned from server');
      }

      setCurrentMigrationId(migrationId);
      console.log("Set currentMigrationId to:", migrationId);

      setMigrationDetails({
        status: result.status,
        migrationId: migrationId,
        projectPath: result.project_path || formData.projectPath
      });

      addLogEntry(`Migration started with ID: ${migrationId}`, 'info');

      // Connect WebSocket
      connectWebSocket(migrationId);

      setMigrationStatus('in-progress');
      setProgress(10);
    } catch (error) {
      console.error('Error starting migration:', error);
      addLogEntry(`Error starting migration: ${error.message}`, 'error');
      setMigrationStatus('error');
      setIsMigrationRunning(false);
    }
  };

  // Connect WebSocket
  const connectWebSocket = (migrationId) => {
    const wsUrl = `${BASE_URL.replace('http', 'ws')}/ws/migrations/${migrationId}`;
    addLogEntry(`Connecting to WebSocket: ${wsUrl}`, 'connection');

    const newWs = new WebSocket(wsUrl);
    setWs(newWs);

    newWs.onopen = function(event) {
      addLogEntry('WebSocket connected successfully', 'connection');
    };

    newWs.onmessage = function(event) {
      try {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data, migrationId);
      } catch (e) {
        addLogEntry(`Error parsing WebSocket message: ${event.data}`, 'error');
      }
    };

    newWs.onclose = function(event) {
      addLogEntry(`WebSocket closed: ${event.code} - ${event.reason}`, 'connection');
      if (isMigrationRunning) {
        // Try to get final status
        setTimeout(() => checkMigrationStatus(migrationId), 1000);
      }
    };

    newWs.onerror = function(error) {
      addLogEntry(`WebSocket error: ${error}`, 'error');
    };
  };

  // Handle WebSocket message
  const handleWebSocketMessage = (data, migrationId) => {
    const { type, agent, message, timestamp } = data;
    const logType = getLogType(type, data.status);
    const time = timestamp ? new Date(timestamp) : new Date();

    addLogEntry(message, logType, agent, time);

    // Update progress based on agent activity
    if (type === 'agent_completion' && data.status === 'success') {
      setProgress(70);
    }

    // Update status display
    if (type === 'workflow_status' && data.message) {
      setMigrationStatus(data.message);
    }

    // Check if migration is complete or any major agent completes
    if (type === 'workflow_complete') {
      console.log("Workflow complete received, checking migration status with ID:", migrationId);
      setTimeout(() => {
        if (migrationId) {
          checkMigrationStatus(migrationId);
        } else {
          console.error("Cannot check migration status: migrationId is null or undefined");
        }
      }, 2000);
    } else if (type === 'agent_completion') {
      console.log("Agent completion received:", agent, "with status:", data.status);
      if (data.status === 'success' && agent === 'staging_deployer') {
        console.log("Staging deployer completed successfully, checking migration status with ID:", migrationId);
        setTimeout(() => {
          if (migrationId) {
            checkMigrationStatus(migrationId);
          } else {
            console.error("Cannot check migration status after staging deployer: migrationId is null or undefined");
          }
        }, 2000);
      }
    }
  };

  // Get log type based on message type
  const getLogType = (type, status = null) => {
    switch (type) {
      case 'workflow_complete':
        return status === 'deployed' || status === 'validated' ? 'success' : 'error';
      case 'agent_completion':
        return status === 'success' ? 'success' : status === 'failed' ? 'error' : 'info';
      case 'workflow_error':
      case 'agent_error':
        return 'error';
      case 'connection':
        return 'connection';
      case 'tool_use':
      case 'agent_thinking':
        return 'agent';
      default:
        return 'info';
    }
  };

  // Fetch report content
  const fetchReportContent = async (reportContentUrl) => {
    try {
      const fullUrl = reportContentUrl.startsWith('http') ?
        reportContentUrl :
        `${BASE_URL}${reportContentUrl}`;

      addLogEntry(`Fetching report content from: ${fullUrl}`, 'info');

      const response = await fetch(fullUrl);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();

      // Create a blob URL for the HTML content to display in iframe
      if (result.content) {
        const blob = new Blob([result.content], { type: 'text/html' });
        const blobUrl = URL.createObjectURL(blob);
        setReportUrl(blobUrl);
        addLogEntry('Report loaded successfully!', 'success');
      }
    } catch (error) {
      console.error('Error fetching report content:', error);
      addLogEntry(`Error fetching report: ${error.message}`, 'error');
    }
  };

  // Check migration status
  const checkMigrationStatus = async (migrationId) => {
    console.log("checkMigrationStatus called with migrationId:", migrationId);
    if (!migrationId) {
      console.error("checkMigrationStatus: migrationId is null or undefined, cannot proceed");
      return;
    }

    try {
      const response = await fetch(`${BASE_URL}/api/migrations/${migrationId}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      
      // Update status display
      setMigrationDetails(prev => ({
        ...prev,
        status: result.status
      }));
      
      if (result.status === 'deployed') {
        setMigrationStatus('deployed');
        setProgress(100);
        addLogEntry('Migration completed successfully!', 'success');

        // Save report links for buttons
        if (result.reports_content) {
          setReportLinks({
            content: result.reports_content,  // For viewing
            download: result.reports           // For downloading
          });
          addLogEntry('Report links available', 'success');
        }
      } else if (result.status === 'error') {
        setMigrationStatus('error');
        addLogEntry('Migration failed', 'error');
        if (result.errors && result.errors.length > 0) {
          result.errors.forEach(error => addLogEntry(`Error: ${error}`, 'error'));
        }
      } else {
        setMigrationStatus(result.status);
        addLogEntry(`Migration status: ${result.status}`, 'info');
      }
      
      setIsMigrationRunning(false);
    } catch (error) {
      console.error('Error checking migration status:', error);
      addLogEntry(`Error checking status: ${error.message}`, 'error');
      setIsMigrationRunning(false);
    }
  };

  // View report - Fetch and display HTML content
  const handleViewReport = async () => {
    if (reportLinks && reportLinks.content && reportLinks.content.html) {
      await fetchReportContent(reportLinks.content.html);
    } else {
      addLogEntry('Report content not available', 'error');
    }
  };

  // Download report - Open download link based on format
  const handleDownloadReport = (format = 'html') => {
    if (reportLinks && reportLinks.download) {
      const downloadUrl = reportLinks.download[format];
      if (downloadUrl) {
        const fullUrl = downloadUrl.startsWith('http') ?
          downloadUrl :
          `${BASE_URL}${downloadUrl}`;
        addLogEntry(`Downloading ${format.toUpperCase()} report...`, 'info');
        window.open(fullUrl, '_blank');
      } else {
        addLogEntry(`${format.toUpperCase()} report not available`, 'error');
      }
    } else {
      addLogEntry('Report download links not available', 'error');
    }
  };

  // Cleanup WebSocket on unmount
  useEffect(() => {
    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, [ws]);

  // Cleanup blob URL on unmount
  useEffect(() => {
    return () => {
      if (reportUrl && reportUrl.startsWith('blob:')) {
        URL.revokeObjectURL(reportUrl);
      }
    };
  }, [reportUrl]);

  return (
    <div className="App">
      <header className="top-ribbon">
        <div className="logo-container">
          <img src={`${process.env.PUBLIC_URL}/images/reflectionsit_logo.jpg`} alt="Logo" className="logo-image" />
          <div className="logo-text">AI Code Modernizer</div>
        </div>
        <div className="user-container">
          <div className="user-icon">
            <i className="fas fa-user"></i>
          </div>
        </div>
      </header>
      
      <main className="main-container">
        <MigrationForm onStartMigration={startMigration} />
        <StatusPanel 
          migrationStatus={migrationStatus} 
          migrationDetails={migrationDetails} 
          progress={progress} 
        />
        <WebSocketLogs logs={logs} />
        <ReportSection
          reportUrl={reportUrl}
          reportLinks={reportLinks}
          onViewReport={handleViewReport}
          onDownloadReport={handleDownloadReport}
        />
      </main>
    </div>
  );
}

export default App;