#!/bin/bash
# sbsync watchdog 크론 등록 헬퍼
# 사용법: ./scripts/install-cron.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SCRIPT_PATH="$SCRIPT_DIR/watchdog-cron.sh"

if [ ! -f "$SCRIPT_PATH" ]; then
    echo "Error: watchdog-cron.sh not found at $SCRIPT_PATH"
    exit 1
fi

# 기존 watchdog-cron 항목 제거 후 새로 등록
(crontab -l 2>/dev/null | grep -v watchdog-cron; echo "*/2 * * * * $SCRIPT_PATH >> /tmp/sbsync-watchdog.log 2>&1") | crontab -

echo "Cron installed successfully."
echo "Verify with: crontab -l"
