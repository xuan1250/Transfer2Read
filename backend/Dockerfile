# Production Dockerfile for Transfer2Read Backend
# Supports both API and Worker deployments via different start commands
# Python 3.13-slim base image for containerized deployment

FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies for PDF processing and LangChain
# python-magic requires libmagic1
# curl needed for health checks
# gcc, g++, make required for building some Python packages (asyncpg, etc.)
# libpq-dev required for asyncpg (PostgreSQL adapter)
RUN apt-get update && apt-get install -y \
    libmagic1 \
    curl \
    gcc \
    g++ \
    make \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies
# Use --no-cache-dir to reduce image size
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ./app ./app

# Create uploads directory for file storage
RUN mkdir -p /app/uploads && chmod 755 /app/uploads

# Default port for API service
ENV PORT=8000

# Expose the port
EXPOSE $PORT

# Health check for API service
# Docker will mark container as unhealthy if this fails
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:${PORT}/api/health || exit 1

# Default command runs API server
# Docker Compose will override this for Worker service with:
# celery -A app.worker worker --loglevel=info
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
