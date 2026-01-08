"""
Upgrade test user to PRO tier for load testing.

This script updates the loadtest@test.com user's metadata to set tier=PRO,
which bypasses all conversion limits during load testing.
"""
import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase connection
supabase_url = os.getenv("SUPABASE_URL")
supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY")  # Fixed: matches .env variable name

if not supabase_url or not supabase_service_key:
    print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in .env")
    exit(1)

# Create Supabase client with service role (bypasses RLS)
supabase: Client = create_client(supabase_url, supabase_service_key)

# Authenticate as loadtest user to get user_id
email = "loadtest@test.com"
password = "LoadTest2026!"

try:
    # Sign in to get user session
    auth_response = supabase.auth.sign_in_with_password({
        "email": email,
        "password": password
    })

    user_id = auth_response.user.id
    print(f"✓ Authenticated as {email}")
    print(f"✓ User ID: {user_id}")

    # Update user metadata using admin API
    # Note: This requires service role key
    supabase_admin: Client = create_client(supabase_url, supabase_service_key)

    # Update user metadata
    update_response = supabase_admin.auth.admin.update_user_by_id(
        user_id,
        {
            "user_metadata": {
                "tier": "PRO"
            }
        }
    )

    print(f"✓ Updated user metadata: tier=PRO")
    print(f"✓ User {email} can now bypass conversion limits")

except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)
