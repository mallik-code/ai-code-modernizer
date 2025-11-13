import React, { useEffect, useRef } from 'react';
import './WebSocketLogs.css';

const WebSocketLogs = ({ logs }) => {
  const logsEndRef = useRef(null);

  // Scroll to bottom when logs update
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  const formatLogType = (type) => {
    switch (type) {
      case 'workflow_complete':
      case 'agent_completion':
        return 'log-success';
      case 'workflow_error':
      case 'agent_error':
        return 'log-error';
      case 'connection':
        return 'log-connection';
      case 'tool_use':
      case 'agent_thinking':
        return 'log-agent';
      default:
        return 'log-info';
    }
  };

  return (
    <div className="card">
      <h2 className="card-title">
        <i className="fas fa-terminal"></i>
        Real-time Updates
      </h2>
      <div className="logs-container">
        {logs.length > 0 ? (
          logs.map((log, index) => {
            const logType = formatLogType(log.type);
            const time = log.timestamp ? new Date(log.timestamp).toISOString().slice(11, -1) : new Date().toISOString().slice(11, -1);
            return (
              <div key={index} className={`log-entry ${logType}`}>
                <span className="log-timestamp">[{time}]</span>
                {log.agent && <span className="log-agent-name">[{log.agent}]</span>}
                {log.message}
              </div>
            );
          })
        ) : (
          <div className="log-entry log-info">
            <span className="log-timestamp">[Waiting...]</span> Waiting for migration to start...
          </div>
        )}
        <div ref={logsEndRef} />
      </div>
    </div>
  );
};

export default WebSocketLogs;