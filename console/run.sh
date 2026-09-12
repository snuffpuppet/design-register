#!/bin/sh
# run.sh [engagement-dir] [port]
# Runs the console in Docker with the engagement folder bind-mounted. Docker only.
set -e
here=$(cd "$(dirname "$0")" && pwd)
eng=$(cd "${1:-$here/../test-data/puppy-gloves}" && pwd)
port=${2:-8085}
docker info >/dev/null 2>&1 || { echo "docker is not running; start it and try again" >&2; exit 1; }
docker build -q -t register-console "$here" >/dev/null
echo "console: http://localhost:$port/  (engagement $eng)"
exec docker run --rm --name register-console -p "$port:8080" -v "$eng:/engagement" register-console
