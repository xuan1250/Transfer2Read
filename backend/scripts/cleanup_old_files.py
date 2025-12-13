#!/usr/bin/env python3
"""
Cleanup Old Storage Files

Deletes files older than 30 days from Supabase Storage buckets.
Can be run manually or scheduled via cron job.

Usage:
    python3 cleanup_old_files.py

Environment Variables Required:
    SUPABASE_URL - Your Supabase project URL
    SUPABASE_SERVICE_KEY - Service role key (admin access)
"""
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.supabase import get_supabase_client
from app.services.storage import SupabaseStorageService


def cleanup_old_files(bucket: str, days: int = 30) -> dict:
    """
    Delete files older than specified number of days from a bucket.

    Args:
        bucket: Bucket name ('uploads' or 'downloads')
        days: Age threshold in days (default: 30)

    Returns:
        dict: Cleanup statistics
            - scanned (int): Total files scanned
            - deleted (int): Number of files deleted
            - failed (int): Number of deletion failures
            - errors (list): Error messages if any
    """
    supabase = get_supabase_client()
    storage_service = SupabaseStorageService(supabase)

    cutoff_date = datetime.utcnow() - timedelta(days=days)
    stats = {
        "scanned": 0,
        "deleted": 0,
        "failed": 0,
        "errors": []
    }

    try:
        # List all files in bucket
        files = storage_service.list_files(bucket, prefix="")
        stats["scanned"] = len(files)

        print(f"Scanning {len(files)} files in '{bucket}' bucket...")

        for file in files:
            # Parse created_at timestamp
            try:
                created_at_str = file.get("created_at", "")
                if not created_at_str:
                    continue

                # Parse ISO format timestamp
                created_at = datetime.fromisoformat(
                    created_at_str.replace('Z', '+00:00')
                )

                # Check if file is older than cutoff
                if created_at < cutoff_date:
                    file_path = file.get("name", "")
                    print(f"  Deleting old file: {file_path} (created: {created_at_str})")

                    success = storage_service.delete_file(bucket, file_path)
                    if success:
                        stats["deleted"] += 1
                    else:
                        stats["failed"] += 1
                        stats["errors"].append(f"Failed to delete: {file_path}")

            except Exception as e:
                stats["failed"] += 1
                stats["errors"].append(f"Error processing file {file.get('name')}: {str(e)}")

    except Exception as e:
        stats["errors"].append(f"Error listing files in {bucket}: {str(e)}")

    return stats


def main():
    """Main cleanup script execution."""
    print("=" * 60)
    print("Supabase Storage Cleanup - Delete files older than 30 days")
    print("=" * 60)
    print()

    # Check environment variables
    if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_SERVICE_KEY"):
        print("ERROR: Missing required environment variables")
        print("Please set SUPABASE_URL and SUPABASE_SERVICE_KEY")
        sys.exit(1)

    # Cleanup both buckets
    buckets = ["uploads", "downloads"]
    total_stats = {
        "scanned": 0,
        "deleted": 0,
        "failed": 0,
        "errors": []
    }

    for bucket in buckets:
        print(f"\nProcessing '{bucket}' bucket...")
        print("-" * 60)

        stats = cleanup_old_files(bucket, days=30)

        # Aggregate stats
        total_stats["scanned"] += stats["scanned"]
        total_stats["deleted"] += stats["deleted"]
        total_stats["failed"] += stats["failed"]
        total_stats["errors"].extend(stats["errors"])

        # Print bucket summary
        print(f"\n{bucket.upper()} Bucket Summary:")
        print(f"  Files scanned: {stats['scanned']}")
        print(f"  Files deleted: {stats['deleted']}")
        print(f"  Deletions failed: {stats['failed']}")

        if stats["errors"]:
            print(f"\n  Errors:")
            for error in stats["errors"]:
                print(f"    - {error}")

    # Print overall summary
    print("\n" + "=" * 60)
    print("OVERALL SUMMARY")
    print("=" * 60)
    print(f"Total files scanned: {total_stats['scanned']}")
    print(f"Total files deleted: {total_stats['deleted']}")
    print(f"Total failures: {total_stats['failed']}")

    if total_stats["errors"]:
        print(f"\nTotal errors: {len(total_stats['errors'])}")

    print("\nCleanup completed successfully!")


if __name__ == "__main__":
    main()
