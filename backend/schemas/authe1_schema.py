from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum

class AUTHE1UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"

class AUTHE1Role(BaseModel):
    role_id: str = Field(..., description="Unique role identifier")
    role_name: str = Field(..., description="Role name")
    permissions: List[str] = Field(default=[], description="List of permissions")
    description: Optional[str] = Field(None, description="Role description")

class AUTHE1UserProfile(BaseModel):
    profile_id: str = Field(..., description="Profile identifier")
    display_name: str = Field(..., description="Display name")
    avatar_url: Optional[str] = Field(None, description="Avatar image URL")
    bio: Optional[str] = Field(None, description="User biography")
    location: Optional[str] = Field(None, description="User location")
    website: Optional[str] = Field(None, description="User website")

class AUTHE1User(BaseModel):
    """AUTHE1.0 User Schema - Legacy format with nested structures"""
    user_id: str = Field(..., description="Unique user identifier")
    username: str = Field(..., description="Username for login")
    email_address: str = Field(..., description="Primary email address")
    password_hash: str = Field(..., description="Hashed password")
    
    # Personal Information
    personal_info: Dict[str, Any] = Field(default={}, description="Personal information")
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    middle_name: Optional[str] = Field(None, description="Middle name")
    date_of_birth: Optional[datetime] = Field(None, description="Date of birth")
    phone_number: Optional[str] = Field(None, description="Phone number")
    
    # Account Status
    account_status: AUTHE1UserStatus = Field(default=AUTHE1UserStatus.ACTIVE, description="Account status")
    is_verified: bool = Field(default=False, description="Email verification status")
    is_locked: bool = Field(default=False, description="Account lock status")
    failed_login_attempts: int = Field(default=0, description="Failed login attempts")
    
    # Timestamps
    created_timestamp: datetime = Field(..., description="Account creation timestamp")
    last_login_timestamp: Optional[datetime] = Field(None, description="Last login timestamp")
    last_updated_timestamp: datetime = Field(..., description="Last update timestamp")
    password_changed_timestamp: Optional[datetime] = Field(None, description="Password change timestamp")
    
    # Roles and Permissions
    assigned_roles: List[AUTHE1Role] = Field(default=[], description="Assigned roles")
    custom_permissions: List[str] = Field(default=[], description="Custom permissions")
    
    # Profile and Preferences
    user_profile: Optional[AUTHE1UserProfile] = Field(None, description="User profile information")
    preferences: Dict[str, Any] = Field(default={}, description="User preferences")
    
    # System Metadata
    tenant_id: Optional[str] = Field(None, description="Tenant identifier")
    source_system: str = Field(default="AUTHE1.0", description="Source system identifier")
    external_ids: Dict[str, str] = Field(default={}, description="External system identifiers")
    
    # Audit Trail
    created_by: Optional[str] = Field(None, description="Created by user ID")
    last_modified_by: Optional[str] = Field(None, description="Last modified by user ID")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class AUTHE1Group(BaseModel):
    """AUTHE1.0 Group Schema"""
    group_id: str = Field(..., description="Unique group identifier")
    group_name: str = Field(..., description="Group name")
    description: Optional[str] = Field(None, description="Group description")
    parent_group_id: Optional[str] = Field(None, description="Parent group ID for hierarchy")
    member_user_ids: List[str] = Field(default=[], description="List of member user IDs")
    group_roles: List[AUTHE1Role] = Field(default=[], description="Roles assigned to group")
    created_timestamp: datetime = Field(..., description="Group creation timestamp")
    last_updated_timestamp: datetime = Field(..., description="Last update timestamp")
    
class AUTHE1Session(BaseModel):
    """AUTHE1.0 Session Schema"""
    session_id: str = Field(..., description="Unique session identifier")
    user_id: str = Field(..., description="Associated user ID")
    session_token: str = Field(..., description="Session token")
    created_timestamp: datetime = Field(..., description="Session creation timestamp")
    expires_timestamp: datetime = Field(..., description="Session expiration timestamp")
    last_activity_timestamp: datetime = Field(..., description="Last activity timestamp")
    ip_address: Optional[str] = Field(None, description="Client IP address")
    user_agent: Optional[str] = Field(None, description="Client user agent")
    is_active: bool = Field(default=True, description="Session active status")