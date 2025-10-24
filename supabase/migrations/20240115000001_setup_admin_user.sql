-- Migration: Setup Admin User
-- Description: Creates the admin user (cc@siwaht.com) with proper profile and permissions
-- Date: 2024-01-15
-- 
-- IMPORTANT: This migration requires manual steps in Supabase Dashboard
-- See USER_MANAGEMENT_SETUP_GUIDE.md for complete instructions

-- Ensure the admin tenant exists
INSERT INTO tenants (id, name, settings)
VALUES (
  'a0000000-0000-0000-0000-000000000001'::uuid,
  'Admin Organization',
  '{"is_system_tenant": true}'::jsonb
)
ON CONFLICT (id) DO UPDATE
SET name = 'Admin Organization',
    settings = '{"is_system_tenant": true}'::jsonb;

-- Create a helper function to setup admin user after auth user is created
CREATE OR REPLACE FUNCTION setup_admin_user_profile(
  p_user_id uuid,
  p_email text DEFAULT 'cc@siwaht.com',
  p_full_name text DEFAULT 'System Administrator'
)
RETURNS jsonb AS $$
DECLARE
  v_result jsonb;
BEGIN
  -- Check if user profile already exists
  IF EXISTS (SELECT 1 FROM user_profiles WHERE id = p_user_id) THEN
    -- Update existing profile to ensure admin role
    UPDATE user_profiles
    SET 
      role = 'admin',
      is_active = true,
      tenant_id = 'a0000000-0000-0000-0000-000000000001'::uuid,
      full_name = COALESCE(full_name, p_full_name),
      updated_at = now()
    WHERE id = p_user_id;
    
    v_result = jsonb_build_object(
      'status', 'updated',
      'user_id', p_user_id,
      'message', 'Admin profile updated successfully'
    );
  ELSE
    -- Create new admin profile
    INSERT INTO user_profiles (id, tenant_id, full_name, role, is_active)
    VALUES (
      p_user_id,
      'a0000000-0000-0000-0000-000000000001'::uuid,
      p_full_name,
      'admin',
      true
    );
    
    v_result = jsonb_build_object(
      'status', 'created',
      'user_id', p_user_id,
      'message', 'Admin profile created successfully'
    );
  END IF;
  
  RETURN v_result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute permission on the function
GRANT EXECUTE ON FUNCTION setup_admin_user_profile TO authenticated;
GRANT EXECUTE ON FUNCTION setup_admin_user_profile TO service_role;

-- Create a function to verify admin setup
CREATE OR REPLACE FUNCTION verify_admin_setup()
RETURNS TABLE (
  check_name text,
  status text,
  details text
) AS $$
BEGIN
  -- Check if admin tenant exists
  RETURN QUERY
  SELECT 
    'Admin Tenant'::text,
    CASE 
      WHEN EXISTS (SELECT 1 FROM tenants WHERE id = 'a0000000-0000-0000-0000-000000000001'::uuid)
      THEN 'OK'::text
      ELSE 'MISSING'::text
    END,
    'Admin tenant should exist with ID a0000000-0000-0000-0000-000000000001'::text;
  
  -- Check if admin user exists
  RETURN QUERY
  SELECT 
    'Admin User Profile'::text,
    CASE 
      WHEN EXISTS (
        SELECT 1 FROM user_profiles 
        WHERE role = 'admin' 
        AND tenant_id = 'a0000000-0000-0000-0000-000000000001'::uuid
        AND is_active = true
      )
      THEN 'OK'::text
      ELSE 'MISSING'::text
    END,
    'At least one active admin user should exist in admin tenant'::text;
  
  -- Check RLS policies
  RETURN QUERY
  SELECT 
    'RLS Policies'::text,
    CASE 
      WHEN EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'user_profiles' 
        AND policyname LIKE '%admin%'
      )
      THEN 'OK'::text
      ELSE 'MISSING'::text
    END,
    'Admin RLS policies should be configured'::text;
  
  -- Check audit table
  RETURN QUERY
  SELECT 
    'Audit Table'::text,
    CASE 
      WHEN EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_name = 'user_management_audit'
      )
      THEN 'OK'::text
      ELSE 'MISSING'::text
    END,
    'User management audit table should exist'::text;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute permission
GRANT EXECUTE ON FUNCTION verify_admin_setup TO authenticated;
GRANT EXECUTE ON FUNCTION verify_admin_setup TO service_role;

-- Add helpful comments
COMMENT ON FUNCTION setup_admin_user_profile IS 'Sets up or updates admin user profile. Call this after creating auth user in Supabase Dashboard.';
COMMENT ON FUNCTION verify_admin_setup IS 'Verifies that admin user management system is properly configured.';

-- Create a view for easy admin user lookup (for debugging)
CREATE OR REPLACE VIEW admin_users AS
SELECT 
  up.id,
  up.email,
  up.full_name,
  up.role,
  up.tenant_id,
  up.is_active,
  up.created_at,
  up.updated_at,
  t.name as tenant_name
FROM user_profiles up
JOIN tenants t ON up.tenant_id = t.id
WHERE up.role = 'admin'
ORDER BY up.created_at;

-- Grant access to the view
GRANT SELECT ON admin_users TO authenticated;
GRANT SELECT ON admin_users TO service_role;

COMMENT ON VIEW admin_users IS 'View of all admin users across all tenants for easy lookup and debugging.';

-- Log migration completion
DO $$
BEGIN
  RAISE NOTICE 'Admin user setup migration completed successfully';
  RAISE NOTICE 'Next steps:';
  RAISE NOTICE '1. Create auth user in Supabase Dashboard with email: cc@siwaht.com';
  RAISE NOTICE '2. Run: SELECT setup_admin_user_profile(<user_id>, ''cc@siwaht.com'', ''System Administrator'');';
  RAISE NOTICE '3. Verify setup: SELECT * FROM verify_admin_setup();';
  RAISE NOTICE '4. View admin users: SELECT * FROM admin_users;';
END $$;
