# User Management Setup Guide

This guide provides step-by-step instructions for setting up the admin user and testing the user management system.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Admin User Setup](#admin-user-setup)
3. [Verification Steps](#verification-steps)
4. [Testing User Management](#testing-user-management)
5. [Permission Levels](#permission-levels)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before setting up the admin user, ensure you have:

- ✅ Supabase project created and configured
- ✅ Database migrations applied (including `20240115000000_add_user_management_and_admin.sql` and `20240115000001_setup_admin_user.sql`)
- ✅ Backend environment variables configured (especially `SUPABASE_SERVICE_ROLE_KEY`)
- ✅ Frontend and backend applications running

---

## Admin User Setup

### Step 1: Run Database Migrations

First, ensure all migrations are applied to your Supabase database:

```bash
# If using Supabase CLI
supabase db push

# Or apply migrations manually in Supabase Dashboard > SQL Editor
```

### Step 2: Create Auth User in Supabase Dashboard

1. **Open Supabase Dashboard**
   - Navigate to your project at https://app.supabase.com
   - Go to **Authentication** > **Users**

2. **Add New User**
   - Click **"Add user"** button
   - Select **"Create new user"**
   - Fill in the details:
     - **Email**: `cc@siwaht.com`
     - **Password**: `Hola173!`
     - **Auto Confirm User**: ✅ (Check this box)
   - Click **"Create user"**

3. **Copy User ID**
   - After creation, you'll see the new user in the list
   - Copy the **User ID** (UUID format, e.g., `a1b2c3d4-e5f6-7890-abcd-ef1234567890`)
   - You'll need this for the next step

### Step 3: Create Admin Profile

Now create the admin profile linked to the auth user:

1. **Open SQL Editor** in Supabase Dashboard

2. **Run the Setup Function**:
   ```sql
   -- Replace <USER_ID> with the actual UUID you copied
   SELECT setup_admin_user_profile(
     '<USER_ID>'::uuid,
     'cc@siwaht.com',
     'System Administrator'
   );
   ```

   Example:
   ```sql
   SELECT setup_admin_user_profile(
     'a1b2c3d4-e5f6-7890-abcd-ef1234567890'::uuid,
     'cc@siwaht.com',
     'System Administrator'
   );
   ```

3. **Verify Success**
   - You should see a JSON response like:
   ```json
   {
     "status": "created",
     "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
     "message": "Admin profile created successfully"
   }
   ```

### Step 4: Update User Metadata (Important!)

For the admin role to work properly in JWT tokens, update the user metadata:

1. **In SQL Editor**, run:
   ```sql
   -- Replace <USER_ID> with your admin user ID
   UPDATE auth.users
   SET 
     raw_app_meta_data = jsonb_set(
       COALESCE(raw_app_meta_data, '{}'::jsonb),
       '{role}',
       '"admin"'
     ),
     raw_app_meta_data = jsonb_set(
       raw_app_meta_data,
       '{tenant_id}',
       '"a0000000-0000-0000-0000-000000000001"'
     )
   WHERE id = '<USER_ID>'::uuid;
   ```

   Example:
   ```sql
   UPDATE auth.users
   SET 
     raw_app_meta_data = jsonb_set(
       COALESCE(raw_app_meta_data, '{}'::jsonb),
       '{role}',
       '"admin"'
     ),
     raw_app_meta_data = jsonb_set(
       raw_app_meta_data,
       '{tenant_id}',
       '"a0000000-0000-0000-0000-000000000001"'
     )
   WHERE id = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'::uuid;
   ```

---

## Verification Steps

### Verify Database Setup

Run the verification function to check if everything is configured correctly:

```sql
SELECT * FROM verify_admin_setup();
```

Expected output:
```
check_name              | status | details
-----------------------|--------|------------------------------------------
Admin Tenant           | OK     | Admin tenant should exist with ID...
Admin User Profile     | OK     | At least one active admin user should...
RLS Policies           | OK     | Admin RLS policies should be configured
Audit Table            | OK     | User management audit table should exist
```

### View Admin Users

Check all admin users in the system:

```sql
SELECT * FROM admin_users;
```

You should see your admin user listed with:
- Email: `cc@siwaht.com`
- Role: `admin`
- Tenant: `Admin Organization`
- Active: `true`

---

## Testing User Management

### Test 1: Login as Admin

1. **Open the Application**
   - Navigate to your frontend URL (e.g., `http://localhost:5173`)

2. **Sign In**
   - Email: `cc@siwaht.com`
   - Password: `Hola173!`
   - Click **"Sign In"**

3. **Verify Admin Badge**
   - After login, you should see an **"ADMIN"** badge next to your name in the sidebar
   - The sidebar should show a **"User Management"** menu item

### Test 2: Access User Management Page

1. **Click "User Management"** in the sidebar
2. You should see the User Management page with:
   - A list of users (at least your admin user)
   - An **"Add User"** button
   - Search and filter options

### Test 3: Create a New User

1. **Click "Add User"** button
2. **Fill in the form**:
   - Email: `test.user@example.com`
   - Password: `TestPassword123!`
   - Full Name: `Test User`
   - Role: Select **"User"** (or any role)
3. **Click "Create"**
4. **Verify**:
   - New user appears in the list
   - User has the correct role badge

### Test 4: Edit User Role

1. **Find the test user** in the list
2. **Click "Edit"** button
3. **Change the role**:
   - Select **"Viewer"** from the role dropdown
4. **Click "Update"**
5. **Verify**:
   - User's role badge updates to "Viewer"

### Test 5: Toggle User Status

1. **Find a user** in the list
2. **Click the status badge** (Active/Inactive)
3. **Verify**:
   - Status changes color
   - User can/cannot log in based on status

### Test 6: Delete User

1. **Find the test user** in the list
2. **Click "Delete"** button
3. **Confirm deletion** in the dialog
4. **Verify**:
   - User is removed from the list

---

## Permission Levels

The system supports three permission levels:

### 🔴 Admin
**Full system access**
- ✅ Manage users (create, edit, delete)
- ✅ Assign roles and permissions
- ✅ Upload and delete documents
- ✅ Manage data sources
- ✅ View analytics
- ✅ Access all features

### 🔵 User
**Standard user access**
- ❌ Cannot manage users
- ✅ Upload and delete documents
- ✅ Use chat interface
- ✅ View analytics
- ✅ Access most features

### ⚪ Viewer
**Read-only access**
- ❌ Cannot manage users
- ❌ Cannot upload documents
- ✅ Use chat interface (read-only)
- ✅ View documents
- ❌ Limited feature access

---

## Troubleshooting

### Issue: Cannot see "User Management" menu

**Possible Causes:**
1. User role is not set to "admin"
2. JWT token doesn't include role metadata

**Solution:**
```sql
-- Verify user profile role
SELECT id, email, role, is_active FROM user_profiles WHERE email = 'cc@siwaht.com';

-- Update user metadata if needed
UPDATE auth.users
SET raw_app_meta_data = jsonb_set(
  COALESCE(raw_app_meta_data, '{}'::jsonb),
  '{role}',
  '"admin"'
)
WHERE email = 'cc@siwaht.com';

-- Log out and log back in to get new token
```

### Issue: "Access Denied" when accessing User Management

**Possible Causes:**
1. User is not active
2. RLS policies not properly configured

**Solution:**
```sql
-- Check if user is active
SELECT id, email, role, is_active FROM user_profiles WHERE email = 'cc@siwaht.com';

-- Activate user if needed
UPDATE user_profiles SET is_active = true WHERE email = 'cc@siwaht.com';

-- Verify RLS policies
SELECT * FROM verify_admin_setup();
```

### Issue: Cannot create new users

**Possible Causes:**
1. Backend service role key not configured
2. Supabase service role key missing or invalid

**Solution:**
1. Check backend `.env` file:
   ```env
   SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here
   ```
2. Get the service role key from Supabase Dashboard > Settings > API
3. Restart the backend server

### Issue: Created users cannot log in

**Possible Causes:**
1. User email not confirmed
2. User account is inactive

**Solution:**
```sql
-- Check user status
SELECT id, email, email_confirmed_at, is_active 
FROM auth.users u
JOIN user_profiles p ON u.id = p.id
WHERE u.email = 'user@example.com';

-- Confirm email if needed
UPDATE auth.users 
SET email_confirmed_at = now() 
WHERE email = 'user@example.com';

-- Activate user profile
UPDATE user_profiles 
SET is_active = true 
WHERE email = 'user@example.com';
```

### Issue: Role changes not taking effect

**Possible Cause:**
JWT token is cached and needs refresh

**Solution:**
1. Log out completely
2. Clear browser cache/cookies
3. Log back in
4. New token will include updated role

### Getting Help

If you encounter issues not covered here:

1. **Check Backend Logs**:
   ```bash
   # View backend logs
   cd backend
   python -m uvicorn app.main:app --reload
   ```

2. **Check Browser Console**:
   - Open Developer Tools (F12)
   - Look for errors in Console tab
   - Check Network tab for failed API calls

3. **Verify Database State**:
   ```sql
   -- Check admin users
   SELECT * FROM admin_users;
   
   -- Check all users
   SELECT id, email, role, is_active FROM user_profiles;
   
   -- Check audit log
   SELECT * FROM user_management_audit ORDER BY created_at DESC LIMIT 10;
   ```

4. **Test Backend API Directly**:
   ```bash
   # Get JWT token from browser (Application > Local Storage > supabase.auth.token)
   curl -H "Authorization: Bearer YOUR_JWT
