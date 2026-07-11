FROM python:3.11-slim

# Install system dependencies (ffmpeg for audio format support)
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY separate.py server.py ./

# Expose API port
EXPOSE 8000

# Default: run the API server
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
