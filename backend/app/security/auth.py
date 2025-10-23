"""
Authentication Module

Handles JWT token verification and user authentication.
Extracts tenant_id from JWT tokens for FGAC enforcement.
"""

import logging
from typing import Dict, Optional
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

from app.config import settings

logger = logging.getLogger(__name__)

# Validate JWT secret is configured at module load time
if not settings.supabase_jwt_secret:
    raise ValueError("SUPABASE_JWT_SECRET must be configured. Please set it in your environment variables.")

# Security scheme
security = HTTPBearer()


class AuthenticatedUser:
    """Represents an authenticated user with tenant context"""
    
    def __init__(self, user_id: str, tenant_id: str, email: Optional[str] = None, role: Optional[str] = None):
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.email = email
        self.role = role
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary"""
        return {
            "user_id": self.user_id,
            "tenant_id": self.tenant_id,
            "email": self.email or "",
            "role": self.role or "user",
        }
    
    def __repr__(self) -> str:
        return f"AuthenticatedUser(user_id={self.user_id}, tenant_id={self.tenant_id})"


async def verify_token(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> Dict[str, str]:
    """
    Verify JWT token and extract user information
    
    Args:
        credentials: HTTP Bearer token credentials
        
    Returns:
        Dictionary containing user_id, tenant_id, email, and role
        
    Raises:
        HTTPException: If token is invalid or missing required claims
    """
    try:
        token = credentials.credentials
        
        # Decode JWT token
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=[settings.jwt_algorithm],
            audience="authenticated",
        )
        
        # Extract user ID (sub claim)
        user_id: str = payload.get("sub")
        if not user_id:
            logger.warning("Token missing 'sub' claim")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Extract email
        email: Optional[str] = payload.get("email")
        
        # Extract role from app_metadata or user_metadata
        app_metadata = payload.get("app_metadata", {})
        user_metadata = payload.get("user_metadata", {})
        role: Optional[str] = app_metadata.get("role") or user_metadata.get("role")
        
        # Extract tenant_id
        # First check app_metadata, then user_metadata, then custom claim
        tenant_id: Optional[str] = (
            app_metadata.get("tenant_id") or
            user_metadata.get("tenant_id") or
            payload.get("tenant_id")
        )
        
        if not tenant_id:
            logger.warning(f"Token for user {user_id} missing tenant_id")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing tenant ID",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        logger.info(f"Authenticated user: {user_id} (tenant: {tenant_id})")
        
        return {
            "user_id": user_id,
            "tenant_id": tenant_id,
            "email": email or "",
            "role": role or "user",
        }
        
    except JWTError as e:
        logger.error(f"JWT verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Unexpected error during token verification: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> AuthenticatedUser:
    """
    Get current authenticated user
    
    Args:
        credentials: HTTP Bearer token credentials
        
    Returns:
        AuthenticatedUser object with user and tenant information
    """
    user_data = await verify_token(credentials)
    
    return AuthenticatedUser(
        user_id=user_data["user_id"],
        tenant_id=user_data["tenant_id"],
        email=user_data.get("email"),
        role=user_data.get("role"),
    )


def verify_admin_role(user: AuthenticatedUser) -> bool:
    """
    Verify if user has admin role
    
    Args:
        user: Authenticated user
        
    Returns:
        True if user is admin
        
    Raises:
        HTTPException: If user is not admin
    """
    if user.role != "admin":
        logger.warning(f"User {user.user_id} attempted admin action without admin role")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return True


async def get_current_admin_user(
    user: AuthenticatedUser = Security(get_current_user)
) -> AuthenticatedUser:
    """
    Get current user and verify admin role
    
    Args:
        user: Authenticated user
        
    Returns:
        AuthenticatedUser object if user is admin
        
    Raises:
        HTTPException: If user is not admin
    """
    verify_admin_role(user)
    return user


def extract_tenant_id_from_token(token: str) -> Optional[str]:
    """
    Extract tenant_id from JWT token without full verification
    Useful for logging and debugging
    
    Args:
        token: JWT token string
        
    Returns:
        Tenant ID if found, None otherwise
    """
    try:
        # Decode without verification (for debugging only)
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=[settings.jwt_algorithm],
            options={"verify_signature": False},
        )
        
        app_metadata = payload.get("app_metadata", {})
        user_metadata = payload.get("user_metadata", {})
        
        return (
            app_metadata.get("tenant_id") or
            user_metadata.get("tenant_id") or
            payload.get("tenant_id")
        )
    except Exception:
        return None
