"""
Transfer2Read Backend API

FastAPI application entrypoint with CORS configuration and route registration.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Transfer2Read API",
    description="AI-powered PDF to EPUB converter with 95%+ fidelity",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
# Allow requests from frontend (localhost for dev, Vercel domain for prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev server
        "http://localhost:3001",  # Alternative port
        "https://transfer2read.vercel.app",  # Production frontend
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint returning API info"""
    return {
        "name": "Transfer2Read API",
        "version": "0.1.0",
        "status": "operational"
    }

# Register health check routes
from app.api.health import router as health_router
app.include_router(health_router, prefix="/api", tags=["health"])

# Register test AI routes
from app.api.v1.test_ai import router as test_ai_router
app.include_router(test_ai_router, prefix="/api/v1", tags=["test-ai"])

# Register auth routes
from app.api.v1.auth import router as auth_router
app.include_router(auth_router, prefix="/api/v1", tags=["auth"])

# Register users routes
from app.api.v1.users import router as users_router
app.include_router(users_router, prefix="/api/v1", tags=["users"])

# Register upload routes
from app.api.v1.upload import router as upload_router
app.include_router(upload_router, prefix="/api/v1", tags=["upload"])

# Register jobs routes
from app.api.v1.jobs import router as jobs_router
app.include_router(jobs_router, prefix="/api/v1", tags=["jobs"])

# Register usage routes
from app.api.v1.usage import router as usage_router
app.include_router(usage_router, prefix="/api/v1", tags=["usage"])


# Global Exception Handlers
from fastapi import Request
from fastapi.responses import JSONResponse
from app.services.validation import (
    InvalidFileTypeError,
    FileTooLargeError,
    ValidationError
)
from app.services.storage.supabase_storage import StorageUploadError


@app.exception_handler(InvalidFileTypeError)
async def invalid_file_type_handler(request: Request, exc: InvalidFileTypeError):
    """Handle invalid file type errors (non-PDF files)"""
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc), "code": "INVALID_FILE_TYPE"}
    )


@app.exception_handler(FileTooLargeError)
async def file_too_large_handler(request: Request, exc: FileTooLargeError):
    """Handle file size limit errors"""
    return JSONResponse(
        status_code=413,
        content={"detail": str(exc), "code": "FILE_TOO_LARGE"}
    )


@app.exception_handler(StorageUploadError)
async def storage_upload_error_handler(request: Request, exc: StorageUploadError):
    """Handle Supabase Storage upload errors"""
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "code": "STORAGE_ERROR"}
    )
