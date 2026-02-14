#!/bin/sh
set -e

if [ -n "$BACKEND_CMD" ]; then
  echo "Starting backend: $BACKEND_CMD"
  sh -c "$BACKEND_CMD" &
else
  echo "BACKEND_CMD not set, starting default uvicorn backend"
  uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 &
fi

exec nginx -g "daemon off;"
