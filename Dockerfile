# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=app.py \
    FLASK_ENV=development \
    FLASK_DEBUG=1 \
    PYTHONPATH=/app \
    GUNICORN_CMD_ARGS="--log-level debug --timeout 120 --reload --capture-output --enable-stdio-inheritance --preload"

# Create a non-root user early
RUN useradd -m appuser

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY --chown=appuser:appuser requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories and set permissions
RUN mkdir -p /app/flask_session /app/app /app/static /app/conf && \
    chown -R appuser:appuser /app && \
    chmod 750 /app/flask_session

# Copy configuration directory first
COPY --chown=appuser:appuser conf /app/conf/

# Copy the application code with correct ownership
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Expose the port
EXPOSE 8050

# Start the application with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8050", "--workers", "4", "--worker-class", "gthread", "--threads", "2", "--timeout", "120", "--log-level", "debug", "--capture-output", "--enable-stdio-inheritance", "--reload", "--reload-extra-file", "/app/conf", "app:server"]
