"""
Celery Tasks Package

Import all tasks here for Celery autodiscovery.
"""
from app.tasks.cleanup import cleanup_job_files_task
from app.tasks.conversion_pipeline import (
    conversion_pipeline,
    analyze_layout,
    extract_content,
    identify_structure,
    generate_epub,
    calculate_quality_score
)

__all__ = [
    "cleanup_job_files_task",
    "conversion_pipeline",
    "analyze_layout",
    "extract_content",
    "identify_structure",
    "generate_epub",
    "calculate_quality_score"
]
