-- Migration: Add User Management and Admin User
-- Description: Adds user management capabilities and creates the admin user
-- Date: 2024-01-15

-- Add is_active column to user_profiles for enable/disable functionality
ALTER TABLE user_profiles 
ADD COLUMN IF NOT EXISTS is_active boolean DEFAULT true;

-- Create index for active users
CREATE INDEX IF NOT EXISTS idx_user_profiles_is_active ON user_profiles(is_active);

-- Create a function to check if user is admin
CREATE OR REPLACE FUNCTION is_user_admin(user_id uuid)
RETURNS boolean AS $$
BEGIN
  RETURN EXISTS (
    SELECT 1 FROM user_profiles 
    WHERE id = user_id AND role = 'admin'
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create a function to check if user can manage other users
CREATE OR REPLACE FUNCTION can_manage_users(user_id uuid)
RETURNS boolean AS $$
BEGIN
  RETURN is_user_admin(user_id);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Add RLS policy for admins to view all users in their tenant
CREATE POLICY "Admins can view all users in their tenant"
  ON user_profiles FOR SELECT
  TO authenticated
  USING (
    tenant_id IN (
      SELECT tenant_id FROM user_profiles 
      WHERE id = auth.uid() AND role = 'admin'
    )
  );

-- Add RLS policy for admins to insert users in their tenant
CREATE POLICY "Admins can insert users in their tenant"
  ON user_profiles FOR INSERT
  TO authenticated
  WITH CHECK (
    tenant_id IN (
      SELECT tenant_id FROM user_profiles 
      WHERE id = auth.uid() AND role = 'admin'
    )
  );

-- Add RLS policy for admins to update users in their tenant
CREATE POLICY "Admins can update users in their tenant"
  ON user_profiles FOR UPDATE
  TO authenticated
  USING (
    tenant_id IN (
      SELECT tenant_id FROM user_profiles 
      WHERE id = auth.uid() AND role = 'admin'
    )
  )
  WITH CHECK (
    tenant_id IN (
      SELECT tenant_id FROM user_profiles 
      WHERE id = auth.uid() AND role = 'admin'
    )
  );

-- Add RLS policy for admins to delete users in their tenant
CREATE POLICY "Admins can delete users in their tenant"
  ON user_profiles FOR DELETE
  TO authenticated
  USING (
    tenant_id IN (
      SELECT tenant_id FROM user_profiles 
      WHERE id = auth.uid() AND role = 'admin'
    )
  );

-- Create admin tenant if it doesn't exist
INSERT INTO tenants (id, name, settings)
VALUES (
  'a0000000-0000-0000-0000-000000000001'::uuid,
  'Admin Organization',
  '{"is_system_tenant": true}'::jsonb
)
ON CONFLICT (id) DO NOTHING;

-- Note: The admin user will be created through Supabase Auth
-- This is a placeholder for documentation purposes
-- The actual user creation should be done via:
-- 1. Supabase Dashboard > Authentication > Users > Add User
-- 2. Or via Supabase Auth API with the following details:
--    Email: cc@siwahtcom
--    Password: Hola173!
--    
-- After creating the auth user, insert the profile:
-- INSERT INTO user_profiles (id, tenant_id, full_name, role, is_active)
-- VALUES (
--   '<auth_user_id>',
--   'a0000000-0000-0000-0000-000000000001',
--   'System Administrator',
--   'admin',
--   true
-- );

-- Create a function to safely create admin user profile
CREATE OR REPLACE FUNCTION create_admin_user_profile(
  p_user_id uuid,
  p_email text,
  p_full_name text DEFAULT 'System Administrator'
)
RETURNS void AS $$
BEGIN
  INSERT INTO user_profiles (id, tenant_id, full_name, role, is_active)
  VALUES (
    p_user_id,
    'a0000000-0000-0000-0000-000000000001'::uuid,
    p_full_name,
    'admin',
    true
  )
  ON CONFLICT (id) DO UPDATE
  SET role = 'admin',
      is_active = true,
      tenant_id = 'a0000000-0000-0000-0000-000000000001'::uuid;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create audit log table for user management actions
CREATE TABLE IF NOT EXISTS user_management_audit (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  performed_by uuid NOT NULL REFERENCES auth.users(id),
  action text NOT NULL CHECK (action IN ('create', 'update', 'delete', 'disable', 'enable')),
  target_user_id uuid NOT NULL,
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  changes jsonb DEFAULT '{}'::jsonb,
  created_at timestamptz DEFAULT now()
);

ALTER TABLE user_management_audit ENABLE ROW LEVEL SECURITY;

CREATE INDEX IF NOT EXISTS idx_user_management_audit_tenant ON user_management_audit(tenant_id);
CREATE INDEX IF NOT EXISTS idx_user_management_audit_performed_by ON user_management_audit(performed_by);
CREATE INDEX IF NOT EXISTS idx_user_management_audit_target ON user_management_audit(target_user_id);

-- RLS policy for audit log - admins can view audit logs in their tenant
CREATE POLICY "Admins can view audit logs in their tenant"
  ON user_management_audit FOR SELECT
  TO authenticated
  USING (
    tenant_id IN (
      SELECT tenant_id FROM user_profiles 
      WHERE id = auth.uid() AND role = 'admin'
    )
  );

-- Function to log user management actions
CREATE OR REPLACE FUNCTION log_user_management_action(
  p_action text,
  p_target_user_id uuid,
  p_changes jsonb DEFAULT '{}'::jsonb
)
RETURNS void AS $$
DECLARE
  v_tenant_id uuid;
BEGIN
  -- Get the tenant_id of the current user
  SELECT tenant_id INTO v_tenant_id
  FROM user_profiles
  WHERE id = auth.uid();

  -- Insert audit log
  INSERT INTO user_management_audit (
    performed_by,
    action,
    target_user_id,
    tenant_id,
    changes
  )
  VALUES (
    auth.uid(),
    p_action,
    p_target_user_id,
    v_tenant_id,
    p_changes
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Add comment for documentation
COMMENT ON TABLE user_management_audit IS 'Audit log for all user management actions performed by admins';
COMMENT ON FUNCTION create_admin_user_profile IS 'Creates or updates a user profile with admin role';
COMMENT ON FUNCTION log_user_management_action IS 'Logs user management actions for audit trail';
COMMENT ON FUNCTION is_user_admin IS 'Checks if a user has admin role';
COMMENT ON FUNCTION can_manage_users IS 'Checks if a user can manage other users';
