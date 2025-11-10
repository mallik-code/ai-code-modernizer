# Docker Container Naming

## Overview

AI Code Modernizer automatically names Docker containers based on the project directory name, making it easy to identify and debug specific projects.

## Naming Convention

### Format
```
ai-modernizer-{project-name}
```

### Rules
- Project name is extracted from the last directory in the project path
- Converted to lowercase
- Underscores replaced with hyphens
- Only alphanumeric characters, hyphens, and underscores allowed

### Examples

| Project Path | Container Name |
|--------------|----------------|
| `/projects/simple-express-app` | `ai-modernizer-simple-express-app` |
| `/repos/MyApp` | `ai-modernizer-myapp` |
| `/code/legacy_system` | `ai-modernizer-legacy-system` |
| `C:\apps\user_service` | `ai-modernizer-user-service` |

## Usage

### Quick Commands

```bash
# Replace {project-name} with your project's directory name

# View container status
docker ps --filter "name=ai-modernizer-{project-name}"

# View logs
docker logs ai-modernizer-{project-name}

# Interactive shell
docker exec -it ai-modernizer-{project-name} sh

# Check running processes
docker exec ai-modernizer-{project-name} ps aux

# View files
docker exec ai-modernizer-{project-name} sh -c "ls -la /app"

# Stop and remove
docker rm -f ai-modernizer-{project-name}
```

### Real Example (simple-express-app)

```bash
# Check status
docker ps --filter "name=ai-modernizer-simple-express-app"

# Output:
# CONTAINER ID   NAMES                              STATUS        IMAGE
# 36b77fc6fb9a   ai-modernizer-simple-express-app   Up 2 minutes  node:18-alpine

# View application logs
docker logs ai-modernizer-simple-express-app

# Access shell
docker exec -it ai-modernizer-simple-express-app sh

# Inside container:
/app # ls -la
/app # cat package.json
/app # node --version
/app # npm list

# Check if Node app is running
docker exec ai-modernizer-simple-express-app sh -c "ps aux | grep node"

# Output:
# 48 root      0:00 node index.js

# View package.json without entering container
docker exec ai-modernizer-simple-express-app sh -c "cat /app/package.json"

# Clean up when done
docker rm -f ai-modernizer-simple-express-app
```

## Benefits

### Easy Identification
- No need to remember random container IDs
- Clear which project a container belongs to
- Easy to search and filter

### Simplified Commands
```bash
# Instead of:
docker logs 36b77fc6fb9a

# You can use:
docker logs ai-modernizer-simple-express-app
```

### Better DevOps
- Easy to identify containers in monitoring tools
- Simplified cleanup scripts
- Better logging and tracking

### Automatic Cleanup of Old Containers
When a new validation runs, any existing container with the same name is automatically removed and replaced. This prevents conflicts and ensures a fresh environment.

## Implementation Details

### Code Location
- File: `tools/docker_tools.py`
- Method: `_create_container()`
- Lines: ~197-220

### Key Logic
```python
# Generate container name from project path
project_name = Path(project_path).name
container_name = f"ai-modernizer-{project_name.lower().replace('_', '-')}"

# Remove any existing container with same name
try:
    old_container = self.client.containers.get(container_name)
    old_container.remove(force=True)
except Exception:
    pass

# Create container with name
container = self.client.containers.create(
    image=image_name,
    name=container_name,
    ...
)
```

### Logging
When containers are created or kept for debugging, the name is logged:

```
[info] container_created_with_name container_id=36b77fc6fb9a name=ai-modernizer-simple-express-app
[info] container_kept_for_debugging container_id=36b77fc6fb9a container_name=ai-modernizer-simple-express-app
```

## Troubleshooting

### Container Name Already Exists
If you see an error about the container name already existing, the old container will be automatically removed and replaced. If this fails:

```bash
# Manually remove the old container
docker rm -f ai-modernizer-{project-name}
```

### Finding All Modernizer Containers
```bash
# List all containers created by AI Modernizer
docker ps -a --filter "name=ai-modernizer-"

# Count them
docker ps -a --filter "name=ai-modernizer-" | wc -l

# Remove all of them
docker ps -a --filter "name=ai-modernizer-" -q | xargs docker rm -f
```

### Container Not Found
If the container name doesn't match expectations:
1. Check the actual project directory name: `basename "$(pwd)"`
2. Apply the naming rules (lowercase, replace underscores)
3. Prefix with `ai-modernizer-`

## Related Configuration

### Cleanup Configuration
Container naming works with the cleanup flag:

```bash
# .env
DOCKER_CLEANUP_CONTAINERS=false  # Keep containers with names
DOCKER_CLEANUP_CONTAINERS=true   # Remove containers after validation
```

When cleanup is disabled, containers remain running with their names, making it easy to debug later.

### See Also
- [Docker Cleanup Configuration](./docker-cleanup-configuration.md)
- [Runtime Validator Agent](../agents/runtime_validator.py)
- [Docker Tools](../tools/docker_tools.py)
