"""FastAPI application for AI Code Modernizer.

Provides REST API endpoints for triggering and monitoring dependency upgrades.
"""

import os
import uuid
from datetime import datetime
from typing import Optional, List
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from graph.workflow import run_workflow
from utils.logger import setup_logger

logger = setup_logger(__name__)

# ============================================================================
# FastAPI App Setup
# ============================================================================

app = FastAPI(
    title="AI Code Modernizer API",
    description="REST API for automated dependency upgrades with multi-agent workflow",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Data Models
# ============================================================================

class MigrationStartRequest(BaseModel):
    """Request model for starting a migration."""
    project_path: str = Field(..., description="Absolute or relative path to the project")
    project_type: str = Field(..., description="Project type: 'nodejs' or 'python'")
    max_retries: int = Field(default=3, ge=0, le=10, description="Maximum retry attempts for failed validations")
    options: Optional[dict] = Field(default_factory=dict, description="Additional options")

    model_config = {
        "json_schema_extra": {
            "example": {
                "project_path": "tmp/projects/simple_express_app",
                "project_type": "nodejs",
                "max_retries": 3,
                "options": {
                    "create_pr": True,
                    "run_tests": True
                }
            }
        }
    }


class MigrationStatusResponse(BaseModel):
    """Response model for migration status."""
    migration_id: str
    status: str  # started, running, deployed, error
    project_path: str
    project_type: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    result: Optional[dict] = None
    errors: List[str] = Field(default_factory=list)


class MigrationListResponse(BaseModel):
    """Response model for listing migrations."""
    total: int
    limit: int
    offset: int
    migrations: List[MigrationStatusResponse]


# ============================================================================
# In-Memory Storage (Replace with Database in Production)
# ============================================================================

# Store migration runs in memory
# In production, use Redis, PostgreSQL, or MongoDB
migrations_db: dict[str, dict] = {}

# Thread pool for async workflow execution
executor = ThreadPoolExecutor(max_workers=3)


# ============================================================================
# Background Task: Run Workflow
# ============================================================================

def run_workflow_task(migration_id: str, project_path: str, project_type: str, max_retries: int):
    """Run workflow in background thread.

    Args:
        migration_id: Unique migration ID
        project_path: Path to project
        project_type: Type of project
        max_retries: Max retry attempts
    """
    try:
        logger.info("starting_background_workflow",
                   migration_id=migration_id,
                   project_path=project_path)

        # Update status to running
        migrations_db[migration_id]["status"] = "running"

        # Execute workflow
        final_state = run_workflow(
            project_path=project_path,
            project_type=project_type,
            max_retries=max_retries
        )

        # Extract results
        result = {
            "workflow_status": final_state["status"],
            "validation_success": final_state.get("validation_success", False),
            "pr_url": final_state.get("pr_url"),
            "branch_name": final_state.get("branch_name"),
            "retry_count": final_state["retry_count"],
            "total_cost_usd": final_state["total_cost"],
            "agent_costs": final_state["agent_costs"]
        }

        # Add validation details if available
        if final_state.get("validation_result"):
            validation_data = final_state["validation_result"].get("validation_result", {})
            result.update({
                "tests_run": validation_data.get("tests_run", False),
                "tests_passed": validation_data.get("tests_passed", False),
                "test_summary": validation_data.get("logs", {}).get("tests", {}).get("test_summary", "N/A")
            })

        # Add migration plan details
        if final_state.get("migration_plan"):
            result["dependencies_upgraded"] = len(final_state["migration_plan"].get("dependencies", {}))
            result["overall_risk"] = final_state["migration_plan"].get("overall_risk")

        # Update database
        migrations_db[migration_id]["status"] = final_state["status"]
        migrations_db[migration_id]["result"] = result
        migrations_db[migration_id]["errors"] = final_state.get("errors", [])
        migrations_db[migration_id]["completed_at"] = datetime.utcnow()

        # Calculate duration
        start_time = migrations_db[migration_id]["started_at"]
        end_time = migrations_db[migration_id]["completed_at"]
        migrations_db[migration_id]["duration_seconds"] = int((end_time - start_time).total_seconds())

        logger.info("background_workflow_complete",
                   migration_id=migration_id,
                   status=final_state["status"],
                   cost=final_state["total_cost"])

    except Exception as e:
        logger.error("background_workflow_failed",
                    migration_id=migration_id,
                    error=str(e),
                    exc_info=True)

        # Update database with error
        migrations_db[migration_id]["status"] = "error"
        migrations_db[migration_id]["errors"] = [str(e)]
        migrations_db[migration_id]["completed_at"] = datetime.utcnow()


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "AI Code Modernizer API",
        "version": "1.0.0",
        "description": "REST API for automated dependency upgrades",
        "endpoints": {
            "docs": "/docs",
            "start_migration": "POST /api/migrations/start",
            "get_status": "GET /api/migrations/{migration_id}",
            "list_migrations": "GET /api/migrations"
        }
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    import docker

    # Check Docker availability
    try:
        client = docker.from_env()
        client.ping()
        docker_status = "healthy"
    except Exception as e:
        docker_status = f"unhealthy: {str(e)}"

    # Check API keys
    has_anthropic_key = bool(os.getenv("ANTHROPIC_API_KEY"))
    has_google_key = bool(os.getenv("GOOGLE_API_KEY"))
    has_github_token = bool(os.getenv("GITHUB_TOKEN"))

    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "docker": docker_status,
            "anthropic_api": "configured" if has_anthropic_key else "not_configured",
            "google_api": "configured" if has_google_key else "not_configured",
            "github_token": "configured" if has_github_token else "not_configured"
        },
        "migrations": {
            "total": len(migrations_db),
            "running": sum(1 for m in migrations_db.values() if m["status"] == "running"),
            "completed": sum(1 for m in migrations_db.values() if m["status"] in ["deployed", "error"])
        }
    }


@app.post("/api/migrations/start", status_code=202)
async def start_migration(request: MigrationStartRequest, background_tasks: BackgroundTasks):
    """Start a new migration workflow.

    Args:
        request: Migration start request
        background_tasks: FastAPI background tasks

    Returns:
        Migration ID and status

    Raises:
        HTTPException: If project path doesn't exist or validation fails
    """
    # Validate project path
    project_path = Path(request.project_path)
    if not project_path.exists():
        raise HTTPException(status_code=404, detail=f"Project path not found: {request.project_path}")

    # Validate project type
    if request.project_type not in ["nodejs", "python"]:
        raise HTTPException(status_code=400, detail="project_type must be 'nodejs' or 'python'")

    # Generate unique migration ID
    migration_id = f"mig_{uuid.uuid4().hex[:12]}"

    # Create migration record
    migration_record = {
        "migration_id": migration_id,
        "status": "started",
        "project_path": str(project_path.absolute()),
        "project_type": request.project_type,
        "max_retries": request.max_retries,
        "started_at": datetime.utcnow(),
        "completed_at": None,
        "duration_seconds": None,
        "result": None,
        "errors": []
    }

    migrations_db[migration_id] = migration_record

    logger.info("migration_started",
               migration_id=migration_id,
               project_path=request.project_path,
               project_type=request.project_type)

    # Start workflow in background
    background_tasks.add_task(
        run_workflow_task,
        migration_id,
        str(project_path.absolute()),
        request.project_type,
        request.max_retries
    )

    return {
        "migration_id": migration_id,
        "status": "started",
        "project_path": str(project_path.absolute()),
        "project_type": request.project_type,
        "started_at": migration_record["started_at"].isoformat(),
        "message": "Migration workflow started successfully. Use GET /api/migrations/{migration_id} to check status."
    }


@app.get("/api/migrations/{migration_id}")
async def get_migration_status(migration_id: str):
    """Get status of a specific migration.

    Args:
        migration_id: Unique migration ID

    Returns:
        Migration status and results

    Raises:
        HTTPException: If migration ID not found
    """
    if migration_id not in migrations_db:
        raise HTTPException(status_code=404, detail=f"Migration not found: {migration_id}")

    migration = migrations_db[migration_id]

    return {
        "migration_id": migration_id,
        "status": migration["status"],
        "project_path": migration["project_path"],
        "project_type": migration["project_type"],
        "started_at": migration["started_at"].isoformat(),
        "completed_at": migration["completed_at"].isoformat() if migration["completed_at"] else None,
        "duration_seconds": migration["duration_seconds"],
        "result": migration["result"],
        "errors": migration["errors"]
    }


@app.get("/api/migrations")
async def list_migrations(limit: int = 10, offset: int = 0):
    """List all migrations with pagination.

    Args:
        limit: Maximum number of results (default: 10)
        offset: Number of results to skip (default: 0)

    Returns:
        List of migrations with pagination info
    """
    # Get all migrations sorted by start time (newest first)
    all_migrations = sorted(
        migrations_db.values(),
        key=lambda m: m["started_at"],
        reverse=True
    )

    # Apply pagination
    paginated = all_migrations[offset:offset + limit]

    # Convert to response format
    migrations_list = [
        {
            "migration_id": m["migration_id"],
            "status": m["status"],
            "project_path": m["project_path"],
            "project_type": m["project_type"],
            "started_at": m["started_at"].isoformat(),
            "completed_at": m["completed_at"].isoformat() if m["completed_at"] else None,
            "duration_seconds": m["duration_seconds"]
        }
        for m in paginated
    ]

    return {
        "total": len(all_migrations),
        "limit": limit,
        "offset": offset,
        "migrations": migrations_list
    }


@app.delete("/api/migrations/{migration_id}")
async def delete_migration(migration_id: str):
    """Delete a migration record.

    Args:
        migration_id: Unique migration ID

    Returns:
        Success message

    Raises:
        HTTPException: If migration not found or still running
    """
    if migration_id not in migrations_db:
        raise HTTPException(status_code=404, detail=f"Migration not found: {migration_id}")

    migration = migrations_db[migration_id]

    if migration["status"] == "running":
        raise HTTPException(status_code=400, detail="Cannot delete running migration")

    del migrations_db[migration_id]

    logger.info("migration_deleted", migration_id=migration_id)

    return {
        "message": f"Migration {migration_id} deleted successfully"
    }


# ============================================================================
# Startup/Shutdown Events
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    logger.info("api_server_starting", version="1.0.0")
    logger.info("cors_origins", origins=os.getenv("CORS_ORIGINS", "http://localhost:5173"))


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    logger.info("api_server_shutdown")
    executor.shutdown(wait=False)


# ============================================================================
# CLI Mode (For Testing)
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    print("=" * 80)
    print("AI CODE MODERNIZER API SERVER")
    print("=" * 80)
    print()
    print("Starting FastAPI server...")
    print("  URL: http://localhost:8000")
    print("  Docs: http://localhost:8000/docs")
    print("  Health: http://localhost:8000/api/health")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 80)

    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
