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

# Copy dependency files first (layer caching optimization)
COPY pyproject.toml .
COPY uv.lock .

# Install Python dependencies
RUN uv sync --frozen

# Copy application code
COPY src/ ./src/

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
# Shell form allows Railway's $PORT environment variable to be expanded
CMD uv run uvicorn cellophanemail.app:app --host 0.0.0.0 --port ${PORT:-8000}
