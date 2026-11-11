# Multi-stage / optimized slim Python build
FROM python:3.11-slim AS base

# Prevent Python from writing .pyc files, enable unbuffered logging and set writable HF cache
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    HF_HOME=/app/.cache/huggingface \
    TORCH_HOME=/app/.cache/torch

WORKDIR /app

# Install system dependencies (curl for healthcheck, git for remote HF model code)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies (with CPU-optimized PyTorch index as extra-index-url for slim image size)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt

# Copy application files
COPY . .

# Create non-root user and ensure directories (including HuggingFace cache) have correct permissions
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/results /app/data /app/static /app/.cache/huggingface /app/.cache/torch && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8080

# Healthcheck to verify the web service is responding
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8080/ || exit 1

CMD ["python", "main.py"]
