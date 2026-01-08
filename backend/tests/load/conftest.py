"""
Load testing configuration and fixtures.

This module provides configuration and helper functions for load testing.
"""

import os
from pathlib import Path

import pytest


# Load testing configuration
LOAD_TEST_CONFIG = {
    "api_base_url": os.getenv("API_BASE_URL", "http://localhost:8000"),
    "test_pdfs_dir": Path(__file__).parent.parent / "fixtures" / "load-test-pdfs",

    # Performance targets from PRD
    "performance_targets": {
        "simple_pdf_max_time": 30,  # seconds
        "complex_pdf_max_time": 120,  # seconds (2 minutes)
        "api_p95_response_time": 500,  # milliseconds
        "api_p99_response_time": 1000,  # milliseconds
        "frontend_landing_page": 2,  # seconds
        "frontend_dashboard": 3,  # seconds
        "frontend_job_status": 3,  # seconds
        "max_ai_cost_per_job": 1.00,  # USD
        "epub_size_ratio_max": 1.20,  # 120% of PDF size
    },

    # Load testing scenarios
    "scenarios": {
        "baseline": {
            "users": 1,
            "spawn_rate": 1,
            "duration": "5m"
        },
        "normal_load": {
            "users": 10,
            "spawn_rate": 1,
            "duration": "10m"
        },
        "stress_test": {
            "users": 50,
            "spawn_rate": 5,
            "duration": "15m"
        }
    },

    # Docker monitoring thresholds
    "docker_thresholds": {
        "max_cpu_percent": 80,
        "max_memory_percent": 80,
        "max_celery_queue_depth": 100
    }
}


@pytest.fixture
def load_test_config():
    """Provide load test configuration."""
    return LOAD_TEST_CONFIG


@pytest.fixture
def test_pdfs_dir():
    """Provide path to test PDFs directory."""
    return LOAD_TEST_CONFIG["test_pdfs_dir"]


@pytest.fixture
def performance_targets():
    """Provide performance targets from PRD."""
    return LOAD_TEST_CONFIG["performance_targets"]
