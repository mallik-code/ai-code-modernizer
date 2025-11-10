# Docker Container Cleanup Configuration

## Overview

By default, the AI Code Modernizer automatically cleans up Docker containers after validation to prevent resource accumulation. However, for debugging purposes, you may want to keep containers running after validation.

## Configuration

### Environment Variable

Set `DOCKER_CLEANUP_CONTAINERS` in your `.env` file:

```bash
# Enable automatic cleanup (default)
DOCKER_CLEANUP_CONTAINERS=true

# Disable cleanup - keep containers for debugging
DOCKER_CLEANUP_CONTAINERS=false
```

### Accepted Values

The following values are recognized as "enabled":
- `true`
- `1`
- `yes`

Any other value (including `false`, `0`, `no`) disables cleanup.

## Usage

### Default Behavior (Cleanup Enabled)

```bash
# In .env
DOCKER_CLEANUP_CONTAINERS=true
```

When validation completes:
1. Container is created with Node.js/Python environment
2. Dependencies are installed
3. Application is started and tested
4. Health checks are performed
5. **Container is automatically stopped and removed**

Logs will show:
```
[info] cleaning_up_container container_id=abc123def456
```

### Debugging Mode (Cleanup Disabled)

```bash
# In .env
DOCKER_CLEANUP_CONTAINERS=false
```

When validation completes:
1. Container is created with Node.js/Python environment
2. Dependencies are installed
3. Application is started and tested
4. Health checks are performed
5. **Container is kept running for inspection**

Logs will show:
```
[info] container_kept_for_debugging container_id=abc123def456
```

## Container Naming Convention

Containers are automatically named based on the project directory:
- Format: `ai-modernizer-{project-name}`
- Example: For project at `tmp/projects/simple-express-app/`, container is named `ai-modernizer-simple-express-app`

This makes it easy to identify and interact with specific project containers.

## Inspecting Kept Containers

### List Running Containers

```bash
# List all containers
docker ps

# List specific project container
docker ps --filter "name=ai-modernizer-simple-express-app"
```

### Inspect Container Logs

```bash
# Using container name (recommended)
docker logs ai-modernizer-simple-express-app

# Using container ID
docker logs <container_id>
```

### Execute Commands in Container

```bash
# Interactive shell (using name)
docker exec -it ai-modernizer-simple-express-app sh

# Run specific commands
docker exec ai-modernizer-simple-express-app npm list
docker exec ai-modernizer-simple-express-app node --version
docker exec ai-modernizer-simple-express-app ps aux
```

### Check Application Files

```bash
# List files in /app directory
docker exec ai-modernizer-simple-express-app sh -c "ls -la /app"

# View package.json
docker exec ai-modernizer-simple-express-app sh -c "cat /app/package.json"

# Check if app is running
docker exec ai-modernizer-simple-express-app sh -c "ps aux | grep node"
```

### Manual Cleanup

When you're done debugging, manually remove the container:

```bash
# Using container name (recommended)
docker stop ai-modernizer-simple-express-app
docker rm ai-modernizer-simple-express-app

# Or force remove
docker rm -f ai-modernizer-simple-express-app

# Using container ID
docker stop <container_id>
docker rm <container_id>
```

## Programmatic Usage

You can also control cleanup behavior programmatically:

```python
from tools.docker_tools import DockerValidator

# Enable cleanup
validator = DockerValidator(cleanup_containers=True)

# Disable cleanup
validator = DockerValidator(cleanup_containers=False)

# Use environment variable (default)
validator = DockerValidator()  # Reads DOCKER_CLEANUP_CONTAINERS from .env
```

## Testing

Run the cleanup test script:

```bash
python test_docker_cleanup.py
```

This script:
1. Tests with cleanup enabled (container removed)
2. Tests with cleanup disabled (container kept)
3. Lists all remaining containers

## Best Practices

### Development

During development, set `DOCKER_CLEANUP_CONTAINERS=false` to:
- Inspect application state after validation
- Debug dependency installation issues
- Examine runtime errors
- Test health check configurations

### Production

In production, always set `DOCKER_CLEANUP_CONTAINERS=true` to:
- Prevent container accumulation
- Avoid resource exhaustion
- Maintain clean Docker environment

### CI/CD

In CI/CD pipelines, use `DOCKER_CLEANUP_CONTAINERS=true` and add cleanup step:

```bash
# After workflow
docker system prune -f
```

## Troubleshooting

### Too Many Containers

If you've accumulated many containers:

```bash
# List all stopped containers
docker ps -a

# Remove all stopped containers
docker container prune -f

# Remove containers by image
docker ps -a --filter "ancestor=node:18-alpine" -q | xargs docker rm -f
```

### Container Not Cleaning Up

If containers aren't cleaning up with `DOCKER_CLEANUP_CONTAINERS=true`:

1. Check the environment variable is set:
   ```bash
   python -c "import os; print(os.getenv('DOCKER_CLEANUP_CONTAINERS'))"
   ```

2. Verify the `.env` file is being loaded:
   ```python
   from dotenv import load_dotenv
   load_dotenv()
   ```

3. Check logs for cleanup errors:
   ```
   [warning] cleanup_failed error=...
   ```

### Disk Space Issues

If Docker is consuming too much disk space:

```bash
# Check disk usage
docker system df

# Clean everything (use with caution)
docker system prune -a --volumes
```

## Architecture Notes

### Implementation

The cleanup behavior is controlled in `tools/docker_tools.py`:

1. **Constructor** (`__init__`):
   - Reads `DOCKER_CLEANUP_CONTAINERS` environment variable
   - Defaults to `true` if not set
   - Stores as `self.cleanup_containers`

2. **Validation** (`validate_project`):
   - Creates container
   - Runs validation
   - In `finally` block: calls `_cleanup_container` if `self.cleanup_containers` is true

3. **Cleanup All** (`cleanup_all`):
   - Skips cleanup if `self.cleanup_containers` is false
   - Otherwise removes all tracked containers

4. **Destructor** (`__del__`):
   - Automatically calls `cleanup_all()` on object destruction
   - Only cleans up if `self.cleanup_containers` is true

### State Management

Containers are tracked in `self.containers` list:
- Added when created in `_create_container`
- Removed when cleaned in `_cleanup_container`
- All cleaned in `cleanup_all()` if cleanup is enabled

## Related Files

- `.env.example` - Example configuration with `DOCKER_CLEANUP_CONTAINERS`
- `tools/docker_tools.py` - Docker validation implementation
- `test_docker_cleanup.py` - Test script for cleanup behavior
- `agents/runtime_validator.py` - Uses DockerValidator
- `graph/workflow.py` - Workflow orchestration

## See Also

- [Docker Documentation](https://docs.docker.com/)
- [Docker SDK for Python](https://docker-py.readthedocs.io/)
- [Runtime Validator Agent](../agents/runtime_validator.py)
