# Admin User Quick Reference Card 🚀

## Admin Credentials
```
Email:    cc@siwaht.com
Password: Hola173!
```

## Quick Setup (5 Steps)

### 1. Apply Migration
```bash
supabase db push
```

### 2. Create Auth User
- Go to Supabase Dashboard > Authentication > Users
- Click "Add user"
- Email: `cc@siwaht.com`
- Password: `Hola173!`
- ✅ Auto Confirm User
- **Copy the User ID**

### 3. Create Profile
```sql
-- Replace <USER_ID> with actual UUID
SELECT setup_admin_user_profile(
  '<USER_ID>'::uuid,
  'cc@siwaht.com',
  'System Administrator'
);
```

### 4. Update Metadata
```sql
-- Replace <USER_ID> with actual UUID
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

### 5. Verify
```sql
SELECT * FROM verify_admin_setup();
SELECT * FROM admin_users;
```

## Quick Verification Queries

### Check Admin User
```sql
SELECT id, email, role, is_active 
FROM user_profiles 
WHERE email = 'cc@siwaht.com';
```

### View All Users
```sql
SELECT email, role, is_active 
FROM user_profiles 
ORDER BY created_at DESC;
```

### Check Audit Log
```sql
SELECT action, target_user_id, created_at 
FROM user_management_audit 
ORDER BY created_at DESC 
LIMIT 5;
```

## Permission Levels

| Role | Manage Users | Upload Docs | Delete Docs | View Analytics |
|------|--------------|-------------|-------------|----------------|
| 🔴 Admin | ✅ | ✅ | ✅ | ✅ |
| 🔵 User | ❌ | ✅ | ✅ | ✅ |
| ⚪ Viewer | ❌ | ❌ | ❌ | ✅ |

## Testing Checklist

- [ ] Login as admin (cc@siwaht.com)
- [ ] See "ADMIN" badge in sidebar
- [ ] Access "User Management" page
- [ ] Create test user
- [ ] Edit user role
- [ ] Toggle user status
- [ ] Delete test user

## Troubleshooting

### Can't see "User Management"?
```sql
-- Check role
SELECT role FROM user_profiles WHERE email = 'cc@siwaht.com';

-- Fix if needed
UPDATE user_profiles SET role = 'admin' WHERE email = 'cc@siwaht.com';
```

### Access Denied?
```sql
-- Check if active
SELECT is_active FROM user_profiles WHERE email = 'cc@siwaht.com';

-- Activate if needed
UPDATE user_profiles SET is_active = true WHERE email = 'cc@siwaht.com';
```

### Can't create users?
Check backend `.env`:
```env
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
```

## API Endpoints

```bash
# Get current user
GET /api/users/me

# List all users (admin only)
GET /api/users

# Create user (admin only)
POST /api/users
{
  "email": "user@example.com",
  "password": "Password123!",
  "full_name": "User Name",
  "role": "user"
}

# Update user (admin only)
PUT /api/users/{id}
{
  "role": "admin",
  "full_name": "Updated Name"
}

# Toggle status (admin only)
PATCH /api/users/{id}/status
{
  "is_active": false
}

# Delete user (admin only)
DELETE /api/users/{id}
```

## Test Script

```bash
python test_user_management.py
```

## Documentation

- **Full Setup Guide:** `USER_MANAGEMENT_SETUP_GUIDE.md`
- **Complete Verification:** `USER_MANAGEMENT_VERIFICATION_COMPLETE.md`
- **Migration File:** `supabase/migrations/20240115000001_setup_admin_user.sql`

## Support

If issues persist:
1. Check backend logs
2. Check browser console (F12)
3. Run verification queries
4. Review setup guide

---

**Need Help?** See `USER_MANAGEMENT_SETUP_GUIDE.md` for detailed instructions and troubleshooting.
