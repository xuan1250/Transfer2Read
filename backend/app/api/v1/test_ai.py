"""
Test AI Endpoints

API endpoints for testing AI connectivity through Celery workers.
Provides task dispatch and status checking.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Literal, Optional
from celery.result import AsyncResult
from app.tasks.ai_tasks import test_ai_connection
from app.core.celery_app import celery_app

router = APIRouter(prefix="/test-ai", tags=["Test AI"])


class TestAIRequest(BaseModel):
    """Request model for AI test"""
    provider: Literal["openai", "anthropic"] = Field(
        default="openai",
        description="AI provider to test: openai (GPT-4o) or anthropic (Claude 3 Haiku)"
    )


class TaskResponse(BaseModel):
    """Celery task dispatch response"""
    task_id: str
    status: str


class TaskStatusResponse(BaseModel):
    """Celery task status response"""
    task_id: str
    status: str
    result: Optional[dict] = None
    error: Optional[str] = None


@router.post("", response_model=TaskResponse)
async def trigger_test_ai(request: TestAIRequest = TestAIRequest()):
    """
    Dispatch AI connectivity test task to Celery worker.
    
    Returns task ID for status polling.
    
    Example:
        POST /api/v1/test-ai
        {
            "provider": "openai"  //  or "anthropic"
        }
        
        Response:
        {
            "task_id": "uuid-here",
            "status": "PENDING"
        }
    """
    try:
        # Dispatch task to Celery worker
        task = test_ai_connection.delay(provider=request.provider)
        
        return TaskResponse(
            task_id=task.id,
            status="PENDING"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to dispatch task: {str(e)}")


@router.get("/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """
    Check Celery task status and retrieve result.
    
    Possible statuses:
    - PENDING: Task waiting to be executed
    - STARTED: Task execution started
    - RETRY: Task failed and will retry
    - SUCCESS: Task completed successfully
    - FAILURE: Task failed permanently
    
    Example:
        GET /api/v1/test-ai/uuid-here
        
        Response (SUCCESS):
        {
            "task_id": "uuid-here",
            "status": "SUCCESS",
            "result": {
                "status": "success",
                "provider": "openai",
                "model": "gpt-4o",
                "response": "AI connection successful"
            },
            "error": null
        }
    """
    try:
        # Get task result from Celery
        task_result = AsyncResult(task_id, app=celery_app)
        
        response = TaskStatusResponse(
            task_id=task_id,
            status=task_result.status,
            result=None,
            error=None
        )
        
        # Add result or error based on status
        if task_result.status == "SUCCESS":
            response.result = task_result.result
        elif task_result.status == "FAILURE":
            response.error = str(task_result.info)
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve task status: {str(e)}")
