from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any, Union
from datetime import datetime
from enum import Enum

class AUTHENGUserStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"
    DELETED = "DELETED"

class AUTHENGSecurityLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class AUTHENGAccessRight(BaseModel):
    resource_id: str = Field(..., description="Resource identifier")
    resource_type: str = Field(..., description="Resource type")
    operations: List[str] = Field(..., description="Allowed operations")
    conditions: Optional[Dict[str, Any]] = Field(None, description="Access conditions")
    effective_from: Optional[datetime] = Field(None, description="Effective from date")
    effective_until: Optional[datetime] = Field(None, description="Effective until date")

class AUTHENGRole(BaseModel):
    role_code: str = Field(..., description="Role code")
    role_title: str = Field(..., description="Role title")
    role_category: str = Field(..., description="Role category")
    access_rights: List[AUTHENGAccessRight] = Field(default=[], description="Access rights")
    security_level: AUTHENGSecurityLevel = Field(..., description="Security level")
    is_delegatable: bool = Field(default=False, description="Can be delegated")

class AUTHENGSecurityProfile(BaseModel):
    security_clearance: AUTHENGSecurityLevel = Field(..., description="Security clearance level")
    background_check_date: Optional[datetime] = Field(None, description="Background check date")
    security_training_completed: bool = Field(default=False, description="Security training status")
    access_card_number: Optional[str] = Field(None, description="Physical access card number")
    biometric_enrolled: bool = Field(default=False, description="Biometric enrollment status")

class AUTHENGComplianceInfo(BaseModel):
    gdpr_consent: bool = Field(default=False, description="GDPR consent status")
    data_retention_policy: str = Field(..., description="Data retention policy")
    audit_trail_enabled: bool = Field(default=True, description="Audit trail enabled")
    compliance_tags: List[str] = Field(default=[], description="Compliance tags")
    last_compliance_review: Optional[datetime] = Field(None, description="Last compliance review")

class AUTHENGUser(BaseModel):
    """AUTHENG User Schema - Enterprise format with compliance and security focus"""
    user_uuid: str = Field(..., description="Unique user UUID")
    employee_number: str = Field(..., description="Employee number")
    login_id: str = Field(..., description="Login identifier")
    primary_email: str = Field(..., description="Primary email address")
    secondary_emails: List[str] = Field(default=[], description="Secondary email addresses")
    password_hash: str = Field(..., description="Password hash")
    
    # Personal Details
    full_name: str = Field(..., description="Full name")
    preferred_name: Optional[str] = Field(None, description="Preferred name")
    name_prefix: Optional[str] = Field(None, description="Name prefix (Mr., Ms., Dr., etc.)")
    name_suffix: Optional[str] = Field(None, description="Name suffix (Jr., Sr., III, etc.)")
    
    # Contact Information
    business_phone: Optional[str] = Field(None, description="Business phone")
    mobile_phone: Optional[str] = Field(None, description="Mobile phone")
    home_phone: Optional[str] = Field(None, description="Home phone")
    business_address: Optional[Dict[str, str]] = Field(None, description="Business address")
    home_address: Optional[Dict[str, str]] = Field(None, description="Home address")
    
    # Employment Information
    organization_unit: str = Field(..., description="Organization unit")
    department_code: str = Field(..., description="Department code")
    position_title: str = Field(..., description="Position title")
    employment_type: str = Field(..., description="Employment type")
    manager_uuid: Optional[str] = Field(None, description="Manager UUID")
    direct_reports: List[str] = Field(default=[], description="Direct report UUIDs")
    cost_center_code: str = Field(..., description="Cost center code")
    location_code: str = Field(..., description="Location code")
    
    # Account Status and Security
    account_status: AUTHENGUserStatus = Field(..., description="Account status")
    account_locked: bool = Field(default=False, description="Account locked status")
    password_expired: bool = Field(default=False, description="Password expired status")
    must_change_password: bool = Field(default=False, description="Must change password flag")
    failed_login_count: int = Field(default=0, description="Failed login attempts")
    security_profile: AUTHENGSecurityProfile = Field(..., description="Security profile")
    
    # Timestamps
    account_created_date: datetime = Field(..., description="Account creation date")
    account_modified_date: datetime = Field(..., description="Last modification date")
    last_successful_login: Optional[datetime] = Field(None, description="Last successful login")
    last_failed_login: Optional[datetime] = Field(None, description="Last failed login")
    password_last_changed: Optional[datetime] = Field(None, description="Password last changed")
    account_expiry_date: Optional[datetime] = Field(None, description="Account expiry date")
    
    # Authorization
    assigned_roles: List[AUTHENGRole] = Field(default=[], description="Assigned roles")
    delegated_roles: List[AUTHENGRole] = Field(default=[], description="Delegated roles")
    temporary_access: List[AUTHENGAccessRight] = Field(default=[], description="Temporary access rights")
    
    # System Integration
    active_directory_dn: Optional[str] = Field(None, description="Active Directory DN")
    ldap_dn: Optional[str] = Field(None, description="LDAP Distinguished Name")
    saml_name_id: Optional[str] = Field(None, description="SAML Name ID")
    oauth_subject: Optional[str] = Field(None, description="OAuth subject identifier")
    external_system_ids: Dict[str, str] = Field(default={}, description="External system identifiers")
    
    # Compliance and Audit
    compliance_info: AUTHENGComplianceInfo = Field(..., description="Compliance information")
    audit_metadata: Dict[str, Any] = Field(default={}, description="Audit metadata")
    
    # Custom Extensions
    custom_attributes: Dict[str, Union[str, int, bool, List[str]]] = Field(default={}, description="Custom attributes")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class AUTHENGOrganizationUnit(BaseModel):
    """AUTHENG Organization Unit Schema"""
    unit_uuid: str = Field(..., description="Unit UUID")
    unit_code: str = Field(..., description="Unit code")
    unit_name: str = Field(..., description="Unit name")
    parent_unit_uuid: Optional[str] = Field(None, description="Parent unit UUID")
    unit_type: str = Field(..., description="Unit type")
    manager_uuid: Optional[str] = Field(None, description="Manager UUID")
    cost_center: str = Field(..., description="Cost center")
    location: str = Field(..., description="Location")
    created_date: datetime = Field(..., description="Creation date")
    modified_date: datetime = Field(..., description="Modification date")

class AUTHENGAccessPolicy(BaseModel):
    """AUTHENG Access Policy Schema"""
    policy_uuid: str = Field(..., description="Policy UUID")
    policy_name: str = Field(..., description="Policy name")
    policy_type: str = Field(..., description="Policy type")
    resource_pattern: str = Field(..., description="Resource pattern")
    allowed_operations: List[str] = Field(..., description="Allowed operations")
    conditions: Dict[str, Any] = Field(default={}, description="Policy conditions")
    priority: int = Field(default=100, description="Policy priority")
    effective_from: datetime = Field(..., description="Effective from")
    effective_until: Optional[datetime] = Field(None, description="Effective until")
    created_by: str = Field(..., description="Created by")
    approved_by: Optional[str] = Field(None, description="Approved by")

class AUTHENGAuditEvent(BaseModel):
    """AUTHENG Audit Event Schema"""
    event_uuid: str = Field(..., description="Event UUID")
    event_type: str = Field(..., description="Event type")
    user_uuid: str = Field(..., description="User UUID")
    resource_id: Optional[str] = Field(None, description="Resource ID")
    action: str = Field(..., description="Action performed")
    result: str = Field(..., description="Action result")
    timestamp: datetime = Field(..., description="Event timestamp")
    source_ip: Optional[str] = Field(None, description="Source IP address")
    user_agent: Optional[str] = Field(None, description="User agent")
    session_id: Optional[str] = Field(None, description="Session ID")
    additional_data: Dict[str, Any] = Field(default={}, description="Additional event data")