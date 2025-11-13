# AI Code Modernizer React App

This is the React frontend for the AI Code Modernizer application, providing a professional UI for managing dependency migrations.

## Features

- Professional dashboard with ribbon navigation and custom logo
- Form to configure and start migration workflows
- Real-time migration status updates via WebSocket
- Progress visualization
- Live log console with color-coded messages
- Report download capability for migration results
- Responsive design for all device sizes
- Default project path pre-filled for quick start

## Architecture

The React app is built with:
- React 18 with functional components and hooks
- Modern CSS with variables and responsive design
- WebSocket integration for real-time updates
- Component-based architecture for maintainability

## How to Run

### Prerequisites
- Node.js (v14 or higher)
- npm or yarn

### Setup
1. Navigate to the reactapp directory:
   ```bash
   cd reactapp
   ```

2. Install dependencies:
   ```bash
   npm install
   # or
   yarn install
   ```

### Configuration
- By default, the app connects to `http://localhost:8000`
- To use a different backend URL, create a `.env` file with:
  ```
  REACT_APP_API_URL=https://your-backend-url.com
  ```

### Development
1. Start the development server:
   ```bash
   npm start
   # or
   yarn start
   ```
   
2. Open http://localhost:3000 in your browser

### Production Build
To create a production build:
```bash
npm run build
# or
yarn build
```

## Components

- `MigrationForm`: Handles migration configuration and submission
- `StatusPanel`: Displays migration status and progress
- `WebSocketLogs`: Shows real-time updates from backend
- `ReportSection`: Handles report download functionality

## Environment Variables

- `REACT_APP_API_URL`: Backend API URL (defaults to http://localhost:8000)

## Folder Structure

```
reactapp/
├── public/
│   ├── index.html
│   ├── favicon.ico
│   ├── logo192.png
│   ├── logo512.png
│   ├── manifest.json
│   └── images/ (for logo files)
├── src/
│   ├── components/
│   │   ├── MigrationForm.js
│   │   ├── StatusPanel.js
│   │   ├── WebSocketLogs.js
│   │   └── ReportSection.js
│   ├── App.js
│   ├── App.css
│   ├── index.js
│   └── index.css
├── package.json
├── README.md
└── .env (optional)
```

## Logo

The application expects the logo file `reflectionsit_logo2.jpg` in the `public/images/` directory. If you have a different logo file, update the path in `src/App.js`.