#!/bin/sh
# run.sh [engagement-dir] [port]
# Runs the console in Docker with the engagement folder bind-mounted. Falls back to the host's
# existing python3 when Docker is not running (python3 is already on the host; nothing is installed).
set -e
here=$(cd "$(dirname "$0")" && pwd)
eng=$(cd "${1:-$here/../test-data/puppy-gloves}" && pwd)
port=${2:-8080}
if docker info >/dev/null 2>&1; then
  docker build -q -t register-console "$here" >/dev/null
  echo "console: http://localhost:$port/  (engagement $eng, in Docker)"
  exec docker run --rm -p "$port:8080" -v "$eng:/engagement" register-console
else
  echo "console: docker is not running; using host python3"
  exec python3 "$here/server.py" "$eng" "$port"
fi
