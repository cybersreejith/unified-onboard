from typing import Dict, Any, List
from datetime import datetime
from .base_transformer import BaseTransformer
import logging

logger = logging.getLogger(__name__)

class AUTHE1ToAUTHE2Transformer(BaseTransformer):
    """Transform data from AUTHE1.0 to AUTHE2.0 format"""
    
    def __init__(self):
        super().__init__("AUTHE1.0", "AUTHE2.0")
        self.setup_field_mappings()
        self.setup_enum_mappings()
    
    def setup_field_mappings(self):
        """Setup field mappings between AUTHE1.0 and AUTHE2.0"""
        self.user_field_mappings = {
            "id": "user_id",
            "username": "username",
            "email": "email_address",
            "password_hash": "password_hash",
            "given_name": "first_name",
            "family_name": "last_name",
            "display_name": "user_profile.display_name",
            "phone": "phone_number",
            "created_at": "created_timestamp",
            "updated_at": "last_updated_timestamp",
            "last_login": "last_login_timestamp"
        }
        
        self.role_field_mappings = {
            "id": "role_id",
            "name": "role_name",
            "description": "description"
        }
    
    def setup_enum_mappings(self):
        """Setup enum value mappings"""
        self.status_mapping = {
            "active": "enabled",
            "inactive": "disabled",
            "suspended": "locked",
            "pending": "disabled"
        }
    
    def transform_user(self, source_user: Dict[str, Any]) -> Dict[str, Any]:
        """Transform AUTHE1.0 user to AUTHE2.0 format"""
        try:
            # Apply basic field mappings
            transformed = self.apply_field_mapping(source_user, self.user_field_mappings)
            
            # Handle status transformation
            if "account_status" in source_user:
                transformed["state"] = self.transform_enum_value(
                    source_user["account_status"], 
                    self.status_mapping
                )
            
            # Handle verification flags
            transformed["email_verified"] = source_user.get("is_verified", False)
            transformed["phone_verified"] = False  # AUTHE1.0 doesn't track this
            transformed["mfa_enabled"] = False  # Default for AUTHE1.0
            
            # Transform roles - extract role IDs from role objects
            if "assigned_roles" in source_user:
                transformed["roles"] = [
                    role.get("role_id", "") for role in source_user["assigned_roles"]
                ]
            
            # Transform permissions
            if "custom_permissions" in source_user:
                transformed["permissions"] = source_user["custom_permissions"]
            
            # Handle address transformation
            if "personal_info" in source_user:
                personal_info = source_user["personal_info"]
                if "address" in personal_info:
                    transformed["address"] = personal_info["address"]
            
            # Transform extended attributes
            attributes = {}
            if "personal_info" in source_user:
                personal_info = source_user["personal_info"]
                attributes.update({
                    "department": personal_info.get("department"),
                    "job_title": personal_info.get("job_title"),
                    "employee_id": personal_info.get("employee_id")
                })
            
            transformed["attributes"] = attributes
            
            # Handle custom fields
            transformed["custom_fields"] = source_user.get("preferences", {})
            
            # System fields
            transformed["tenant"] = source_user.get("tenant_id")
            transformed["source"] = "AUTHE2.0"
            transformed["external_id"] = source_user.get("user_id")
            
            # Audit fields
            transformed["created_by"] = source_user.get("created_by")
            transformed["updated_by"] = source_user.get("last_modified_by")
            
            # Transform datetime fields
            for field in ["created_at", "updated_at", "last_login"]:
                if field in transformed and transformed[field]:
                    transformed[field] = self.transform_datetime(transformed[field])
            
            # Generate new ID for AUTHE2.0
            transformed["id"] = self.generate_id("authe2_", source_user.get("user_id", ""))
            
            return transformed
            
        except Exception as e:
            logger.error(f"Error transforming user {source_user.get('user_id', 'unknown')}: {str(e)}")
            raise
    
    def transform_role(self, source_role: Dict[str, Any]) -> Dict[str, Any]:
        """Transform AUTHE1.0 role to AUTHE2.0 format"""
        try:
            # Apply basic field mappings
            transformed = self.apply_field_mapping(source_role, self.role_field_mappings)
            
            # Transform permissions to AUTHE2.0 format
            if "permissions" in source_role:
                authe2_permissions = []
                for perm in source_role["permissions"]:
                    authe2_permissions.append({
                        "permission_id": self.generate_id("perm_", perm),
                        "resource": perm.split(":")[0] if ":" in perm else "unknown",
                        "action": perm.split(":")[1] if ":" in perm else perm,
                        "scope": None
                    })
                transformed["permissions"] = authe2_permissions
            
            # System role flag
            transformed["is_system_role"] = False
            
            # Generate new ID
            transformed["id"] = self.generate_id("role_", source_role.get("role_id", ""))
            
            return transformed
            
        except Exception as e:
            logger.error(f"Error transforming role {source_role.get('role_id', 'unknown')}: {str(e)}")
            raise
    
    def transform_group(self, source_group: Dict[str, Any]) -> Dict[str, Any]:
        """Transform AUTHE1.0 group to AUTHE2.0 format"""
        try:
            transformed = {
                "id": self.generate_id("group_", source_group.get("group_id", "")),
                "name": source_group.get("group_name", ""),
                "description": source_group.get("description"),
                "type": "security",
                "parent_id": source_group.get("parent_group_id"),
                "members": source_group.get("member_user_ids", []),
                "roles": [role.get("role_id", "") for role in source_group.get("group_roles", [])],
                "created_at": self.transform_datetime(source_group.get("created_timestamp")),
                "updated_at": self.transform_datetime(source_group.get("last_updated_timestamp"))
            }
            
            return transformed
            
        except Exception as e:
            logger.error(f"Error transforming group {source_group.get('group_id', 'unknown')}: {str(e)}")
            raise
    
    def get_required_fields(self) -> List[str]:
        """Get required fields for AUTHE2.0"""
        return ["id", "username", "email", "given_name", "family_name", "created_at"]
    
    def validate_business_rules(self, source_data: Dict[str, Any], transformed_data: Dict[str, Any]) -> bool:
        """Validate AUTHE2.0 specific business rules"""
        # Email format validation
        email = transformed_data.get("email", "")
        if not email or "@" not in email:
            logger.error("Invalid email format")
            return False
        
        # Username uniqueness (would need database check in real implementation)
        username = transformed_data.get("username", "")
        if not username or len(username) < 3:
            logger.error("Username must be at least 3 characters")
            return False
        
        return True