#!/usr/bin/env bash
# Measures time-to-ready: container start -> first 200 from /v1/ready.
set -e

docker compose down >/dev/null 2>&1 || true

docker compose up -d --build
START=$(date +%s)
until curl -fsS http://localhost:8000/v1/ready >/dev/null 2>&1; do
  sleep 0.2
done
END=$(date +%s)
echo "time-to-ready: $((END - START))s"
