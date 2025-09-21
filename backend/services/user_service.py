"""User service for authentication and user management."""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from ..database.models import User
from ..models.user_models import (
    UserCreate, UserUpdate, UserResponse, UserLogin, Token, 
    UserDashboard, UserPreferences, UserStats
)
from ..core.security import security_manager, get_password_hash, verify_password
from ..core.logging import LoggerMixin
from ..core.config import settings


class UserService(LoggerMixin):
    """Service for user management and authentication."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_user(self, user_data: UserCreate) -> UserResponse:
        """Create a new user."""
        try:
            # Check if user already exists
            existing = self.db.query(User).filter(
                (User.username == user_data.username) | 
                (User.email == user_data.email)
            ).first()
            
            if existing:
                raise ValueError("User with this username or email already exists")
            
            # Create user
            user = User(
                username=user_data.username,
                email=user_data.email,
                hashed_password=get_password_hash(user_data.password),
                full_name=user_data.full_name,
                affiliation=user_data.affiliation,
                research_interests=user_data.research_interests or [],
                preferred_frameworks=user_data.preferred_frameworks or [],
                experience_level=user_data.experience_level
            )
            
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            
            self.log_event("user_created", user_id=user.id, username=user.username)
            return self._to_response(user)
            
        except Exception as e:
            self.db.rollback()
            self.log_error(e, operation="create_user")
            raise
    
    async def authenticate_user(self, login_data: UserLogin) -> Optional[Token]:
        """Authenticate user and return token."""
        try:
            # Find user by username or email
            user = self.db.query(User).filter(
                (User.username == login_data.username) | 
                (User.email == login_data.username)
            ).first()
            
            if not user or not user.is_active:
                return None
            
            # Verify password
            if not verify_password(login_data.password, user.hashed_password):
                return None
            
            # Update last login
            user.last_login = datetime.utcnow()
            self.db.commit()
            
            # Create token
            user_data = {
                "user_id": user.id,
                "username": user.username,
                "email": user.email,
                "is_active": user.is_active
            }
            
            access_token = security_manager.create_user_token(user_data)
            
            self.log_event("user_authenticated", user_id=user.id, username=user.username)
            
            return Token(
                access_token=access_token,
                token_type="bearer",
                expires_in=settings.access_token_expire_minutes * 60,
                user_id=user.id,
                username=user.username
            )
            
        except Exception as e:
            self.log_error(e, operation="authenticate_user")
            return None
    
    async def get_user(self, user_id: str) -> Optional[UserResponse]:
        """Get user by ID."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        return self._to_response(user)
    
    async def get_user_by_username(self, username: str) -> Optional[UserResponse]:
        """Get user by username."""
        user = self.db.query(User).filter(User.username == username).first()
        if not user:
            return None
        return self._to_response(user)
    
    async def update_user(self, user_id: str, user_update: UserUpdate) -> Optional[UserResponse]:
        """Update user information."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        update_data = user_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        self.db.commit()
        self.db.refresh(user)
        
        self.log_event("user_updated", user_id=user_id)
        return self._to_response(user)
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete user (soft delete by deactivating)."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        user.is_active = False
        self.db.commit()
        
        self.log_event("user_deleted", user_id=user_id)
        return True
    
    async def get_user_dashboard(self, user_id: str) -> Optional[UserDashboard]:
        """Get personalized dashboard data for user."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        # Get user's research interests
        interests = user.research_interests or []
        
        # Placeholder dashboard data (would be populated from actual services)
        dashboard_data = {
            "user_id": user_id,
            "personalized_papers": await self._get_personalized_papers(user),
            "active_agents": await self._get_user_agents(user_id),
            "recent_conversations": await self._get_recent_conversations(user_id),
            "research_progress": await self._get_research_progress(user),
            "trending_in_interests": await self._get_trending_papers(interests),
            "implementation_tutorials": await self._get_user_tutorials(user_id),
            "recommended_papers": await self._get_recommended_papers(user),
            "usage_stats": await self._get_usage_stats(user_id)
        }
        
        return UserDashboard(**dashboard_data)
    
    async def get_user_preferences(self, user_id: str) -> Optional[UserPreferences]:
        """Get user preferences."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        return UserPreferences(
            research_interests=user.research_interests or [],
            preferred_frameworks=user.preferred_frameworks or [],
            experience_level=user.experience_level,
            notification_preferences=user.notification_preferences or {},
            dashboard_layout={}  # Would be stored in user preferences
        )
    
    async def update_user_preferences(self, user_id: str, preferences: UserPreferences) -> bool:
        """Update user preferences."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        user.research_interests = preferences.research_interests
        user.preferred_frameworks = preferences.preferred_frameworks
        user.experience_level = preferences.experience_level
        user.notification_preferences = preferences.notification_preferences
        
        self.db.commit()
        
        self.log_event("user_preferences_updated", user_id=user_id)
        return True
    
    async def get_user_stats(self, user_id: str) -> Optional[UserStats]:
        """Get user statistics."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        # Calculate time-based statistics
        week_ago = datetime.utcnow() - timedelta(days=7)
        month_ago = datetime.utcnow() - timedelta(days=30)
        
        # Placeholder statistics (would query actual conversation and activity data)
        stats = UserStats(
            user_id=user_id,
            total_queries=user.total_queries,
            total_agents_created=user.total_agents_created,
            total_papers_viewed=0,  # Would be tracked in user activity
            total_tutorials_accessed=0,  # Would be tracked in user activity
            queries_this_week=0,  # Would query conversation data
            queries_this_month=0,  # Would query conversation data
            active_days_this_month=0,  # Would calculate from activity data
            favorite_research_areas=user.research_interests[:3] if user.research_interests else [],
            most_used_frameworks=user.preferred_frameworks[:3] if user.preferred_frameworks else []
        )
        
        return stats
    
    async def increment_user_query_count(self, user_id: str):
        """Increment user's query count."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            user.total_queries += 1
            self.db.commit()
    
    async def increment_user_agent_count(self, user_id: str):
        """Increment user's agent creation count."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            user.total_agents_created += 1
            self.db.commit()
    
    def _to_response(self, user: User) -> UserResponse:
        """Convert User model to response."""
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            affiliation=user.affiliation,
            is_active=user.is_active,
            is_verified=user.is_verified,
            last_login=user.last_login,
            research_interests=user.research_interests,
            preferred_frameworks=user.preferred_frameworks,
            experience_level=user.experience_level,
            total_queries=user.total_queries,
            total_agents_created=user.total_agents_created,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
    
    async def _get_personalized_papers(self, user: User) -> list:
        """Get personalized papers for user dashboard."""
        # Placeholder - would implement actual recommendation logic
        return [
            {
                "id": "paper_1",
                "title": "Recent Advances in Transformer Architecture",
                "relevance_score": 0.95,
                "reason": "Matches your interest in deep learning"
            }
        ]
    
    async def _get_user_agents(self, user_id: str) -> list:
        """Get user's active agents."""
        # Placeholder - would query actual agent data
        return [
            {
                "agent_id": "agent_1",
                "paper_title": "Attention Is All You Need",
                "agent_type": "interactive",
                "last_interaction": datetime.utcnow().isoformat()
            }
        ]
    
    async def _get_recent_conversations(self, user_id: str) -> list:
        """Get user's recent conversations."""
        # Placeholder - would query conversation data
        return [
            {
                "session_id": "session_1",
                "agent_id": "agent_1",
                "last_message": "Can you explain the attention mechanism?",
                "timestamp": datetime.utcnow().isoformat()
            }
        ]
    
    async def _get_research_progress(self, user: User) -> dict:
        """Get user's research progress."""
        return {
            "papers_read": 15,
            "agents_created": user.total_agents_created,
            "tutorials_completed": 3,
            "current_focus": user.research_interests[0] if user.research_interests else "General AI"
        }
    
    async def _get_trending_papers(self, interests: list) -> list:
        """Get trending papers in user's interests."""
        return [
            {
                "id": "trending_1",
                "title": "Latest Developments in Large Language Models",
                "trend_score": 0.9,
                "category": "cs.CL"
            }
        ]
    
    async def _get_user_tutorials(self, user_id: str) -> list:
        """Get user's implementation tutorials."""
        return [
            {
                "tutorial_id": "tutorial_1",
                "title": "Implementing Transformer from Scratch",
                "progress": 0.6,
                "framework": "pytorch"
            }
        ]
    
    async def _get_recommended_papers(self, user: User) -> list:
        """Get recommended papers for user."""
        return [
            {
                "id": "rec_1",
                "title": "Emerging Trends in Neural Architecture Search",
                "recommendation_score": 0.85,
                "reason": "Based on your reading history"
            }
        ]
    
    async def _get_usage_stats(self, user_id: str) -> dict:
        """Get user usage statistics."""
        return {
            "sessions_this_week": 5,
            "avg_session_duration": 25.5,  # minutes
            "most_active_day": "Tuesday",
            "preferred_time": "afternoon"
        }