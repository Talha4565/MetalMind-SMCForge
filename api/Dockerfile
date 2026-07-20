# MetalMind SMCForge — API Dockerfile (optimized)
# Stage 1: Install dependencies (cached across builds)
FROM python:3.11-slim AS deps

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ curl \
    && rm -rf /var/lib/apt/lists/*

COPY api/requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime (slim, only code + installed packages)
FROM python:3.11-slim AS runtime

WORKDIR /app

# Copy installed packages from deps stage
COPY --from=deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

# Copy application code
COPY api/ ./api/
COPY config/ ./config/
COPY data/ ./data/
COPY etl/ ./etl/
COPY explainability/ ./explainability/
COPY features/ ./features/
COPY backtesting/ ./backtesting/
COPY signal_memory/ ./signal_memory/
COPY self_learning/ ./self_learning/
COPY models/ ./models/
COPY reports/ ./reports/
COPY scripts/ ./scripts/
COPY start_api.py .
COPY run_pipeline.py .

# Create runtime directories
RUN mkdir -p /app/instance /app/reports /app/data /app/data/chromadb

# Create non-root user
RUN groupadd --gid 1001 metalmind \
    && useradd --uid 1001 --gid metalmind --shell /bin/bash --no-create-home metalmind \
    && chown -R metalmind:metalmind /app

USER metalmind

EXPOSE 5000

ENV FLASK_APP=api/app/main.py
ENV FLASK_ENV=production
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "--worker-class", "sync", "api.app.main:app"]
