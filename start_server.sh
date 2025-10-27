#!/bin/bash
# Start the API server

cd "$(dirname "$0")"

export PYTHONPATH="${PYTHONPATH}:$(pwd)"

uvicorn server.api:app --host 0.0.0.0 --port 8000 --reload
