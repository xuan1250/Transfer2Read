# Production Dockerfile for Transfer2Read Backend
# Supports both API and Worker deployments via different start commands
# Python 3.12.9 base image (matches local development environment)

FROM python:3.12.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies for PDF processing
# PyMuPDF requires libmupdf-dev and mupdf-tools
# python-magic requires libmagic1
RUN apt-get update && apt-get install -y \
    libmupdf-dev \
    mupdf-tools \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies
# Use --no-cache-dir to reduce image size
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ./app ./app

# Railway provides $PORT environment variable for API service
# Default to 8000 if not provided (for local testing)
ENV PORT=8000

# Expose the port (Railway ignores this, but useful for documentation)
EXPOSE $PORT

# Default command runs API server
# Railway will override this for Worker service with:
# celery -A app.worker worker --loglevel=info
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
