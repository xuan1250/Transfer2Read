"""
Integration tests for Jobs API with RLS policies.

Tests Row Level Security enforcement with real Supabase interactions.
Requires environment variables:
- TEST_SUPABASE_URL
- TEST_SUPABASE_ANON_KEY (for user auth)
- TEST_SUPABASE_SERVICE_KEY (for admin operations)

Run with: pytest tests/integration/test_rls_jobs.py -v
Skip if env vars missing: pytest -m "not integration"
"""
import pytest
from httpx import AsyncClient
from supabase import create_client, Client
from datetime import datetime
import os
import uuid
from typing import Tuple

# Check if integration test environment is configured
INTEGRATION_TESTS_ENABLED = all([
    os.getenv("TEST_SUPABASE_URL"),
    os.getenv("TEST_SUPABASE_ANON_KEY"),
    os.getenv("TEST_SUPABASE_SERVICE_KEY")
])

pytestmark = pytest.mark.skipif(
    not INTEGRATION_TESTS_ENABLED,
    reason="Integration tests require TEST_SUPABASE_URL, TEST_SUPABASE_ANON_KEY, and TEST_SUPABASE_SERVICE_KEY environment variables"
)


@pytest.fixture(scope="module")
def test_supabase_client() -> Client:
    """
    Create Supabase client for integration tests.

    Uses service role key for admin operations (user creation, cleanup).
    """
    url = os.getenv("TEST_SUPABASE_URL")
    key = os.getenv("TEST_SUPABASE_SERVICE_KEY")
    return create_client(url, key)


@pytest.fixture(scope="module")
async def test_users(test_supabase_client: Client) -> Tuple[dict, dict]:
    """
    Create two test users (Alice and Bob) for RLS testing.

    Returns:
        Tuple of (alice_data, bob_data) where each contains:
        - user_id: UUID of the user
        - email: Email address
        - access_token: JWT token for API requests
    """
    # Generate unique emails for this test run
    test_run_id = str(uuid.uuid4())[:8]
    alice_email = f"alice-{test_run_id}@test.local"
    bob_email = f"bob-{test_run_id}@test.local"
    password = "TestPassword123!"

    # Create Alice
    try:
        alice_response = test_supabase_client.auth.sign_up({
            "email": alice_email,
            "password": password,
            "options": {
                "data": {"tier": "FREE"}
            }
        })
        alice_user = alice_response.user
        alice_session = alice_response.session

        alice_data = {
            "user_id": alice_user.id,
            "email": alice_email,
            "access_token": alice_session.access_token
        }
    except Exception as e:
        pytest.fail(f"Failed to create Alice: {str(e)}")

    # Create Bob
    try:
        bob_response = test_supabase_client.auth.sign_up({
            "email": bob_email,
            "password": password,
            "options": {
                "data": {"tier": "FREE"}
            }
        })
        bob_user = bob_response.user
        bob_session = bob_response.session

        bob_data = {
            "user_id": bob_user.id,
            "email": bob_email,
            "access_token": bob_session.access_token
        }
    except Exception as e:
        pytest.fail(f"Failed to create Bob: {str(e)}")

    yield alice_data, bob_data

    # Cleanup: Delete test users and their jobs
    try:
        # Delete Alice's jobs
        test_supabase_client.table("conversion_jobs").delete().eq("user_id", alice_data["user_id"]).execute()
        # Delete Bob's jobs
        test_supabase_client.table("conversion_jobs").delete().eq("user_id", bob_data["user_id"]).execute()

        # Note: User deletion requires admin API, not available in standard Supabase client
        # In production, consider using Supabase Admin API or manual cleanup
    except Exception as e:
        print(f"Warning: Cleanup failed: {str(e)}")


@pytest.fixture
async def alice_job(test_supabase_client: Client, test_users: Tuple[dict, dict]) -> dict:
    """
    Create a test job for Alice.

    Returns job data including job_id for testing.
    """
    alice_data, _ = test_users

    job_id = str(uuid.uuid4())
    job_data = {
        "id": job_id,
        "user_id": alice_data["user_id"],
        "status": "COMPLETED",
        "input_path": f"uploads/{alice_data['user_id']}/{job_id}/test.pdf",
        "output_path": f"downloads/{alice_data['user_id']}/{job_id}/test.epub",
        "quality_report": {"overall_confidence": 95},
        "created_at": datetime.utcnow().isoformat(),
        "completed_at": datetime.utcnow().isoformat()
    }

    # Insert job using service role (bypasses RLS)
    test_supabase_client.table("conversion_jobs").insert(job_data).execute()

    yield job_data

    # Cleanup
    try:
        test_supabase_client.table("conversion_jobs").delete().eq("id", job_id).execute()
    except:
        pass


@pytest.mark.asyncio
@pytest.mark.integration
class TestRLSJobAccess:
    """Test RLS policies prevent cross-user access"""

    async def test_alice_can_read_own_job(self, client: AsyncClient, test_users: Tuple[dict, dict], alice_job: dict):
        """Test that Alice can read her own job"""
        alice_data, _ = test_users

        response = await client.get(
            f"/api/v1/jobs/{alice_job['id']}",
            headers={"Authorization": f"Bearer {alice_data['access_token']}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == alice_job["id"]
        assert data["user_id"] == alice_data["user_id"]

    async def test_bob_cannot_read_alice_job(self, client: AsyncClient, test_users: Tuple[dict, dict], alice_job: dict):
        """Test that Bob cannot read Alice's job (RLS blocks)"""
        _, bob_data = test_users

        response = await client.get(
            f"/api/v1/jobs/{alice_job['id']}",
            headers={"Authorization": f"Bearer {bob_data['access_token']}"}
        )

        # RLS should block access, returning 404 (not 403, to avoid leaking existence)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]["detail"].lower()

    async def test_alice_lists_only_own_jobs(self, client: AsyncClient, test_users: Tuple[dict, dict], alice_job: dict, test_supabase_client: Client):
        """Test that Alice's job list only shows her jobs"""
        alice_data, bob_data = test_users

        # Create a job for Bob
        bob_job_id = str(uuid.uuid4())
        bob_job_data = {
            "id": bob_job_id,
            "user_id": bob_data["user_id"],
            "status": "COMPLETED",
            "input_path": f"uploads/{bob_data['user_id']}/{bob_job_id}/test.pdf",
            "created_at": datetime.utcnow().isoformat()
        }
        test_supabase_client.table("conversion_jobs").insert(bob_job_data).execute()

        try:
            # Alice lists jobs
            response = await client.get(
                "/api/v1/jobs",
                headers={"Authorization": f"Bearer {alice_data['access_token']}"}
            )

            assert response.status_code == 200
            data = response.json()

            # Alice should only see her own job
            job_ids = [job["id"] for job in data["jobs"]]
            assert alice_job["id"] in job_ids
            assert bob_job_id not in job_ids

            # Verify all returned jobs belong to Alice
            for job in data["jobs"]:
                # We can't see user_id in JobSummary, but we verified Alice's job is there
                # and Bob's job is not, which proves RLS works
                pass
        finally:
            # Cleanup Bob's job
            test_supabase_client.table("conversion_jobs").delete().eq("id", bob_job_id).execute()

    async def test_bob_lists_only_own_jobs(self, client: AsyncClient, test_users: Tuple[dict, dict], alice_job: dict):
        """Test that Bob's job list doesn't show Alice's jobs"""
        _, bob_data = test_users

        response = await client.get(
            "/api/v1/jobs",
            headers={"Authorization": f"Bearer {bob_data['access_token']}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Bob should not see Alice's job
        job_ids = [job["id"] for job in data["jobs"]]
        assert alice_job["id"] not in job_ids


@pytest.mark.asyncio
@pytest.mark.integration
class TestRLSJobDeletion:
    """Test RLS policies for job deletion"""

    async def test_alice_can_delete_own_job(self, client: AsyncClient, test_users: Tuple[dict, dict], test_supabase_client: Client):
        """Test that Alice can delete her own job"""
        alice_data, _ = test_users

        # Create a job for Alice
        job_id = str(uuid.uuid4())
        job_data = {
            "id": job_id,
            "user_id": alice_data["user_id"],
            "status": "COMPLETED",
            "input_path": f"uploads/{alice_data['user_id']}/{job_id}/test.pdf",
            "created_at": datetime.utcnow().isoformat()
        }
        test_supabase_client.table("conversion_jobs").insert(job_data).execute()

        # Alice deletes her job
        response = await client.delete(
            f"/api/v1/jobs/{job_id}",
            headers={"Authorization": f"Bearer {alice_data['access_token']}"}
        )

        assert response.status_code == 204

        # Verify job is soft-deleted (deleted_at is set)
        result = test_supabase_client.table("conversion_jobs").select("deleted_at").eq("id", job_id).execute()
        assert len(result.data) > 0
        assert result.data[0]["deleted_at"] is not None

        # Verify Alice can no longer see the job in her list
        response = await client.get(
            f"/api/v1/jobs/{job_id}",
            headers={"Authorization": f"Bearer {alice_data['access_token']}"}
        )
        assert response.status_code == 404  # RLS excludes deleted jobs

    async def test_bob_cannot_delete_alice_job(self, client: AsyncClient, test_users: Tuple[dict, dict], alice_job: dict):
        """Test that Bob cannot delete Alice's job (RLS blocks)"""
        _, bob_data = test_users

        response = await client.delete(
            f"/api/v1/jobs/{alice_job['id']}",
            headers={"Authorization": f"Bearer {bob_data['access_token']}"}
        )

        # RLS should block deletion, returning 404
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]["detail"].lower()


@pytest.mark.asyncio
@pytest.mark.integration
class TestRLSJobDownload:
    """Test RLS policies for job download"""

    async def test_alice_can_download_own_job(self, client: AsyncClient, test_users: Tuple[dict, dict], alice_job: dict):
        """Test that Alice can download her own completed job"""
        alice_data, _ = test_users

        response = await client.get(
            f"/api/v1/jobs/{alice_job['id']}/download",
            headers={"Authorization": f"Bearer {alice_data['access_token']}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "download_url" in data
        assert "expires_at" in data
        assert "supabase" in data["download_url"].lower() or "signed" in data["download_url"].lower()

    async def test_bob_cannot_download_alice_job(self, client: AsyncClient, test_users: Tuple[dict, dict], alice_job: dict):
        """Test that Bob cannot download Alice's job (RLS blocks)"""
        _, bob_data = test_users

        response = await client.get(
            f"/api/v1/jobs/{alice_job['id']}/download",
            headers={"Authorization": f"Bearer {bob_data['access_token']}"}
        )

        # RLS should block access, returning 404
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]["detail"].lower()


@pytest.mark.asyncio
@pytest.mark.integration
class TestRLSSoftDelete:
    """Test RLS policies respect soft delete"""

    async def test_deleted_jobs_not_visible_in_list(self, client: AsyncClient, test_users: Tuple[dict, dict], test_supabase_client: Client):
        """Test that soft-deleted jobs don't appear in list"""
        alice_data, _ = test_users

        # Create a job for Alice
        job_id = str(uuid.uuid4())
        job_data = {
            "id": job_id,
            "user_id": alice_data["user_id"],
            "status": "COMPLETED",
            "input_path": f"uploads/{alice_data['user_id']}/{job_id}/test.pdf",
            "created_at": datetime.utcnow().isoformat()
        }
        test_supabase_client.table("conversion_jobs").insert(job_data).execute()

        # Verify job appears in list
        response = await client.get(
            "/api/v1/jobs",
            headers={"Authorization": f"Bearer {alice_data['access_token']}"}
        )
        job_ids_before = [job["id"] for job in response.json()["jobs"]]
        assert job_id in job_ids_before

        # Soft delete the job
        test_supabase_client.table("conversion_jobs").update(
            {"deleted_at": datetime.utcnow().isoformat()}
        ).eq("id", job_id).execute()

        # Verify job no longer appears in list (RLS excludes deleted_at IS NOT NULL)
        response = await client.get(
            "/api/v1/jobs",
            headers={"Authorization": f"Bearer {alice_data['access_token']}"}
        )
        job_ids_after = [job["id"] for job in response.json()["jobs"]]
        assert job_id not in job_ids_after

    async def test_deleted_jobs_not_accessible_directly(self, client: AsyncClient, test_users: Tuple[dict, dict], test_supabase_client: Client):
        """Test that soft-deleted jobs return 404 on direct access"""
        alice_data, _ = test_users

        # Create a job for Alice
        job_id = str(uuid.uuid4())
        job_data = {
            "id": job_id,
            "user_id": alice_data["user_id"],
            "status": "COMPLETED",
            "input_path": f"uploads/{alice_data['user_id']}/{job_id}/test.pdf",
            "created_at": datetime.utcnow().isoformat()
        }
        test_supabase_client.table("conversion_jobs").insert(job_data).execute()

        # Verify job is accessible
        response = await client.get(
            f"/api/v1/jobs/{job_id}",
            headers={"Authorization": f"Bearer {alice_data['access_token']}"}
        )
        assert response.status_code == 200

        # Soft delete the job
        test_supabase_client.table("conversion_jobs").update(
            {"deleted_at": datetime.utcnow().isoformat()}
        ).eq("id", job_id).execute()

        # Verify job is no longer accessible
        response = await client.get(
            f"/api/v1/jobs/{job_id}",
            headers={"Authorization": f"Bearer {alice_data['access_token']}"}
        )
        assert response.status_code == 404
