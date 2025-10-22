"""
Fine-Grained Access Control (FGAC) Module

Enforces tenant isolation at the data access layer.
CRITICAL: All data queries MUST be filtered by tenant_id to prevent cross-tenant data leakage.
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


class FGACEnforcer:
    """
    Fine-Grained Access Control Enforcer
    
    Ensures that all data access is properly scoped to the authenticated tenant.
    This is the PRIMARY security mechanism for multi-tenant data isolation.
    """
    
    @staticmethod
    def validate_tenant_access(
        resource_tenant_id: str,
        user_tenant_id: str,
        resource_type: str = "resource"
    ) -> bool:
        """
        Validate that a user has access to a resource
        
        Args:
            resource_tenant_id: Tenant ID of the resource
            user_tenant_id: Tenant ID of the authenticated user
            resource_type: Type of resource (for logging)
            
        Returns:
            True if access is allowed
            
        Raises:
            HTTPException: If access is denied
        """
        if resource_tenant_id != user_tenant_id:
            logger.warning(
                f"FGAC violation: User from tenant {user_tenant_id} "
                f"attempted to access {resource_type} from tenant {resource_tenant_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: {resource_type} belongs to different tenant",
            )
        
        return True
    
    @staticmethod
    def filter_by_tenant(
        items: List[Dict[str, Any]],
        tenant_id: str,
        tenant_field: str = "tenant_id"
    ) -> List[Dict[str, Any]]:
        """
        Filter a list of items by tenant_id
        
        Args:
            items: List of items to filter
            tenant_id: Tenant ID to filter by
            tenant_field: Name of the tenant ID field
            
        Returns:
            Filtered list containing only items for the specified tenant
        """
        filtered = [
            item for item in items
            if item.get(tenant_field) == tenant_id
        ]
        
        if len(filtered) < len(items):
            logger.warning(
                f"FGAC filter removed {len(items) - len(filtered)} items "
                f"not belonging to tenant {tenant_id}"
            )
        
        return filtered
    
    @staticmethod
    def build_tenant_filter(tenant_id: str, field_name: str = "tenant_id") -> Dict[str, str]:
        """
        Build a filter dictionary for tenant isolation
        
        Args:
            tenant_id: Tenant ID to filter by
            field_name: Name of the tenant ID field
            
        Returns:
            Filter dictionary for use in database queries
        """
        return {field_name: tenant_id}
    
    @staticmethod
    def validate_metadata_has_tenant(
        metadata: Dict[str, Any],
        tenant_id: str,
        strict: bool = True
    ) -> bool:
        """
        Validate that metadata contains the correct tenant_id
        
        Args:
            metadata: Metadata dictionary to validate
            tenant_id: Expected tenant ID
            strict: If True, raise exception on mismatch. If False, return False.
            
        Returns:
            True if metadata is valid
            
        Raises:
            HTTPException: If strict=True and validation fails
        """
        metadata_tenant_id = metadata.get("tenant_id")
        
        if not metadata_tenant_id:
            logger.error("Metadata missing tenant_id field")
            if strict:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid metadata: missing tenant_id",
                )
            return False
        
        if metadata_tenant_id != tenant_id:
            logger.error(
                f"Metadata tenant_id mismatch: expected {tenant_id}, "
                f"got {metadata_tenant_id}"
            )
            if strict:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid metadata: tenant_id mismatch",
                )
            return False
        
        return True
    
    @staticmethod
    def inject_tenant_id(
        data: Dict[str, Any],
        tenant_id: str,
        field_name: str = "tenant_id",
        overwrite: bool = False
    ) -> Dict[str, Any]:
        """
        Inject tenant_id into data dictionary
        
        Args:
            data: Data dictionary to modify
            tenant_id: Tenant ID to inject
            field_name: Name of the tenant ID field
            overwrite: If True, overwrite existing tenant_id. If False, validate match.
            
        Returns:
            Modified data dictionary
            
        Raises:
            HTTPException: If tenant_id exists and doesn't match (when overwrite=False)
        """
        existing_tenant_id = data.get(field_name)
        
        if existing_tenant_id and not overwrite:
            if existing_tenant_id != tenant_id:
                logger.error(
                    f"Attempted to inject tenant_id {tenant_id} but data already "
                    f"contains different tenant_id {existing_tenant_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Data contains conflicting tenant_id",
                )
        
        data[field_name] = tenant_id
        return data
    
    @staticmethod
    def create_vector_search_filter(
        tenant_id: str,
        additional_filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a filter for vector similarity search with mandatory tenant isolation
        
        CRITICAL: This filter MUST be applied to ALL vector search queries
        
        Args:
            tenant_id: Tenant ID to filter by
            additional_filters: Optional additional filters to combine
            
        Returns:
            Combined filter dictionary
        """
        base_filter = {"tenant_id": tenant_id}
        
        if additional_filters:
            # Ensure tenant_id cannot be overridden
            if "tenant_id" in additional_filters:
                logger.warning(
                    "Attempted to override tenant_id in additional_filters - ignoring"
                )
                additional_filters = {
                    k: v for k, v in additional_filters.items()
                    if k != "tenant_id"
                }
            
            base_filter.update(additional_filters)
        
        logger.debug(f"Created vector search filter: {base_filter}")
        return base_filter
    
    @staticmethod
    def audit_log_access(
        user_id: str,
        tenant_id: str,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        success: bool = True,
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create an audit log entry for data access
        
        Args:
            user_id: ID of the user performing the action
            tenant_id: Tenant ID
            action: Action being performed (e.g., "read", "write", "delete")
            resource_type: Type of resource being accessed
            resource_id: Optional ID of the specific resource
            success: Whether the action was successful
            details: Optional additional details
            
        Returns:
            Audit log entry dictionary
        """
        from datetime import datetime
        
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "tenant_id": tenant_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "success": success,
            "details": details or {},
        }
        
        logger.info(f"Audit log: {log_entry}")
        return log_entry


# Convenience functions for common FGAC operations

def require_tenant_match(resource_tenant_id: str, user_tenant_id: str) -> None:
    """
    Require that resource and user tenant IDs match
    
    Raises:
        HTTPException: If tenant IDs don't match
    """
    FGACEnforcer.validate_tenant_access(resource_tenant_id, user_tenant_id)


def get_tenant_filter(tenant_id: str) -> Dict[str, str]:
    """
    Get a tenant filter for database queries
    
    Args:
        tenant_id: Tenant ID
        
    Returns:
        Filter dictionary
    """
    return FGACEnforcer.build_tenant_filter(tenant_id)


def get_vector_filter(tenant_id: str, **kwargs) -> Dict[str, Any]:
    """
    Get a filter for vector similarity search with tenant isolation
    
    Args:
        tenant_id: Tenant ID
        **kwargs: Additional filter parameters
        
    Returns:
        Combined filter dictionary
    """
    return FGACEnforcer.create_vector_search_filter(tenant_id, kwargs if kwargs else None)
