"""FastAPI application for AI Code Modernizer.

Provides REST API endpoints for triggering and monitoring dependency upgrades.
"""

import os
import uuid
import glob
from datetime import datetime
from typing import Optional, List
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading

import json
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from fastapi import WebSocket, WebSocketDisconnect

from graph.workflow import run_workflow
from graph.helpers import create_initial_state_with_broadcaster
from utils.logger import setup_logger
from utils.report_generator import ReportGenerator
from api.websocket_manager import manager

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
# If CORS_ALLOW_ALL is set to true, allow all origins (for development only)
if os.getenv("CORS_ALLOW_ALL", "").lower() == "true":
    cors_origins = ["*"]
    allow_credentials = False
else:
    # Default to allowing common local development origins including React dev servers
    cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000,http://localhost:4000,http://127.0.0.1:5500,http://localhost:5500").split(",")
    allow_credentials = True

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Data Models
# ============================================================================

class MigrationStartRequest(BaseModel):
    """Request model for starting a migration."""
    project_path: Optional[str] = Field(default=None, description="Absolute or relative path to the local project (required if git_repo_url not provided)")
    git_repo_url: Optional[str] = Field(default=None, description="URL of Git repository to clone (required if project_path not provided)")
    project_type: str = Field(..., description="Project type: 'nodejs' or 'python'")
    max_retries: int = Field(default=3, ge=0, le=10, description="Maximum retry attempts for failed validations")
    git_branch: str = Field(default="main", description="Git branch to use for the migration (default: main)")
    github_token: Optional[str] = Field(default=None, description="GitHub Personal Access Token for API operations (optional)")
    force_fresh_clone: bool = Field(default=False, description="Force fresh clone of the repository (default: False)")
    options: Optional[dict] = Field(default_factory=dict, description="Additional options")

    model_config = {
        "json_schema_extra": {
            "example": {
                "git_repo_url": "https://github.com/user/repo.git",
                "git_branch": "main",
                "github_token": "ghp_xxxxxxxxxxxxx",
                "project_type": "nodejs",
                "max_retries": 3,
                "force_fresh_clone": False,
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

# Report generator
report_generator = ReportGenerator(output_dir="reports")


# ============================================================================
# Background Task: Run Workflow
# ============================================================================

def run_workflow_task(migration_id: str, project_path: str, project_type: str, max_retries: int, git_branch: str = "main", github_token: Optional[str] = None):
    """Run workflow in background thread.

    Args:
        migration_id: Unique migration ID
        project_path: Path to project
        project_type: Type of project
        max_retries: Max retry attempts
        git_branch: Git branch to use for the migration (default: main)
        github_token: GitHub Personal Access Token for API operations (optional)
    """
    is_cloned_repo = migrations_db[migration_id].get("original_repo_url") is not None

    try:
        logger.info("starting_background_workflow",
                   migration_id=migration_id,
                   project_path=project_path,
                   git_branch=git_branch,
                   has_github_token=bool(github_token),
                   is_cloned_repo=is_cloned_repo)

        # Update status to running
        migrations_db[migration_id]["status"] = "running"

        # Create a partial function for broadcasting
        def broadcast_update(msg):
            # Since this runs in a thread, we need to handle event loops properly
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.run_coroutine_threadsafe(
                        manager.broadcast(msg, migration_id),
                        loop
                    )
                else:
                    # If loop is not running, run it briefly
                    asyncio.run(manager.broadcast(msg, migration_id))
            except RuntimeError:
                # If there's no running loop, create a temporary one
                asyncio.run(manager.broadcast(msg, migration_id))

        # Execute workflow with broadcaster
        final_state = run_workflow(
            project_path=project_path,
            project_type=project_type,
            max_retries=max_retries,
            git_branch=git_branch,
            github_token=github_token,
            broadcaster=broadcast_update
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

        # Generate comprehensive reports
        try:
            project_name = Path(project_path).name
            report_paths = report_generator.generate_all_reports(final_state, project_name)

            # Store report paths in migration record
            migrations_db[migration_id]["reports"] = {
                "html": f"/api/migrations/{migration_id}/report?type=html",
                "markdown": f"/api/migrations/{migration_id}/report?type=markdown",
                "json": f"/api/migrations/{migration_id}/report?type=json"
            }
            migrations_db[migration_id]["report_files"] = report_paths

            logger.info("reports_generated",
                       migration_id=migration_id,
                       reports=list(report_paths.keys()))
        except Exception as e:
            logger.warning("report_generation_failed",
                          migration_id=migration_id,
                          error=str(e))

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

    finally:
        # Clean up cloned repository if applicable
        if is_cloned_repo:
            try:
                import shutil
                shutil.rmtree(project_path, ignore_errors=True)
                logger.info("cloned_repo_cleaned_up",
                           migration_id=migration_id,
                           project_path=project_path)
            except Exception as e:
                logger.error("cloned_repo_cleanup_failed",
                            migration_id=migration_id,
                            project_path=project_path,
                            error=str(e))


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
    from utils.git_utils import clone_repository, get_repo_name_from_url, is_valid_git_repo_url
    import subprocess

    # Validate that either project_path or git_repo_url is provided
    if not request.project_path and not request.git_repo_url:
        raise HTTPException(status_code=400, detail="Either project_path or git_repo_url must be provided")

    if request.project_path and request.git_repo_url:
        raise HTTPException(status_code=400, detail="Only one of project_path or git_repo_url should be provided")

    # Validate project type
    if request.project_type not in ["nodejs", "python"]:
        raise HTTPException(status_code=400, detail="project_type must be 'nodejs' or 'python'")

    # Generate unique migration ID
    migration_id = f"mig_{uuid.uuid4().hex[:12]}"

    # Create migration record with status history
    migration_record = {
        "migration_id": migration_id,
        "status": "initializing",
        "project_path": "",
        "project_type": request.project_type,
        "max_retries": request.max_retries,
        "started_at": datetime.utcnow(),
        "completed_at": None,
        "duration_seconds": None,
        "result": None,
        "errors": [],
        "original_repo_url": request.git_repo_url,  # Store original repo URL if provided
        "status_history": []  # History of status updates
    }

    migrations_db[migration_id] = migration_record

    # If git_repo_url is provided, clone the repository
    if request.git_repo_url:
        # Validate the Git repository URL
        if not is_valid_git_repo_url(request.git_repo_url):
            raise HTTPException(status_code=400, detail=f"Invalid Git repository URL: {request.git_repo_url}")

        # Clone the repository to a temporary directory
        cloned_project_path = f"cloned_repos/{get_repo_name_from_url(request.git_repo_url)}_{uuid.uuid4().hex[:8]}"

        # Send WebSocket update about starting clone
        # Create a temporary broadcaster to send updates during cloning
        def create_temp_broadcast(mid):
            def temp_broadcast(msg):
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.run_coroutine_threadsafe(
                            manager.broadcast(msg, mid),
                            loop
                        )
                    else:
                        asyncio.run(manager.broadcast(msg, mid))
                except RuntimeError:
                    asyncio.run(manager.broadcast(msg, mid))
            return temp_broadcast

        temp_broadcast = create_temp_broadcast(migration_id)

        # Create and send the starting clone message
        clone_start_msg = {
            "type": "workflow_status",
            "agent": "system",
            "message": f"Starting to clone repository from {request.git_repo_url}",
            "timestamp": datetime.now().isoformat(),
            "extra_data": {
                "status": "cloning_repository",
                "repo_url": request.git_repo_url
            }
        }

        # Add to status history
        migrations_db[migration_id]["status_history"].append(clone_start_msg)
        temp_broadcast(json.dumps(clone_start_msg))

        success = clone_repository(
            repo_url=request.git_repo_url,
            local_path=cloned_project_path,
            branch=request.git_branch,
            github_token=request.github_token,
            force_fresh_clone=request.force_fresh_clone
        )

        if not success:
            # Send WebSocket update about clone failure
            clone_error_msg = {
                "type": "workflow_error",
                "agent": "system",
                "message": f"Failed to clone repository from {request.git_repo_url}",
                "timestamp": datetime.now().isoformat(),
                "extra_data": {
                    "status": "clone_failed",
                    "repo_url": request.git_repo_url
                }
            }

            # Add to status history
            migrations_db[migration_id]["status_history"].append(clone_error_msg)
            temp_broadcast(json.dumps(clone_error_msg))

            # If cloning failed, provide specific guidance for private repository access
            from utils.git_utils import handle_git_permission_errors
            permission_help = handle_git_permission_errors(request.git_repo_url, request.github_token)

            # Create a more informative error message
            error_msg = f"Failed to clone repository: {request.git_repo_url}\n\n{permission_help}"
            raise HTTPException(status_code=500, detail=error_msg)

        # Send WebSocket update about successful clone
        clone_success_msg = {
            "type": "workflow_status",
            "agent": "system",
            "message": f"Successfully cloned repository from {request.git_repo_url} to {cloned_project_path}",
            "timestamp": datetime.now().isoformat(),
            "extra_data": {
                "status": "repository_cloned",
                "repo_url": request.git_repo_url,
                "local_path": cloned_project_path
            }
        }

        # Add to status history
        migrations_db[migration_id]["status_history"].append(clone_success_msg)
        temp_broadcast(json.dumps(clone_success_msg))

        project_path = Path(cloned_project_path)
        logger.info("repository_cloned",
                   repo_url=request.git_repo_url,
                   local_path=str(project_path),
                   branch=request.git_branch)
    else:
        # Use local project path
        project_path = Path(request.project_path)
        if not project_path.exists():
            raise HTTPException(status_code=404, detail=f"Project path not found: {request.project_path}")

        # Checkout the specified branch if the directory is a git repository
        if request.git_branch:
            try:
                # Check if it's a git repository
                git_dir = project_path / ".git"
                if git_dir.exists():
                    # Change to project directory and checkout the specified branch
                    result = subprocess.run(
                        ["git", "checkout", request.git_branch],
                        cwd=project_path,
                        capture_output=True,
                        text=True,
                        timeout=30
                    )

                    if result.returncode != 0:
                        # If checkout fails, try fetching the branch first
                        fetch_result = subprocess.run(
                            ["git", "fetch", "origin", request.git_branch],
                            cwd=project_path,
                            capture_output=True,
                            text=True,
                            timeout=30
                        )

                        if fetch_result.returncode == 0:
                            # Try checkout again after fetch
                            result = subprocess.run(
                                ["git", "checkout", request.git_branch],
                                cwd=project_path,
                                capture_output=True,
                                text=True,
                                timeout=30
                            )

                    if result.returncode != 0:
                        logger.warning("branch_checkout_failed",
                                     branch=request.git_branch,
                                     project_path=str(project_path),
                                     error=result.stderr)
                        # We'll continue anyway as this might not be critical for all use cases
                    else:
                        logger.info("branch_checked_out",
                                   branch=request.git_branch,
                                   project_path=str(project_path))
                        # Also pull latest changes for the branch
                        pull_result = subprocess.run(
                            ["git", "pull", "origin", request.git_branch],
                            cwd=project_path,
                            capture_output=True,
                            text=True,
                            timeout=30
                        )
                        if pull_result.returncode == 0:
                            logger.info("branch_pulled",
                                       branch=request.git_branch,
                                       project_path=str(project_path))
                else:
                    logger.info("not_a_git_repository", project_path=str(project_path))
            except subprocess.TimeoutExpired:
                logger.warning("git_operation_timeout",
                              operation="checkout",
                              branch=request.git_branch,
                              project_path=str(project_path))
            except Exception as e:
                logger.warning("git_operation_error",
                              error=str(e),
                              operation="checkout",
                              branch=request.git_branch,
                              project_path=str(project_path))

    # Update migration record with determined project_path
    migrations_db[migration_id]["project_path"] = str(project_path.absolute())
    migrations_db[migration_id]["status"] = "started"

    logger.info("migration_started",
               migration_id=migration_id,
               project_path=str(project_path.absolute()),
               project_type=request.project_type,
               git_repo_url=request.git_repo_url)

    # Start workflow in background
    background_tasks.add_task(
        run_workflow_task,
        migration_id,
        str(project_path.absolute()),
        request.project_type,
        request.max_retries,
        request.git_branch,
        request.github_token
    )

    return {
        "migration_id": migration_id,
        "status": "started",
        "project_path": str(project_path.absolute()),
        "project_type": request.project_type,
        "git_repo_url": request.git_repo_url,
        "started_at": migration_record["started_at"].isoformat(),
        "message": "Migration workflow started successfully. Use GET /api/migrations/{migration_id} to check status."
    }


@app.get("/api/migrations/{migration_id}")
async def get_migration_status(migration_id: str):
    """Get status of a specific migration.

    Args:
        migration_id: Unique migration ID

    Returns:
        Migration status and results with report download links

    Raises:
        HTTPException: If migration ID not found
    """
    if migration_id not in migrations_db:
        raise HTTPException(status_code=404, detail=f"Migration not found: {migration_id}")

    migration = migrations_db[migration_id]

    response = {
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

    # Add report download links if available
    if migration.get("reports"):
        response["reports"] = migration["reports"]
    elif migration["status"] in ["deployed", "error"]:
        # If migration is complete but reports key is missing, check for report files
        project_name = Path(migration["project_path"]).name
        report_pattern = f"reports/{project_name}_migration_report_*.html"
        matching_reports = sorted(glob.glob(report_pattern), key=lambda x: Path(x).stat().st_mtime, reverse=True)

        if matching_reports:
            # Use the most recent report
            base_name = Path(matching_reports[0]).stem
            response["reports"] = {
                "html": f"/api/migrations/{migration_id}/report?type=html",
                "markdown": f"/api/migrations/{migration_id}/report?type=markdown",
                "json": f"/api/migrations/{migration_id}/report?type=json"
            }
            # Store in migration record for future requests
            migrations_db[migration_id]["reports"] = response["reports"]
            migrations_db[migration_id]["report_files"] = {
                "html": matching_reports[0],
                "markdown": matching_reports[0].replace('.html', '.md'),
                "json": matching_reports[0].replace('.html', '.json')
            }

    # Add report content API links (individual format endpoints)
    if migration.get("report_files"):
        response["reports_content"] = {
            "html": f"/api/migrations/{migration_id}/report_content?type=html",
            "markdown": f"/api/migrations/{migration_id}/report_content?type=markdown",
            "json": f"/api/migrations/{migration_id}/report_content?type=json"
        }

    return response


@app.get("/api/migrations/{migration_id}/content")
async def get_migration_content(migration_id: str, type: str = "all"):
    """Get content of migration reports.

    Args:
        migration_id: Unique migration ID
        type: Report type - 'html', 'markdown', 'json', or 'all' (default: 'all')

    Returns:
        Content of requested report format(s)

    Raises:
        HTTPException: If migration ID not found or reports not available
    """
    if migration_id not in migrations_db:
        raise HTTPException(status_code=404, detail=f"Migration not found: {migration_id}")

    migration = migrations_db[migration_id]

    # Check if reports are available
    if not migration.get("report_files"):
        raise HTTPException(
            status_code=404,
            detail="Report files not available yet. Migration may still be running or failed before completion."
        )

    # Validate report type
    valid_types = ["html", "markdown", "json", "all"]
    if type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid report type. Must be one of: {', '.join(valid_types)}"
        )

    if type == "all":
        report_content = {
            "html": "",
            "markdown": "",
            "json": ""
        }

        # Read all report files content
        report_files = migration["report_files"]
        
        for format_type, file_path in report_files.items():
            try:
                if Path(file_path).exists():
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                        # Store content based on file extension
                        if file_path.endswith('.html'):
                            report_content['html'] = content
                        elif file_path.endswith('.md'):
                            report_content['markdown'] = content
                        elif file_path.endswith('.json'):
                            report_content['json'] = content
            except Exception as e:
                logger.warning(f"Error reading report file: {e}")
        
        return {
            "migration_id": migration_id,
            "status": migration["status"],
            "content": report_content
        }
    else:
        # Return content for specific type only
        report_files = migration["report_files"]
        file_path = report_files.get(type)
        
        if not file_path or not Path(file_path).exists():
            raise HTTPException(status_code=404, detail=f"Report file not found for type: {type}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            return {
                "migration_id": migration_id,
                "status": migration["status"],
                "type": type,
                "content": content
            }
        except Exception as e:
            logger.error(f"Error reading {type} report file: {e}")
            raise HTTPException(status_code=500, detail=f"Error reading {type} report file")


@app.get("/api/migrations/{migration_id}/report_content")
async def get_migration_report_content(migration_id: str, type: str = "html"):
    """Get content of a specific migration report format.

    This endpoint returns the actual content of the report in the requested format,
    suitable for direct display in the browser.

    Args:
        migration_id: Unique migration ID
        type: Report type - 'html', 'markdown', or 'json' (default: 'html')

    Returns:
        JSON response with report content

    Raises:
        HTTPException: If migration ID not found or reports not available
    """
    if migration_id not in migrations_db:
        raise HTTPException(status_code=404, detail=f"Migration not found: {migration_id}")

    migration = migrations_db[migration_id]

    # Check if reports are available
    if not migration.get("report_files"):
        raise HTTPException(
            status_code=404,
            detail="Report files not available yet. Migration may still be running or failed before completion."
        )

    # Validate report type
    valid_types = ["html", "markdown", "json"]
    if type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid report type. Must be one of: {', '.join(valid_types)}"
        )

    # Get file path
    report_files = migration["report_files"]
    file_path = report_files.get(type)

    if not file_path or not Path(file_path).exists():
        raise HTTPException(status_code=404, detail=f"Report file not found for type: {type}")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        return {
            "migration_id": migration_id,
            "status": migration["status"],
            "type": type,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error reading {type} report file: {e}")
        raise HTTPException(status_code=500, detail=f"Error reading {type} report file: {str(e)}")


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


@app.get("/api/migrations/{migration_id}/report")
async def download_migration_report(migration_id: str, type: str = "html"):
    """Download migration report in specified format.

    Args:
        migration_id: Unique migration ID
        type: Report type - 'html', 'markdown', or 'json' (default: 'html')

    Returns:
        File download response

    Raises:
        HTTPException: If migration not found or report not available
    """
    if migration_id not in migrations_db:
        raise HTTPException(status_code=404, detail=f"Migration not found: {migration_id}")

    migration = migrations_db[migration_id]

    # Check if reports are available
    if not migration.get("report_files"):
        raise HTTPException(
            status_code=404,
            detail="Report not available yet. Migration may still be running or failed before completion."
        )

    # Validate report type
    valid_types = ["html", "markdown", "json"]
    if type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid report type. Must be one of: {', '.join(valid_types)}"
        )

    # Get file path
    report_file = migration["report_files"].get(type)
    if not report_file or not Path(report_file).exists():
        raise HTTPException(status_code=404, detail=f"Report file not found: {type}")

    # Determine media type and filename extension
    media_types = {
        "html": "text/html",
        "markdown": "text/markdown",
        "json": "application/json"
    }

    extensions = {
        "html": ".html",
        "markdown": ".md",
        "json": ".json"
    }

    project_name = Path(migration["project_path"]).name
    filename = f"{project_name}_migration_report{extensions[type]}"

    logger.info("report_downloaded",
               migration_id=migration_id,
               report_type=type,
               filename=filename)

    return FileResponse(
        path=report_file,
        media_type=media_types[type],
        filename=filename
    )


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
# WebSocket Endpoint
# ============================================================================

@app.websocket("/ws/migrations/{migration_id}")
async def migration_progress(websocket: WebSocket, migration_id: str):
    """WebSocket endpoint for real-time migration updates."""
    await manager.connect(websocket, migration_id)
    try:
        # Check if migration exists in DB and send initial status
        if migration_id in migrations_db:
            migration_record = migrations_db[migration_id]
            # Send initial status based on current migration state
            initial_status_msg = {
                "type": "workflow_status",
                "agent": "system",
                "message": f"Connected to migration {migration_id} (Status: {migration_record['status']})",
                "timestamp": datetime.now().isoformat(),
                "extra_data": {
                    "status": migration_record["status"],
                    "project_path": migration_record["project_path"],
                    "git_repo_url": migration_record.get("original_repo_url")
                }
            }

            # Send the status history (if any) to catch up client on previous events
            for status_msg in migration_record.get("status_history", []):
                await websocket.send_text(json.dumps(status_msg))

            # If this was a git repo clone, send information about it
            if migration_record.get("original_repo_url"):
                clone_info_msg = {
                    "type": "workflow_status",
                    "agent": "system",
                    "message": f"Repository cloned from {migration_record['original_repo_url']} to {migration_record['project_path']}",
                    "timestamp": datetime.now().isoformat(),
                    "extra_data": {
                        "status": "repository_cloned_info",
                        "repo_url": migration_record["original_repo_url"],
                        "local_path": migration_record["project_path"]
                    }
                }
                await websocket.send_text(json.dumps(clone_info_msg))
        else:
            initial_status_msg = {
                "type": "connection",
                "message": "Connected to migration updates",
                "migration_id": migration_id,
                "timestamp": datetime.now().isoformat()
            }

        await websocket.send_text(json.dumps(initial_status_msg))

        while True:
            # Listen for incoming messages from client
            data = await websocket.receive_text()
            # Could handle client messages here if needed, for now just acknowledge
            # In a more complex implementation, this could include commands to the server
    except WebSocketDisconnect:
        manager.disconnect(websocket, migration_id)
        logger.info(f"WebSocket disconnected for migration {migration_id}")


# ============================================================================
# Startup/Shutdown Events
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    logger.info("api_server_starting", version="1.0.0")
    
    # Check for CORS_ALLOW_ALL setting
    cors_allow_all = os.getenv("CORS_ALLOW_ALL", "").lower() == "true"
    origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5500,http://localhost:5500")
    
    logger.info("cors_configuration", 
               cors_allow_all=cors_allow_all,
               allowed_origins=origins,
               note="For direct HTML file access, set CORS_ALLOW_ALL=true in .env")


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
