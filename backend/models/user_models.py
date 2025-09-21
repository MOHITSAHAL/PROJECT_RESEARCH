"""Pydantic models for user management and authentication."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr, validator


class UserBase(BaseModel):
    """Base user model with common fields."""
    username: str = Field(..., min_length=3, max_length=50, regex="^[a-zA-Z0-9_-]+$")
    email: EmailStr
    full_name: Optional[str] = Field(None, max_length=200)
    affiliation: Optional[str] = Field(None, max_length=200)


class UserCreate(UserBase):
    """Model for user registration."""
    password: str = Field(..., min_length=8, max_length=100)
    research_interests: Optional[List[str]] = None
    preferred_frameworks: Optional[List[str]] = None
    experience_level: str = Field("intermediate", regex="^(beginner|intermediate|expert)$")
    
    @validator("password")
    def validate_password(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserUpdate(BaseModel):
    """Model for updating user information."""
    full_name: Optional[str] = Field(None, max_length=200)
    affiliation: Optional[str] = Field(None, max_length=200)
    research_interests: Optional[List[str]] = None
    preferred_frameworks: Optional[List[str]] = None
    experience_level: Optional[str] = Field(None, regex="^(beginner|intermediate|expert)$")
    notification_preferences: Optional[Dict[str, bool]] = None


class UserResponse(UserBase):
    """Model for user API responses."""
    id: str
    is_active: bool
    is_verified: bool
    last_login: Optional[datetime] = None
    
    # Profile
    research_interests: Optional[List[str]] = None
    preferred_frameworks: Optional[List[str]] = None
    experience_level: str
    
    # Usage metrics
    total_queries: int = 0
    total_agents_created: int = 0
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """Model for user login."""
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class Token(BaseModel):
    """Model for authentication tokens."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user_id: str
    username: str


class TokenData(BaseModel):
    """Model for token payload data."""
    user_id: Optional[str] = None
    username: Optional[str] = None
    email: Optional[str] = None


class UserPreferences(BaseModel):
    """Model for user preferences."""
    research_interests: List[str] = []
    preferred_frameworks: List[str] = []
    experience_level: str = "intermediate"
    notification_preferences: Dict[str, bool] = {
        "new_papers": True,
        "agent_updates": True,
        "implementation_guides": True,
        "research_trends": False,
        "collaboration_invites": True
    }
    dashboard_layout: Dict[str, Any] = {}
    
    class Config:
        from_attributes = True


class UserDashboard(BaseModel):
    """Model for user dashboard data."""
    user_id: str
    
    # Personalized content
    personalized_papers: List[Dict[str, Any]] = []
    active_agents: List[Dict[str, Any]] = []
    recent_conversations: List[Dict[str, Any]] = []
    
    # Research progress
    research_progress: Dict[str, Any] = {}
    trending_in_interests: List[Dict[str, Any]] = []
    
    # Implementation tutorials
    implementation_tutorials: List[Dict[str, Any]] = []
    saved_tutorials: List[Dict[str, Any]] = []
    
    # Recommendations
    recommended_papers: List[Dict[str, Any]] = []
    recommended_agents: List[Dict[str, Any]] = []
    
    # Statistics
    usage_stats: Dict[str, Any] = {}
    
    class Config:
        from_attributes = True


class UserActivity(BaseModel):
    """Model for user activity tracking."""
    user_id: str
    activity_type: str = Field(..., regex="^(login|query|agent_create|paper_view|tutorial_access)$")
    activity_data: Dict[str, Any] = {}
    timestamp: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class UserNotification(BaseModel):
    """Model for user notifications."""
    id: str
    user_id: str
    notification_type: str = Field(..., regex="^(new_paper|agent_update|tutorial|trend|system)$")
    title: str
    message: str
    data: Optional[Dict[str, Any]] = None
    is_read: bool = False
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserStats(BaseModel):
    """Model for user statistics."""
    user_id: str
    
    # Usage statistics
    total_queries: int = 0
    total_agents_created: int = 0
    total_papers_viewed: int = 0
    total_tutorials_accessed: int = 0
    
    # Time-based statistics
    queries_this_week: int = 0
    queries_this_month: int = 0
    active_days_this_month: int = 0
    
    # Quality metrics
    average_session_duration: Optional[float] = None  # minutes
    favorite_research_areas: List[str] = []
    most_used_frameworks: List[str] = []
    
    # Engagement metrics
    agent_interaction_rate: Optional[float] = None
    tutorial_completion_rate: Optional[float] = None
    
    class Config:
        from_attributes = True


class PasswordReset(BaseModel):
    """Model for password reset requests."""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Model for password reset confirmation."""
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)
    
    @validator("new_password")
    def validate_password(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserInvite(BaseModel):
    """Model for user invitations."""
    email: EmailStr
    invited_by: str
    role: str = Field("user", regex="^(user|admin|researcher)$")
    message: Optional[str] = Field(None, max_length=500)