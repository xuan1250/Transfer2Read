-- Admin Dashboard Helper Functions
-- Execute this in Supabase SQL Editor

-- Function: Count total users in auth.users
CREATE OR REPLACE FUNCTION count_total_users()
RETURNS integer
LANGUAGE sql
SECURITY DEFINER
AS $$
  SELECT COUNT(*)::integer FROM auth.users;
$$;

-- Grant execute permission to authenticated users (admin endpoints will validate superuser separately)
GRANT EXECUTE ON FUNCTION count_total_users() TO authenticated;

COMMENT ON FUNCTION count_total_users() IS 'Returns total count of registered users for admin dashboard';
