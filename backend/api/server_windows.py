"""
Windows-compatible FastAPI server
Uses simple agents instead of LangGraph to avoid Rust compilation issues
"""
import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Import our simple agents
from agents.simple_agents import run_simple_migration

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(title="Unified Onboard - IDP Migration API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for demo (replace with database in production)
migration_jobs: Dict[str, Dict] = {}

# Pydantic models
class MigrationRequest(BaseModel):
    source_system: str
    destination_system: str
    migration_type: str  # "onetime" or "runtime"

class MigrationResponse(BaseModel):
    id: str
    source_system: str
    destination_system: str
    migration_type: str
    status: str
    created_at: str
    updated_at: str
    progress_percentage: float
    total_records: int
    migrated_records: int
    failed_records: int
    error_message: Optional[str]
    estimated_completion: Optional[str]

# API Routes
@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Unified Onboard - IDP Migration API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/migrations", response_model=MigrationResponse)
async def create_migration(request: MigrationRequest):
    """Create a new migration job"""
    try:
        # Validate systems
        valid_systems = ["AUTHE1.0", "AUTHE2.0", "AUTHENG"]
        if request.source_system not in valid_systems:
            raise HTTPException(status_code=400, detail=f"Invalid source system: {request.source_system}")
        if request.destination_system not in valid_systems:
            raise HTTPException(status_code=400, detail=f"Invalid destination system: {request.destination_system}")
        if request.source_system == request.destination_system:
            raise HTTPException(status_code=400, detail="Source and destination systems cannot be the same")
        
        # Validate migration type
        if request.migration_type.lower() not in ["onetime", "runtime"]:
            raise HTTPException(status_code=400, detail="Migration type must be 'onetime' or 'runtime'")
        
        # Create job
        job_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        job = {
            "id": job_id,
            "source_system": request.source_system,
            "destination_system": request.destination_system,
            "migration_type": request.migration_type.lower(),
            "status": "pending",
            "created_at": now,
            "updated_at": now,
            "progress_percentage": 0.0,
            "total_records": 0,
            "migrated_records": 0,
            "failed_records": 0,
            "error_message": None,
            "estimated_completion": None
        }
        
        # Store job
        migration_jobs[job_id] = job
        
        # Start migration in background
        asyncio.create_task(execute_migration_job(job_id))
        
        return MigrationResponse(**job)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating migration: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/migrations/{job_id}", response_model=MigrationResponse)
async def get_migration(job_id: str):
    """Get migration job status"""
    if job_id not in migration_jobs:
        raise HTTPException(status_code=404, detail="Migration job not found")
    
    job = migration_jobs[job_id]
    return MigrationResponse(**job)

@app.get("/migrations", response_model=List[MigrationResponse])
async def list_migrations():
    """List all migration jobs"""
    jobs = list(migration_jobs.values())
    # Sort by created_at descending
    jobs.sort(key=lambda x: x["created_at"], reverse=True)
    return [MigrationResponse(**job) for job in jobs]

@app.delete("/migrations/{job_id}")
async def delete_migration(job_id: str):
    """Delete a migration job"""
    if job_id not in migration_jobs:
        raise HTTPException(status_code=404, detail="Migration job not found")
    
    job = migration_jobs[job_id]
    if job["status"] == "in_progress":
        raise HTTPException(status_code=400, detail="Cannot delete job in progress")
    
    del migration_jobs[job_id]
    return {"message": "Migration job deleted successfully"}

@app.get("/systems")
async def get_systems():
    """Get available IDP systems"""
    return {
        "systems": ["AUTHE1.0", "AUTHE2.0", "AUTHENG"],
        "supported_migrations": [
            {"source": "AUTHE1.0", "destination": "AUTHE2.0"},
            {"source": "AUTHE2.0", "destination": "AUTHENG"},
            {"source": "AUTHE1.0", "destination": "AUTHENG"}
        ]
    }

@app.get("/stats")
async def get_stats():
    """Get migration statistics"""
    jobs = list(migration_jobs.values())
    
    total_jobs = len(jobs)
    completed_jobs = len([j for j in jobs if j["status"] == "completed"])
    failed_jobs = len([j for j in jobs if j["status"] == "failed"])
    in_progress_jobs = len([j for j in jobs if j["status"] == "in_progress"])
    
    total_records = sum(j["total_records"] for j in jobs)
    migrated_records = sum(j["migrated_records"] for j in jobs)
    failed_records = sum(j["failed_records"] for j in jobs)
    
    success_rate = (migrated_records / total_records * 100) if total_records > 0 else 0
    
    return {
        "total_jobs": total_jobs,
        "completed_jobs": completed_jobs,
        "failed_jobs": failed_jobs,
        "in_progress_jobs": in_progress_jobs,
        "total_records": total_records,
        "migrated_records": migrated_records,
        "failed_records": failed_records,
        "success_rate": round(success_rate, 1)
    }

# Background task to execute migration
async def execute_migration_job(job_id: str):
    """Execute migration job in background"""
    try:
        job = migration_jobs[job_id]
        
        # Update status to in_progress
        job["status"] = "in_progress"
        job["updated_at"] = datetime.now().isoformat()
        
        # Run migration using simple agents
        result = await run_simple_migration(
            source_system=job["source_system"],
            destination_system=job["destination_system"],
            migration_type=job["migration_type"],
            job_id=job_id
        )
        
        # Update job with results
        job.update({
            "status": result["status"],
            "progress_percentage": result["progress"],
            "total_records": result["total_records"],
            "migrated_records": result["migrated_records"],
            "failed_records": result["failed_records"],
            "error_message": result["error_message"],
            "updated_at": datetime.now().isoformat()
        })
        
        logger.info(f"Migration job {job_id} completed: {result['status']}")
        
    except Exception as e:
        logger.error(f"Migration job {job_id} failed: {e}")
        job = migration_jobs.get(job_id, {})
        job.update({
            "status": "failed",
            "error_message": str(e),
            "updated_at": datetime.now().isoformat()
        })

if __name__ == "__main__":
    # Add some sample data for demo
    sample_jobs = [
        {
            "id": "1a16a18c-2103-41d9-ac5d-cd3c589942ee",
            "source_system": "AUTHE1.0",
            "destination_system": "AUTHE2.0",
            "migration_type": "onetime",
            "status": "completed",
            "created_at": "2025-08-20T22:17:00.000000",
            "updated_at": "2025-08-20T22:17:05.000000",
            "progress_percentage": 100.0,
            "total_records": 100,
            "migrated_records": 98,
            "failed_records": 2,
            "error_message": None,
            "estimated_completion": None
        }
    ]
    
    for job in sample_jobs:
        migration_jobs[job["id"]] = job
    
    # Run server
    uvicorn.run(
        "server_windows:app",
        host="0.0.0.0",
        port=12001,
        reload=True,
        log_level="info"
    )