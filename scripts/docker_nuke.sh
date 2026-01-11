#!/usr/bin/env bash
set -euo pipefail

# DANGER: This script deletes ALL containers and prunes images/volumes/build cache.
# Usage:
#   scripts/docker_nuke.sh --yes
#
# Notes:
# - We force docker context to "default" (Docker Desktop) unless DOCKER_CONTEXT is already set.
# - If you intentionally use another runtime, export DOCKER_CONTEXT accordingly before running.

if [[ "${1:-}" != "--yes" ]]; then
  cat <<'EOF'
This will DELETE:
- all containers (running/stopped)
- all unused images
- all unused volumes
- build cache

Run again with:
  scripts/docker_nuke.sh --yes
EOF
  exit 2
fi

if [[ -z "${DOCKER_CONTEXT:-}" ]]; then
  docker context use default >/dev/null 2>&1 || true
fi

echo "[docker_nuke] context: $(docker context show 2>/dev/null || echo '?')"

# Ensure daemon is reachable
docker info >/dev/null

echo "[docker_nuke] removing all containers..."
if ids="$(docker ps -aq)"; [[ -n "${ids}" ]]; then
  # shellcheck disable=SC2086
  docker rm -f ${ids} >/dev/null
else
  echo "[docker_nuke] no containers to remove"
fi

echo "[docker_nuke] pruning unused images/volumes/networks/build cache..."
docker system prune -a --volumes -f >/dev/null
docker builder prune -a -f >/dev/null || true

echo "[docker_nuke] done."
