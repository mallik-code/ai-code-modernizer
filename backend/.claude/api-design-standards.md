# API Design Standards

## RESTful API Principles

### URL Structure
Follow RESTful conventions for URL design:

```python
# ✅ CORRECT - RESTful URL structure
from fastapi import APIRouter, Path, Query
from typing import Optional

router = APIRouter(prefix="/api/v1", tags=["projects"])

# Resource-based URLs
@router.post("/projects")  # Create new project
async def create_project(project: ProjectCreate):
    """Create a new project for analysis."""
    pass

@router.get("/projects/{project_id}")  # Get specific project
async def get_project(project_id: str = Path(..., description="Project ID")):
    """Get project details by ID."""
    pass

@router.get("/projects")  # List projects
async def list_projects(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """List all projects with pagination."""
    pass

@router.patch("/projects/{project_id}")  # Partial update
async def update_project(project_id: str, update: ProjectUpdate):
    """Update project details."""
    pass

@router.delete("/projects/{project_id}")  # Delete project
async def delete_project(project_id: str):
    """Delete a project."""
    pass

# Nested resources
@router.post("/projects/{project_id}/analyze")  # Action on resource
async def analyze_project(project_id: str):
    """Start analysis workflow for project."""
    pass

@router.get("/projects/{project_id}/upgrades")  # Related resource
async def get_project_upgrades(project_id: str):
    """Get upgrade recommendations for project."""
    pass

# ❌ INCORRECT - Non-RESTful URLs
@router.post("/createProject")  # Use POST /projects
@router.get("/getProjectById/{id}")  # Use GET /projects/{id}
@router.post("/analyzeProjectById/{id}")  # Use POST /projects/{id}/analyze
@router.get("/projectList")  # Use GET /projects
```

### HTTP Methods
Use appropriate HTTP methods:

```python
# ✅ CORRECT - Proper HTTP method usage
from fastapi import status

# GET - Safe and idempotent, no body
@router.get("/projects/{project_id}")
async def get_project(project_id: str):
    """Retrieve project (safe, cacheable)."""
    return {"project": project}

# POST - Not idempotent, has body, creates resource
@router.post("/projects", status_code=status.HTTP_201_CREATED)
async def create_project(project: ProjectCreate):
    """Create new project."""
    created = await db.create(project)
    return created

# PUT - Idempotent, replaces entire resource
@router.put("/projects/{project_id}")
async def replace_project(project_id: str, project: ProjectReplace):
    """Replace entire project."""
    return await db.replace(project_id, project)

# PATCH - Idempotent, partial update
@router.patch("/projects/{project_id}")
async def update_project(project_id: str, update: ProjectUpdate):
    """Partially update project."""
    return await db.update(project_id, update)

# DELETE - Idempotent, removes resource
@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: str):
    """Delete project."""
    await db.delete(project_id)
    return None

# ❌ INCORRECT - Wrong HTTP methods
@router.get("/projects/{id}/delete")  # Use DELETE method
@router.post("/projects/{id}/update")  # Use PUT or PATCH
@router.get("/projects/create")  # Use POST with body
```

## Request/Response Models

### Pydantic Models
Define clear input/output models:

```python
# ✅ CORRECT - Well-defined models
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from enum import Enum

class ProjectStatus(str, Enum):
    """Project status enum."""
    PENDING = "pending"
    ANALYZING = "analyzing"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"

class ProjectCreate(BaseModel):
    """Request model for creating a project."""
    name: str = Field(..., min_length=1, max_length=100, description="Project name")
    repository_url: str = Field(..., description="Git repository URL")
    branch: str = Field("main", description="Branch to analyze")
    include_dev_dependencies: bool = Field(True, description="Include dev dependencies")

    @validator("repository_url")
    def validate_repo_url(cls, v):
        """Validate repository URL format."""
        if not v.startswith(("https://", "git@")):
            raise ValueError("Invalid repository URL")
        return v

    class Config:
        schema_extra = {
            "example": {
                "name": "My Project",
                "repository_url": "https://github.com/user/repo",
                "branch": "main",
                "include_dev_dependencies": True
            }
        }

class ProjectResponse(BaseModel):
    """Response model for project details."""
    id: str = Field(..., description="Unique project ID")
    name: str
    repository_url: str
    branch: str
    status: ProjectStatus
    created_at: str
    updated_at: str

    class Config:
        orm_mode = True  # Allow ORM objects

class MigrationStrategy(BaseModel):
    """Migration strategy details."""
    phases: List[dict] = Field(default_factory=list)
    estimated_duration: int = Field(..., ge=0, description="Estimated duration in minutes")
    risk_level: str = Field(..., pattern="^(low|medium|high)$")
    dependencies_to_upgrade: List[str]

class AnalysisResponse(BaseModel):
    """Response for project analysis."""
    project_id: str
    status: str
    strategy: Optional[MigrationStrategy] = None
    message: str

class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Machine-readable error code")
    details: Optional[dict] = Field(None, description="Additional error details")
    request_id: str = Field(..., description="Request ID for tracking")

    class Config:
        schema_extra = {
            "example": {
                "error": "Project not found",
                "error_code": "PROJECT_NOT_FOUND",
                "details": {"project_id": "abc123"},
                "request_id": "req_xyz789"
            }
        }

# ❌ INCORRECT - Untyped or poorly defined models
class ProjectCreate(BaseModel):
    data: dict  # Too generic, no validation

class ProjectResponse(BaseModel):
    # Missing field descriptions and validation
    id: str
    stuff: dict
```

### Response Format
Standardize response structure:

```python
# ✅ CORRECT - Consistent response format
from typing import Generic, TypeVar, Optional
from pydantic import BaseModel

T = TypeVar('T')

class APIResponse(BaseModel, Generic[T]):
    """Standard API response wrapper."""
    success: bool
    data: Optional[T] = None
    error: Optional[ErrorResponse] = None
    metadata: Optional[dict] = None

# Success response
@router.get("/projects/{project_id}")
async def get_project(project_id: str) -> APIResponse[ProjectResponse]:
    """Get project details."""
    project = await db.get_project(project_id)

    if not project:
        return APIResponse(
            success=False,
            error=ErrorResponse(
                error="Project not found",
                error_code="PROJECT_NOT_FOUND",
                details={"project_id": project_id},
                request_id=get_request_id()
            )
        )

    return APIResponse(
        success=True,
        data=ProjectResponse.from_orm(project),
        metadata={"retrieved_at": datetime.utcnow().isoformat()}
    )

# List response with pagination
class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper."""
    success: bool
    data: List[T]
    pagination: dict

@router.get("/projects")
async def list_projects(
    limit: int = 10,
    offset: int = 0
) -> PaginatedResponse[ProjectResponse]:
    """List projects with pagination."""
    projects, total = await db.list_projects(limit, offset)

    return PaginatedResponse(
        success=True,
        data=[ProjectResponse.from_orm(p) for p in projects],
        pagination={
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total
        }
    )

# ❌ INCORRECT - Inconsistent responses
@router.get("/projects/{id}")
async def get_project(id: str):
    return project  # Sometimes dict, sometimes object

@router.get("/projects")
async def list_projects():
    return [...]  # No pagination info, no metadata
```

## Error Handling

### HTTP Status Codes
Use appropriate status codes:

```python
# ✅ CORRECT - Proper status codes
from fastapi import HTTPException, status

@router.post("/projects", status_code=status.HTTP_201_CREATED)
async def create_project(project: ProjectCreate):
    """Create project - returns 201 on success."""
    try:
        created = await db.create(project)
        return created
    except DuplicateError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Project already exists"
        )

@router.get("/projects/{project_id}")
async def get_project(project_id: str):
    """Get project - returns 404 if not found."""
    project = await db.get_project(project_id)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found"
        )

    return project

@router.patch("/projects/{project_id}")
async def update_project(project_id: str, update: ProjectUpdate):
    """Update project - returns 400 for invalid data."""
    try:
        updated = await db.update(project_id, update)
        return updated
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/projects/{project_id}/analyze")
async def analyze_project(project_id: str):
    """Start analysis - returns 202 for async operation."""
    task_id = await queue.enqueue_analysis(project_id)

    return {
        "task_id": task_id,
        "status": "accepted",
        "status_url": f"/api/v1/tasks/{task_id}"
    }

# Status code reference:
# 200 OK - Successful GET, PUT, PATCH, DELETE
# 201 Created - Successful POST creating resource
# 202 Accepted - Async operation started
# 204 No Content - Successful DELETE with no response body
# 400 Bad Request - Invalid request data
# 401 Unauthorized - Authentication required
# 403 Forbidden - Authenticated but not authorized
# 404 Not Found - Resource doesn't exist
# 409 Conflict - Resource conflict (duplicate, etc.)
# 422 Unprocessable Entity - Validation failed
# 429 Too Many Requests - Rate limit exceeded
# 500 Internal Server Error - Server error
# 503 Service Unavailable - Service temporarily unavailable
```

### Exception Handlers
Create global exception handlers:

```python
# ✅ CORRECT - Global exception handling
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import traceback

app = FastAPI()

class APIError(Exception):
    """Base API exception."""
    def __init__(self, message: str, status_code: int = 500, error_code: str = "INTERNAL_ERROR"):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(message)

class ResourceNotFoundError(APIError):
    """Resource not found."""
    def __init__(self, resource: str, resource_id: str):
        super().__init__(
            message=f"{resource} {resource_id} not found",
            status_code=404,
            error_code=f"{resource.upper()}_NOT_FOUND"
        )

@app.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError):
    """Handle custom API errors."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "message": exc.message,
                "error_code": exc.error_code,
                "request_id": request.state.request_id
            }
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(
        "unhandled_exception",
        error=str(exc),
        traceback=traceback.format_exc(),
        request_id=request.state.request_id
    )

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "message": "An unexpected error occurred",
                "error_code": "INTERNAL_ERROR",
                "request_id": request.state.request_id
            }
        }
    )
```

## Authentication and Authorization

```python
# ✅ CORRECT - API key authentication
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader
from typing import Optional

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def get_api_key(
    api_key: Optional[str] = Security(api_key_header)
) -> str:
    """Validate API key."""
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "ApiKey"}
        )

    # Validate key (check database, cache, etc.)
    if not await is_valid_api_key(api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )

    return api_key

# Protected endpoint
@router.post("/projects", dependencies=[Security(get_api_key)])
async def create_project(project: ProjectCreate):
    """Create project (requires API key)."""
    return await db.create(project)

# Role-based access control
async def require_role(required_role: str):
    """Dependency for role-based access."""
    async def role_checker(api_key: str = Security(get_api_key)):
        user = await get_user_from_api_key(api_key)

        if user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires {required_role} role"
            )

        return user

    return role_checker

@router.delete(
    "/projects/{project_id}",
    dependencies=[Depends(require_role("admin"))]
)
async def delete_project(project_id: str):
    """Delete project (admin only)."""
    await db.delete(project_id)
```

## Request Validation

```python
# ✅ CORRECT - Comprehensive validation
from pydantic import BaseModel, Field, validator, root_validator
from typing import List, Optional
import re

class ProjectCreate(BaseModel):
    """Project creation request."""
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Project name"
    )
    repository_url: str = Field(..., description="Git repository URL")
    branch: str = Field("main", regex="^[a-zA-Z0-9/_-]+$")
    dependencies: Optional[List[str]] = Field(None, max_items=100)

    @validator("name")
    def validate_name(cls, v):
        """Validate project name."""
        if not re.match(r"^[a-zA-Z0-9\s-]+$", v):
            raise ValueError("Name can only contain letters, numbers, spaces, and hyphens")
        return v.strip()

    @validator("repository_url")
    def validate_repo_url(cls, v):
        """Validate repository URL."""
        allowed_hosts = ["github.com", "gitlab.com", "bitbucket.org"]

        if not any(host in v for host in allowed_hosts):
            raise ValueError(f"Repository must be from: {', '.join(allowed_hosts)}")

        return v

    @root_validator
    def validate_project(cls, values):
        """Cross-field validation."""
        name = values.get("name")
        repo_url = values.get("repository_url")

        # Custom business logic
        if name and repo_url and name.lower() in repo_url.lower():
            values["name"] = name  # All good

        return values

    class Config:
        schema_extra = {
            "example": {
                "name": "My Project",
                "repository_url": "https://github.com/user/repo",
                "branch": "main",
                "dependencies": ["express", "lodash"]
            }
        }
```

## Rate Limiting

```python
# ✅ CORRECT - Rate limiting implementation
from fastapi import Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Global rate limit
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Apply rate limits."""
    response = await call_next(request)
    return response

# Per-endpoint rate limits
@router.post("/projects")
@limiter.limit("10/minute")  # 10 requests per minute
async def create_project(request: Request, project: ProjectCreate):
    """Create project with rate limit."""
    return await db.create(project)

@router.post("/projects/{project_id}/analyze")
@limiter.limit("5/minute")  # Expensive operation, lower limit
async def analyze_project(request: Request, project_id: str):
    """Start analysis with stricter rate limit."""
    return await queue.enqueue(project_id)

# Different limits for authenticated users
@router.get("/projects")
@limiter.limit("100/minute", key_func=lambda r: r.headers.get("X-API-Key", get_remote_address(r)))
async def list_projects(request: Request):
    """List projects with higher limit for authenticated users."""
    return await db.list_projects()
```

## API Versioning

```python
# ✅ CORRECT - URL-based versioning
from fastapi import APIRouter

# Version 1
v1_router = APIRouter(prefix="/api/v1", tags=["v1"])

@v1_router.get("/projects/{project_id}")
async def get_project_v1(project_id: str):
    """Get project (v1)."""
    return await db.get_project(project_id)

# Version 2 with breaking changes
v2_router = APIRouter(prefix="/api/v2", tags=["v2"])

@v2_router.get("/projects/{project_id}")
async def get_project_v2(project_id: str):
    """Get project (v2 - new response format)."""
    project = await db.get_project(project_id)
    # Return enhanced response
    return {
        "project": project,
        "metadata": {"version": "2.0"}
    }

# Register routers
app.include_router(v1_router)
app.include_router(v2_router)
```

## WebSocket Standards

```python
# ✅ CORRECT - WebSocket implementation
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json

class ConnectionManager:
    """Manage WebSocket connections."""

    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept WebSocket connection."""
        await websocket.accept()

        if client_id not in self.active_connections:
            self.active_connections[client_id] = set()

        self.active_connections[client_id].add(websocket)
        logger.info("websocket_connected", client_id=client_id)

    def disconnect(self, websocket: WebSocket, client_id: str):
        """Remove WebSocket connection."""
        if client_id in self.active_connections:
            self.active_connections[client_id].discard(websocket)

            if not self.active_connections[client_id]:
                del self.active_connections[client_id]

        logger.info("websocket_disconnected", client_id=client_id)

    async def send_personal_message(
        self,
        message: dict,
        client_id: str
    ):
        """Send message to specific client."""
        if client_id in self.active_connections:
            for connection in self.active_connections[client_id]:
                await connection.send_json(message)

    async def broadcast(self, message: dict):
        """Broadcast message to all connections."""
        for connections in self.active_connections.values():
            for connection in connections:
                await connection.send_json(message)

manager = ConnectionManager()

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time updates."""
    await manager.connect(websocket, client_id)

    try:
        while True:
            # Receive message
            data = await websocket.receive_text()
            message = json.loads(data)

            # Handle message
            await handle_websocket_message(message, client_id)

    except WebSocketDisconnect:
        manager.disconnect(websocket, client_id)
    except Exception as e:
        logger.error("websocket_error", client_id=client_id, error=str(e))
        manager.disconnect(websocket, client_id)
```

## API Documentation

```python
# ✅ CORRECT - Comprehensive API docs
from fastapi import FastAPI

app = FastAPI(
    title="AI Code Modernizer API",
    description="""
    API for autonomous code dependency upgrades.

    ## Features

    * **Project Analysis** - Analyze dependencies and identify upgrades
    * **Runtime Validation** - Test upgrades in Docker containers
    * **Automated Deployment** - Create PRs with validated changes

    ## Authentication

    Use API key in `X-API-Key` header for all requests.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "projects",
            "description": "Project management operations"
        },
        {
            "name": "analysis",
            "description": "Dependency analysis and upgrade planning"
        }
    ]
)

@router.post(
    "/projects",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["projects"],
    summary="Create new project",
    description="""
    Create a new project for dependency analysis.

    The project will be queued for analysis, and you can track
    progress via the WebSocket connection or status endpoint.
    """,
    responses={
        201: {
            "description": "Project created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "proj_abc123",
                        "name": "My Project",
                        "status": "pending"
                    }
                }
            }
        },
        400: {"description": "Invalid project data"},
        409: {"description": "Project already exists"},
        429: {"description": "Rate limit exceeded"}
    }
)
async def create_project(project: ProjectCreate):
    """Create new project."""
    return await db.create(project)
```

## API Standards Checklist

- [ ] RESTful URL structure (resource-based, not action-based)
- [ ] Appropriate HTTP methods (GET, POST, PUT, PATCH, DELETE)
- [ ] Proper HTTP status codes
- [ ] Pydantic models for request/response validation
- [ ] Consistent response format across all endpoints
- [ ] Global exception handling
- [ ] Authentication and authorization
- [ ] Rate limiting
- [ ] API versioning strategy
- [ ] Comprehensive OpenAPI documentation
- [ ] Request/response examples in docs
- [ ] WebSocket for real-time updates
- [ ] CORS configuration
- [ ] Request ID tracking
- [ ] Structured error responses
