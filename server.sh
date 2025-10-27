#!/bin/bash

# server process helper
# wraps api, worker, and dashboard commands

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"
APP_MODULE="server.api.main:app"
CELERY_APP="server.workers.celery_config.celery_app"

usage() {
    cat <<EOF
Usage: ./server.sh <command> [options]

Commands:
  api        Start FastAPI server (uvicorn)
  worker     Start Celery worker
  flower     Launch Flower monitoring UI
  all        Start API and Celery worker together
  help       Show this message

Options for 'api':
  --host HOST    Bind host (default: 0.0.0.0)
  --port PORT    Bind port (default: 8000)
  --reload       Enable autoreload (development)

Examples:
  ./server.sh api --reload
  ./server.sh worker
  ./server.sh all
EOF
}

ensure_environment() {
    if [ ! -d "$VENV_DIR" ]; then
        echo "Creating virtual environment..."
        python3 -m venv "$VENV_DIR"
    fi

    source "$VENV_DIR/bin/activate"
    pip install -q --upgrade pip
    pip install -q -r "$SCRIPT_DIR/requirements.txt"
}

start_api() {
    local host="0.0.0.0"
    local port="8000"
    local reload_flag=""

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --host)
                host="$2"
                shift 2
                ;;
            --port)
                port="$2"
                shift 2
                ;;
            --reload)
                reload_flag="--reload"
                shift
                ;;
            *)
                echo "Unknown option for api: $1"
                exit 1
                ;;
        esac
    done

    echo "Starting API server on http://${host}:${port} ..."
    exec uvicorn "$APP_MODULE" --host "$host" --port "$port" $reload_flag
}

start_worker() {
    echo "Starting Celery worker..."
    exec celery -A "$CELERY_APP" worker --loglevel=info
}

start_flower() {
    echo "Starting Flower dashboard on http://localhost:5555 ..."
    exec celery -A "$CELERY_APP" flower --address=0.0.0.0 --port=5555
}

start_all() {
    echo "Starting API and Celery worker..."
    set +e

    uvicorn "$APP_MODULE" --host 0.0.0.0 --port 8000 "$@" &
    API_PID=$!

    celery -A "$CELERY_APP" worker --loglevel=info &
    WORKER_PID=$!

    trap "echo 'Stopping services...'; kill $API_PID $WORKER_PID; wait $API_PID $WORKER_PID 2>/dev/null" SIGINT SIGTERM
    wait $API_PID $WORKER_PID
}

if [[ $# -lt 1 ]]; then
    usage
    exit 1
fi

COMMAND="$1"
shift || true

case "$COMMAND" in
    help|-h|--help)
        usage
        ;;
    api|worker|flower|all)
        ensure_environment
        case "$COMMAND" in
            api) start_api "$@";;
            worker) start_worker "$@";;
            flower) start_flower "$@";;
            all) start_all "$@";;
        esac
        ;;
    *)
        echo "Unknown command: $COMMAND"
        usage
        exit 1
        ;;
esac
