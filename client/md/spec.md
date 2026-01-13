# System Specifications - Client (Pull Client)

> This document describes the **client** component that periodically pulls from remote. For the push server, see [server specifications](../../server/md/spec.md).

## 1. Pull Operations
- **Trigger**: Periodic schedule based on configurable interval.
- **Operations**:
  1. `git fetch`: Fetch latest state from remote.
  2. **Smart Clean**: Remove only untracked files that conflict with the incoming remote state.
  3. `git checkout .`: Discard all local changes to tracked files.
  4. `git pull`: Pull latest changes from remote.
- **Safety**: Ensures no conflicts prevent pull, while preserving non-conflicting untracked files.

## 2. Synchronization Logic
- **Mechanism**: Remote -> Work PC 방향의 자동 pull.
- **Startup Initial Sync**:
  - 시작 시점에 1회 sync를 호출하여 최신 상태로 업데이트.
  - remote가 설정되어 있고 `.git`이 없으며 디렉토리가 비어있으면, clone으로 초기화.
- **Periodic Sync**: Configurable interval (default 5 minutes).
- **Clean Working Directory**: 항상 Smart Clean/Checkout 후 pull하여 로컬 변경사항을 무시 (충돌하는 Untracked file만 제거).

## 3. Configuration
| Variable | Default | Description |
|---|---|---|
| `TARGET_DIR` | `/vault` | Directory to sync (Docker에서는 호스트 경로를 그대로 마운트) |
| `PULL_INTERVAL_MINUTES` | `5` | Pull interval in minutes |
| `METRICS_PORT` | `8001` | Prometheus metrics port |
| `GIT_REMOTE_URL` | Required | Git remote repository URL |
| `SSH_KEY_PATH` | `/root/.ssh/id_ed25519` | SSH private key path |

## 4. Technical Stack
- **Language**: Python 3.11+
- **Key Libraries**:
  - `GitPython`: Git command wrapping.
  - `schedule`: Periodic task scheduling.
  - `prometheus_client`: Observability.
  - `python-dotenv`: Config loading.

## 5. Use Case
- **Work PC에서 Obsidian Vault를 읽기 전용으로 동기화**.
- 로컬 변경사항은 항상 폐기되며, remote의 상태를 따라감.
- Personal PC에서 sbsync로 push한 내용을 Work PC에서 pull.
