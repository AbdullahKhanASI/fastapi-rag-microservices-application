# API Gateway Service Dockerfile - Production Ready
FROM python:3.12-slim

LABEL maintainer="RAG Chatbot Team"
LABEL service="gateway"
LABEL version="1.0.0"

# Set working directory
WORKDIR /app

# Install system dependencies and cleanup
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install UV for faster package management
RUN pip install --no-cache-dir uv

# Copy requirements first for better layer caching
COPY requirements.txt .

# Create virtual environment and install dependencies
RUN uv venv && \
    . .venv/bin/activate && \
    uv pip install --no-cache -r requirements.txt

# Copy shared modules
COPY ../../shared /app/shared

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash --uid 1000 app && \
    chown -R app:app /app
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Run the application
CMD [".venv/bin/uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]