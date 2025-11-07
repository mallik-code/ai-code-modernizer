# Frontend Development Plan

## 🎯 Goal: Real-Time Agent Visualization Dashboard

Build an interactive dashboard that visualizes agent activity, workflow progress, and provides human-in-the-loop controls.

---

## 📋 Prerequisites Checklist

### Environment Setup
- [ ] Node.js 18+ installed (`node --version`)
- [ ] npm or yarn installed
- [ ] Dependencies installed (`npm install`)
- [ ] Backend API running on `http://localhost:8000`

### Verification Commands
```bash
# Test Node.js
node --version  # Should be 18+

# Install dependencies
npm install

# Start dev server
npm run dev

# Should open http://localhost:5173
```

---

## 🏗️ Development Phases

## Phase 1: Project Setup & Foundation (Day 1 - 2 hours)

### 1.1 Initial Setup (30 minutes)

**Commands**:
```bash
cd frontend
npm install
npm run dev
```

**Verify**:
- [ ] Vite dev server starts
- [ ] Can access http://localhost:5173
- [ ] Hot reload works

---

### 1.2 Basic Layout & Routing (1 hour)
**Files**:
- `src/App.tsx` - Main app component with routing
- `src/pages/Dashboard.tsx` - Main dashboard
- `src/pages/Upload.tsx` - Project upload page

**Implementation**:
```tsx
// src/App.tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Upload from './pages/Upload'

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-background text-text">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/upload" element={<Upload />} />
        </Routes>
      </div>
    </BrowserRouter>
  )
}

export default App
```

```tsx
// src/pages/Dashboard.tsx
export default function Dashboard() {
  return (
    <div className="p-8">
      <h1 className="text-4xl font-bold mb-4">
        AI Code Modernization Platform
      </h1>
      <p className="text-gray-400">
        Dashboard coming soon...
      </p>
    </div>
  )
}
```

**Checklist**:
- [ ] Files created
- [ ] Routing works
- [ ] Basic layout visible
- [ ] Tailwind CSS working

---

### 1.3 API Client Setup (30 minutes)
**File**: `src/lib/api.ts`

**Implementation**:
```typescript
// src/lib/api.ts
import axios from 'axios'

const API_BASE_URL = 'http://localhost:8000/api'

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export interface AnalyzeProjectRequest {
  projectPath: string
  projectType: 'nodejs' | 'python'
}

export interface AnalyzeProjectResponse {
  projectId: string
  status: string
  message: string
}

export const apiClient = {
  // Health check
  health: async () => {
    const response = await api.get('/health')
    return response.data
  },

  // Analyze project
  analyzeProject: async (data: AnalyzeProjectRequest): Promise<AnalyzeProjectResponse> => {
    const response = await api.post('/projects/analyze', data)
    return response.data
  },

  // Get project status
  getProjectStatus: async (projectId: string) => {
    const response = await api.get(`/projects/${projectId}/status`)
    return response.data
  },
}

// Test it
if (import.meta.env.DEV) {
  apiClient.health().then(() => console.log('✅ API connected'))
}
```

**Checklist**:
- [ ] File created
- [ ] Can connect to backend API
- [ ] Type definitions correct
- [ ] Console shows "API connected"

---

## Phase 2: Core Components (Day 2 - 4 hours)

### 2.1 Agent Card Component (1 hour)
**File**: `src/components/AgentCard.tsx`

**Goal**: Display individual agent status and activity

**Implementation**:
```tsx
// src/components/AgentCard.tsx
import { CheckCircle, Clock, AlertCircle, Loader2 } from 'lucide-react'

interface AgentCardProps {
  name: string
  status: 'idle' | 'running' | 'complete' | 'error'
  currentAction?: string
  result?: string
}

export default function AgentCard({ name, status, currentAction, result }: AgentCardProps) {
  const statusIcons = {
    idle: <Clock className="w-5 h-5 text-gray-400" />,
    running: <Loader2 className="w-5 h-5 text-primary animate-spin" />,
    complete: <CheckCircle className="w-5 h-5 text-secondary" />,
    error: <AlertCircle className="w-5 h-5 text-error" />,
  }

  const statusColors = {
    idle: 'bg-gray-800',
    running: 'bg-primary/10 border-primary',
    complete: 'bg-secondary/10 border-secondary',
    error: 'bg-error/10 border-error',
  }

  return (
    <div className={`p-4 rounded-lg border-2 ${statusColors[status]} transition-all`}>
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-lg font-semibold">{name}</h3>
        {statusIcons[status]}
      </div>

      {currentAction && (
        <p className="text-sm text-gray-400 mb-2">
          {currentAction}
        </p>
      )}

      {result && (
        <div className="mt-2 p-2 bg-background/50 rounded text-xs">
          {result}
        </div>
      )}
    </div>
  )
}
```

**Test Component**:
```tsx
// src/pages/Dashboard.tsx - Add test
<AgentCard
  name="Migration Planner"
  status="running"
  currentAction="Analyzing dependencies..."
/>
```

**Checklist**:
- [ ] File created
- [ ] Component renders correctly
- [ ] All status states work
- [ ] Icons display properly
- [ ] Animations work

---

### 2.2 Activity Feed Component (1 hour)
**File**: `src/components/ActivityFeed.tsx`

**Goal**: Show real-time agent activity log

**Implementation**:
```tsx
// src/components/ActivityFeed.tsx
import { useEffect, useRef } from 'react'

interface Activity {
  id: string
  timestamp: string
  agent: string
  action: string
  level: 'info' | 'success' | 'warning' | 'error'
}

interface ActivityFeedProps {
  activities: Activity[]
}

export default function ActivityFeed({ activities }: ActivityFeedProps) {
  const feedRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    // Auto-scroll to bottom
    if (feedRef.current) {
      feedRef.current.scrollTop = feedRef.current.scrollHeight
    }
  }, [activities])

  const levelColors = {
    info: 'text-gray-400',
    success: 'text-secondary',
    warning: 'text-accent',
    error: 'text-error',
  }

  return (
    <div
      ref={feedRef}
      className="h-96 overflow-y-auto bg-gray-900 rounded-lg p-4 font-mono text-sm"
    >
      {activities.map((activity) => (
        <div key={activity.id} className="mb-2">
          <span className="text-gray-600">{activity.timestamp}</span>
          {' '}
          <span className="text-primary font-semibold">[{activity.agent}]</span>
          {' '}
          <span className={levelColors[activity.level]}>{activity.action}</span>
        </div>
      ))}
    </div>
  )
}
```

**Checklist**:
- [ ] File created
- [ ] Auto-scrolls to bottom
- [ ] Color coding works
- [ ] Handles long lists

---

### 2.3 Project Upload Component (1 hour)
**File**: `src/components/ProjectUpload.tsx`

**Goal**: Allow users to upload or specify project

**Implementation**:
```tsx
// src/components/ProjectUpload.tsx
import { useState } from 'react'
import { Upload, Github, Folder } from 'lucide-react'

interface ProjectUploadProps {
  onSubmit: (projectInfo: { type: string; path: string }) => void
}

export default function ProjectUpload({ onSubmit }: ProjectUploadProps) {
  const [uploadType, setUploadType] = useState<'github' | 'local' | null>(null)
  const [projectPath, setProjectPath] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (projectPath) {
      onSubmit({
        type: uploadType || 'local',
        path: projectPath,
      })
    }
  }

  return (
    <div className="max-w-2xl mx-auto p-8">
      <h2 className="text-2xl font-bold mb-6">Upload Project</h2>

      <div className="grid grid-cols-2 gap-4 mb-6">
        <button
          onClick={() => setUploadType('github')}
          className={`p-6 rounded-lg border-2 transition-all ${
            uploadType === 'github'
              ? 'border-primary bg-primary/10'
              : 'border-gray-700 hover:border-gray-600'
          }`}
        >
          <Github className="w-8 h-8 mx-auto mb-2" />
          <p className="font-semibold">GitHub Repository</p>
        </button>

        <button
          onClick={() => setUploadType('local')}
          className={`p-6 rounded-lg border-2 transition-all ${
            uploadType === 'local'
              ? 'border-primary bg-primary/10'
              : 'border-gray-700 hover:border-gray-600'
          }`}
        >
          <Folder className="w-8 h-8 mx-auto mb-2" />
          <p className="font-semibold">Local Path</p>
        </button>
      </div>

      {uploadType && (
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">
              {uploadType === 'github' ? 'Repository URL' : 'Project Path'}
            </label>
            <input
              type="text"
              value={projectPath}
              onChange={(e) => setProjectPath(e.target.value)}
              placeholder={
                uploadType === 'github'
                  ? 'https://github.com/user/repo'
                  : '/path/to/project'
              }
              className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:border-primary focus:outline-none"
            />
          </div>

          <button
            type="submit"
            className="w-full py-3 bg-primary hover:bg-primary/90 rounded-lg font-semibold transition-colors"
          >
            Analyze Project
          </button>
        </form>
      )}
    </div>
  )
}
```

**Checklist**:
- [ ] File created
- [ ] Both upload types work
- [ ] Form validation
- [ ] Calls onSubmit correctly

---

### 2.4 Status Badge Component (30 minutes)
**File**: `src/components/StatusBadge.tsx`

**Simple reusable status indicator**

```tsx
// src/components/StatusBadge.tsx
interface StatusBadgeProps {
  status: 'pending' | 'running' | 'success' | 'error'
  text?: string
}

export default function StatusBadge({ status, text }: StatusBadgeProps) {
  const colors = {
    pending: 'bg-gray-600',
    running: 'bg-primary animate-pulse',
    success: 'bg-secondary',
    error: 'bg-error',
  }

  return (
    <span className={`inline-block px-3 py-1 rounded-full text-xs font-semibold ${colors[status]}`}>
      {text || status}
    </span>
  )
}
```

**Checklist**:
- [ ] File created
- [ ] All statuses render correctly

---

## Phase 3: State Management & WebSocket (Day 3 - 4 hours)

### 3.1 Zustand Store Setup (1 hour)
**File**: `src/lib/store.ts`

**Goal**: Global state management for agent data

**Implementation**:
```typescript
// src/lib/store.ts
import { create } from 'zustand'

interface Agent {
  name: string
  status: 'idle' | 'running' | 'complete' | 'error'
  currentAction?: string
  result?: string
}

interface Activity {
  id: string
  timestamp: string
  agent: string
  action: string
  level: 'info' | 'success' | 'warning' | 'error'
}

interface AppState {
  // Project state
  projectId: string | null
  projectPath: string | null
  workflowStatus: 'idle' | 'running' | 'complete' | 'error'

  // Agent state
  agents: Record<string, Agent>

  // Activity feed
  activities: Activity[]

  // Actions
  setProject: (id: string, path: string) => void
  updateAgent: (name: string, updates: Partial<Agent>) => void
  addActivity: (activity: Omit<Activity, 'id' | 'timestamp'>) => void
  reset: () => void
}

export const useStore = create<AppState>((set) => ({
  projectId: null,
  projectPath: null,
  workflowStatus: 'idle',
  agents: {},
  activities: [],

  setProject: (id, path) => set({ projectId: id, projectPath: path, workflowStatus: 'running' }),

  updateAgent: (name, updates) =>
    set((state) => ({
      agents: {
        ...state.agents,
        [name]: { ...state.agents[name], name, ...updates },
      },
    })),

  addActivity: (activity) =>
    set((state) => ({
      activities: [
        ...state.activities,
        {
          ...activity,
          id: Date.now().toString(),
          timestamp: new Date().toISOString(),
        },
      ],
    })),

  reset: () =>
    set({
      projectId: null,
      projectPath: null,
      workflowStatus: 'idle',
      agents: {},
      activities: [],
    }),
}))
```

**Checklist**:
- [ ] File created
- [ ] Store works correctly
- [ ] Can update agents
- [ ] Can add activities

---

### 3.2 WebSocket Hook (2 hours)
**File**: `src/hooks/useWebSocket.ts`

**Goal**: Real-time updates from backend

**Implementation**:
```typescript
// src/hooks/useWebSocket.ts
import { useEffect, useRef } from 'react'
import { useStore } from '../lib/store'

const WS_URL = 'ws://localhost:8000/ws'

export function useWebSocket(projectId: string | null) {
  const ws = useRef<WebSocket | null>(null)
  const { updateAgent, addActivity } = useStore()

  useEffect(() => {
    if (!projectId) return

    // Connect to WebSocket
    ws.current = new WebSocket(`${WS_URL}/${projectId}`)

    ws.current.onopen = () => {
      console.log('✅ WebSocket connected')
      addActivity({
        agent: 'system',
        action: 'Connected to server',
        level: 'success',
      })
    }

    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data)

      // Handle different message types
      switch (data.type) {
        case 'agent_update':
          updateAgent(data.agent, {
            status: data.status,
            currentAction: data.action,
          })
          addActivity({
            agent: data.agent,
            action: data.action,
            level: 'info',
          })
          break

        case 'agent_complete':
          updateAgent(data.agent, {
            status: 'complete',
            result: data.result,
          })
          addActivity({
            agent: data.agent,
            action: `Completed: ${data.result}`,
            level: 'success',
          })
          break

        case 'agent_error':
          updateAgent(data.agent, {
            status: 'error',
            result: data.error,
          })
          addActivity({
            agent: data.agent,
            action: `Error: ${data.error}`,
            level: 'error',
          })
          break
      }
    }

    ws.current.onerror = (error) => {
      console.error('❌ WebSocket error:', error)
      addActivity({
        agent: 'system',
        action: 'Connection error',
        level: 'error',
      })
    }

    ws.current.onclose = () => {
      console.log('WebSocket disconnected')
      addActivity({
        agent: 'system',
        action: 'Disconnected from server',
        level: 'warning',
      })
    }

    // Cleanup
    return () => {
      if (ws.current) {
        ws.current.close()
      }
    }
  }, [projectId])

  return ws
}
```

**Checklist**:
- [ ] File created
- [ ] Connects to backend WebSocket
- [ ] Handles messages correctly
- [ ] Auto-reconnects on error
- [ ] Updates store properly

---

### 3.3 Workflow Hook (1 hour)
**File**: `src/hooks/useWorkflow.ts`

**Goal**: Manage workflow execution

**Implementation**:
```typescript
// src/hooks/useWorkflow.ts
import { useState } from 'react'
import { useStore } from '../lib/store'
import { apiClient } from '../lib/api'
import { useWebSocket } from './useWebSocket'

export function useWorkflow() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const { projectId, setProject } = useStore()

  useWebSocket(projectId)

  const startWorkflow = async (projectPath: string) => {
    try {
      setLoading(true)
      setError(null)

      const response = await apiClient.analyzeProject({
        projectPath,
        projectType: 'nodejs',
      })

      setProject(response.projectId, projectPath)

      return response
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error'
      setError(errorMessage)
      throw err
    } finally {
      setLoading(false)
    }
  }

  return {
    startWorkflow,
    loading,
    error,
  }
}
```

**Checklist**:
- [ ] File created
- [ ] Can start workflow
- [ ] Error handling
- [ ] Loading states

---

## Phase 4: Graph Visualization (Day 3 - 2 hours)

### 4.1 Graph Component (2 hours)
**File**: `src/components/GraphView.tsx`

**Goal**: Visualize agent workflow as a graph

**Implementation**:
```tsx
// src/components/GraphView.tsx
import ReactFlow, {
  Node,
  Edge,
  Background,
  Controls,
  MiniMap,
} from 'reactflow'
import 'reactflow/dist/style.css'
import { useStore } from '../lib/store'

export default function GraphView() {
  const { agents } = useStore()

  // Define workflow nodes
  const nodes: Node[] = [
    {
      id: 'planner',
      position: { x: 100, y: 50 },
      data: {
        label: 'Migration Planner',
        status: agents['planner']?.status || 'idle',
      },
      type: 'default',
    },
    {
      id: 'validator',
      position: { x: 100, y: 150 },
      data: {
        label: 'Runtime Validator',
        status: agents['validator']?.status || 'idle',
      },
      type: 'default',
    },
    {
      id: 'analyzer',
      position: { x: 300, y: 150 },
      data: {
        label: 'Error Analyzer',
        status: agents['analyzer']?.status || 'idle',
      },
      type: 'default',
    },
    {
      id: 'deployer',
      position: { x: 100, y: 250 },
      data: {
        label: 'Staging Deployer',
        status: agents['deployer']?.status || 'idle',
      },
      type: 'default',
    },
  ]

  const edges: Edge[] = [
    { id: 'e1', source: 'planner', target: 'validator' },
    { id: 'e2', source: 'validator', target: 'analyzer', label: 'on error' },
    { id: 'e3', source: 'analyzer', target: 'validator', label: 'retry' },
    { id: 'e4', source: 'validator', target: 'deployer', label: 'success' },
  ]

  return (
    <div className="h-96 bg-gray-900 rounded-lg overflow-hidden">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        fitView
      >
        <Background />
        <Controls />
        <MiniMap />
      </ReactFlow>
    </div>
  )
}
```

**Checklist**:
- [ ] File created
- [ ] Graph renders
- [ ] Shows workflow structure
- [ ] Updates with agent status

---

## Phase 5: Complete Dashboard (Day 4 - 4 hours)

### 5.1 Main Dashboard Page (2 hours)
**File**: `src/pages/Dashboard.tsx` (complete version)

**Implementation**:
```tsx
// src/pages/Dashboard.tsx
import { useStore } from '../lib/store'
import { useWorkflow } from '../hooks/useWorkflow'
import AgentCard from '../components/AgentCard'
import ActivityFeed from '../components/ActivityFeed'
import GraphView from '../components/GraphView'
import ProjectUpload from '../components/ProjectUpload'
import StatusBadge from '../components/StatusBadge'

export default function Dashboard() {
  const { projectId, agents, activities, workflowStatus } = useStore()
  const { startWorkflow, loading } = useWorkflow()

  const handleProjectSubmit = async (projectInfo: any) => {
    await startWorkflow(projectInfo.path)
  }

  if (!projectId) {
    return <ProjectUpload onSubmit={handleProjectSubmit} />
  }

  return (
    <div className="min-h-screen p-8">
      <header className="mb-8">
        <h1 className="text-4xl font-bold mb-2">
          AI Code Modernization Platform
        </h1>
        <div className="flex items-center gap-4">
          <StatusBadge status={workflowStatus} />
          <span className="text-gray-400">Project: {projectId}</span>
        </div>
      </header>

      <div className="grid grid-cols-12 gap-6">
        {/* Agent Cards */}
        <div className="col-span-4 space-y-4">
          <h2 className="text-2xl font-semibold mb-4">Agents</h2>
          {Object.values(agents).map((agent) => (
            <AgentCard key={agent.name} {...agent} />
          ))}
        </div>

        {/* Graph and Activity */}
        <div className="col-span-8 space-y-6">
          <div>
            <h2 className="text-2xl font-semibold mb-4">Workflow</h2>
            <GraphView />
          </div>

          <div>
            <h2 className="text-2xl font-semibold mb-4">Activity Feed</h2>
            <ActivityFeed activities={activities} />
          </div>
        </div>
      </div>
    </div>
  )
}
```

**Checklist**:
- [ ] Complete dashboard layout
- [ ] All components integrated
- [ ] Real-time updates working
- [ ] Responsive design

---

### 5.2 CSS Utilities (1 hour)
**File**: `src/index.css`

**Add custom styles**:
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  body {
    @apply bg-background text-text;
  }
}

@layer components {
  .btn-primary {
    @apply px-4 py-2 bg-primary hover:bg-primary/90 rounded-lg font-semibold transition-colors;
  }

  .card {
    @apply p-6 bg-gray-800 rounded-lg border border-gray-700;
  }
}
```

**Checklist**:
- [ ] Styles added
- [ ] Theme working
- [ ] Components styled consistently

---

### 5.3 Error Boundary (1 hour)
**File**: `src/components/ErrorBoundary.tsx`

**Goal**: Catch React errors gracefully

**Checklist**:
- [ ] File created
- [ ] Catches errors
- [ ] Shows error UI
- [ ] Wrapped around app

---

## Phase 6: Polish & Testing (Day 5 - 4 hours)

### 6.1 Loading States (1 hour)
- [ ] Add skeleton loaders
- [ ] Add loading spinners
- [ ] Smooth transitions

### 6.2 Error Handling (1 hour)
- [ ] User-friendly error messages
- [ ] Retry mechanisms
- [ ] Toast notifications

### 6.3 Responsive Design (1 hour)
- [ ] Mobile layout
- [ ] Tablet layout
- [ ] Desktop optimization

### 6.4 Demo Scenarios (1 hour)
- [ ] Demo data generator
- [ ] Mock mode for offline demo
- [ ] Perfect demo flow

---

## 🎯 Daily Checkpoints

### End of Day 1
- [ ] Project setup complete
- [ ] Basic routing works
- [ ] API client connected
- [ ] Can see basic UI

### End of Day 2
- [ ] All core components built
- [ ] Agent cards render
- [ ] Activity feed works
- [ ] Upload flow functional

### End of Day 3
- [ ] State management working
- [ ] WebSocket connected
- [ ] Real-time updates
- [ ] Graph visualization

### End of Day 4
- [ ] Complete dashboard
- [ ] All features integrated
- [ ] End-to-end working
- [ ] UI polished

### End of Day 5
- [ ] Loading states added
- [ ] Error handling complete
- [ ] Responsive design done
- [ ] Demo ready

---

## 🚀 Quick Commands

```bash
# Development
npm run dev          # Start dev server
npm run build        # Build for production
npm run preview      # Preview production build
npm run lint         # Lint code

# Testing
npm test            # Run tests (when added)
```

---

## 📊 Component Hierarchy

```
App
├── Dashboard
│   ├── AgentCard (multiple)
│   ├── GraphView
│   └── ActivityFeed
└── Upload
    └── ProjectUpload
```

---

**Status**: Ready for Day 1 implementation 🚀
**Focus**: Build incrementally, test frequently!
