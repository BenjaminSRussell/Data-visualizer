#!/bin/bash

# Data Visualizer - Start Script

echo "========================================="
echo "  Data Visualizer 2.0"
echo "========================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Creating from template..."
    cp .env.example .env
    echo "[OK] Created .env file. Please edit it with your database credentials."
    echo ""
fi

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Set defaults
HOST=${HOST:-0.0.0.0}
PORT=${PORT:-8000}

echo "Starting Data Visualizer..."
echo "Host: $HOST"
echo "Port: $PORT"
echo ""
echo "Access points:"
echo "  - Web UI:  http://localhost:$PORT"
echo "  - API Docs: http://localhost:$PORT/api/docs"
echo ""

# Start the application
uvicorn app.main:app --host "$HOST" --port "$PORT" --reload
