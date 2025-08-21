from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class MigrationStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class MigrationState:
    """State object for migration process"""
    job_id: str
    source_system: str
    target_system: str
    status: MigrationStatus
    total_records: int = 0
    processed_records: int = 0
    successful_records: int = 0
    failed_records: int = 0
    current_batch: int = 0
    batch_size: int = 1000
    errors: List[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.metadata is None:
            self.metadata = {}
    
    @property
    def progress_percentage(self) -> float:
        if self.total_records == 0:
            return 0.0
        return (self.processed_records / self.total_records) * 100
    
    @property
    def success_rate(self) -> float:
        if self.processed_records == 0:
            return 0.0
        return (self.successful_records / self.processed_records) * 100

class BaseMigrationAgent(ABC):
    """Base class for migration agents"""
    
    def __init__(self, name: str):
        self.name = name
        self.state: Optional[MigrationState] = None
        self.callbacks: Dict[str, List[Callable]] = {
            "on_start": [],
            "on_progress": [],
            "on_batch_complete": [],
            "on_error": [],
            "on_complete": [],
            "on_pause": [],
            "on_resume": []
        }
        self.is_paused = False
        self.should_stop = False
    
    def add_callback(self, event: str, callback: Callable):
        """Add callback for specific events"""
        if event in self.callbacks:
            self.callbacks[event].append(callback)
    
    def trigger_callback(self, event: str, *args, **kwargs):
        """Trigger callbacks for specific event"""
        for callback in self.callbacks.get(event, []):
            try:
                callback(self.state, *args, **kwargs)
            except Exception as e:
                logger.error(f"Callback error for {event}: {str(e)}")
    
    @abstractmethod
    async def initialize_migration(self, config: Dict[str, Any]) -> bool:
        """Initialize migration with configuration"""
        pass
    
    @abstractmethod
    async def fetch_source_data(self, batch_offset: int, batch_size: int) -> List[Dict[str, Any]]:
        """Fetch data from source system"""
        pass
    
    @abstractmethod
    async def transform_data(self, source_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transform data from source to target format"""
        pass
    
    @abstractmethod
    async def load_target_data(self, transformed_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Load data into target system"""
        pass
    
    @abstractmethod
    async def validate_migration(self) -> Dict[str, Any]:
        """Validate migration results"""
        pass
    
    async def start_migration(self, config: Dict[str, Any]) -> MigrationState:
        """Start the migration process"""
        try:
            # Initialize migration
            if not await self.initialize_migration(config):
                raise Exception("Migration initialization failed")
            
            self.state.status = MigrationStatus.RUNNING
            self.state.start_time = datetime.now()
            self.trigger_callback("on_start")
            
            # Main migration loop
            while (self.state.processed_records < self.state.total_records and 
                   not self.should_stop):
                
                # Check for pause
                while self.is_paused and not self.should_stop:
                    await asyncio.sleep(1)
                
                if self.should_stop:
                    break
                
                # Process batch
                await self.process_batch()
                
                # Update progress
                self.trigger_callback("on_progress")
            
            # Finalize migration
            await self.finalize_migration()
            
            return self.state
            
        except Exception as e:
            logger.error(f"Migration failed: {str(e)}")
            self.state.status = MigrationStatus.FAILED
            self.state.errors.append(str(e))
            self.trigger_callback("on_error", e)
            return self.state
    
    async def process_batch(self):
        """Process a single batch of data"""
        try:
            batch_offset = self.state.current_batch * self.state.batch_size
            
            # Fetch source data
            source_data = await self.fetch_source_data(batch_offset, self.state.batch_size)
            
            if not source_data:
                # No more data to process
                return
            
            # Transform data
            transformed_data = await self.transform_data(source_data)
            
            # Load data to target
            load_result = await self.load_target_data(transformed_data)
            
            # Update state
            self.state.processed_records += len(source_data)
            self.state.successful_records += load_result.get("successful", 0)
            self.state.failed_records += load_result.get("failed", 0)
            self.state.current_batch += 1
            
            # Add any errors
            if "errors" in load_result:
                self.state.errors.extend(load_result["errors"])
            
            self.trigger_callback("on_batch_complete", load_result)
            
            logger.info(f"Processed batch {self.state.current_batch}: "
                       f"{len(source_data)} records, "
                       f"{load_result.get('successful', 0)} successful, "
                       f"{load_result.get('failed', 0)} failed")
            
        except Exception as e:
            logger.error(f"Batch processing failed: {str(e)}")
            self.state.errors.append(f"Batch {self.state.current_batch}: {str(e)}")
            self.state.failed_records += self.state.batch_size
            raise
    
    async def finalize_migration(self):
        """Finalize migration process"""
        try:
            # Validate migration
            validation_result = await self.validate_migration()
            
            # Update final state
            self.state.end_time = datetime.now()
            
            if self.should_stop:
                self.state.status = MigrationStatus.CANCELLED
            elif self.state.failed_records == 0:
                self.state.status = MigrationStatus.COMPLETED
            else:
                self.state.status = MigrationStatus.COMPLETED  # Partial success
            
            self.state.metadata.update(validation_result)
            self.trigger_callback("on_complete", validation_result)
            
            logger.info(f"Migration completed: {self.state.successful_records} successful, "
                       f"{self.state.failed_records} failed")
            
        except Exception as e:
            logger.error(f"Migration finalization failed: {str(e)}")
            self.state.status = MigrationStatus.FAILED
            self.state.errors.append(f"Finalization error: {str(e)}")
    
    def pause_migration(self):
        """Pause the migration"""
        self.is_paused = True
        if self.state:
            self.state.status = MigrationStatus.PAUSED
        self.trigger_callback("on_pause")
        logger.info("Migration paused")
    
    def resume_migration(self):
        """Resume the migration"""
        self.is_paused = False
        if self.state:
            self.state.status = MigrationStatus.RUNNING
        self.trigger_callback("on_resume")
        logger.info("Migration resumed")
    
    def stop_migration(self):
        """Stop the migration"""
        self.should_stop = True
        self.is_paused = False
        if self.state:
            self.state.status = MigrationStatus.CANCELLED
        logger.info("Migration stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current migration status"""
        if not self.state:
            return {"status": "not_started"}
        
        return {
            "job_id": self.state.job_id,
            "status": self.state.status.value,
            "progress_percentage": self.state.progress_percentage,
            "total_records": self.state.total_records,
            "processed_records": self.state.processed_records,
            "successful_records": self.state.successful_records,
            "failed_records": self.state.failed_records,
            "success_rate": self.state.success_rate,
            "current_batch": self.state.current_batch,
            "errors": self.state.errors[-10:],  # Last 10 errors
            "start_time": self.state.start_time.isoformat() if self.state.start_time else None,
            "end_time": self.state.end_time.isoformat() if self.state.end_time else None,
            "metadata": self.state.metadata
        }