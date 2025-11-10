# Testing Simple Express App

## Overview

The `simple-express-app` is a legacy Express.js application with outdated dependencies, created for testing the AI Code Modernizer workflow. It provides a simple REST API for user management.

## Application Details

### Technology Stack
- **Framework**: Express 4.16.0 (outdated)
- **Dependencies**: body-parser, cors, morgan, dotenv
- **Dev Dependencies**: nodemon
- **Port**: 3000 (default)

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Welcome message with version info |
| GET | `/health` | Health check endpoint |
| GET | `/api/users` | List all users |
| GET | `/api/users/:id` | Get user by ID |
| POST | `/api/users` | Create new user |
| PUT | `/api/users/:id` | Update user |
| DELETE | `/api/users/:id` | Delete user |

## Testing Methods

### Method 1: Test Inside Docker Container

When the container is kept for debugging (`DOCKER_CLEANUP_CONTAINERS=false`):

```bash
# Container name: ai-modernizer-simple-express-app

# 1. Check if app is running
docker exec ai-modernizer-simple-express-app ps aux | grep node

# 2. Test root endpoint
docker exec ai-modernizer-simple-express-app sh -c "wget -qO- http://localhost:3000/"

# Expected output:
# {"message":"Welcome to the Legacy Express App","version":"1.0.0","framework":"Express 4.16.0"}

# 3. Test health endpoint
docker exec ai-modernizer-simple-express-app sh -c "wget -qO- http://localhost:3000/health"

# Expected output:
# {"status":"healthy","timestamp":"2025-11-10T04:54:22.529Z","uptime":581.686370879}

# 4. Test users API
docker exec ai-modernizer-simple-express-app sh -c "wget -qO- http://localhost:3000/api/users"

# Expected output:
# {"success":true,"count":2,"users":[{"id":1,"name":"Alice","email":"alice@example.com"},{"id":2,"name":"Bob","email":"bob@example.com"}]}

# 5. Test specific user
docker exec ai-modernizer-simple-express-app sh -c "wget -qO- http://localhost:3000/api/users/1"

# Expected output:
# {"success":true,"user":{"id":1,"name":"Alice","email":"alice@example.com"}}

# 6. Test 404
docker exec ai-modernizer-simple-express-app sh -c "wget -qO- http://localhost:3000/notfound"

# Expected output:
# {"success":false,"error":"Route not found"}
```

### Method 2: Test with Port Mapping

If you want to access the app from your host machine, recreate the container with port mapping:

```bash
# Stop current container
docker stop ai-modernizer-simple-express-app

# Recreate with port mapping
docker run -d \
  --name ai-modernizer-simple-express-app \
  -p 3000:3000 \
  -v "$(pwd)/tmp/projects/simple_express_app:/app" \
  -w /app \
  node:18-alpine \
  sh -c "npm install && node index.js"

# Test from host machine
curl http://localhost:3000/
curl http://localhost:3000/health
curl http://localhost:3000/api/users
```

### Method 3: Run Locally

Run the app directly on your machine:

```bash
cd tmp/projects/simple_express_app

# Install dependencies
npm install

# Run the app
node index.js

# Or with nodemon for auto-reload
npm run dev
```

Then test with curl or browser:
```bash
curl http://localhost:3000/
curl http://localhost:3000/health
curl http://localhost:3000/api/users
```

### Method 4: Use Postman or Similar

Import these endpoints into Postman:

**Base URL**: `http://localhost:3000`

**Collection**:
```json
{
  "info": {
    "name": "Simple Express App",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Get Welcome",
      "request": {
        "method": "GET",
        "url": "{{base_url}}/"
      }
    },
    {
      "name": "Health Check",
      "request": {
        "method": "GET",
        "url": "{{base_url}}/health"
      }
    },
    {
      "name": "List Users",
      "request": {
        "method": "GET",
        "url": "{{base_url}}/api/users"
      }
    },
    {
      "name": "Get User by ID",
      "request": {
        "method": "GET",
        "url": "{{base_url}}/api/users/1"
      }
    },
    {
      "name": "Create User",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\"name\":\"Charlie\",\"email\":\"charlie@example.com\"}"
        },
        "url": "{{base_url}}/api/users"
      }
    },
    {
      "name": "Update User",
      "request": {
        "method": "PUT",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\"name\":\"Alice Updated\"}"
        },
        "url": "{{base_url}}/api/users/1"
      }
    },
    {
      "name": "Delete User",
      "request": {
        "method": "DELETE",
        "url": "{{base_url}}/api/users/2"
      }
    }
  ],
  "variable": [
    {
      "key": "base_url",
      "value": "http://localhost:3000"
    }
  ]
}
```

## Complete Test Suite

### Test Script (test_api.sh)

```bash
#!/bin/bash

BASE_URL="http://localhost:3000"

echo "Testing Simple Express App"
echo "=========================="

# Test 1: Root endpoint
echo -e "\n1. Testing root endpoint..."
curl -s $BASE_URL/ | jq '.'

# Test 2: Health check
echo -e "\n2. Testing health check..."
curl -s $BASE_URL/health | jq '.'

# Test 3: List users
echo -e "\n3. Listing users..."
curl -s $BASE_URL/api/users | jq '.'

# Test 4: Get user by ID
echo -e "\n4. Getting user by ID (1)..."
curl -s $BASE_URL/api/users/1 | jq '.'

# Test 5: Create new user
echo -e "\n5. Creating new user..."
curl -s -X POST $BASE_URL/api/users \
  -H "Content-Type: application/json" \
  -d '{"name":"Charlie","email":"charlie@example.com"}' | jq '.'

# Test 6: Update user
echo -e "\n6. Updating user (1)..."
curl -s -X PUT $BASE_URL/api/users/1 \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice Updated"}' | jq '.'

# Test 7: Delete user
echo -e "\n7. Deleting user (2)..."
curl -s -X DELETE $BASE_URL/api/users/2 | jq '.'

# Test 8: Verify deletion
echo -e "\n8. Listing users after deletion..."
curl -s $BASE_URL/api/users | jq '.'

# Test 9: 404 test
echo -e "\n9. Testing 404..."
curl -s $BASE_URL/notfound | jq '.'

echo -e "\n=========================="
echo "Tests complete!"
```

Make executable and run:
```bash
chmod +x test_api.sh
./test_api.sh
```

### Test Script for Docker Container

```bash
#!/bin/bash

CONTAINER="ai-modernizer-simple-express-app"

echo "Testing Simple Express App in Docker"
echo "====================================="

# Check container status
echo -e "\n0. Checking container status..."
docker ps --filter "name=$CONTAINER" --format "{{.Names}} - {{.Status}}"

# Check if app is running
echo -e "\n1. Checking if Node.js is running..."
docker exec $CONTAINER ps aux | grep -v grep | grep node

# Test root endpoint
echo -e "\n2. Testing root endpoint..."
docker exec $CONTAINER sh -c "wget -qO- http://localhost:3000/" | jq '.'

# Test health check
echo -e "\n3. Testing health check..."
docker exec $CONTAINER sh -c "wget -qO- http://localhost:3000/health" | jq '.'

# Test users API
echo -e "\n4. Listing users..."
docker exec $CONTAINER sh -c "wget -qO- http://localhost:3000/api/users" | jq '.'

# Test specific user
echo -e "\n5. Getting user by ID..."
docker exec $CONTAINER sh -c "wget -qO- http://localhost:3000/api/users/1" | jq '.'

echo -e "\n====================================="
echo "Tests complete!"
```

## Troubleshooting

### App Not Running

If the Node.js process is not running:

```bash
# Check processes
docker exec ai-modernizer-simple-express-app ps aux

# Check logs
docker logs ai-modernizer-simple-express-app

# Restart the app
docker exec -d ai-modernizer-simple-express-app sh -c "cd /app && node index.js"
```

### Connection Refused

If you get "Connection refused":

1. Check if app is listening on correct port:
   ```bash
   docker exec ai-modernizer-simple-express-app sh -c "netstat -tuln | grep 3000"
   ```

2. Check application logs:
   ```bash
   docker logs ai-modernizer-simple-express-app 2>&1 | grep -i error
   ```

3. Restart the application:
   ```bash
   docker exec ai-modernizer-simple-express-app sh -c "pkill node"
   docker exec -d ai-modernizer-simple-express-app sh -c "cd /app && node index.js"
   ```

### Port Already in Use

If port 3000 is already in use on your host:

```bash
# Find what's using port 3000
lsof -i :3000

# Or on Windows
netstat -ano | findstr :3000

# Use a different port
docker run -d -p 3001:3000 ...
```

### Dependencies Not Installed

```bash
# Install dependencies inside container
docker exec ai-modernizer-simple-express-app sh -c "cd /app && npm install"

# Check if node_modules exists
docker exec ai-modernizer-simple-express-app ls -la /app/node_modules
```

## Expected Test Results

### Successful Health Check
```json
{
  "status": "healthy",
  "timestamp": "2025-11-10T04:54:22.529Z",
  "uptime": 581.686370879
}
```

### Successful User List
```json
{
  "success": true,
  "count": 2,
  "users": [
    {
      "id": 1,
      "name": "Alice",
      "email": "alice@example.com"
    },
    {
      "id": 2,
      "name": "Bob",
      "email": "bob@example.com"
    }
  ]
}
```

### Successful User Creation
```json
{
  "success": true,
  "user": {
    "id": 3,
    "name": "Charlie",
    "email": "charlie@example.com"
  }
}
```

## Related Documentation

- [Docker Container Naming](./docker-container-naming.md)
- [Docker Cleanup Configuration](./docker-cleanup-configuration.md)
- [Runtime Validator](../agents/runtime_validator.py)
