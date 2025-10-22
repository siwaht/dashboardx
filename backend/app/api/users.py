"""
User Management API

Provides endpoints for admin users to manage other users within their tenant.
Includes CRUD operations and user status management.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Security, status, Depends
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

from app.security.auth import get_current_user, get_current_admin_user, AuthenticatedUser
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== Pydantic Models ====================

class UserBase(BaseModel):
    """Base user model"""
    email: EmailStr
    full_name: Optional[str] = None
    role: str = Field(default="user", pattern="^(admin|user|viewer)$")


class UserCreate(UserBase):
    """Model for creating a new user"""
    password: str = Field(min_length=8)
    tenant_id: Optional[str] = None  # Optional, defaults to admin's tenant


class UserUpdate(BaseModel):
    """Model for updating a user"""
    full_name: Optional[str] = None
    role: Optional[str] = Field(None, pattern="^(admin|user|viewer)$")
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    """User response model"""
    id: str
    email: str
    full_name: Optional[str]
    role: str
    tenant_id: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class UserStatusUpdate(BaseModel):
    """Model for updating user status"""
    is_active: bool


# ==================== Helper Functions ====================

async def get_supabase_admin_client():
    """
    Get Supabase admin client for user management
    This requires the service role key
    """
    from supabase import create_client, Client
    
    supabase_url = settings.supabase_url
    supabase_service_key = settings.supabase_service_role_key
    
    if not supabase_service_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Supabase service role key not configured"
        )
    
    return create_client(supabase_url, supabase_service_key)


async def log_audit_action(
    supabase_client,
    action: str,
    target_user_id: str,
    changes: dict = None
):
    """Log user management action to audit table"""
    try:
        await supabase_client.rpc(
            'log_user_management_action',
            {
                'p_action': action,
                'p_target_user_id': target_user_id,
                'p_changes': changes or {}
            }
        ).execute()
    except Exception as e:
        logger.error(f"Failed to log audit action: {e}")


# ==================== API Endpoints ====================

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: AuthenticatedUser = Security(get_current_user)
):
    """
    Get current user's profile
    
    Returns:
        Current user's profile information
    """
    try:
        supabase = await get_supabase_admin_client()
        
        response = supabase.table('user_profiles').select('*').eq('id', current_user.user_id).single().execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        return response.data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user profile"
        )


@router.get("/", response_model=List[UserResponse])
async def list_users(
    admin_user: AuthenticatedUser = Security(get_current_admin_user),
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    role: Optional[str] = None,
    is_active: Optional[bool] = None
):
    """
    List all users in the admin's tenant
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        search: Search term for email or name
        role: Filter by role
        is_active: Filter by active status
        
    Returns:
        List of users in the tenant
    """
    try:
        supabase = await get_supabase_admin_client()
        
        # Build query
        query = supabase.table('user_profiles').select('*').eq('tenant_id', admin_user.tenant_id)
        
        # Apply filters
        if role:
            query = query.eq('role', role)
        if is_active is not None:
            query = query.eq('is_active', is_active)
        if search:
            query = query.or_(f'email.ilike.%{search}%,full_name.ilike.%{search}%')
        
        # Apply pagination
        query = query.range(skip, skip + limit - 1).order('created_at', desc=True)
        
        response = query.execute()
        
        logger.info(f"Admin {admin_user.user_id} listed {len(response.data)} users")
        
        return response.data
        
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list users"
        )


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    admin_user: AuthenticatedUser = Security(get_current_admin_user)
):
    """
    Create a new user in the admin's tenant
    
    Args:
        user_data: User creation data
        
    Returns:
        Created user profile
    """
    try:
        supabase = await get_supabase_admin_client()
        
        # Use admin's tenant if not specified
        tenant_id = user_data.tenant_id or admin_user.tenant_id
        
        # Verify admin can create users in this tenant
        if tenant_id != admin_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot create users in other tenants"
            )
        
        # Create auth user
        auth_response = supabase.auth.admin.create_user({
            "email": user_data.email,
            "password": user_data.password,
            "email_confirm": True,
            "user_metadata": {
                "full_name": user_data.full_name,
                "role": user_data.role
            }
        })
        
        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create auth user"
            )
        
        # Create user profile
        profile_data = {
            "id": auth_response.user.id,
            "tenant_id": tenant_id,
            "full_name": user_data.full_name,
            "role": user_data.role,
            "is_active": True
        }
        
        profile_response = supabase.table('user_profiles').insert(profile_data).execute()
        
        if not profile_response.data:
            # Rollback: delete auth user if profile creation fails
            try:
                supabase.auth.admin.delete_user(auth_response.user.id)
            except:
                pass
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user profile"
            )
        
        # Log audit action
        await log_audit_action(
            supabase,
            'create',
            auth_response.user.id,
            {'email': user_data.email, 'role': user_data.role}
        )
        
        logger.info(f"Admin {admin_user.user_id} created user {auth_response.user.id}")
        
        return profile_response.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    admin_user: AuthenticatedUser = Security(get_current_admin_user)
):
    """
    Get a specific user by ID
    
    Args:
        user_id: User ID to retrieve
        
    Returns:
        User profile
    """
    try:
        supabase = await get_supabase_admin_client()
        
        response = supabase.table('user_profiles').select('*').eq('id', user_id).eq('tenant_id', admin_user.tenant_id).single().execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return response.data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user"
        )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    admin_user: AuthenticatedUser = Security(get_current_admin_user)
):
    """
    Update a user's profile
    
    Args:
        user_id: User ID to update
        user_data: Updated user data
        
    Returns:
        Updated user profile
    """
    try:
        supabase = await get_supabase_admin_client()
        
        # Verify user exists and is in admin's tenant
        existing = supabase.table('user_profiles').select('*').eq('id', user_id).eq('tenant_id', admin_user.tenant_id).single().execute()
        
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Prevent admin from demoting themselves
        if user_id == admin_user.user_id and user_data.role and user_data.role != 'admin':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot change your own admin role"
            )
        
        # Build update data
        update_data = {}
        if user_data.full_name is not None:
            update_data['full_name'] = user_data.full_name
        if user_data.role is not None:
            update_data['role'] = user_data.role
        if user_data.is_active is not None:
            update_data['is_active'] = user_data.is_active
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )
        
        # Update profile
        response = supabase.table('user_profiles').update(update_data).eq('id', user_id).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update user"
            )
        
        # Log audit action
        await log_audit_action(
            supabase,
            'update',
            user_id,
            update_data
        )
        
        logger.info(f"Admin {admin_user.user_id} updated user {user_id}")
        
        return response.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )


@router.patch("/{user_id}/status", response_model=UserResponse)
async def update_user_status(
    user_id: str,
    status_data: UserStatusUpdate,
    admin_user: AuthenticatedUser = Security(get_current_admin_user)
):
    """
    Enable or disable a user
    
    Args:
        user_id: User ID to update
        status_data: Status update data
        
    Returns:
        Updated user profile
    """
    try:
        supabase = await get_supabase_admin_client()
        
        # Verify user exists and is in admin's tenant
        existing = supabase.table('user_profiles').select('*').eq('id', user_id).eq('tenant_id', admin_user.tenant_id).single().execute()
        
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Prevent admin from disabling themselves
        if user_id == admin_user.user_id and not status_data.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot disable your own account"
            )
        
        # Update status
        response = supabase.table('user_profiles').update({
            'is_active': status_data.is_active
        }).eq('id', user_id).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update user status"
            )
        
        # Log audit action
        action = 'enable' if status_data.is_active else 'disable'
        await log_audit_action(
            supabase,
            action,
            user_id,
            {'is_active': status_data.is_active}
        )
        
        logger.info(f"Admin {admin_user.user_id} {action}d user {user_id}")
        
        return response.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user status"
        )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    admin_user: AuthenticatedUser = Security(get_current_admin_user)
):
    """
    Delete a user (soft delete by disabling)
    
    Args:
        user_id: User ID to delete
    """
    try:
        supabase = await get_supabase_admin_client()
        
        # Verify user exists and is in admin's tenant
        existing = supabase.table('user_profiles').select('*').eq('id', user_id).eq('tenant_id', admin_user.tenant_id).single().execute()
        
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Prevent admin from deleting themselves
        if user_id == admin_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own account"
            )
        
        # Delete auth user (this will cascade to profile due to FK constraint)
        supabase.auth.admin.delete_user(user_id)
        
        # Log audit action
        await log_audit_action(
            supabase,
            'delete',
            user_id,
            {'email': existing.data.get('email')}
        )
        
        logger.info(f"Admin {admin_user.user_id} deleted user {user_id}")
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )
