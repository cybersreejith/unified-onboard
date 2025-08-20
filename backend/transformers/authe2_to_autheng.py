from typing import Dict, Any, List
from datetime import datetime
from .base_transformer import BaseTransformer
import logging

logger = logging.getLogger(__name__)

class AUTHE2ToAUTHENGTransformer(BaseTransformer):
    """Transform data from AUTHE2.0 to AUTHENG format"""
    
    def __init__(self):
        super().__init__("AUTHE2.0", "AUTHENG")
        self.setup_field_mappings()
        self.setup_enum_mappings()
    
    def setup_field_mappings(self):
        """Setup field mappings between AUTHE2.0 and AUTHENG"""
        self.user_field_mappings = {
            "user_uuid": "id",
            "login_id": "username",
            "primary_email": "email",
            "password_hash": "password_hash",
            "full_name": "display_name",
            "business_phone": "phone",
            "mobile_phone": "mobile"
        }
    
    def setup_enum_mappings(self):
        """Setup enum value mappings"""
        self.status_mapping = {
            "enabled": "ACTIVE",
            "disabled": "INACTIVE",
            "locked": "SUSPENDED",
            "expired": "INACTIVE"
        }
        
        self.security_level_mapping = {
            "basic": "LOW",
            "standard": "MEDIUM",
            "elevated": "HIGH",
            "admin": "CRITICAL"
        }
    
    def transform_user(self, source_user: Dict[str, Any]) -> Dict[str, Any]:
        """Transform AUTHE2.0 user to AUTHENG format"""
        try:
            # Apply basic field mappings
            transformed = self.apply_field_mapping(source_user, self.user_field_mappings)
            
            # Generate employee number
            transformed["employee_number"] = f"EMP{source_user.get('id', '')[-6:]}"
            
            # Handle name fields
            transformed["full_name"] = f"{source_user.get('given_name', '')} {source_user.get('family_name', '')}".strip()
            transformed["preferred_name"] = source_user.get("nickname")
            
            # Handle secondary emails
            transformed["secondary_emails"] = []
            
            # Handle addresses
            if "address" in source_user and source_user["address"]:
                transformed["business_address"] = source_user["address"]
                transformed["home_address"] = source_user["address"]  # Assume same for now
            
            # Employment information from attributes
            attributes = source_user.get("attributes", {})
            transformed.update({
                "organization_unit": attributes.get("department", "UNKNOWN"),
                "department_code": attributes.get("department", "UNK"),
                "position_title": attributes.get("job_title", "Employee"),
                "employment_type": "FULL_TIME",  # Default
                "manager_uuid": attributes.get("manager_id"),
                "direct_reports": [],
                "cost_center_code": attributes.get("cost_center", "DEFAULT"),
                "location_code": "HQ"  # Default
            })
            
            # Account status transformation
            transformed["account_status"] = self.transform_enum_value(
                source_user.get("state", "enabled"),
                self.status_mapping
            )
            
            # Security flags
            transformed["account_locked"] = source_user.get("state") == "locked"
            transformed["password_expired"] = False  # Default
            transformed["must_change_password"] = False  # Default
            transformed["failed_login_count"] = 0  # Default
            
            # Security profile
            security_profile = {
                "security_clearance": "MEDIUM",  # Default
                "background_check_date": None,
                "security_training_completed": False,
                "access_card_number": None,
                "biometric_enrolled": source_user.get("mfa_enabled", False)
            }
            transformed["security_profile"] = security_profile
            
            # Transform timestamps
            transformed["account_created_date"] = self.transform_datetime(source_user.get("created_at"))
            transformed["account_modified_date"] = self.transform_datetime(source_user.get("updated_at"))
            transformed["last_successful_login"] = self.transform_datetime(source_user.get("last_login"))
            transformed["last_failed_login"] = None
            transformed["password_last_changed"] = None
            transformed["account_expiry_date"] = None
            
            # Transform roles to AUTHENG format
            assigned_roles = []
            for role_id in source_user.get("roles", []):
                autheng_role = {
                    "role_code": role_id,
                    "role_title": role_id.replace("_", " ").title(),
                    "role_category": "BUSINESS",
                    "access_rights": [],
                    "security_level": "MEDIUM",
                    "is_delegatable": False
                }
                assigned_roles.append(autheng_role)
            
            transformed["assigned_roles"] = assigned_roles
            transformed["delegated_roles"] = []
            transformed["temporary_access"] = []
            
            # System integration fields
            transformed["active_directory_dn"] = None
            transformed["ldap_dn"] = None
            transformed["saml_name_id"] = source_user.get("id")
            transformed["oauth_subject"] = source_user.get("id")
            transformed["external_system_ids"] = {
                "authe2_id": source_user.get("id", ""),
                "external_id": source_user.get("external_id", "")
            }
            
            # Compliance information
            compliance_info = {
                "gdpr_consent": True,  # Assume consent
                "data_retention_policy": "STANDARD_7_YEARS",
                "audit_trail_enabled": True,
                "compliance_tags": ["GDPR", "SOX"],
                "last_compliance_review": None
            }
            transformed["compliance_info"] = compliance_info
            
            # Audit metadata
            transformed["audit_metadata"] = {
                "migrated_from": "AUTHE2.0",
                "migration_date": datetime.now().isoformat(),
                "original_id": source_user.get("id")
            }
            
            # Custom attributes
            transformed["custom_attributes"] = source_user.get("custom_fields", {})
            
            # Generate new UUID
            transformed["user_uuid"] = self.generate_id("", source_user.get("id", ""))
            
            return transformed
            
        except Exception as e:
            logger.error(f"Error transforming user {source_user.get('id', 'unknown')}: {str(e)}")
            raise
    
    def transform_role(self, source_role: Dict[str, Any]) -> Dict[str, Any]:
        """Transform AUTHE2.0 role to AUTHENG format"""
        try:
            # Transform permissions to access rights
            access_rights = []
            for perm in source_role.get("permissions", []):
                access_right = {
                    "resource_id": perm.get("resource", "unknown"),
                    "resource_type": "APPLICATION",
                    "operations": [perm.get("action", "read")],
                    "conditions": {},
                    "effective_from": None,
                    "effective_until": None
                }
                access_rights.append(access_right)
            
            transformed = {
                "role_code": source_role.get("id", ""),
                "role_title": source_role.get("name", ""),
                "role_category": "BUSINESS",
                "access_rights": access_rights,
                "security_level": "MEDIUM",  # Default
                "is_delegatable": not source_role.get("is_system_role", False)
            }
            
            return transformed
            
        except Exception as e:
            logger.error(f"Error transforming role {source_role.get('id', 'unknown')}: {str(e)}")
            raise
    
    def transform_group(self, source_group: Dict[str, Any]) -> Dict[str, Any]:
        """Transform AUTHE2.0 group to AUTHENG organization unit"""
        try:
            transformed = {
                "unit_uuid": self.generate_id("", source_group.get("id", "")),
                "unit_code": source_group.get("name", "").upper().replace(" ", "_"),
                "unit_name": source_group.get("name", ""),
                "parent_unit_uuid": source_group.get("parent_id"),
                "unit_type": source_group.get("type", "DEPARTMENT"),
                "manager_uuid": None,  # Would need additional logic
                "cost_center": "DEFAULT",
                "location": "HQ",
                "created_date": self.transform_datetime(source_group.get("created_at")),
                "modified_date": self.transform_datetime(source_group.get("updated_at"))
            }
            
            return transformed
            
        except Exception as e:
            logger.error(f"Error transforming group {source_group.get('id', 'unknown')}: {str(e)}")
            raise
    
    def get_required_fields(self) -> List[str]:
        """Get required fields for AUTHENG"""
        return [
            "user_uuid", "employee_number", "login_id", "primary_email",
            "full_name", "organization_unit", "department_code", "position_title",
            "employment_type", "account_status", "security_profile", "compliance_info"
        ]
    
    def validate_business_rules(self, source_data: Dict[str, Any], transformed_data: Dict[str, Any]) -> bool:
        """Validate AUTHENG specific business rules"""
        # Employee number format validation
        emp_num = transformed_data.get("employee_number", "")
        if not emp_num.startswith("EMP"):
            logger.error("Employee number must start with 'EMP'")
            return False
        
        # Security profile validation
        security_profile = transformed_data.get("security_profile", {})
        if not isinstance(security_profile, dict):
            logger.error("Security profile must be a dictionary")
            return False
        
        # Compliance info validation
        compliance_info = transformed_data.get("compliance_info", {})
        if not isinstance(compliance_info, dict):
            logger.error("Compliance info must be a dictionary")
            return False
        
        return True