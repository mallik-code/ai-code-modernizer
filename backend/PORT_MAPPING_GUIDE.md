# Docker Port Mapping Guide

## Overview

The AI Code Modernizer now automatically exposes application ports from Docker containers to the host machine, enabling direct browser access to deployed applications during and after validation.

**Status**: ✅ **IMPLEMENTED** (Commit: e8d3ae5)

---

## Automatic Port Mapping

### Default Ports

The system automatically maps standard application ports:

| Project Type | Container Port | Host Port | Protocol |
|--------------|---------------|-----------|----------|
| **Node.js**  | 3000          | 3000      | TCP      |
| **Python**   | 5000          | 5000      | TCP      |

### How It Works

When a Docker container is created during validation:

1. **Container Creation** (`tools/docker_tools.py:_create_container()`)
   ```python
   container = self.client.containers.create(
       image=image_name,
       name=container_name,
       command="tail -f /dev/null",
       working_dir=working_dir,
       detach=True,
       network_mode="bridge",
       ports={f'{app_port}/tcp': app_port}  # Port mapping
   )
   ```

2. **Port Selection**
   - Node.js projects: Port 3000 (Express default)
   - Python projects: Port 5000 (Flask/FastAPI default)

3. **Validation Result**
   ```python
   {
       "status": "success",
       "container_id": "999ff32f5b53",
       "container_name": "ai-modernizer-simple-express-app",
       "port": 3000,  # Exposed port
       "build_success": True,
       "install_success": True,
       "runtime_success": True,
       "health_check_success": True,
       "tests_run": True,
       "tests_passed": True
   }
   ```

---

## Accessing Applications

### During Development

After running a migration workflow:

```bash
python -m graph.workflow "tmp/projects/simple_express_app" nodejs
```

**Output:**
```
[INFO] container_created_with_port_mapping container_id=999ff32f5b53 port=3000
[INFO] validation_successful_with_tests test_summary='32 passed, 32 total'
```

**Browser Access:**
- **Node.js Apps**: http://localhost:3000
- **Python Apps**: http://localhost:5000

### Via API

When using the REST API:

```bash
# Start migration
curl -X POST http://localhost:8000/api/migrations/start \
  -H "Content-Type: application/json" \
  -d '{
    "project_path": "tmp/projects/simple_express_app",
    "project_type": "nodejs"
  }'

# Response
{
  "migration_id": "mig_abc123",
  "status": "started"
}

# Check status
curl http://localhost:8000/api/migrations/mig_abc123

# Response includes port
{
  "migration_id": "mig_abc123",
  "status": "deployed",
  "result": {
    "validation_result": {
      "port": 3000,
      "container_name": "ai-modernizer-simple-express-app"
    }
  }
}
```

**Access the app**: http://localhost:3000

---

## Testing Port Mapping

### Manual Test

```bash
cd backend

# Run port mapping test
python test_port_mapping.py
```

**Expected Output:**
```
================================================================================
PORT MAPPING TEST
================================================================================

1. Running Docker validation with port mapping...
2. Validation Results:
   Status: success
   Container ID: 999ff32f5b53
   Container Name: ai-modernizer-simple-express-app
   Port: 3000
   Tests Run: True
   Tests Passed: True

3. Testing browser access at http://localhost:3000...
   Response Status: 200
   Response Body: {'message': 'Welcome to the Legacy Express App'}

SUCCESS: Application is accessible from browser!

   You can now open your browser and visit:
   - http://localhost:3000/
   - http://localhost:3000/health
   - http://localhost:3000/api/users
```

### Verify Container

```bash
docker ps | grep ai-modernizer
```

**Output:**
```
999ff32f5b53   node:18-alpine   ...   0.0.0.0:3000->3000/tcp   ai-modernizer-simple-express-app
```

The `0.0.0.0:3000->3000/tcp` confirms port 3000 is mapped from container to host.

---

## Common Use Cases

### 1. Live Testing During Development

```bash
# Run validation
python -m graph.workflow "tmp/projects/my-app" nodejs

# Container starts with port mapped
# Open browser immediately: http://localhost:3000

# Test endpoints manually
curl http://localhost:3000/api/users
curl http://localhost:3000/health
```

### 2. Debugging Failed Migrations

```bash
# Set environment to keep containers
export DOCKER_CLEANUP_CONTAINERS=false

# Run migration
python -m graph.workflow "tmp/projects/my-app" nodejs

# If validation fails, container is kept running
# Access it in browser to debug: http://localhost:3000
```

### 3. Frontend Integration

When building a frontend that uses the API:

```bash
# Start migration via API
curl -X POST http://localhost:8000/api/migrations/start -d '...'

# Get container port from status
curl http://localhost:8000/api/migrations/mig_abc123 | jq '.result.validation_result.port'
# Output: 3000

# Frontend can now access: http://localhost:3000
```

---

## Port Conflicts

### Issue: Port Already in Use

If port 3000 (or 5000) is already in use on your host machine:

**Symptom:**
```
docker: Error response from daemon: driver failed programming external connectivity:
Bind for 0.0.0.0:3000 failed: port is already allocated
```

**Solutions:**

1. **Stop the conflicting process:**
   ```bash
   # Windows
   netstat -ano | findstr :3000
   taskkill /PID <PID> /F

   # Linux/Mac
   lsof -ti:3000 | xargs kill
   ```

2. **Use a different port** (future enhancement):
   ```python
   # Currently hardcoded, but can be made configurable
   validator = DockerValidator(port=3001)
   ```

3. **Stop existing containers:**
   ```bash
   docker stop $(docker ps -q --filter "name=ai-modernizer")
   ```

---

## Environment Variables

### Control Container Cleanup

```bash
# Keep containers after validation (for testing)
export DOCKER_CLEANUP_CONTAINERS=false

# Auto-cleanup containers (default)
export DOCKER_CLEANUP_CONTAINERS=true
```

When `DOCKER_CLEANUP_CONTAINERS=false`:
- Containers remain running after validation
- Ports stay exposed for browser access
- Useful for manual testing and debugging

When `DOCKER_CLEANUP_CONTAINERS=true`:
- Containers are automatically stopped and removed
- Ports are freed immediately
- Useful for CI/CD and automated testing

---

## Architecture Integration

### Workflow Integration

The port mapping is seamlessly integrated into the validation workflow:

```
Migration Planner
    ↓
Runtime Validator
    ↓ (creates container with port mapping)
    ├─ Install Dependencies
    ├─ Start Application
    ├─ Run Tests ✓
    └─ Port 3000 exposed ← NEW
    ↓
Application accessible at http://localhost:3000
    ↓
Staging Deployer
```

### API Integration

The FastAPI endpoints automatically include port information:

```python
@app.get("/api/migrations/{migration_id}")
async def get_migration_status(migration_id: str):
    migration = migrations_db[migration_id]
    return {
        "migration_id": migration_id,
        "status": migration["status"],
        "result": {
            "port": migration["result"]["validation_result"]["port"],  # Port info
            "container_name": migration["result"]["validation_result"]["container_name"]
        }
    }
```

---

## Benefits

### 1. **No Manual Intervention**
   - Previously: Had to manually recreate container with `-p 3000:3000`
   - Now: Automatic port exposure during validation

### 2. **Immediate Browser Access**
   - Test upgraded application in browser right away
   - Verify UI/UX changes visually
   - Debug issues interactively

### 3. **Consistent Experience**
   - Same port mapping for all projects of same type
   - Predictable URLs (always localhost:3000 for Node.js)
   - Easy to document and share

### 4. **Better Testing**
   - Automated tests verify port accessibility
   - End-to-end validation includes browser access
   - Reduces manual verification steps

---

## Troubleshooting

### Container Created but Not Accessible

**Check 1: Verify Port Mapping**
```bash
docker ps | grep ai-modernizer
# Should show: 0.0.0.0:3000->3000/tcp
```

**Check 2: Verify Application Started**
```bash
docker exec ai-modernizer-simple-express-app ps aux | grep node
# Should show: node index.js
```

**Check 3: Check Application Logs**
```bash
docker logs ai-modernizer-simple-express-app
# Should show: "Server running on port 3000"
```

**Check 4: Test from Inside Container**
```bash
docker exec ai-modernizer-simple-express-app curl -s http://localhost:3000
# Should return: {"message":"Welcome to..."}
```

### Port Mapping Not Working

If `docker ps` shows no port mapping:

1. **Check Docker version**
   ```bash
   docker --version
   # Need: Docker 20.10+
   ```

2. **Check network mode**
   ```bash
   docker inspect ai-modernizer-simple-express-app | grep NetworkMode
   # Should be: "bridge"
   ```

3. **Recreate container**
   ```bash
   docker stop ai-modernizer-simple-express-app
   docker rm ai-modernizer-simple-express-app
   python -m graph.workflow "tmp/projects/simple_express_app" nodejs
   ```

---

## Future Enhancements

### 1. **Configurable Ports**
```python
# Allow custom port specification
validator = DockerValidator(port=8080)
```

### 2. **Dynamic Port Assignment**
```python
# Find available port automatically
validator = DockerValidator(auto_port=True)
# Returns: "port": 3001 (if 3000 is taken)
```

### 3. **Multi-Service Support**
```python
# Map multiple ports for microservices
validator = DockerValidator(ports={
    "app": 3000,
    "db": 5432,
    "redis": 6379
})
```

### 4. **HTTPS Support**
```python
# Map HTTPS port
validator = DockerValidator(ssl=True, port=443)
```

---

## Related Documentation

- **TEST_EXECUTION_UPDATE.md** - Test execution in Docker
- **MIGRATION_INVOCATION_GUIDE.md** - All migration methods
- **QUICK_START_API.md** - API usage guide
- **tools/docker_tools.py** - Implementation details

---

**Last Updated**: 2025-11-12
**Commit**: e8d3ae5
**Status**: ✅ Production Ready
