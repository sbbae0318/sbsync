# System Specifications

## 1. File Monitoring
- **Trigger**: File system events (Create, Modify, Delete, Move).
- **Scope**: Recursive monitoring of `TARGET_DIR`.
- **Exclusions**: 
  - `.git` directory.
  - Folders/Files matched by `.gitignore` in the Vault.

## 2. Synchronization Logic
- **Mechanism**: 기본은 Personal PC -> Remote 방향의 자동 커밋/푸시.
- **Startup Initial Sync Attempt**:
  - 시작 시점에 1회 `GitHandler.sync()`를 호출하여 best-effort로 “먼저 동기화”를 시도.
  - remote가 설정되어 있고 working tree가 깨끗하며 upstream이 있으면 `git pull --rebase` 시도.
  - remote가 설정되어 있고 `.git`이 없으며 디렉토리가 비어있으면, clone으로 초기화.
- **Debounce**: 300 seconds (Configurable). Timer resets on new events.
- **Batching**: All pending changes are grouped into a single commit with timestamp.

## 3. Configuration
| Variable | Default | Description |
|---|---|---|
| `TARGET_DIR` | `/vault` | Directory to monitor (Docker에서는 호스트 경로를 그대로 마운트해도 됨) |
| `DEBOUNCE_SECONDS` | `300` | Wait time before syncing |
| `METRICS_PORT` | `8000` | Prometheus metrics port |

## 4. Technical Stack
- **Language**: Python 3.11+
- **Key Libraries**:
  - `watchdog`: Event listening.
  - `GitPython`: Git command wrapping.
  - `prometheus_client`: Observability.
  - `python-dotenv`: Config loading.
