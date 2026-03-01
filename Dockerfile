FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install --no-cache-dir uv

# Copy project files
COPY pyproject.toml uv.lock* ./
COPY README.md ./
COPY .env.example ./
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY rubric.json ./
COPY tests/ ./tests/

# Install dependencies using uv
RUN uv sync --frozen

# Set environment variables
ENV PYTHONPATH=/app
ENV LANGCHAIN_TRACING_V2=false
ENV PYTHONUNBUFFERED=1

# Create directories for outputs
RUN mkdir -p /app/audit /app/reports

# Default command (can be overridden)
CMD ["uv", "run", "python", "scripts/self_audit.py"]
