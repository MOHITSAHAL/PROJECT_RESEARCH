"""
Security utilities for authentication and authorization.
AWS Cognito compatible for production migration.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from .config import settings


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify and decode JWT token."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError:
        return None


class SecurityManager:
    """Security manager for handling authentication and authorization."""
    
    def __init__(self):
        self.pwd_context = pwd_context
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user credentials."""
        # TODO: Implement user lookup from database
        # This is a placeholder for POC
        if username == "admin" and password == "admin":
            return {
                "user_id": "admin",
                "username": username,
                "email": "admin@example.com",
                "is_active": True
            }
        return None
    
    def create_user_token(self, user_data: Dict[str, Any]) -> str:
        """Create access token for authenticated user."""
        token_data = {
            "sub": user_data["user_id"],
            "username": user_data["username"],
            "email": user_data["email"]
        }
        return create_access_token(token_data)
    
    def get_current_user(self, token: str) -> Optional[Dict[str, Any]]:
        """Get current user from token."""
        payload = verify_token(token)
        if payload is None:
            return None
        
        return {
            "user_id": payload.get("sub"),
            "username": payload.get("username"),
            "email": payload.get("email")
        }


# Global security manager instance
security_manager = SecurityManager()