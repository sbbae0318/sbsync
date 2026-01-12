# System Specifications

## 1. Pull Operations
- **Trigger**: Periodic schedule based on configurable interval.
- **Operations**:
  1. `git clean -fd`: Remove untracked files and directories.
  2. `git checkout .`: Discard all local changes.
  3. `git pull`: Pull latest changes from remote.
- **Safety**: Always clean and checkout before pull to ensure clean state.

## 2. Synchronization Logic
- **Mechanism**: Remote -> Work PC 방향의 자동 pull.
- **Startup Initial Sync**:
  - 시작 시점에 1회 sync를 호출하여 최신 상태로 업데이트.
  - remote가 설정되어 있고 `.git`이 없으며 디렉토리가 비어있으면, clone으로 초기화.
- **Periodic Sync**: Configurable interval (default 5 minutes).
- **Clean Working Directory**: 항상 clean/checkout 후 pull하여 로컬 변경사항을 무시.

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
