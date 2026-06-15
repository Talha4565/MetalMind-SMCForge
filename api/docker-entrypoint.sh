#!/bin/sh
set -e

# Docker entrypoint: run DB migrations, then exec the passed command (Gunicorn)
export FLASK_APP=${FLASK_APP:-api/app/main.py}

attempts=10
delay=3
i=1

echo "Starting entrypoint: running migrations (up to $attempts attempts)"
until flask db upgrade; do
  if [ "$i" -ge "$attempts" ]; then
    echo "Migrations failed after $attempts attempts" >&2
    exit 1
  fi
  echo "Migration attempt $i failed, retrying in $delay seconds..."
  i=$((i+1))
  sleep $delay
done

echo "Migrations applied successfully. Starting application..."

exec "$@"
