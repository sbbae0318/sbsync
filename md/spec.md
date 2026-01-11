# System Specifications

## 1. File Monitoring
- **Trigger**: File system events (Create, Modify, Delete, Move).
- **Scope**: Recursive monitoring of `TARGET_DIR`.
- **Exclusions**: 
  - `.git` directory.
  - Folders/Files matched by `.gitignore` in the Vault.

## 2. Synchronization Logic
- **Mechanism**: One-way Push (Personal PC -> Remote).
- **Debounce**: 300 seconds (Configurable). Timer resets on new events.
- **Batching**: All pending changes are grouped into a single commit with timestamp.

## 3. Configuration
| Variable | Default | Description |
|---|---|---|
| `TARGET_DIR` | `/vault` | Directory to monitor |
| `DEBOUNCE_SECONDS` | `300` | Wait time before syncing |
| `METRICS_PORT` | `8000` | Prometheus metrics port |

## 4. Technical Stack
- **Language**: Python 3.11+
- **Key Libraries**:
  - `watchdog`: Event listening.
  - `GitPython`: Git command wrapping.
  - `prometheus_client`: Observability.
  - `python-dotenv`: Config loading.
