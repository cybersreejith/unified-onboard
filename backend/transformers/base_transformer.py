from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class BaseTransformer(ABC):
    """Base class for all data transformers"""
    
    def __init__(self, source_system: str, target_system: str):
        self.source_system = source_system
        self.target_system = target_system
        self.transformation_rules = {}
        self.field_mappings = {}
        self.validation_rules = {}
    
    @abstractmethod
    def transform_user(self, source_user: Dict[str, Any]) -> Dict[str, Any]:
        """Transform a user record from source to target format"""
        pass
    
    @abstractmethod
    def transform_role(self, source_role: Dict[str, Any]) -> Dict[str, Any]:
        """Transform a role record from source to target format"""
        pass
    
    @abstractmethod
    def transform_group(self, source_group: Dict[str, Any]) -> Dict[str, Any]:
        """Transform a group record from source to target format"""
        pass
    
    def validate_transformation(self, source_data: Dict[str, Any], transformed_data: Dict[str, Any]) -> bool:
        """Validate the transformation result"""
        try:
            # Basic validation - ensure required fields are present
            required_fields = self.get_required_fields()
            for field in required_fields:
                if field not in transformed_data or transformed_data[field] is None:
                    logger.error(f"Required field '{field}' missing in transformed data")
                    return False
            
            # Data type validation
            if not self.validate_data_types(transformed_data):
                return False
            
            # Business rule validation
            if not self.validate_business_rules(source_data, transformed_data):
                return False
            
            return True
        except Exception as e:
            logger.error(f"Validation error: {str(e)}")
            return False
    
    def get_required_fields(self) -> List[str]:
        """Get list of required fields for target system"""
        return []
    
    def validate_data_types(self, data: Dict[str, Any]) -> bool:
        """Validate data types in transformed data"""
        return True
    
    def validate_business_rules(self, source_data: Dict[str, Any], transformed_data: Dict[str, Any]) -> bool:
        """Validate business rules"""
        return True
    
    def apply_field_mapping(self, source_data: Dict[str, Any], field_mappings: Dict[str, str]) -> Dict[str, Any]:
        """Apply field mappings to transform data structure"""
        transformed = {}
        
        for target_field, source_field in field_mappings.items():
            if '.' in source_field:
                # Handle nested field access
                value = self.get_nested_value(source_data, source_field)
            else:
                value = source_data.get(source_field)
            
            if value is not None:
                transformed[target_field] = value
        
        return transformed
    
    def get_nested_value(self, data: Dict[str, Any], field_path: str) -> Any:
        """Get value from nested dictionary using dot notation"""
        keys = field_path.split('.')
        value = data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value
    
    def set_nested_value(self, data: Dict[str, Any], field_path: str, value: Any) -> None:
        """Set value in nested dictionary using dot notation"""
        keys = field_path.split('.')
        current = data
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    def transform_datetime(self, dt_value: Any, target_format: str = "iso") -> Optional[str]:
        """Transform datetime values between different formats"""
        if dt_value is None:
            return None
        
        try:
            if isinstance(dt_value, str):
                # Parse string datetime
                dt = datetime.fromisoformat(dt_value.replace('Z', '+00:00'))
            elif isinstance(dt_value, datetime):
                dt = dt_value
            else:
                return None
            
            if target_format == "iso":
                return dt.isoformat()
            elif target_format == "timestamp":
                return str(int(dt.timestamp()))
            else:
                return dt.strftime(target_format)
        
        except Exception as e:
            logger.error(f"DateTime transformation error: {str(e)}")
            return None
    
    def transform_enum_value(self, source_value: str, enum_mapping: Dict[str, str]) -> Optional[str]:
        """Transform enum values between systems"""
        return enum_mapping.get(source_value, source_value)
    
    def generate_id(self, prefix: str = "", source_id: str = "") -> str:
        """Generate new ID for target system"""
        import uuid
        if source_id:
            # Create deterministic ID based on source ID
            namespace = uuid.NAMESPACE_DNS
            return str(uuid.uuid5(namespace, f"{self.source_system}:{source_id}"))
        else:
            # Generate random ID
            return f"{prefix}{uuid.uuid4()}"
    
    def log_transformation(self, source_id: str, target_id: str, status: str, errors: List[str] = None):
        """Log transformation details"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "source_system": self.source_system,
            "target_system": self.target_system,
            "source_id": source_id,
            "target_id": target_id,
            "status": status,
            "errors": errors or []
        }
        logger.info(f"Transformation log: {log_entry}")
        return log_entry