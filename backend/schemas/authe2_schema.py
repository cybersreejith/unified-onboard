from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum

class AUTHE2UserState(str, Enum):
    ENABLED = "enabled"
    DISABLED = "disabled"
    LOCKED = "locked"
    EXPIRED = "expired"

class AUTHE2Permission(BaseModel):
    permission_id: str = Field(..., description="Permission identifier")
    resource: str = Field(..., description="Resource name")
    action: str = Field(..., description="Action type (read, write, delete, etc.)")
    scope: Optional[str] = Field(None, description="Permission scope")

class AUTHE2Role(BaseModel):
    id: str = Field(..., description="Role identifier")
    name: str = Field(..., description="Role name")
    description: Optional[str] = Field(None, description="Role description")
    permissions: List[AUTHE2Permission] = Field(default=[], description="Role permissions")
    is_system_role: bool = Field(default=False, description="System role flag")

class AUTHE2UserAttributes(BaseModel):
    department: Optional[str] = Field(None, description="Department")
    job_title: Optional[str] = Field(None, description="Job title")
    manager_id: Optional[str] = Field(None, description="Manager user ID")
    cost_center: Optional[str] = Field(None, description="Cost center")
    employee_id: Optional[str] = Field(None, description="Employee ID")
    hire_date: Optional[datetime] = Field(None, description="Hire date")
    termination_date: Optional[datetime] = Field(None, description="Termination date")

class AUTHE2User(BaseModel):
    """AUTHE2.0 User Schema - Modern format with flattened structure"""
    id: str = Field(..., description="Unique user identifier")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    password_hash: str = Field(..., description="Password hash")
    
    # Basic Information
    given_name: str = Field(..., description="Given name (first name)")
    family_name: str = Field(..., description="Family name (last name)")
    display_name: str = Field(..., description="Display name")
    nickname: Optional[str] = Field(None, description="Nickname")
    
    # Contact Information
    phone: Optional[str] = Field(None, description="Phone number")
    mobile: Optional[str] = Field(None, description="Mobile number")
    address: Optional[Dict[str, str]] = Field(None, description="Address information")
    
    # Account Status
    state: AUTHE2UserState = Field(default=AUTHE2UserState.ENABLED, description="User state")
    email_verified: bool = Field(default=False, description="Email verification status")
    phone_verified: bool = Field(default=False, description="Phone verification status")
    mfa_enabled: bool = Field(default=False, description="MFA enabled status")
    
    # Timestamps (ISO format)
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    password_changed_at: Optional[datetime] = Field(None, description="Password change timestamp")
    
    # Authorization
    roles: List[str] = Field(default=[], description="Assigned role IDs")
    permissions: List[str] = Field(default=[], description="Direct permission IDs")
    groups: List[str] = Field(default=[], description="Group memberships")
    
    # Extended Attributes
    attributes: AUTHE2UserAttributes = Field(default_factory=AUTHE2UserAttributes, description="Extended user attributes")
    custom_fields: Dict[str, Any] = Field(default={}, description="Custom fields")
    
    # System Fields
    tenant: Optional[str] = Field(None, description="Tenant identifier")
    source: str = Field(default="AUTHE2.0", description="Source system")
    external_id: Optional[str] = Field(None, description="External system ID")
    
    # Audit
    created_by: Optional[str] = Field(None, description="Created by user")
    updated_by: Optional[str] = Field(None, description="Updated by user")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class AUTHE2Group(BaseModel):
    """AUTHE2.0 Group Schema"""
    id: str = Field(..., description="Group identifier")
    name: str = Field(..., description="Group name")
    description: Optional[str] = Field(None, description="Group description")
    type: str = Field(default="security", description="Group type")
    parent_id: Optional[str] = Field(None, description="Parent group ID")
    members: List[str] = Field(default=[], description="Member user IDs")
    roles: List[str] = Field(default=[], description="Assigned role IDs")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Update timestamp")
    
class AUTHE2Application(BaseModel):
    """AUTHE2.0 Application Schema"""
    id: str = Field(..., description="Application identifier")
    name: str = Field(..., description="Application name")
    client_id: str = Field(..., description="OAuth client ID")
    client_secret: str = Field(..., description="OAuth client secret")
    redirect_uris: List[str] = Field(default=[], description="Redirect URIs")
    allowed_scopes: List[str] = Field(default=[], description="Allowed OAuth scopes")
    token_lifetime: int = Field(default=3600, description="Token lifetime in seconds")
    refresh_token_lifetime: int = Field(default=86400, description="Refresh token lifetime")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Update timestamp")

class AUTHE2Token(BaseModel):
    """AUTHE2.0 Token Schema"""
    id: str = Field(..., description="Token identifier")
    user_id: str = Field(..., description="Associated user ID")
    application_id: str = Field(..., description="Associated application ID")
    token_type: str = Field(..., description="Token type (access, refresh)")
    token_value: str = Field(..., description="Token value")
    scopes: List[str] = Field(default=[], description="Token scopes")
    expires_at: datetime = Field(..., description="Expiration timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")
    revoked: bool = Field(default=False, description="Revocation status")