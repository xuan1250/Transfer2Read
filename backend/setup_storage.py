"""
Setup Supabase Storage Buckets

Creates required storage buckets if they don't exist.
Run this script once to initialize storage.
"""
import os
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env")
    exit(1)

# Create Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

print("🔧 Setting up Supabase Storage buckets...\n")

# Buckets to create
buckets = [
    {
        "name": "uploads",
        "public": False,
        "file_size_limit": 524288000  # 500MB
    },
    {
        "name": "downloads",
        "public": False,
        "file_size_limit": 524288000  # 500MB
    }
]

for bucket_config in buckets:
    bucket_name = bucket_config["name"]

    try:
        # Check if bucket exists
        existing_buckets = supabase.storage.list_buckets()
        bucket_exists = any(b.name == bucket_name for b in existing_buckets)

        if bucket_exists:
            print(f"✅ Bucket '{bucket_name}' already exists")
        else:
            # Create bucket
            supabase.storage.create_bucket(
                bucket_name,
                options={
                    "public": bucket_config["public"],
                    "file_size_limit": bucket_config["file_size_limit"]
                }
            )
            print(f"✨ Created bucket '{bucket_name}'")

    except Exception as e:
        print(f"⚠️  Error with bucket '{bucket_name}': {str(e)}")

print("\n🎉 Storage setup complete!")
print("\nBucket configuration:")
print("  - uploads: Private bucket for PDF uploads (max 500MB)")
print("  - downloads: Private bucket for EPUB downloads (max 500MB)")
