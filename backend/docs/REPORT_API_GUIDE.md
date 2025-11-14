# Report Generation and Download API Guide

## Overview

The AI Code Modernizer automatically generates comprehensive migration reports in multiple formats (HTML, Markdown, JSON) and provides API endpoints to download them.

**Status**: ✅ **IMPLEMENTED** (Commit: d06efa8)

---

## Features

### 1. **Automatic Report Generation**
- Reports generated automatically when migration completes
- Three formats available: HTML, Markdown, JSON
- Stored in `reports/` directory
- No manual intervention required

### 2. **Downloadable via API**
- Simple GET endpoint with format selection
- Proper content types and filenames
- Direct browser download support

### 3. **Comprehensive Content**
- Migration summary (status, duration, cost)
- Dependencies analysis with risk assessment
- Breaking changes details
- Migration strategy phases
- Validation results (including test results)
- Cost breakdown by agent
- Errors and warnings

---

## API Endpoints

### 1. Get Migration Status (with Report Links)

```http
GET /api/migrations/{migration_id}
```

**Response:**
```json
{
  "migration_id": "mig_abc123def456",
  "status": "deployed",
  "project_path": "/path/to/project",
  "project_type": "nodejs",
  "started_at": "2025-11-12T10:30:00Z",
  "completed_at": "2025-11-12T10:35:00Z",
  "duration_seconds": 300,
  "result": {
    "validation_success": true,
    "tests_run": true,
    "tests_passed": true,
    "pr_url": "https://github.com/user/repo/pull/123",
    "total_cost_usd": 0.1234
  },
  "errors": [],
  "reports": {
    "html": "/api/migrations/mig_abc123def456/report?type=html",
    "markdown": "/api/migrations/mig_abc123def456/report?type=markdown",
    "json": "/api/migrations/mig_abc123def456/report?type=json"
  }
}
```

### 2. Download Migration Report

```http
GET /api/migrations/{migration_id}/report?type={format}
```

**Parameters:**
- `migration_id` (required): Unique migration identifier
- `type` (optional): Report format - `html`, `markdown`, or `json` (default: `html`)

**Example Requests:**

```bash
# Download HTML report (default)
curl http://localhost:8000/api/migrations/mig_abc123/report \
  -o migration_report.html

# Download Markdown report
curl "http://localhost:8000/api/migrations/mig_abc123/report?type=markdown" \
  -o migration_report.md

# Download JSON report
curl "http://localhost:8000/api/migrations/mig_abc123/report?type=json" \
  -o migration_report.json
```

**Response Headers:**
```
Content-Type: text/html (or text/markdown, application/json)
Content-Disposition: attachment; filename="simple_express_app_migration_report.html"
```

---

## Report Formats

### 1. HTML Report

**File**: `{project_name}_migration_report_{timestamp}.html`

**Features:**
- Professional styled layout
- Color-coded risk levels (🟢 LOW, 🟡 MEDIUM, 🔴 HIGH)
- Responsive tables
- Status badges
- Interactive navigation
- Print-friendly

**Use Cases:**
- Executive summaries
- Sharing with stakeholders
- Archiving for compliance

**Preview:**
```html
<!DOCTYPE html>
<html>
<head>
    <title>Migration Report - simple_express_app</title>
    <style>/* Professional styling */</style>
</head>
<body>
    <div class="container">
        <h1>Migration Report</h1>
        <div class="summary">
            <!-- Summary grid -->
        </div>
        <h2>Dependencies Analysis</h2>
        <table><!-- Dependencies table --></table>
        <!-- More sections -->
    </div>
</body>
</html>
```

### 2. Markdown Report

**File**: `{project_name}_migration_report_{timestamp}.md`

**Features:**
- GitHub-flavored markdown
- Tables with alignment
- Emoji indicators
- Code blocks for technical details
- Easy to version control

**Use Cases:**
- Documentation in Git repos
- Pull request descriptions
- Technical reviews

**Preview:**
```markdown
# Migration Report

**Generated:** 2025-11-12 10:35:00
**Status:** DEPLOYED
**Overall Risk:** 🟢 LOW

## Dependencies Analysis

| Package | Current | Target | Risk | Action |
|---------|---------|--------|------|--------|
| express | 4.16.0  | 4.19.2 | 🟢 LOW | UPGRADE |
...
```

### 3. JSON Report

**File**: `{project_name}_migration_report_{timestamp}.json`

**Features:**
- Complete workflow state
- Machine-readable
- All data fields included
- Easy to parse programmatically

**Use Cases:**
- Automated processing
- Integration with other tools
- Data analysis
- Custom reporting

**Preview:**
```json
{
  "project_path": "/path/to/project",
  "status": "deployed",
  "migration_plan": {
    "dependencies": {...},
    "overall_risk": "low"
  },
  "validation_result": {...},
  "total_cost": 0.1234,
  "agent_costs": {...}
}
```

---

## Usage Examples

### Example 1: Basic Workflow with Reports

```bash
# 1. Start migration
curl -X POST http://localhost:8000/api/migrations/start \
  -H "Content-Type: application/json" \
  -d '{
    "project_path": "tmp/projects/simple_express_app",
    "project_type": "nodejs"
  }'

# Response:
{
  "migration_id": "mig_abc123def456",
  "status": "started"
}

# 2. Wait for completion, then check status
curl http://localhost:8000/api/migrations/mig_abc123def456

# Response includes report links:
{
  "status": "deployed",
  "reports": {
    "html": "/api/migrations/mig_abc123def456/report?type=html",
    "markdown": "/api/migrations/mig_abc123def456/report?type=markdown",
    "json": "/api/migrations/mig_abc123def456/report?type=json"
  }
}

# 3. Download HTML report
curl http://localhost:8000/api/migrations/mig_abc123def456/report?type=html \
  -o migration_report.html

# 4. Open in browser
open migration_report.html  # macOS
start migration_report.html # Windows
xdg-open migration_report.html # Linux
```

### Example 2: Python Script

```python
import requests
import time

# Start migration
response = requests.post(
    "http://localhost:8000/api/migrations/start",
    json={
        "project_path": "tmp/projects/simple_express_app",
        "project_type": "nodejs"
    }
)
migration_id = response.json()["migration_id"]

# Poll for completion
while True:
    status = requests.get(
        f"http://localhost:8000/api/migrations/{migration_id}"
    ).json()

    if status["status"] in ["deployed", "error"]:
        break

    time.sleep(5)

# Download all report formats
if status.get("reports"):
    for format_type, url in status["reports"].items():
        report = requests.get(f"http://localhost:8000{url}")

        filename = f"migration_report.{format_type}"
        if format_type == "markdown":
            filename = "migration_report.md"

        with open(filename, "wb") as f:
            f.write(report.content)

        print(f"Downloaded: {filename}")
```

### Example 3: JavaScript/Fetch

```javascript
// Start migration
const response = await fetch('http://localhost:8000/api/migrations/start', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    project_path: 'tmp/projects/simple_express_app',
    project_type: 'nodejs'
  })
});

const { migration_id } = await response.json();

// Poll for completion
let status;
while (true) {
  const statusResponse = await fetch(
    `http://localhost:8000/api/migrations/${migration_id}`
  );
  status = await statusResponse.json();

  if (status.status === 'deployed' || status.status === 'error') {
    break;
  }

  await new Promise(resolve => setTimeout(resolve, 5000));
}

// Download HTML report
if (status.reports) {
  const reportUrl = `http://localhost:8000${status.reports.html}`;
  const a = document.createElement('a');
  a.href = reportUrl;
  a.download = 'migration_report.html';
  a.click();
}
```

---

## Report Content Details

### Summary Section
- **Project Information**: Path, type, status
- **Migration Metrics**: Dependencies count, phases, risk level
- **Results**: Validation status, tests passed, total cost
- **Links**: Pull request URL, branch name

### Dependencies Analysis
- **Table Format**: Package, current version, target version, risk, action, breaking changes count
- **Risk Levels**: Color-coded (GREEN/LOW, YELLOW/MEDIUM, RED/HIGH)
- **Actions**: UPGRADE, KEEP, REMOVE

### Breaking Changes Detail
- **Per Package**: Grouped by dependency
- **Version**: Specific version introducing the change
- **Description**: Clear explanation of the breaking change
- **Impact**: CRITICAL, HIGH, MEDIUM, LOW

### Migration Strategy
- **Phases**: Sequential upgrade phases
- **Dependencies per Phase**: Which packages in each phase
- **Estimated Time**: Time estimate for each phase
- **Rollback Plan**: Recovery steps if phase fails

### Validation Results
- **Container Info**: Container ID/name
- **Stage Status**: Build, Install, Runtime, Health Check
- **Test Results**: Tests run, tests passed, test summary
- **Port Info**: Exposed port for browser access
- **Errors**: Any errors encountered

### Cost Report
- **Per Agent**: Migration Planner, Runtime Validator, Error Analyzer, Staging Deployer
- **Total Cost**: Sum of all agent costs in USD
- **Token Usage**: Input/output tokens per agent

---

## Error Handling

### Error 1: Migration Not Found
```bash
curl http://localhost:8000/api/migrations/invalid_id/report

# Response: 404 Not Found
{
  "detail": "Migration not found: invalid_id"
}
```

### Error 2: Report Not Available Yet
```bash
# Migration still running
curl http://localhost:8000/api/migrations/mig_abc123/report

# Response: 404 Not Found
{
  "detail": "Report not available yet. Migration may still be running or failed before completion."
}
```

### Error 3: Invalid Report Type
```bash
curl "http://localhost:8000/api/migrations/mig_abc123/report?type=pdf"

# Response: 400 Bad Request
{
  "detail": "Invalid report type. Must be one of: html, markdown, json"
}
```

### Error 4: Report File Missing
```bash
# Report file was deleted from filesystem
curl http://localhost:8000/api/migrations/mig_abc123/report?type=html

# Response: 404 Not Found
{
  "detail": "Report file not found: html"
}
```

---

## Storage and Cleanup

### Report Storage
- **Location**: `backend/reports/` directory
- **Naming**: `{project_name}_migration_report_{timestamp}.{ext}`
- **Formats**: `.html`, `.md`, `.json`

### Disk Usage
- **HTML**: ~50-100 KB per report
- **Markdown**: ~10-20 KB per report
- **JSON**: ~20-50 KB per report
- **Total per migration**: ~80-170 KB

### Cleanup Strategy

**Manual Cleanup:**
```bash
# Remove old reports (older than 30 days)
find reports/ -name "*.html" -mtime +30 -delete
find reports/ -name "*.md" -mtime +30 -delete
find reports/ -name "*.json" -mtime +30 -delete
```

**Automated Cleanup (Future):**
```python
# Could add to API:
@app.delete("/api/migrations/{migration_id}/reports")
async def delete_migration_reports(migration_id: str):
    """Delete all reports for a migration."""
    # Implementation
```

---

## Integration with Frontend

### React Component Example

```typescript
interface MigrationReport {
  html: string;
  markdown: string;
  json: string;
}

const ReportDownloader: React.FC<{ migrationId: string }> = ({ migrationId }) => {
  const [reports, setReports] = useState<MigrationReport | null>(null);

  useEffect(() => {
    fetch(`/api/migrations/${migrationId}`)
      .then(res => res.json())
      .then(data => setReports(data.reports));
  }, [migrationId]);

  const downloadReport = (type: 'html' | 'markdown' | 'json') => {
    if (!reports) return;

    const url = reports[type];
    const a = document.createElement('a');
    a.href = url;
    a.download = `migration_report.${type === 'markdown' ? 'md' : type}`;
    a.click();
  };

  if (!reports) return <div>Loading reports...</div>;

  return (
    <div className="report-downloader">
      <h3>Migration Reports</h3>
      <button onClick={() => downloadReport('html')}>
        Download HTML Report
      </button>
      <button onClick={() => downloadReport('markdown')}>
        Download Markdown Report
      </button>
      <button onClick={() => downloadReport('json')}>
        Download JSON Report
      </button>
    </div>
  );
};
```

---

## Production Considerations

### 1. **Database Storage**
Replace in-memory storage with database:
```python
# Store report_files in database
class Migration(Base):
    id = Column(String, primary_key=True)
    report_html_path = Column(String)
    report_markdown_path = Column(String)
    report_json_path = Column(String)
```

### 2. **Cloud Storage**
Store reports in S3/Azure Blob Storage:
```python
# Upload to S3 after generation
s3.upload_file(
    report_paths["html"],
    bucket="migration-reports",
    key=f"{migration_id}/report.html"
)

# Return S3 URL instead of local path
reports = {
    "html": f"https://s3.amazonaws.com/migration-reports/{migration_id}/report.html"
}
```

### 3. **Access Control**
Add authentication and authorization:
```python
@app.get("/api/migrations/{migration_id}/report")
async def download_report(
    migration_id: str,
    type: str = "html",
    current_user: User = Depends(get_current_user)
):
    # Check if user has permission to access this migration
    if not has_permission(current_user, migration_id):
        raise HTTPException(403, "Forbidden")

    # Return report
```

### 4. **Rate Limiting**
Prevent abuse:
```python
from slowapi import Limiter

limiter = Limiter(key_func=get_remote_address)

@app.get("/api/migrations/{migration_id}/report")
@limiter.limit("10/minute")
async def download_report(...):
    ...
```

---

## Related Documentation

- **MIGRATION_INVOCATION_GUIDE.md** - How to start migrations
- **QUICK_START_API.md** - API quick reference
- **PORT_MAPPING_GUIDE.md** - Browser access guide
- **utils/report_generator.py** - Report generation implementation

---

**Last Updated**: 2025-11-12
**Commit**: d06efa8
**Status**: ✅ Production Ready
