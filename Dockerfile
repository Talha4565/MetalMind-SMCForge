FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Install system deps needed for some Python packages
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       gcc \
       libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY api/requirements.txt /app/
RUN python -m pip install --upgrade pip setuptools wheel \
    && pip install -r /app/requirements.txt

# Copy project
COPY . /app

ENV FLASK_APP=manage
ENV FLASK_ENV=development

EXPOSE 5000

CMD ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=5000"]
