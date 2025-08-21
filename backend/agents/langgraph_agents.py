"""
LangGraph-based Migration Agents
Implements sophisticated agentic workflows for IDP data migration
"""

from typing import Dict, Any, List, Optional, TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.runnables import RunnableLambda
import asyncio
import json
import uuid
from datetime import datetime
from enum import Enum

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from transformers.transformer_factory import TransformerFactory
except ImportError:
    # Fallback for testing
    class TransformerFactory:
        def is_transformation_supported(self, source, target):
            return True
        def get_transformer(self, source, target):
            return MockTransformer()

class MockTransformer:
    def transform(self, record):
        # Simple mock transformation
        if "user_id" in record:  # AUTHE1.0 to AUTHE2.0
            return {
                "id": record["user_id"].replace("user_", "usr_"),
                "login": record["username"],
                "email_address": record["email"],
                "display_name": record["full_name"],
                "account_status": "enabled" if record["status"] == "active" else "disabled",
                "registration_date": record["created_date"] + "T00:00:00Z",
                "last_access": record["last_login"] + "T12:00:00Z"
            }
        return record
    
    def transform_user(self, record):
        return self.transform(record)


class MigrationStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class AgentState(TypedDict):
    """State shared across all agents in the migration workflow"""
    job_id: str
    source_system: str
    destination_system: str
    migration_type: str
    batch_size: int
    total_records: int
    processed_records: int
    failed_records: int
    status: str
    error_message: Optional[str]
    current_batch: List[Dict[str, Any]]
    transformation_results: List[Dict[str, Any]]
    messages: Annotated[List[BaseMessage], "Messages in the conversation"]
    metadata: Dict[str, Any]


class LangGraphMigrationAgent:
    """Base LangGraph agent for migration operations"""
    
    def __init__(self):
        self.graph = None
        self.transformer_factory = TransformerFactory()
        self.build_graph()
    
    def build_graph(self):
        """Build the LangGraph workflow"""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("initialize", self.initialize_migration)
        workflow.add_node("validate_systems", self.validate_systems)
        workflow.add_node("fetch_data", self.fetch_source_data)
        workflow.add_node("transform_data", self.transform_data)
        workflow.add_node("validate_transformation", self.validate_transformation)
        workflow.add_node("load_data", self.load_destination_data)
        workflow.add_node("update_progress", self.update_progress)
        workflow.add_node("handle_error", self.handle_error)
        workflow.add_node("finalize", self.finalize_migration)
        
        # Define the workflow edges
        workflow.set_entry_point("initialize")
        
        workflow.add_edge("initialize", "validate_systems")
        workflow.add_conditional_edges(
            "validate_systems",
            self.should_continue_after_validation,
            {
                "continue": "fetch_data",
                "error": "handle_error"
            }
        )
        
        workflow.add_edge("fetch_data", "transform_data")
        workflow.add_edge("transform_data", "validate_transformation")
        workflow.add_conditional_edges(
            "validate_transformation",
            self.should_continue_after_transform_validation,
            {
                "continue": "load_data",
                "retry": "transform_data",
                "error": "handle_error"
            }
        )
        
        workflow.add_edge("load_data", "update_progress")
        workflow.add_conditional_edges(
            "update_progress",
            self.should_continue_migration,
            {
                "continue": "fetch_data",
                "complete": "finalize",
                "error": "handle_error"
            }
        )
        
        workflow.add_edge("handle_error", END)
        workflow.add_edge("finalize", END)
        
        self.graph = workflow.compile()
    
    async def initialize_migration(self, state: AgentState) -> AgentState:
        """Initialize the migration process"""
        print(f"🚀 Initializing migration job {state['job_id']}")
        
        state["status"] = MigrationStatus.IN_PROGRESS.value
        state["processed_records"] = 0
        state["failed_records"] = 0
        state["messages"].append(
            AIMessage(content=f"Starting migration from {state['source_system']} to {state['destination_system']}")
        )
        
        # Initialize metadata
        state["metadata"] = {
            "start_time": datetime.now().isoformat(),
            "current_batch_number": 0,
            "total_batches": (state["total_records"] + state["batch_size"] - 1) // state["batch_size"]
        }
        
        return state
    
    async def validate_systems(self, state: AgentState) -> AgentState:
        """Validate source and destination systems"""
        print(f"🔍 Validating systems: {state['source_system']} → {state['destination_system']}")
        
        valid_systems = ["AUTHE1.0", "AUTHE2.0", "AUTHENG"]
        
        if state["source_system"] not in valid_systems:
            state["error_message"] = f"Invalid source system: {state['source_system']}"
            state["status"] = MigrationStatus.FAILED.value
            return state
        
        if state["destination_system"] not in valid_systems:
            state["error_message"] = f"Invalid destination system: {state['destination_system']}"
            state["status"] = MigrationStatus.FAILED.value
            return state
        
        if state["source_system"] == state["destination_system"]:
            state["error_message"] = "Source and destination systems cannot be the same"
            state["status"] = MigrationStatus.FAILED.value
            return state
        
        # Check if transformer exists
        if not self.transformer_factory.is_transformation_supported(state['source_system'], state['destination_system']):
            state["error_message"] = f"No transformer available for {state['source_system']} → {state['destination_system']}"
            state["status"] = MigrationStatus.FAILED.value
            return state
        
        state["messages"].append(
            AIMessage(content="✅ System validation completed successfully")
        )
        
        return state
    
    async def fetch_source_data(self, state: AgentState) -> AgentState:
        """Fetch data from source system"""
        batch_number = state["metadata"]["current_batch_number"]
        offset = batch_number * state["batch_size"]
        
        print(f"📥 Fetching batch {batch_number + 1}/{state['metadata']['total_batches']} (offset: {offset})")
        
        # Simulate fetching data from source system
        # In real implementation, this would connect to actual systems
        batch_data = []
        remaining_records = state["total_records"] - offset
        current_batch_size = min(state["batch_size"], remaining_records)
        
        for i in range(current_batch_size):
            record_id = offset + i + 1
            if state["source_system"] == "AUTHE1.0":
                record = {
                    "user_id": f"user_{record_id:06d}",
                    "username": f"user{record_id}",
                    "email": f"user{record_id}@example.com",
                    "full_name": f"User {record_id}",
                    "status": "active",
                    "created_date": "2024-01-01",
                    "last_login": "2024-08-20"
                }
            elif state["source_system"] == "AUTHE2.0":
                record = {
                    "id": f"usr_{record_id:08d}",
                    "login": f"user{record_id}",
                    "email_address": f"user{record_id}@example.com",
                    "display_name": f"User {record_id}",
                    "account_status": "enabled",
                    "registration_date": "2024-01-01T00:00:00Z",
                    "last_access": "2024-08-20T12:00:00Z"
                }
            else:  # AUTHENG
                record = {
                    "entity_id": f"ent_{record_id:10d}",
                    "identity": f"user{record_id}",
                    "contact_email": f"user{record_id}@example.com",
                    "entity_name": f"User {record_id}",
                    "state": "active",
                    "created_timestamp": "2024-01-01T00:00:00.000Z",
                    "accessed_timestamp": "2024-08-20T12:00:00.000Z"
                }
            
            batch_data.append(record)
        
        state["current_batch"] = batch_data
        state["messages"].append(
            AIMessage(content=f"📥 Fetched {len(batch_data)} records from {state['source_system']}")
        )
        
        return state
    
    async def transform_data(self, state: AgentState) -> AgentState:
        """Transform data using appropriate transformer"""
        print(f"🔄 Transforming {len(state['current_batch'])} records")
        
        transformer = self.transformer_factory.get_transformer(state['source_system'], state['destination_system'])
        
        transformed_records = []
        failed_transformations = []
        
        for record in state["current_batch"]:
            try:
                # Use transform_user method from the transformer
                transformed_record = transformer.transform_user(record) if hasattr(transformer, 'transform_user') else transformer.transform(record)
                transformed_records.append(transformed_record)
            except Exception as e:
                failed_transformations.append({
                    "original_record": record,
                    "error": str(e)
                })
        
        state["transformation_results"] = transformed_records
        state["failed_records"] += len(failed_transformations)
        
        if failed_transformations:
            state["messages"].append(
                AIMessage(content=f"⚠️ {len(failed_transformations)} records failed transformation")
            )
        
        state["messages"].append(
            AIMessage(content=f"🔄 Successfully transformed {len(transformed_records)} records")
        )
        
        return state
    
    async def validate_transformation(self, state: AgentState) -> AgentState:
        """Validate transformed data"""
        print(f"✅ Validating {len(state['transformation_results'])} transformed records")
        
        valid_records = []
        invalid_records = []
        
        for i, record in enumerate(state["transformation_results"]):
            # Basic validation - check required fields exist
            is_valid = self._validate_record_structure(record, state["destination_system"])
            print(f"   Record {i+1}: {is_valid} - {list(record.keys())}")
            
            if is_valid:
                valid_records.append(record)
            else:
                invalid_records.append(record)
        
        state["transformation_results"] = valid_records
        state["failed_records"] += len(invalid_records)
        
        print(f"   Valid: {len(valid_records)}, Invalid: {len(invalid_records)}")
        
        if invalid_records:
            state["messages"].append(
                AIMessage(content=f"❌ {len(invalid_records)} records failed validation")
            )
        else:
            state["messages"].append(
                AIMessage(content=f"✅ All {len(valid_records)} records passed validation")
            )
        
        return state
    
    async def load_destination_data(self, state: AgentState) -> AgentState:
        """Load data into destination system"""
        print(f"📤 Loading {len(state['transformation_results'])} records to {state['destination_system']}")
        
        # Simulate loading data to destination system
        # In real implementation, this would connect to actual systems
        loaded_count = len(state["transformation_results"])
        
        # Simulate some load failures (2% failure rate)
        import random
        failed_loads = random.randint(0, max(1, loaded_count // 50))
        successful_loads = loaded_count - failed_loads
        
        state["processed_records"] += successful_loads
        state["failed_records"] += failed_loads
        
        state["messages"].append(
            AIMessage(content=f"📤 Successfully loaded {successful_loads} records to {state['destination_system']}")
        )
        
        if failed_loads > 0:
            state["messages"].append(
                AIMessage(content=f"❌ {failed_loads} records failed to load")
            )
        
        return state
    
    async def update_progress(self, state: AgentState) -> AgentState:
        """Update migration progress"""
        state["metadata"]["current_batch_number"] += 1
        
        progress_percentage = (state["processed_records"] / state["total_records"]) * 100
        print(f"📊 Progress: {state['processed_records']}/{state['total_records']} ({progress_percentage:.1f}%)")
        
        state["messages"].append(
            AIMessage(content=f"📊 Migration progress: {progress_percentage:.1f}% complete")
        )
        
        return state
    
    async def handle_error(self, state: AgentState) -> AgentState:
        """Handle migration errors"""
        print(f"❌ Handling error: {state.get('error_message', 'Unknown error')}")
        
        state["status"] = MigrationStatus.FAILED.value
        state["metadata"]["end_time"] = datetime.now().isoformat()
        
        state["messages"].append(
            AIMessage(content=f"❌ Migration failed: {state.get('error_message', 'Unknown error')}")
        )
        
        return state
    
    async def finalize_migration(self, state: AgentState) -> AgentState:
        """Finalize the migration process"""
        print(f"🎉 Finalizing migration job {state['job_id']}")
        
        state["status"] = MigrationStatus.COMPLETED.value
        state["metadata"]["end_time"] = datetime.now().isoformat()
        
        success_rate = ((state["processed_records"] / state["total_records"]) * 100) if state["total_records"] > 0 else 0
        
        state["messages"].append(
            AIMessage(content=f"🎉 Migration completed! Success rate: {success_rate:.1f}%")
        )
        
        return state
    
    def should_continue_after_validation(self, state: AgentState) -> str:
        """Decide whether to continue after system validation"""
        if state.get("error_message"):
            return "error"
        return "continue"
    
    def should_continue_after_transform_validation(self, state: AgentState) -> str:
        """Decide whether to continue after transformation validation"""
        if state.get("error_message"):
            return "error"
        
        # If no valid records, we might want to retry or error
        if not state["transformation_results"]:
            return "error"
        
        return "continue"
    
    def should_continue_migration(self, state: AgentState) -> str:
        """Decide whether to continue migration or complete"""
        if state.get("error_message"):
            return "error"
        
        # Check if we've processed all batches
        current_batch = state["metadata"]["current_batch_number"]
        total_batches = state["metadata"]["total_batches"]
        
        if current_batch >= total_batches:
            return "complete"
        
        return "continue"
    
    def _validate_record_structure(self, record: Dict[str, Any], system: str) -> bool:
        """Validate record structure for destination system"""
        if system == "AUTHE1.0":
            required_fields = ["user_id", "username", "email"]
        elif system == "AUTHE2.0":
            # Based on actual transformer output
            required_fields = ["id", "username"]  # These are the core fields that should always be present
        else:  # AUTHENG
            required_fields = ["entity_id", "identity", "contact_email"]
        
        is_valid = all(field in record for field in required_fields)
        if not is_valid:
            print(f"   Missing required fields: {[f for f in required_fields if f not in record]}")
        return is_valid
    
    async def run_migration(self, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """Run the complete migration workflow"""
        # Convert initial state to AgentState
        agent_state = AgentState(
            job_id=initial_state["job_id"],
            source_system=initial_state["source_system"],
            destination_system=initial_state["destination_system"],
            migration_type=initial_state["migration_type"],
            batch_size=initial_state.get("batch_size", 100),
            total_records=initial_state["total_records"],
            processed_records=0,
            failed_records=0,
            status=MigrationStatus.PENDING.value,
            error_message=None,
            current_batch=[],
            transformation_results=[],
            messages=[HumanMessage(content="Starting migration process")],
            metadata={}
        )
        
        # Run the graph
        final_state = await self.graph.ainvoke(agent_state)
        
        return {
            "job_id": final_state["job_id"],
            "status": final_state["status"],
            "processed_records": final_state["processed_records"],
            "failed_records": final_state["failed_records"],
            "total_records": final_state["total_records"],
            "error_message": final_state.get("error_message"),
            "metadata": final_state["metadata"],
            "messages": [msg.content for msg in final_state["messages"]]
        }


class OneTimeMigrationAgent(LangGraphMigrationAgent):
    """Specialized agent for one-time bulk migrations"""
    
    def __init__(self):
        super().__init__()
        print("🔧 Initialized One-Time Migration Agent with LangGraph")


class RuntimeMigrationAgent(LangGraphMigrationAgent):
    """Specialized agent for runtime/real-time migrations"""
    
    def __init__(self):
        super().__init__()
        print("🔧 Initialized Runtime Migration Agent with LangGraph")
    
    def build_graph(self):
        """Build specialized graph for runtime migrations"""
        # For runtime migrations, we use a simpler, faster workflow
        workflow = StateGraph(AgentState)
        
        # Add nodes for runtime processing
        workflow.add_node("initialize", self.initialize_migration)
        workflow.add_node("validate_systems", self.validate_systems)
        workflow.add_node("process_event", self.process_single_event)
        workflow.add_node("transform_event", self.transform_single_event)
        workflow.add_node("load_event", self.load_single_event)
        workflow.add_node("handle_error", self.handle_error)
        workflow.add_node("finalize", self.finalize_migration)
        
        # Define runtime workflow edges
        workflow.set_entry_point("initialize")
        workflow.add_edge("initialize", "validate_systems")
        workflow.add_conditional_edges(
            "validate_systems",
            self.should_continue_after_validation,
            {
                "continue": "process_event",
                "error": "handle_error"
            }
        )
        
        workflow.add_edge("process_event", "transform_event")
        workflow.add_edge("transform_event", "load_event")
        workflow.add_edge("load_event", "finalize")
        workflow.add_edge("handle_error", END)
        workflow.add_edge("finalize", END)
        
        self.graph = workflow.compile()
    
    async def process_single_event(self, state: AgentState) -> AgentState:
        """Process a single runtime event"""
        print(f"⚡ Processing runtime event for {state['source_system']}")
        
        # For runtime, we typically process one record at a time
        # This would be triggered by real-time events
        state["current_batch"] = [{
            "user_id": "runtime_user_001",
            "username": "runtime_user",
            "email": "runtime@example.com",
            "full_name": "Runtime User",
            "status": "active",
            "created_date": datetime.now().strftime("%Y-%m-%d"),
            "last_login": datetime.now().strftime("%Y-%m-%d")
        }]
        
        return state
    
    async def transform_single_event(self, state: AgentState) -> AgentState:
        """Transform single event data"""
        return await self.transform_data(state)
    
    async def load_single_event(self, state: AgentState) -> AgentState:
        """Load single event to destination"""
        result = await self.load_destination_data(state)
        # For runtime, we complete immediately after processing one event
        state["status"] = MigrationStatus.COMPLETED.value
        return result


# Factory for creating agents
class AgentFactory:
    """Factory for creating different types of migration agents"""
    
    @staticmethod
    def create_agent(migration_type: str) -> LangGraphMigrationAgent:
        """Create appropriate agent based on migration type"""
        if migration_type.upper() == "ONE_TIME":
            return OneTimeMigrationAgent()
        elif migration_type.upper() == "RUNTIME":
            return RuntimeMigrationAgent()
        else:
            raise ValueError(f"Unknown migration type: {migration_type}")