#!/bin/bash
# Start Celery worker

cd "$(dirname "$0")"

export PYTHONPATH="${PYTHONPATH}:$(pwd)"

celery -A server.workers.celery_config worker --loglevel=info
