"""
Locust load testing scenarios for Transfer2Read conversion system.

This module defines load test scenarios for:
- Simple PDF conversion (10-20 pages)
- Complex PDF conversion (300 pages with tables/images/equations)
- Concurrent user simulation (10 users, 50 users)
- API endpoint performance testing

Usage:
    # Run simple test (10 users)
    locust -f tests/load/scenarios.py --users 10 --spawn-rate 1 --run-time 5m --host http://localhost:8000

    # Run stress test (50 users)
    locust -f tests/load/scenarios.py --users 50 --spawn-rate 5 --run-time 10m --host http://localhost:8000

    # Run with web UI
    locust -f tests/load/scenarios.py --web-host 0.0.0.0 --host http://localhost:8000
"""

import os
import time
from pathlib import Path
from typing import Optional

from locust import HttpUser, task, between, events
from locust.runners import MasterRunner
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables from root .env file
env_path = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class ConversionUser(HttpUser):
    """
    Simulates a user performing PDF to EPUB conversions.

    Attributes:
        wait_time: Time between tasks (5-10 seconds)
        test_pdfs_dir: Directory containing test PDF files
    """

    wait_time = between(5, 10)

    def on_start(self):
        """Initialize test user and locate test PDFs."""
        self.test_pdfs_dir = Path(__file__).parent.parent / "fixtures" / "load-test-pdfs"
        self.access_token = None
        self.auth_headers = {}

        # Authenticate to get access token for protected endpoints
        self._authenticate()

    def _authenticate(self):
        """
        Authenticate user and get access token from Supabase.

        Uses credentials:
        - Email: loadtest@test.com
        - Password: LoadTest2026!
        """
        try:
            # Get Supabase credentials from environment
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_ANON_KEY")

            if not supabase_url or not supabase_key:
                print("Warning: SUPABASE_URL or SUPABASE_ANON_KEY not set. Using unauthenticated requests.")
                return

            # Create Supabase client
            supabase: Client = create_client(supabase_url, supabase_key)

            # Sign in with test user credentials
            response = supabase.auth.sign_in_with_password({
                "email": "loadtest@test.com",
                "password": "LoadTest2026!"
            })

            # Extract access token
            if response.session and response.session.access_token:
                self.access_token = response.session.access_token
                self.auth_headers = {"Authorization": f"Bearer {self.access_token}"}
                print(f"✓ Authenticated as loadtest@test.com")
            else:
                print("Warning: Authentication succeeded but no access token received")

        except Exception as e:
            print(f"Warning: Authentication failed: {e}")
            print("Continuing with unauthenticated requests (will fail for protected endpoints)")

    @task(3)
    def health_check(self):
        """Test API health check endpoint (frequent task)."""
        with self.client.get(
            "/api/health",
            catch_response=True,
            name="/api/health"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")

    @task(2)
    def upload_simple_pdf(self):
        """
        Test simple PDF upload and conversion (10-20 pages).

        Performance target: < 30 seconds end-to-end
        """
        pdf_path = self.test_pdfs_dir / "simple-text.pdf"

        if not pdf_path.exists():
            print(f"Warning: Test PDF not found at {pdf_path}")
            return

        # Upload PDF with authentication
        start_time = time.time()
        with open(pdf_path, "rb") as pdf_file:
            files = {"file": ("simple-text.pdf", pdf_file, "application/pdf")}

            with self.client.post(
                "/api/v1/upload",
                files=files,
                headers=self.auth_headers,  # Add authentication header
                catch_response=True,
                name="/api/v1/upload [simple PDF]"
            ) as response:
                if response.status_code == 202:
                    job_id = response.json().get("job_id")
                    response.success()

                    # Poll for completion
                    self._poll_job_status(job_id, start_time, max_wait=30)
                else:
                    response.failure(f"Upload failed: {response.status_code} - {response.text}")

    @task(1)
    def upload_complex_pdf(self):
        """
        Test complex PDF upload and conversion (300 pages).

        Performance target: < 2 minutes (120 seconds)
        AI cost target: < $1.00 per job
        """
        pdf_path = self.test_pdfs_dir / "complex-technical.pdf"

        if not pdf_path.exists():
            print(f"Warning: Test PDF not found at {pdf_path}")
            return

        # Upload PDF with authentication
        start_time = time.time()
        with open(pdf_path, "rb") as pdf_file:
            files = {"file": ("complex-technical.pdf", pdf_file, "application/pdf")}

            with self.client.post(
                "/api/v1/upload",
                files=files,
                headers=self.auth_headers,  # Add authentication header
                catch_response=True,
                name="/api/v1/upload [complex PDF]"
            ) as response:
                if response.status_code == 202:
                    job_id = response.json().get("job_id")
                    response.success()

                    # Poll for completion
                    self._poll_job_status(job_id, start_time, max_wait=120)
                else:
                    response.failure(f"Upload failed: {response.status_code} - {response.text}")

    def _poll_job_status(self, job_id: str, start_time: float, max_wait: int = 30):
        """
        Poll job status until completion or timeout.

        Args:
            job_id: Job ID to poll
            start_time: Start time of the conversion
            max_wait: Maximum wait time in seconds
        """
        poll_interval = 2  # seconds
        elapsed = 0

        while elapsed < max_wait:
            time.sleep(poll_interval)
            elapsed = time.time() - start_time

            with self.client.get(
                f"/api/v1/jobs/{job_id}",
                headers=self.auth_headers,  # Add authentication header
                catch_response=True,
                name="/api/v1/jobs/{id} [polling]"
            ) as response:
                if response.status_code == 200:
                    job_data = response.json()
                    status = job_data.get("status")

                    if status == "completed":
                        total_time = time.time() - start_time
                        response.success()

                        # Custom metric: record conversion time
                        events.request.fire(
                            request_type="CONVERSION",
                            name="PDF Conversion Time",
                            response_time=total_time * 1000,  # milliseconds
                            response_length=0,
                            exception=None,
                            context={}
                        )

                        # Test download
                        self._test_download(job_id)
                        return

                    elif status == "failed":
                        response.failure(f"Job failed: {job_data.get('error')}")
                        return

                    # Status is still processing, continue polling
                    response.success()
                else:
                    response.failure(f"Status check failed: {response.status_code}")
                    return

        # Timeout
        print(f"Job {job_id} timed out after {max_wait}s")

    def _test_download(self, job_id: str):
        """
        Test EPUB download via signed URL.

        Performance target: < 5 seconds for download
        """
        with self.client.get(
            f"/api/v1/jobs/{job_id}/download",
            headers=self.auth_headers,  # Add authentication header
            catch_response=True,
            name="/api/v1/jobs/{id}/download",
            allow_redirects=False
        ) as response:
            if response.status_code == 302:
                # Got redirect to signed URL
                response.success()

                # Optionally, follow the redirect to test Supabase Storage
                # signed_url = response.headers.get("Location")
                # Download from signed URL would be tested here
            else:
                response.failure(f"Download failed: {response.status_code}")

    @task(1)
    def list_jobs(self):
        """Test job listing endpoint."""
        with self.client.get(
            "/api/v1/jobs",
            headers=self.auth_headers,  # Add authentication header
            catch_response=True,
            name="/api/v1/jobs [list]"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"List jobs failed: {response.status_code}")


class ApiPerformanceUser(HttpUser):
    """
    Simulates a user testing API endpoint performance without conversions.

    Used for testing API response times under load without AI processing overhead.
    """

    wait_time = between(1, 3)

    @task(5)
    def health_check(self):
        """Frequent health check to test API responsiveness."""
        with self.client.get("/api/health", catch_response=True, name="/api/health") as response:
            # Target: P95 < 500ms, P99 < 1s
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")

    @task(2)
    def get_job_status(self):
        """Test job status endpoint with non-existent job (fast path)."""
        with self.client.get(
            "/api/v1/jobs/test-job-id",
            catch_response=True,
            name="/api/v1/jobs/{id} [not found]"
        ) as response:
            # Expecting 404, testing fast response
            if response.status_code in [404, 401]:
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")


@events.init_command_line_parser.add_listener
def _(parser):
    """Add custom command-line arguments for load testing."""
    parser.add_argument(
        "--test-scenario",
        type=str,
        default="all",
        choices=["all", "conversion", "api"],
        help="Test scenario to run: all, conversion, or api"
    )


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Log test start information."""
    if isinstance(environment.runner, MasterRunner):
        print(f"Load test starting with {environment.runner.target_user_count} users")
        print(f"Host: {environment.host}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Log test completion statistics."""
    if isinstance(environment.runner, MasterRunner):
        stats = environment.stats
        print("\n" + "="*60)
        print("LOAD TEST SUMMARY")
        print("="*60)
        print(f"Total requests: {stats.total.num_requests}")
        print(f"Total failures: {stats.total.num_failures}")
        print(f"Average response time: {stats.total.avg_response_time:.2f}ms")
        print(f"P95 response time: {stats.total.get_response_time_percentile(0.95):.2f}ms")
        print(f"P99 response time: {stats.total.get_response_time_percentile(0.99):.2f}ms")
        print(f"Requests per second: {stats.total.total_rps:.2f}")
        print("="*60)
