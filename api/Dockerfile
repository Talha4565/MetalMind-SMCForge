# MetalMind SMCForge — API Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy entire project
COPY . .
COPY api/docker-entrypoint.sh /app/docker-entrypoint.sh

# Create instance directory for SQLite and other runtime dirs
RUN mkdir -p /app/instance /app/reports /app/models /app/data

# Create non-root user and group for security
RUN groupadd --gid 1001 metalmind \
    && useradd --uid 1001 --gid metalmind --shell /bin/bash --no-create-home metalmind \
    && chown -R metalmind:metalmind /app

# Switch to non-root user
USER metalmind

# Ensure entrypoint is executable by the non-root user
RUN chmod +x /app/docker-entrypoint.sh || true

# Expose Flask port
EXPOSE 5000

# Environment variables
ENV FLASK_APP=api/app/main.py
ENV FLASK_ENV=production
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Start Flask with Gunicorn via entrypoint (runs migrations first)
ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "--worker-class", "sync", "api.app.main:app"]
