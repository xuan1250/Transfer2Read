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
