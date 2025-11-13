# AI Code Modernizer Frontend

This is the frontend UI for the AI Code Modernizer application that provides a user interface for starting dependency migrations and monitoring real-time progress.

## Features

- Professional dashboard with ribbon navigation and custom logo
- Form to configure and start migration workflows
- Real-time migration status updates via WebSocket
- Progress visualization
- Live log console with color-coded messages
- Report download capability for migration results

## How to Use

### Method 1: Using a Local Web Server (Recommended)

1. **Start the backend server first** (in the `../backend` directory):
   ```bash
   uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Serve this frontend directory with a local web server**:

   **Option 1: Using Python's built-in server:**
   ```bash
   cd frontend
   python -m http.server 5500
   ```
   Then open http://localhost:5500 in your browser

   **Option 2: Using Node's http-server:**
   ```bash
   cd frontend
   npx http-server
   ```
   Then open the provided URL in your browser

   **Option 3: Using Live Server extension in VS Code:**
   - Right-click `index.html` and select "Open with Live Server"

### Method 2: Direct File Access (with backend CORS configuration)

1. **Start the backend server** with `CORS_ALLOW_ALL=true` in your `.env` file:
   ```
   CORS_ALLOW_ALL=true
   ```
   
2. **Open `index.html` directly** with your browser
   - Double-click the `index.html` file or open it directly

## Configuration

- The default backend API URL is `http://localhost:8000`
- The default project path is set to `target_repos/simple_express_app`

## Architecture

The frontend is a single HTML file with:
- Modern CSS styling
- Responsive design
- WebSocket integration for real-time updates
- API integration for starting/monitoring migrations
- Report viewing capability

For more information about the backend system and the complete application, see the main README in the project root directory.