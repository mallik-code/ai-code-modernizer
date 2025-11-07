# CLAUDE.md - Frontend

This file provides guidance to Claude Code (claude.ai/code) when working with the frontend codebase.

## Frontend Overview

React 18 + TypeScript application built with Vite. Provides real-time visualization of the multi-agent workflow, displaying agent thinking streams, graph state, and enabling human-in-the-loop decision points.

## Architecture

### Tech Stack
- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **TailwindCSS** - Utility-first styling
- **ReactFlow** - Graph visualization
- **Zustand** - State management
- **Axios** - HTTP client
- **React Router** - Routing

### Key Features
1. **Live Agent Visualization** - Real-time display of agent status and progress
2. **Graph Workflow Display** - Interactive ReactFlow graph showing agent connections
3. **Thinking Stream** - Live streaming of LLM reasoning process
4. **Human Decision Prompts** - Modal dialogs for approval/rejection
5. **Cost Tracking** - Display of token usage and API costs

### Component Architecture

**Pages** (`src/pages/`):
- `Dashboard.tsx` - Main dashboard with workflow overview
- `ProjectUpload.tsx` - Project submission interface
- `Results.tsx` - Migration results and summary

**Components** (`src/components/`):
- `AgentCard.tsx` - Individual agent status display (name, status, progress)
- `GraphView.tsx` - ReactFlow visualization of workflow graph
- `ThinkingStream.tsx` - Live stream of agent reasoning
- `DecisionModal.tsx` - Human approval interface
- `CostTracker.tsx` - Token usage and cost display

**Hooks** (`src/hooks/`):
- `useWebSocket.ts` - WebSocket connection management
- `useAgentState.ts` - Agent state synchronization
- `useWorkflow.ts` - Workflow tracking

**Utils** (`src/lib/`):
- `api.ts` - API client for backend communication
- `types.ts` - TypeScript type definitions
- `utils.ts` - Helper functions

## Development Commands

### Setup
```bash
cd frontend
npm install
```

### Running
```bash
npm run dev        # Start dev server (http://localhost:5173)
npm run build      # Build for production
npm run preview    # Preview production build
npm run lint       # Run ESLint
```

### Development Server
Vite dev server with:
- Hot Module Replacement (HMR)
- Fast refresh for React
- Instant server start
- Port: 5173

## Backend Communication

### REST API Client (`src/lib/api.ts`)
```typescript
import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';

export const api = {
  health: () => axios.get(`${API_BASE}/health`),
  analyzeProject: (formData: FormData) =>
    axios.post(`${API_BASE}/projects/analyze`, formData),
  startUpgrade: (projectId: string) =>
    axios.post(`${API_BASE}/projects/upgrade`, { projectId }),
  getStatus: (projectId: string) =>
    axios.get(`${API_BASE}/projects/${projectId}/status`),
};
```

### WebSocket Connection (`src/hooks/useWebSocket.ts`)
Connects to backend WebSocket for real-time updates:

```typescript
const {
  messages,      // Array of received messages
  sendMessage,   // Function to send message
  connected,     // Connection status
  error          // Connection error
} = useWebSocket('ws://localhost:8000/ws');
```

**Message Types from Backend:**
- `agent_update` - Agent status change
- `thinking_stream` - LLM reasoning chunk
- `graph_state` - Workflow state update
- `validation_result` - Docker validation complete
- `decision_required` - Human approval needed

## State Management with Zustand

Create stores for global state:

```typescript
// src/lib/store.ts
import { create } from 'zustand';

interface WorkflowState {
  agents: Agent[];
  currentStatus: string;
  updateAgent: (id: string, status: string) => void;
}

export const useWorkflowStore = create<WorkflowState>((set) => ({
  agents: [],
  currentStatus: 'idle',
  updateAgent: (id, status) =>
    set((state) => ({
      agents: state.agents.map(a =>
        a.id === id ? { ...a, status } : a
      )
    })),
}));
```

## ReactFlow Graph Visualization

Display LangGraph workflow as interactive graph:

```typescript
import ReactFlow, {
  Node,
  Edge,
  Background,
  Controls
} from 'reactflow';
import 'reactflow/dist/style.css';

const nodes: Node[] = [
  { id: 'planner', data: { label: 'Migration Planner' }, position: { x: 0, y: 0 } },
  { id: 'validator', data: { label: 'Runtime Validator' }, position: { x: 200, y: 0 } },
  // ...
];

const edges: Edge[] = [
  { id: 'e1-2', source: 'planner', target: 'validator' },
  // ...
];

function GraphView() {
  return (
    <ReactFlow nodes={nodes} edges={edges}>
      <Background />
      <Controls />
    </ReactFlow>
  );
}
```

**Dynamic Updates:**
- Highlight active node when agent is running
- Animate edges when state transitions
- Show error state with red highlighting
- Display retry arrows for error recovery

## TypeScript Types

Define types matching backend state:

```typescript
// src/lib/types.ts

export type AgentStatus = 'idle' | 'running' | 'success' | 'error';

export interface Agent {
  id: string;
  name: string;
  status: AgentStatus;
  progress: number;
  logs: string[];
}

export interface MigrationState {
  projectPath: string;
  dependencies: Record<string, string>;
  migrationStrategy?: MigrationStrategy;
  validationResult?: ValidationResult;
  errors: string[];
  retryCount: number;
  status: string;
}

export interface ValidationResult {
  success: boolean;
  logs: string[];
  errors: string[];
  metrics: {
    duration: number;
    memoryUsage: number;
  };
}
```

## Styling with TailwindCSS

Utility-first CSS framework configured in `tailwind.config.js`:

```typescript
// Component example
function AgentCard({ agent }: { agent: Agent }) {
  return (
    <div className="bg-white rounded-lg shadow-md p-4 border border-gray-200">
      <h3 className="text-lg font-semibold text-gray-800">{agent.name}</h3>
      <span className={`
        px-2 py-1 rounded text-sm
        ${agent.status === 'running' ? 'bg-blue-100 text-blue-800' : ''}
        ${agent.status === 'success' ? 'bg-green-100 text-green-800' : ''}
        ${agent.status === 'error' ? 'bg-red-100 text-red-800' : ''}
      `}>
        {agent.status}
      </span>
    </div>
  );
}
```

**Utility Pattern:**
- Use Tailwind utilities for spacing, colors, typography
- Create custom components for complex patterns
- Use `clsx` or `tailwind-merge` for conditional classes

## Real-Time Thinking Stream

Display LLM reasoning in real-time:

```typescript
function ThinkingStream({ messages }: { messages: string[] }) {
  const streamRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    streamRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="h-64 overflow-y-auto bg-gray-50 p-4 rounded">
      {messages.map((msg, i) => (
        <div key={i} className="text-sm text-gray-700 mb-2">
          {msg}
        </div>
      ))}
      <div ref={streamRef} />
    </div>
  );
}
```

## Human Decision Modal

Prompt user for approval/rejection:

```typescript
function DecisionModal({
  open,
  decision,
  onApprove,
  onReject
}: DecisionModalProps) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
      <div className="bg-white rounded-lg p-6 max-w-md">
        <h2 className="text-xl font-bold mb-4">Approval Required</h2>
        <p className="mb-4">{decision.message}</p>

        <div className="flex gap-2 justify-end">
          <button
            onClick={onReject}
            className="px-4 py-2 bg-gray-200 rounded hover:bg-gray-300"
          >
            Reject
          </button>
          <button
            onClick={onApprove}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Approve
          </button>
        </div>
      </div>
    </div>
  );
}
```

## Error Handling

Handle API and WebSocket errors gracefully:

```typescript
// API error handling
try {
  const response = await api.analyzeProject(formData);
  // Handle success
} catch (error) {
  if (axios.isAxiosError(error)) {
    // Handle API error
    console.error('API Error:', error.response?.data);
  }
}

// WebSocket reconnection
useEffect(() => {
  if (error) {
    console.error('WebSocket error:', error);
    // Attempt reconnection after delay
    setTimeout(() => reconnect(), 3000);
  }
}, [error]);
```

## Routing with React Router

```typescript
import { BrowserRouter, Routes, Route } from 'react-router-dom';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/upload" element={<ProjectUpload />} />
        <Route path="/results/:projectId" element={<Results />} />
      </Routes>
    </BrowserRouter>
  );
}
```

## Build Configuration

### Vite Config (`vite.config.ts`)
```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000',
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
    },
  },
});
```

### TypeScript Config (`tsconfig.json`)
Strict mode enabled for type safety.

## Icons with Lucide React

```typescript
import { PlayCircle, CheckCircle, XCircle, Loader } from 'lucide-react';

function StatusIcon({ status }: { status: AgentStatus }) {
  switch (status) {
    case 'running': return <Loader className="animate-spin" />;
    case 'success': return <CheckCircle className="text-green-500" />;
    case 'error': return <XCircle className="text-red-500" />;
    default: return <PlayCircle />;
  }
}
```

## Performance Optimization

- Use `React.memo()` for expensive components
- Lazy load routes with `React.lazy()`
- Debounce WebSocket message processing
- Virtualize long lists
- Optimize ReactFlow rendering with `useMemo()`

## Testing

```bash
npm test              # Run tests
npm run test:watch    # Watch mode
npm run test:coverage # With coverage
```

## Common Patterns

### Custom Hook Pattern
```typescript
function useAgentStatus(agentId: string) {
  const [status, setStatus] = useState<AgentStatus>('idle');

  // Subscribe to WebSocket updates
  useEffect(() => {
    const unsubscribe = subscribeToAgent(agentId, setStatus);
    return unsubscribe;
  }, [agentId]);

  return status;
}
```

### Component Composition
```typescript
function Dashboard() {
  return (
    <div className="container mx-auto p-4">
      <Header />
      <div className="grid grid-cols-2 gap-4">
        <AgentList />
        <GraphView />
      </div>
      <ThinkingStream />
      <CostTracker />
    </div>
  );
}
```

## Next Steps

Refer to `DEVELOPMENT_PLAN.md` Day 4-5 for frontend implementation tasks and integration with backend WebSocket API.
