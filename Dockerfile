FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    gcc \
    g++ \
    python3-dev \
    libpq-dev \
    curl \
    cmake \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
RUN pip install uv

# Create non-root user to avoid permission issues with mounted volumes
ARG UID=1000
ARG GID=1000
RUN groupadd -g ${GID} appuser && \
    useradd -u ${UID} -g ${GID} -m appuser && \
    chown -R appuser:appuser /app

# Switch to non-root user before installing dependencies
USER appuser

# Copy dependency files first (layer caching optimization)
COPY --chown=appuser:appuser pyproject.toml .
COPY --chown=appuser:appuser uv.lock .

# Install Python dependencies
RUN uv sync --frozen

# Copy application code
COPY --chown=appuser:appuser src/ ./src/

# Create necessary directories
RUN mkdir -p logs

# Set environment variables
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

# Expose ports
EXPOSE 8000
EXPOSE 2525

# Health check using existing endpoint
HEALTHCHECK --interval=30s --timeout=30s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Default command (Litestar API)
# Use 'uv run' to activate virtual environment for Railway deployment
# Explicitly invoke shell to ensure $PORT environment variable is expanded
CMD ["/bin/sh", "-c", "uv run uvicorn cellophanemail.app:create_app --factory --host 0.0.0.0 --port ${PORT:-8000}"]
