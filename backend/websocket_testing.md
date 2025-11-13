# WebSocket Testing Instructions

The AI Code Modernizer API includes a WebSocket endpoint for real-time updates during migration workflows. This endpoint can't be tested directly in a standard Postman collection, so here are instructions for testing it:

## WebSocket Endpoint
- URL: `ws://localhost:8000/ws/migrations/{migration_id}`
- Replace `{migration_id}` with the actual migration ID from the `/api/migrations/start` endpoint response

## Test with a WebSocket Client

### Using Python WebSocket Client:
```python
import asyncio
import websockets
import json

async def test_websocket(migration_id):
    uri = f"ws://localhost:8000/ws/migrations/{migration_id}"
    
    async with websockets.connect(uri) as websocket:
        print(f"Connected to WebSocket for migration: {migration_id}")
        
        # Listen for messages
        async for message in websocket:
            try:
                data = json.loads(message)
                print(f"Received: {data}")
            except json.JSONDecodeError:
                print(f"Received: {message}")

# Usage after starting a migration:
# asyncio.run(test_websocket("mig_abc123def456"))
```

### Using wscat (npm package):
```bash
npm install -g wscat
wscat -c ws://localhost:8000/ws/migrations/MIGRATION_ID_HERE
```

### Example Message Format
The WebSocket sends JSON messages in this format:
```json
{
  "type": "agent_completion",
  "agent": "migration_planner",
  "status": "success",
  "message": "Migration plan created successfully",
  "dependencies_count": 5,
  "timestamp": "2023-10-27T10:30:00.123456"
}
```

## Message Types
- `connection`: When a client connects
- `workflow_start`: When the workflow begins
- `workflow_status`: Status updates about which agent is running
- `agent_completion`: When an agent completes (success or failure)
- `workflow_complete`: When the entire workflow completes
- `workflow_error`: If the workflow encounters an error
- `agent_thinking`: When an agent is using LLM to think
- `agent_thinking_complete`: When an agent completes thinking
- `tool_use`: When an agent uses a tool
- `tool_complete`: When a tool use completes
```

## Testing Workflow
1. Start a migration using the POST /api/migrations/start endpoint
2. Extract the migration ID from the response
3. Connect to the WebSocket endpoint with the migration ID
4. Start the migration workflow by triggering the background task
5. Observe real-time updates as the agents work