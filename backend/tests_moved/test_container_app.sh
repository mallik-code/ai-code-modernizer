#!/bin/bash

# Test script for Simple Express App running in Docker container
# Container: ai-modernizer-simple-express-app

CONTAINER="ai-modernizer-simple-express-app"
BASE_URL="http://localhost:3000"

echo "========================================"
echo "Testing Simple Express App in Docker"
echo "========================================"

# Check container status
echo -e "\n[1/8] Checking container status..."
docker ps --filter "name=$CONTAINER" --format "  Status: {{.Status}}"

# Check if Node.js is running
echo -e "\n[2/8] Checking if Node.js is running..."
PROCESS_COUNT=$(docker exec $CONTAINER sh -c "ps aux | grep -v grep | grep 'node index.js' | wc -l")
if [ "$PROCESS_COUNT" -gt "0" ]; then
    echo "  ✓ Node.js is running"
else
    echo "  ✗ Node.js not running - starting it..."
    docker exec -d $CONTAINER sh -c "cd /app && node index.js"
    sleep 2
fi

# Test root endpoint
echo -e "\n[3/8] Testing root endpoint (GET /)..."
RESULT=$(docker exec $CONTAINER sh -c "wget -qO- $BASE_URL/")
echo "  Response: $RESULT"

# Test health check
echo -e "\n[4/8] Testing health endpoint (GET /health)..."
RESULT=$(docker exec $CONTAINER sh -c "wget -qO- $BASE_URL/health")
echo "  Response: $RESULT"

# Test list users
echo -e "\n[5/8] Testing list users (GET /api/users)..."
RESULT=$(docker exec $CONTAINER sh -c "wget -qO- $BASE_URL/api/users")
echo "  Response: $RESULT"

# Test get user by ID
echo -e "\n[6/8] Testing get user by ID (GET /api/users/1)..."
RESULT=$(docker exec $CONTAINER sh -c "wget -qO- $BASE_URL/api/users/1")
echo "  Response: $RESULT"

# Test 404
echo -e "\n[7/8] Testing 404 handler (GET /notfound)..."
RESULT=$(docker exec $CONTAINER sh -c "wget -qO- $BASE_URL/notfound 2>&1")
echo "  Response: $RESULT"

# Test package.json
echo -e "\n[8/8] Checking package.json..."
docker exec $CONTAINER sh -c "cat /app/package.json | grep '\"name\"\\|\"version\"\\|\"express\"'" | head -5

echo -e "\n========================================"
echo "✓ All tests completed!"
echo "========================================"
echo ""
echo "To interact with the container:"
echo "  docker exec -it $CONTAINER sh"
echo ""
echo "To view logs:"
echo "  docker logs $CONTAINER"
echo ""
echo "To stop and remove:"
echo "  docker rm -f $CONTAINER"
echo ""
