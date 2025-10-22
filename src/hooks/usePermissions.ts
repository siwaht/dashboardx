/**
 * usePermissions Hook
 * 
 * Custom hook for checking user permissions based on role.
 * Provides helper functions for role-based access control.
 */

import { useAuth } from '../contexts/AuthContext';

export function usePermissions() {
  const { profile } = useAuth();

  /**
   * Check if current user is an admin
   */
  const isAdmin = (): boolean => {
    return profile?.role === 'admin';
  };

  /**
   * Check if current user can manage other users
   */
  const canManageUsers = (): boolean => {
    return isAdmin();
  };

  /**
   * Check if current user can delete documents
   */
  const canDeleteDocuments = (): boolean => {
    return isAdmin() || profile?.role === 'user';
  };

  /**
   * Check if current user can upload documents
   */
  const canUploadDocuments = (): boolean => {
    return isAdmin() || profile?.role === 'user';
  };

  /**
   * Check if current user can manage data sources
   */
  const canManageDataSources = (): boolean => {
    return isAdmin();
  };

  /**
   * Check if current user can view analytics
   */
  const canViewAnalytics = (): boolean => {
    return isAdmin() || profile?.role === 'user';
  };

  /**
   * Check if current user has a specific role
   */
  const hasRole = (role: 'admin' | 'user' | 'viewer'): boolean => {
    return profile?.role === role;
  };

  /**
   * Check if current user has at least a certain role level
   * Role hierarchy: admin > user > viewer
   */
  const hasMinimumRole = (minimumRole: 'admin' | 'user' | 'viewer'): boolean => {
    if (!profile?.role) return false;

    const roleHierarchy = {
      admin: 3,
      user: 2,
      viewer: 1,
    };

    return roleHierarchy[profile.role] >= roleHierarchy[minimumRole];
  };

  /**
   * Check if current user is active
   */
  const isActive = (): boolean => {
    return profile?.is_active === true;
  };

  return {
    isAdmin,
    canManageUsers,
    canDeleteDocuments,
    canUploadDocuments,
    canManageDataSources,
    canViewAnalytics,
    hasRole,
    hasMinimumRole,
    isActive,
    role: profile?.role,
  };
}
