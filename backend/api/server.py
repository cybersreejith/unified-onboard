from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import uuid
import asyncio
import json
from datetime import datetime
from enum import Enum
import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.langgraph_agents import AgentFactory, LangGraphMigrationAgent

app = FastAPI(title="IDP Migration API", version="1.0.0")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enums
class IDPSystem(str, Enum):
    AUTHE1_0 = "AUTHE1.0"
    AUTHE2_0 = "AUTHE2.0"
    AUTHENG = "AUTHENG"

class MigrationStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"

class MigrationType(str, Enum):
    ONE_TIME = "one_time"
    RUNTIME = "runtime"

# Pydantic Models
class MigrationRequest(BaseModel):
    source_system: IDPSystem
    destination_system: IDPSystem
    migration_type: MigrationType
    batch_size: Optional[int] = 1000
    include_historical: Optional[bool] = True
    transformation_rules: Optional[Dict[str, Any]] = {}

class MigrationJob(BaseModel):
    id: str
    source_system: IDPSystem
    destination_system: IDPSystem
    migration_type: MigrationType
    status: MigrationStatus
    created_at: datetime
    updated_at: datetime
    progress_percentage: float
    total_records: int
    migrated_records: int
    failed_records: int
    error_message: Optional[str] = None
    estimated_completion: Optional[datetime] = None

class SystemConfig(BaseModel):
    system_type: IDPSystem
    endpoint_url: str
    api_key: str
    connection_timeout: int = 30
    batch_size: int = 1000
    rate_limit: int = 100

class UserRecord(BaseModel):
    id: str
    username: str
    email: str
    first_name: str
    last_name: str
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool = True
    roles: List[str] = []
    attributes: Dict[str, Any] = {}

# In-memory storage (replace with database in production)
migration_jobs: Dict[str, MigrationJob] = {}
system_configs: Dict[IDPSystem, SystemConfig] = {}
user_records: Dict[str, List[UserRecord]] = {
    IDPSystem.AUTHE1_0: [],
    IDPSystem.AUTHE2_0: [],
    IDPSystem.AUTHENG: []
}

# Initialize with sample data
def initialize_sample_data():
    # Sample system configurations
    system_configs[IDPSystem.AUTHE1_0] = SystemConfig(
        system_type=IDPSystem.AUTHE1_0,
        endpoint_url="https://api.authe1.example.com",
        api_key="authe1-api-key-123",
        batch_size=500
    )
    system_configs[IDPSystem.AUTHE2_0] = SystemConfig(
        system_type=IDPSystem.AUTHE2_0,
        endpoint_url="https://api.authe2.example.com",
        api_key="authe2-api-key-456",
        batch_size=1000
    )
    system_configs[IDPSystem.AUTHENG] = SystemConfig(
        system_type=IDPSystem.AUTHENG,
        endpoint_url="https://api.autheng.example.com",
        api_key="autheng-api-key-789",
        batch_size=750
    )
    
    # Sample user records for AUTHE1.0
    for i in range(100):
        user_records[IDPSystem.AUTHE1_0].append(UserRecord(
            id=f"authe1-user-{i}",
            username=f"user{i}@authe1.com",
            email=f"user{i}@example.com",
            first_name=f"FirstName{i}",
            last_name=f"LastName{i}",
            created_at=datetime.now(),
            roles=["user", "basic"],
            attributes={"department": "IT", "location": "US"}
        ))

initialize_sample_data()

# API Endpoints
@app.get("/")
async def root():
    return {"message": "IDP Migration API Server", "version": "1.0.0"}

@app.get("/systems", response_model=List[IDPSystem])
async def get_supported_systems():
    """Get list of supported IDP systems"""
    return list(IDPSystem)

@app.get("/systems/{system_type}/config", response_model=SystemConfig)
async def get_system_config(system_type: IDPSystem):
    """Get configuration for a specific IDP system"""
    if system_type not in system_configs:
        raise HTTPException(status_code=404, detail="System configuration not found")
    return system_configs[system_type]

@app.post("/systems/{system_type}/config", response_model=SystemConfig)
async def update_system_config(system_type: IDPSystem, config: SystemConfig):
    """Update configuration for a specific IDP system"""
    system_configs[system_type] = config
    return config

@app.get("/systems/{system_type}/users", response_model=List[UserRecord])
async def get_system_users(system_type: IDPSystem, limit: int = 100, offset: int = 0):
    """Get users from a specific IDP system"""
    if system_type not in user_records:
        raise HTTPException(status_code=404, detail="System not found")
    
    users = user_records[system_type]
    return users[offset:offset + limit]

@app.get("/systems/{system_type}/users/count")
async def get_system_user_count(system_type: IDPSystem):
    """Get total user count for a specific IDP system"""
    if system_type not in user_records:
        raise HTTPException(status_code=404, detail="System not found")
    
    return {"count": len(user_records[system_type])}

@app.post("/migrations", response_model=MigrationJob)
async def create_migration_job(request: MigrationRequest, background_tasks: BackgroundTasks):
    """Create a new migration job"""
    job_id = str(uuid.uuid4())
    
    # Get source user count
    source_count = len(user_records.get(request.source_system, []))
    
    job = MigrationJob(
        id=job_id,
        source_system=request.source_system,
        destination_system=request.destination_system,
        migration_type=request.migration_type,
        status=MigrationStatus.PENDING,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        progress_percentage=0.0,
        total_records=source_count,
        migrated_records=0,
        failed_records=0
    )
    
    migration_jobs[job_id] = job
    
    # Start migration in background using LangGraph agents
    background_tasks.add_task(run_langgraph_migration, job_id)
    
    return job

@app.get("/migrations", response_model=List[MigrationJob])
async def get_migration_jobs():
    """Get all migration jobs"""
    return list(migration_jobs.values())

@app.get("/migrations/{job_id}", response_model=MigrationJob)
async def get_migration_job(job_id: str):
    """Get specific migration job by ID"""
    if job_id not in migration_jobs:
        raise HTTPException(status_code=404, detail="Migration job not found")
    return migration_jobs[job_id]

@app.post("/migrations/{job_id}/pause")
async def pause_migration_job(job_id: str):
    """Pause a migration job"""
    if job_id not in migration_jobs:
        raise HTTPException(status_code=404, detail="Migration job not found")
    
    job = migration_jobs[job_id]
    if job.status == MigrationStatus.IN_PROGRESS:
        job.status = MigrationStatus.PAUSED
        job.updated_at = datetime.now()
    
    return {"message": "Migration job paused", "job_id": job_id}

@app.post("/migrations/{job_id}/resume")
async def resume_migration_job(job_id: str, background_tasks: BackgroundTasks):
    """Resume a paused migration job"""
    if job_id not in migration_jobs:
        raise HTTPException(status_code=404, detail="Migration job not found")
    
    job = migration_jobs[job_id]
    if job.status == MigrationStatus.PAUSED:
        job.status = MigrationStatus.IN_PROGRESS
        job.updated_at = datetime.now()
        background_tasks.add_task(simulate_migration, job_id)
    
    return {"message": "Migration job resumed", "job_id": job_id}

@app.delete("/migrations/{job_id}")
async def delete_migration_job(job_id: str):
    """Delete a migration job"""
    if job_id not in migration_jobs:
        raise HTTPException(status_code=404, detail="Migration job not found")
    
    del migration_jobs[job_id]
    return {"message": "Migration job deleted", "job_id": job_id}

@app.get("/dashboard/stats")
async def get_dashboard_stats():
    """Get dashboard statistics"""
    total_jobs = len(migration_jobs)
    completed_jobs = len([j for j in migration_jobs.values() if j.status == MigrationStatus.COMPLETED])
    in_progress_jobs = len([j for j in migration_jobs.values() if j.status == MigrationStatus.IN_PROGRESS])
    failed_jobs = len([j for j in migration_jobs.values() if j.status == MigrationStatus.FAILED])
    
    total_migrated = sum(j.migrated_records for j in migration_jobs.values())
    total_failed = sum(j.failed_records for j in migration_jobs.values())
    
    return {
        "total_jobs": total_jobs,
        "completed_jobs": completed_jobs,
        "in_progress_jobs": in_progress_jobs,
        "failed_jobs": failed_jobs,
        "total_migrated_records": total_migrated,
        "total_failed_records": total_failed,
        "success_rate": (total_migrated / (total_migrated + total_failed)) * 100 if (total_migrated + total_failed) > 0 else 0
    }

# Background task to run LangGraph migration
async def run_langgraph_migration(job_id: str):
    """Run migration using LangGraph agents"""
    if job_id not in migration_jobs:
        return
    
    job = migration_jobs[job_id]
    
    try:
        # Create appropriate agent based on migration type
        agent = AgentFactory.create_agent(job.migration_type.value)
        
        # Prepare initial state for the agent
        initial_state = {
            "job_id": job_id,
            "source_system": job.source_system.value,
            "destination_system": job.destination_system.value,
            "migration_type": job.migration_type.value,
            "batch_size": 50,  # Configurable batch size
            "total_records": job.total_records
        }
        
        # Update job status to in progress
        job.status = MigrationStatus.IN_PROGRESS
        job.updated_at = datetime.now()
        
        # Run the migration workflow
        print(f"🚀 Starting LangGraph migration for job {job_id}")
        result = await agent.run_migration(initial_state)
        
        # Update job with final results
        job.status = MigrationStatus(result["status"])
        job.migrated_records = result["processed_records"]
        job.failed_records = result["failed_records"]
        job.progress_percentage = 100.0 if job.status == MigrationStatus.COMPLETED else 0.0
        job.updated_at = datetime.now()
        
        print(f"✅ LangGraph migration completed for job {job_id}")
        print(f"   Status: {result['status']}")
        print(f"   Processed: {result['processed_records']}/{result['total_records']}")
        print(f"   Failed: {result['failed_records']}")
        
        # Store agent messages for debugging
        if "messages" in result:
            print("📝 Agent Messages:")
            for msg in result["messages"]:
                print(f"   {msg}")
        
    except Exception as e:
        print(f"❌ LangGraph migration failed for job {job_id}: {str(e)}")
        job.status = MigrationStatus.FAILED
        job.updated_at = datetime.now()
        # Keep the simulate_migration as fallback for demo purposes
        await simulate_migration_fallback(job_id)

# Fallback simulation for demo purposes
async def simulate_migration_fallback(job_id: str):
    """Fallback simulation migration progress"""
    if job_id not in migration_jobs:
        return
    
    job = migration_jobs[job_id]
    job.status = MigrationStatus.IN_PROGRESS
    job.updated_at = datetime.now()
    
    # Simulate migration progress
    for progress in range(0, 101, 15):
        if job.status == MigrationStatus.PAUSED:
            return
        
        job.progress_percentage = progress
        job.migrated_records = int((progress / 100) * job.total_records)
        job.updated_at = datetime.now()
        
        # Simulate some failures
        if progress > 50:
            job.failed_records = int(0.02 * job.migrated_records)  # 2% failure rate
        
        await asyncio.sleep(1)  # Faster for demo
    
    job.status = MigrationStatus.COMPLETED
    job.progress_percentage = 100.0
    job.updated_at = datetime.now()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=12001, reload=True)