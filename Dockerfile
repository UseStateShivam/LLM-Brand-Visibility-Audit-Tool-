# Multi-stage Dockerfile for LLM Brand Visibility Audit Tool
# Production-ready, non-root user execution, minimal image footprint

FROM python:3.11-slim as base

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_HOME=/app

WORKDIR ${APP_HOME}

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy build definition files first for efficient Docker layer caching
COPY pyproject.toml README.md ${APP_HOME}/

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Copy application source, configuration, and scripts
COPY app/ ${APP_HOME}/app/
COPY scripts/ ${APP_HOME}/scripts/
COPY docs/ ${APP_HOME}/docs/

# Create data directories with appropriate permissions
RUN mkdir -p ${APP_HOME}/data/audits \
             ${APP_HOME}/data/raw \
             ${APP_HOME}/data/processed \
             ${APP_HOME}/data/reports && \
    useradd -u 1000 -m appuser && \
    chown -R appuser:appuser ${APP_HOME}

# Switch to unprivileged user
USER appuser

# Expose FastAPI HTTP server port
EXPOSE 8000

# Health check to verify application readiness
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start Uvicorn ASGI server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
