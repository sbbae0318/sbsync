#!/bin/bash
# sbsync-server 자동 복구 스크립트
# crontab: */2 * * * * /path/to/scripts/watchdog-cron.sh >> /tmp/sbsync-watchdog.log 2>&1

COMPOSE_DIR="/Users/sbbae/project/sbsync/server"
CONTAINER_NAME="sbsync-server"
DRIVE_MOUNT="/Volumes/External4TB"

# 1. 드라이브 마운트 확인
if ! mount | grep -q "$DRIVE_MOUNT"; then
    echo "$(date): Drive not mounted. Skipping."
    exit 0
fi

# 2. 컨테이너 상태 확인
STATUS=$(docker inspect --format='{{.State.Health.Status}}' "$CONTAINER_NAME" 2>/dev/null)
RUNNING=$(docker inspect --format='{{.State.Running}}' "$CONTAINER_NAME" 2>/dev/null)

# 3. 복구 필요 시 재생성
if [ "$RUNNING" != "true" ] || [ "$STATUS" = "unhealthy" ]; then
    echo "$(date): Recreating $CONTAINER_NAME (running=$RUNNING, health=$STATUS)"
    cd "$COMPOSE_DIR" && docker compose up -d --build
fi
