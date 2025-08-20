from typing import Dict, Any, List, Optional, Callable
import asyncio
import logging
from datetime import datetime, timedelta
import uuid
import json
from dataclasses import dataclass, field

from .base_agent import BaseMigrationAgent, MigrationState, MigrationStatus
from ..transformers.transformer_factory import TransformerFactory, TransformationPipeline

logger = logging.getLogger(__name__)

@dataclass
class RuntimeMigrationEvent:
    """Represents a runtime migration event"""
    event_id: str
    event_type: str  # CREATE, UPDATE, DELETE, LOGIN, etc.
    source_system: str
    target_systems: List[str]
    user_id: str
    data: Dict[str, Any]
    timestamp: datetime
    processed: bool = False
    retry_count: int = 0
    max_retries: int = 3
    errors: List[str] = field(default_factory=list)

class RuntimeMigratorAgent(BaseMigrationAgent):
    """Agent for real-time data migration during runtime transactions"""
    
    def __init__(self):
        super().__init__("RuntimeMigrator")
        self.event_queue = asyncio.Queue()
        self.processing_tasks = []
        self.is_running = False
        self.transformation_pipelines = {}
        self.event_handlers = {}
        self.retry_queue = asyncio.Queue()
        self.dead_letter_queue = []
        self.metrics = {
            "events_processed": 0,
            "events_failed": 0,
            "events_retried": 0,
            "average_processing_time": 0.0,
            "last_processed": None
        }
    
    async def initialize_migration(self, config: Dict[str, Any]) -> bool:
        """Initialize runtime migration"""
        try:
            self.migration_config = config
            
            # Create migration state
            self.state = MigrationState(
                job_id=config.get("job_id", str(uuid.uuid4())),
                source_system=config["source_system"],
                target_system=config["target_system"],
                status=MigrationStatus.PENDING,
                batch_size=1  # Runtime processes one event at a time
            )
            
            # Initialize transformation pipelines for all target systems
            target_systems = config.get("target_systems", [config["target_system"]])
            for target_system in target_systems:
                pipeline = TransformationPipeline()
                if pipeline.create_pipeline_for_path(config["source_system"], target_system):
                    self.transformation_pipelines[target_system] = pipeline
                else:
                    logger.warning(f"No transformation path from {config['source_system']} to {target_system}")
            
            # Setup event handlers
            self.setup_event_handlers()
            
            # Start background tasks
            await self.start_background_tasks()
            
            self.is_running = True
            self.state.status = MigrationStatus.RUNNING
            self.state.start_time = datetime.now()
            
            logger.info("Runtime migrator initialized and started")
            return True
            
        except Exception as e:
            logger.error(f"Runtime migration initialization failed: {str(e)}")
            if self.state:
                self.state.errors.append(f"Initialization error: {str(e)}")
            return False
    
    def setup_event_handlers(self):
        """Setup handlers for different event types"""
        self.event_handlers = {
            "USER_CREATE": self.handle_user_create,
            "USER_UPDATE": self.handle_user_update,
            "USER_DELETE": self.handle_user_delete,
            "USER_LOGIN": self.handle_user_login,
            "ROLE_ASSIGN": self.handle_role_assign,
            "ROLE_REVOKE": self.handle_role_revoke,
            "PASSWORD_CHANGE": self.handle_password_change,
            "PROFILE_UPDATE": self.handle_profile_update
        }
    
    async def start_background_tasks(self):
        """Start background processing tasks"""
        # Main event processor
        self.processing_tasks.append(
            asyncio.create_task(self.process_events())
        )
        
        # Retry processor
        self.processing_tasks.append(
            asyncio.create_task(self.process_retry_queue())
        )
        
        # Metrics collector
        self.processing_tasks.append(
            asyncio.create_task(self.collect_metrics())
        )
        
        # Health monitor
        self.processing_tasks.append(
            asyncio.create_task(self.monitor_health())
        )
    
    async def add_event(self, event_data: Dict[str, Any]) -> str:
        """Add a new event to the processing queue"""
        try:
            event = RuntimeMigrationEvent(
                event_id=str(uuid.uuid4()),
                event_type=event_data["event_type"],
                source_system=event_data["source_system"],
                target_systems=event_data.get("target_systems", [self.state.target_system]),
                user_id=event_data["user_id"],
                data=event_data["data"],
                timestamp=datetime.now()
            )
            
            await self.event_queue.put(event)
            logger.debug(f"Added event {event.event_id} to queue")
            return event.event_id
            
        except Exception as e:
            logger.error(f"Failed to add event: {str(e)}")
            raise
    
    async def process_events(self):
        """Main event processing loop"""
        while self.is_running:
            try:
                # Get event from queue with timeout
                event = await asyncio.wait_for(
                    self.event_queue.get(), 
                    timeout=1.0
                )
                
                start_time = datetime.now()
                
                # Process the event
                success = await self.process_single_event(event)
                
                # Update metrics
                processing_time = (datetime.now() - start_time).total_seconds()
                await self.update_metrics(success, processing_time)
                
                if success:
                    event.processed = True
                    self.state.successful_records += 1
                else:
                    # Add to retry queue if not exceeded max retries
                    if event.retry_count < event.max_retries:
                        event.retry_count += 1
                        await self.retry_queue.put(event)
                        self.metrics["events_retried"] += 1
                    else:
                        # Move to dead letter queue
                        self.dead_letter_queue.append(event)
                        self.state.failed_records += 1
                
                self.state.processed_records += 1
                
            except asyncio.TimeoutError:
                # No events in queue, continue
                continue
            except Exception as e:
                logger.error(f"Event processing error: {str(e)}")
                self.state.errors.append(str(e))
    
    async def process_single_event(self, event: RuntimeMigrationEvent) -> bool:
        """Process a single migration event"""
        try:
            # Get appropriate handler
            handler = self.event_handlers.get(event.event_type)
            if not handler:
                logger.warning(f"No handler for event type: {event.event_type}")
                return False
            
            # Process event for each target system
            success = True
            for target_system in event.target_systems:
                if target_system not in self.transformation_pipelines:
                    logger.warning(f"No transformation pipeline for {target_system}")
                    continue
                
                try:
                    # Execute handler
                    result = await handler(event, target_system)
                    if not result:
                        success = False
                        event.errors.append(f"Handler failed for {target_system}")
                        
                except Exception as e:
                    success = False
                    error_msg = f"Handler error for {target_system}: {str(e)}"
                    event.errors.append(error_msg)
                    logger.error(error_msg)
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to process event {event.event_id}: {str(e)}")
            event.errors.append(str(e))
            return False
    
    async def handle_user_create(self, event: RuntimeMigrationEvent, target_system: str) -> bool:
        """Handle user creation event"""
        try:
            # Transform user data
            pipeline = self.transformation_pipelines[target_system]
            transformed_data = pipeline.execute_pipeline(event.data, "user")
            
            # Simulate API call to create user in target system
            await asyncio.sleep(0.1)  # Simulate network delay
            
            # Mock validation
            if not self.validate_user_data(transformed_data, target_system):
                return False
            
            logger.debug(f"Created user {event.user_id} in {target_system}")
            return True
            
        except Exception as e:
            logger.error(f"User creation failed: {str(e)}")
            return False
    
    async def handle_user_update(self, event: RuntimeMigrationEvent, target_system: str) -> bool:
        """Handle user update event"""
        try:
            # Transform updated data
            pipeline = self.transformation_pipelines[target_system]
            transformed_data = pipeline.execute_pipeline(event.data, "user")
            
            # Simulate API call to update user in target system
            await asyncio.sleep(0.05)
            
            logger.debug(f"Updated user {event.user_id} in {target_system}")
            return True
            
        except Exception as e:
            logger.error(f"User update failed: {str(e)}")
            return False
    
    async def handle_user_delete(self, event: RuntimeMigrationEvent, target_system: str) -> bool:
        """Handle user deletion event"""
        try:
            # Simulate API call to delete/deactivate user in target system
            await asyncio.sleep(0.05)
            
            logger.debug(f"Deleted user {event.user_id} in {target_system}")
            return True
            
        except Exception as e:
            logger.error(f"User deletion failed: {str(e)}")
            return False
    
    async def handle_user_login(self, event: RuntimeMigrationEvent, target_system: str) -> bool:
        """Handle user login event"""
        try:
            # Update last login timestamp in target system
            await asyncio.sleep(0.02)
            
            logger.debug(f"Updated login timestamp for user {event.user_id} in {target_system}")
            return True
            
        except Exception as e:
            logger.error(f"Login update failed: {str(e)}")
            return False
    
    async def handle_role_assign(self, event: RuntimeMigrationEvent, target_system: str) -> bool:
        """Handle role assignment event"""
        try:
            # Transform role data and assign to user
            await asyncio.sleep(0.05)
            
            logger.debug(f"Assigned role to user {event.user_id} in {target_system}")
            return True
            
        except Exception as e:
            logger.error(f"Role assignment failed: {str(e)}")
            return False
    
    async def handle_role_revoke(self, event: RuntimeMigrationEvent, target_system: str) -> bool:
        """Handle role revocation event"""
        try:
            # Remove role from user in target system
            await asyncio.sleep(0.05)
            
            logger.debug(f"Revoked role from user {event.user_id} in {target_system}")
            return True
            
        except Exception as e:
            logger.error(f"Role revocation failed: {str(e)}")
            return False
    
    async def handle_password_change(self, event: RuntimeMigrationEvent, target_system: str) -> bool:
        """Handle password change event"""
        try:
            # Update password hash in target system
            await asyncio.sleep(0.05)
            
            logger.debug(f"Updated password for user {event.user_id} in {target_system}")
            return True
            
        except Exception as e:
            logger.error(f"Password update failed: {str(e)}")
            return False
    
    async def handle_profile_update(self, event: RuntimeMigrationEvent, target_system: str) -> bool:
        """Handle profile update event"""
        try:
            # Transform and update profile data
            pipeline = self.transformation_pipelines[target_system]
            transformed_data = pipeline.execute_pipeline(event.data, "user")
            
            await asyncio.sleep(0.05)
            
            logger.debug(f"Updated profile for user {event.user_id} in {target_system}")
            return True
            
        except Exception as e:
            logger.error(f"Profile update failed: {str(e)}")
            return False
    
    def validate_user_data(self, data: Dict[str, Any], target_system: str) -> bool:
        """Validate user data for target system"""
        # Basic validation based on target system
        if target_system == "AUTHE2.0":
            required_fields = ["id", "username", "email"]
        elif target_system == "AUTHENG":
            required_fields = ["user_uuid", "login_id", "primary_email"]
        else:
            required_fields = ["id", "username", "email"]
        
        for field in required_fields:
            if field not in data or not data[field]:
                return False
        
        return True
    
    async def process_retry_queue(self):
        """Process events in retry queue"""
        while self.is_running:
            try:
                # Wait for retry event with exponential backoff
                event = await asyncio.wait_for(
                    self.retry_queue.get(),
                    timeout=5.0
                )
                
                # Calculate backoff delay
                delay = min(2 ** event.retry_count, 60)  # Max 60 seconds
                await asyncio.sleep(delay)
                
                # Retry processing
                success = await self.process_single_event(event)
                
                if success:
                    event.processed = True
                    self.state.successful_records += 1
                else:
                    # Check if we should retry again
                    if event.retry_count < event.max_retries:
                        event.retry_count += 1
                        await self.retry_queue.put(event)
                    else:
                        # Move to dead letter queue
                        self.dead_letter_queue.append(event)
                        self.state.failed_records += 1
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Retry processing error: {str(e)}")
    
    async def update_metrics(self, success: bool, processing_time: float):
        """Update processing metrics"""
        self.metrics["events_processed"] += 1
        if not success:
            self.metrics["events_failed"] += 1
        
        # Update average processing time
        current_avg = self.metrics["average_processing_time"]
        total_events = self.metrics["events_processed"]
        self.metrics["average_processing_time"] = (
            (current_avg * (total_events - 1) + processing_time) / total_events
        )
        
        self.metrics["last_processed"] = datetime.now().isoformat()
    
    async def collect_metrics(self):
        """Collect and log metrics periodically"""
        while self.is_running:
            try:
                await asyncio.sleep(60)  # Collect metrics every minute
                
                logger.info(f"Runtime Migration Metrics: {json.dumps(self.metrics, indent=2)}")
                
                # Trigger metrics callback
                self.trigger_callback("on_progress", self.metrics)
                
            except Exception as e:
                logger.error(f"Metrics collection error: {str(e)}")
    
    async def monitor_health(self):
        """Monitor system health"""
        while self.is_running:
            try:
                await asyncio.sleep(30)  # Check health every 30 seconds
                
                # Check queue sizes
                queue_size = self.event_queue.qsize()
                retry_queue_size = self.retry_queue.qsize()
                dead_letter_size = len(self.dead_letter_queue)
                
                # Log warnings if queues are growing
                if queue_size > 1000:
                    logger.warning(f"Event queue size is high: {queue_size}")
                
                if retry_queue_size > 100:
                    logger.warning(f"Retry queue size is high: {retry_queue_size}")
                
                if dead_letter_size > 50:
                    logger.warning(f"Dead letter queue size is high: {dead_letter_size}")
                
                # Update state metadata
                self.state.metadata.update({
                    "queue_size": queue_size,
                    "retry_queue_size": retry_queue_size,
                    "dead_letter_size": dead_letter_size,
                    "health_check_time": datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Health monitoring error: {str(e)}")
    
    async def stop_migration(self):
        """Stop runtime migration"""
        self.is_running = False
        self.should_stop = True
        
        # Cancel all background tasks
        for task in self.processing_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self.processing_tasks, return_exceptions=True)
        
        if self.state:
            self.state.status = MigrationStatus.CANCELLED
            self.state.end_time = datetime.now()
        
        logger.info("Runtime migrator stopped")
    
    def get_dead_letter_events(self) -> List[Dict[str, Any]]:
        """Get events that failed processing"""
        return [
            {
                "event_id": event.event_id,
                "event_type": event.event_type,
                "user_id": event.user_id,
                "retry_count": event.retry_count,
                "errors": event.errors,
                "timestamp": event.timestamp.isoformat()
            }
            for event in self.dead_letter_queue
        ]
    
    # Required abstract methods (not used in runtime migration)
    async def fetch_source_data(self, batch_offset: int, batch_size: int) -> List[Dict[str, Any]]:
        return []
    
    async def transform_data(self, source_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return []
    
    async def load_target_data(self, transformed_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {"successful": 0, "failed": 0}
    
    async def validate_migration(self) -> Dict[str, Any]:
        return {
            "runtime_migration": True,
            "metrics": self.metrics,
            "dead_letter_events": len(self.dead_letter_queue)
        }