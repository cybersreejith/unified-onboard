from typing import Dict, Any, Optional
from .base_transformer import BaseTransformer
from .authe1_to_authe2 import AUTHE1ToAUTHE2Transformer
from .authe2_to_autheng import AUTHE2ToAUTHENGTransformer
import logging

logger = logging.getLogger(__name__)

class TransformerFactory:
    """Factory class to create appropriate transformers based on source and target systems"""
    
    _transformers = {}
    
    @classmethod
    def register_transformer(cls, source_system: str, target_system: str, transformer_class):
        """Register a transformer for a specific source-target combination"""
        key = f"{source_system}_to_{target_system}"
        cls._transformers[key] = transformer_class
        logger.info(f"Registered transformer: {key}")
    
    @classmethod
    def get_transformer(cls, source_system: str, target_system: str) -> Optional[BaseTransformer]:
        """Get transformer instance for source-target combination"""
        key = f"{source_system}_to_{target_system}"
        
        if key in cls._transformers:
            return cls._transformers[key]()
        
        # Try reverse transformation if direct not available
        reverse_key = f"{target_system}_to_{source_system}"
        if reverse_key in cls._transformers:
            logger.warning(f"Direct transformer not found, attempting reverse transformation")
            # Note: This would require implementing reverse transformation logic
            return None
        
        logger.error(f"No transformer found for {source_system} to {target_system}")
        return None
    
    @classmethod
    def get_supported_transformations(cls) -> Dict[str, list]:
        """Get all supported transformation paths"""
        transformations = {}
        
        for key in cls._transformers.keys():
            source, target = key.split("_to_")
            if source not in transformations:
                transformations[source] = []
            transformations[source].append(target)
        
        return transformations
    
    @classmethod
    def is_transformation_supported(cls, source_system: str, target_system: str) -> bool:
        """Check if transformation is supported"""
        key = f"{source_system}_to_{target_system}"
        return key in cls._transformers

# Register available transformers
TransformerFactory.register_transformer("AUTHE1.0", "AUTHE2.0", AUTHE1ToAUTHE2Transformer)
TransformerFactory.register_transformer("AUTHE2.0", "AUTHENG", AUTHE2ToAUTHENGTransformer)

# Additional transformers can be registered here
# TransformerFactory.register_transformer("AUTHE1.0", "AUTHENG", AUTHE1ToAUTHENGTransformer)
# TransformerFactory.register_transformer("AUTHENG", "AUTHE2.0", AUTHENGToAUTHE2Transformer)

class TransformationPipeline:
    """Pipeline to handle multi-step transformations"""
    
    def __init__(self):
        self.transformation_steps = []
    
    def add_transformation_step(self, source_system: str, target_system: str):
        """Add a transformation step to the pipeline"""
        transformer = TransformerFactory.get_transformer(source_system, target_system)
        if transformer:
            self.transformation_steps.append({
                "source": source_system,
                "target": target_system,
                "transformer": transformer
            })
            return True
        return False
    
    def execute_pipeline(self, data: Dict[str, Any], data_type: str = "user") -> Dict[str, Any]:
        """Execute the transformation pipeline"""
        current_data = data
        
        for step in self.transformation_steps:
            transformer = step["transformer"]
            
            try:
                if data_type == "user":
                    current_data = transformer.transform_user(current_data)
                elif data_type == "role":
                    current_data = transformer.transform_role(current_data)
                elif data_type == "group":
                    current_data = transformer.transform_group(current_data)
                else:
                    raise ValueError(f"Unsupported data type: {data_type}")
                
                # Validate transformation
                if not transformer.validate_transformation(data, current_data):
                    raise ValueError(f"Validation failed for {step['source']} to {step['target']}")
                
                logger.info(f"Successfully transformed from {step['source']} to {step['target']}")
                
            except Exception as e:
                logger.error(f"Transformation failed at step {step['source']} to {step['target']}: {str(e)}")
                raise
        
        return current_data
    
    def find_transformation_path(self, source_system: str, target_system: str) -> list:
        """Find transformation path between two systems"""
        # Simple implementation - can be enhanced with graph algorithms
        supported = TransformerFactory.get_supported_transformations()
        
        # Direct transformation
        if source_system in supported and target_system in supported[source_system]:
            return [(source_system, target_system)]
        
        # Two-step transformation through intermediate system
        if source_system in supported:
            for intermediate in supported[source_system]:
                if intermediate in supported and target_system in supported[intermediate]:
                    return [(source_system, intermediate), (intermediate, target_system)]
        
        return []  # No path found
    
    def create_pipeline_for_path(self, source_system: str, target_system: str) -> bool:
        """Create pipeline for transformation path"""
        path = self.find_transformation_path(source_system, target_system)
        
        if not path:
            logger.error(f"No transformation path found from {source_system} to {target_system}")
            return False
        
        self.transformation_steps = []
        for source, target in path:
            if not self.add_transformation_step(source, target):
                logger.error(f"Failed to add transformation step: {source} to {target}")
                return False
        
        return True