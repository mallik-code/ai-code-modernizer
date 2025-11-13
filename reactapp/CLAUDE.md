# CLAUDE.md - React Frontend

This file provides guidance for working with the React frontend application.

## Frontend Overview

Vanilla JavaScript React application (no build tools) providing real-time visualization of the multi-agent workflow with WebSocket integration for live updates.

**Implementation Status**: Complete (100% - 2025-11-14)
- ✅ Migration form with project configuration
- ✅ Real-time WebSocket connection and message handling
- ✅ Live status panel with progress visualization
- ✅ WebSocket logs viewer with color-coded messages
- ✅ Report viewing in browser (HTML content in iframe)
- ✅ Report download dropdown (HTML, Markdown, JSON)
- ✅ Responsive design with professional UI
- ✅ Migration ID state management fix

## Architecture

### Tech Stack
- **React 18** - Loaded via CDN (no build tools)
- **Vanilla JavaScript** - ES6+ features
- **CSS3** - Custom styles with CSS variables
- **WebSocket** - Real-time backend communication
- **Font Awesome** - Icon library via CDN

### File Structure
```
reactapp/
├── public/
│   ├── index.html              # Main HTML file
│   ├── images/
│   │   └── reflectionsit_logo.jpg
│   └── manifest.json
├── src/
│   ├── App.js                  # Main application component
│   ├── App.css                 # Main application styles
│   ├── index.js                # React DOM entry point
│   ├── index.css               # Global styles
│   └── components/
│       ├── MigrationForm.js    # Migration configuration form
│       ├── MigrationForm.css
│       ├── StatusPanel.js      # Migration status display
│       ├── StatusPanel.css
│       ├── WebSocketLogs.js    # Real-time log viewer
│       ├── WebSocketLogs.css
│       ├── ReportSection.js    # Report viewing/downloading
│       └── ReportSection.css
├── package.json
└── README.md
```

## Running the Frontend

### Option 1: Python HTTP Server (Recommended)
```bash
cd reactapp
python -m http.server 5500
# Then open http://localhost:5500 in browser
```

### Option 2: Node.js http-server
```bash
cd reactapp
npx http-server
# Then open the provided URL
```

### Option 3: VS Code Live Server
1. Install "Live Server" extension in VS Code
2. Right-click `index.html`
3. Select "Open with Live Server"

### CORS Configuration
If using direct file access (`file://` protocol), you'll encounter CORS issues.

**Solution**: Set `CORS_ALLOW_ALL=true` in backend `.env` file:
```bash
CORS_ALLOW_ALL=true
```
Then restart the backend server.

## Component Architecture

### App.js (Main Component)
**State Management:**
```javascript
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
const [ws, setWs] = useState(null);
const [currentMigrationId, setCurrentMigrationId] = useState(null);
```

**Key Functions:**
- `startMigration(formData)` - Initiates migration workflow via REST API
- `connectWebSocket(migrationId)` - Establishes WebSocket connection
- `handleWebSocketMessage(data, migrationId)` - Processes WebSocket messages
- `checkMigrationStatus(migrationId)` - Fetches final migration status
- `fetchReportContent(reportContentUrl)` - Fetches HTML report for viewing
- `handleViewReport()` - Displays report in browser iframe
- `handleDownloadReport(format)` - Downloads report in specified format

### MigrationForm Component
**Props:** `onStartMigration` function

**Features:**
- Project path input (default: `target_repos/simple_express_app`)
- Project type selector (nodejs/python)
- Max retries configuration
- Git branch specification
- Form validation

### StatusPanel Component
**Props:**
- `migrationStatus` - Current status text
- `migrationDetails` - Migration metadata
- `progress` - Progress percentage (0-100)

**Features:**
- Color-coded status indicator (active/success/error)
- Progress bar visualization
- Migration ID and project path display

### WebSocketLogs Component
**Props:** `logs` array

**Features:**
- Auto-scrolling log viewer
- Color-coded messages by type:
  - `log-info` - Blue (general information)
  - `log-success` - Green (successful operations)
  - `log-error` - Red (errors and failures)
  - `log-connection` - Purple (WebSocket connection events)
  - `log-agent` - Pink (agent thinking/tool use)
- Timestamp and agent name display
- Dark terminal-style interface

### ReportSection Component
**Props:**
- `reportUrl` - Blob URL for iframe display
- `reportLinks` - API links for content and download
- `onViewReport` - Handler for viewing report
- `onDownloadReport` - Handler for downloading report

**Features:**
- **View Report Button** - Fetches and displays HTML in iframe
- **Download Report Dropdown** - Three format options:
  - HTML (with file-code icon)
  - Markdown (with markdown icon)
  - JSON (with file-code icon)
- Auto-close dropdown after selection
- Conditional rendering (only shows when reports available)

## Backend Communication

### REST API Endpoints

**Start Migration:**
```javascript
const response = await fetch(`${BASE_URL}/api/migrations/start`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    project_path: formData.projectPath,
    project_type: formData.projectType,
    max_retries: parseInt(formData.maxRetries),
    git_branch: formData.gitBranch,
    github_token: formData.githubToken || null
  })
});
```

**Get Migration Status:**
```javascript
const response = await fetch(`${BASE_URL}/api/migrations/${migrationId}`);
const result = await response.json();
// Returns: status, reports, reports_content links
```

**Get Report Content:**
```javascript
const response = await fetch(`${BASE_URL}/api/migrations/${migrationId}/report_content?type=html`);
const result = await response.json();
// Returns: { migration_id, status, type, content, timestamp }
```

**Download Report:**
```javascript
window.open(`${BASE_URL}/api/migrations/${migrationId}/report?type=html`, '_blank');
// Triggers file download
```

### WebSocket Connection

**Connection Setup:**
```javascript
const wsUrl = `ws://localhost:8000/ws/migrations/${migrationId}`;
const ws = new WebSocket(wsUrl);

ws.onopen = () => console.log('WebSocket connected');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  handleWebSocketMessage(data, migrationId);
};
ws.onclose = () => console.log('WebSocket closed');
ws.onerror = (error) => console.error('WebSocket error:', error);
```

**Message Types:**
- `connection` - Client connected
- `workflow_start` - Workflow beginning
- `workflow_status` - Agent currently running
- `agent_completion` - Agent finished (success/failure)
- `workflow_complete` - Entire workflow finished
- `workflow_error` - Workflow encountered error
- `agent_thinking` - Agent using LLM
- `agent_thinking_complete` - Agent thinking finished
- `tool_use` - Agent using tool
- `tool_complete` - Tool use completed

**Message Structure:**
```javascript
{
  type: "agent_completion",
  agent: "migration_planner",
  status: "success",
  message: "Migration plan created successfully",
  timestamp: "2025-11-14T10:30:00.123456",
  // ... additional fields based on message type
}
```

## State Management Flow

### Migration Lifecycle

1. **User Submits Form** → `startMigration(formData)`
2. **POST /api/migrations/start** → Receives `migration_id`
3. **Set State** → `setCurrentMigrationId(migrationId)`
4. **Connect WebSocket** → `connectWebSocket(migrationId)`
5. **Receive Real-time Updates** → `handleWebSocketMessage(data, migrationId)`
6. **Workflow Complete** → `checkMigrationStatus(migrationId)`
7. **Get Report Links** → Store in `reportLinks` state
8. **User Views Report** → `handleViewReport()` → Fetch content → Create Blob URL
9. **User Downloads Report** → `handleDownloadReport(format)` → Open download link

### Critical Bug Fix: Migration ID State Management

**Problem:** Migration ID was `null` when calling `checkMigrationStatus()` due to:
1. Invalid `useEffect` hook inside function (lines 88-90)
2. Stale closure in WebSocket message handler
3. React state not updating immediately

**Solution:**
1. Removed invalid `useEffect` from inside `startMigration()`
2. Pass `migrationId` through function parameters (closure scope)
3. Updated `handleWebSocketMessage(data, migrationId)` to accept ID
4. Use parameter instead of state in callbacks

## Styling

### CSS Variables (`App.css`)
```css
:root {
  --primary: #2563eb;
  --primary-dark: #1d4ed8;
  --secondary: #64748b;
  --success: #10b981;
  --warning: #f59e0b;
  --danger: #ef4444;
  --light: #f8fafc;
  --dark: #0f172a;
  --gray: #e2e8f0;
  --border: #cbd5e1;
}
```

### Responsive Design
- Mobile-first approach
- Flexbox and Grid layouts
- Breakpoint at 768px for tablets/mobile
- Stacked button layout on small screens

### Component Styles
- **Card**: White background, rounded corners, subtle shadow
- **Buttons**: Primary (blue), Secondary (gray), hover effects
- **Dropdown**: Absolute positioning, shadow, animated chevron
- **Logs**: Dark terminal theme, auto-scroll, monospace font
- **Progress Bar**: Smooth transitions, color-coded status

## Environment Configuration

### API Base URL
```javascript
const BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
```

**Default**: `http://localhost:8000` (for local development)

**Production**: Set `REACT_APP_API_URL` environment variable

## Memory Management

### Blob URL Cleanup
```javascript
useEffect(() => {
  return () => {
    if (reportUrl && reportUrl.startsWith('blob:')) {
      URL.revokeObjectURL(reportUrl);
    }
  };
}, [reportUrl]);
```

Prevents memory leaks by revoking blob URLs when component unmounts.

### WebSocket Cleanup
```javascript
useEffect(() => {
  return () => {
    if (ws) {
      ws.close();
    }
  };
}, [ws]);
```

Closes WebSocket connection when component unmounts.

## Features Implemented

✅ **Migration Form**
- Project configuration inputs
- Form validation
- Submit handler with payload transformation

✅ **Real-time Status**
- WebSocket connection management
- Live message processing
- Progress bar updates
- Status indicator with icons

✅ **Log Viewer**
- Auto-scrolling terminal
- Color-coded message types
- Timestamp and agent display
- Dark theme with monospace font

✅ **Report Management**
- View Report button (HTML in iframe)
- Download dropdown (HTML/Markdown/JSON)
- Blob URL creation for viewing
- File download via window.open()

✅ **Error Handling**
- API error messages
- WebSocket connection errors
- Migration failure display
- User-friendly error logs

## Testing Locally

1. **Start Backend**:
   ```bash
   cd backend
   venv\Scripts\activate  # Windows
   uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Start Frontend**:
   ```bash
   cd reactapp
   python -m http.server 5500
   ```

3. **Open Browser**: http://localhost:5500

4. **Test Flow**:
   - Fill in project path (e.g., `target_repos/simple_express_app`)
   - Select project type (nodejs)
   - Click "Start Migration"
   - Watch real-time WebSocket logs
   - Wait for completion
   - Click "View Report" to see HTML
   - Use "Download Report" dropdown for other formats

## Common Issues

### CORS Errors
**Symptom**: Fetch requests fail with CORS error

**Solution**: Set `CORS_ALLOW_ALL=true` in backend `.env` and restart backend

### WebSocket Connection Failed
**Symptom**: "WebSocket error" in logs

**Solution**: Ensure backend is running on port 8000 and WebSocket endpoint is accessible

### Report Not Showing
**Symptom**: Buttons appear but report doesn't load

**Solution**: Check browser console for errors, verify report content API returns valid HTML

### Migration ID is null
**Symptom**: API call to `/api/migrations/null`

**Solution**: Already fixed - ensure using latest App.js with proper state management

## Next Steps

For production deployment:
1. Build process for minification and bundling
2. Environment-based configuration
3. CDN hosting for static assets
4. Service worker for offline support
5. Analytics integration
