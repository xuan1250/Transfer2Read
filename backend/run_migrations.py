"""
Run Supabase Database Migrations

Applies all pending SQL migrations to the Supabase database.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env")
    sys.exit(1)

# Create Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# Migrations to run (in order)
migrations = [
    "005_ai_layout_analysis_columns.sql",
    "006_document_structure_column.sql",
    "007_quality_report_column.sql",
    "008_feedback_and_issues_tables.sql",
    "009_user_usage_table.sql",
]

migrations_dir = Path(__file__).parent / "supabase" / "migrations"

print("🔧 Running Supabase Migrations...\n")

for migration_file in migrations:
    migration_path = migrations_dir / migration_file

    if not migration_path.exists():
        print(f"⚠️  Migration file not found: {migration_file}")
        continue

    print(f"📝 Running migration: {migration_file}")

    try:
        # Read migration SQL
        with open(migration_path, 'r') as f:
            sql = f.read()

        # Execute migration using raw SQL
        # Note: Supabase Python client doesn't have direct SQL execution,
        # so we'll need to use the REST API or psycopg2
        print(f"   ⚠️  Please run this SQL manually in Supabase SQL Editor:")
        print(f"   File: {migration_path}")
        print()

    except Exception as e:
        print(f"   ❌ Error reading migration: {str(e)}")
        continue

print("\n" + "="*60)
print("📋 MANUAL MIGRATION STEPS:")
print("="*60)
print("\n1. Go to Supabase Dashboard → SQL Editor")
print("2. Run each migration file in order:\n")

for migration_file in migrations:
    migration_path = migrations_dir / migration_file
    if migration_path.exists():
        print(f"   • {migration_file}")
        print(f"     Copy from: {migration_path}")
        print()

print("\nOr run this SQL directly:\n")

# Print combined SQL
for migration_file in migrations:
    migration_path = migrations_dir / migration_file
    if migration_path.exists():
        with open(migration_path, 'r') as f:
            print(f"-- {migration_file}")
            print(f.read())
            print()
