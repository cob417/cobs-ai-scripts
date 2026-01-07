# Cob's AI Scripts - Docker Image
# Single container with FastAPI backend serving React frontend

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements files first (for better layer caching)
COPY requirements.txt ./requirements.txt
COPY backend/requirements.txt ./backend/requirements.txt

# Install Python dependencies from both requirements files
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir -r backend/requirements.txt

# Copy application code
COPY backend/ ./backend/
COPY utils/ ./utils/
COPY run_ai_script.py ./

# Create directories for persistent data (will be overwritten by volume mounts)
RUN mkdir -p /app/data /app/prompts

# Copy default prompts (can be overwritten by volume mount)
COPY prompts/ ./prompts/

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Expose the FastAPI port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/status')" || exit 1

# Run the FastAPI application
WORKDIR /app/backend
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
