# sbSync Client Usage Guide

## 1. Prerequisites
- **Python 3.11+**
- **uv** (Package Manager)
- **Git**
- **Docker** (Optional for containerized run)

## 2. Local Development (with uv)

### Setup
```bash
# Clone repository
git clone <repo_url>
cd sbsync-client

# Initialize environment and install dependencies
uv sync
```

### Configuration
Copy `.env.example` to `.env` and edit:
```bash
cp .env.example .env
vi .env
```
Key variables:
- `TARGET_DIR`: Absolute path to your local Obsidian Vault.
- `GIT_REMOTE_URL`: URL of the remote git repo for the vault (Required).
- `SSH_KEY_PATH`: Path to private SSH key (if using SSH).
- `PULL_INTERVAL_MINUTES`: Pull interval in minutes (default 5).

### Running
```bash
uv run sbsync-client
```

또는 모듈로 실행:

```bash
uv run python -m src.main
```

### Startup behavior (Initial Sync)
- sbSync Client는 **시작 시점에 1회** sync를 호출하여 최신 상태로 업데이트합니다.
- remote가 설정되어 있고 대상 디렉토리에 `.git`이 없으며 **디렉토리가 비어있으면**, 초기 실행에서 **clone으로 부트스트랩**합니다.
- 이후부터는 설정된 interval마다 주기적으로 pull합니다.
- **중요**: 로컬 변경사항은 항상 폐기됩니다 (`git clean -fd && git checkout .`).

## 3. Docker Deployment

### docker-compose (추천)

1) `.env` 설정
- `GIT_REMOTE_URL`, `SSH_KEY_PATH` 등 설정은 그대로 사용합니다.
- docker-compose에서는 `TARGET_DIR`을 **호스트 절대 경로로 설정**하고, 해당 경로를 컨테이너에도 **동일 경로로 bind mount**합니다.
  - 예: `TARGET_DIR=/Users/sbbae/Vault` 이면 컨테이너도 `/Users/sbbae/Vault`를 pull 대상으로 사용합니다.
- `SSH_KEY_PATH`는 컨테이너 내부 경로(`/root/.ssh/...`)여야 합니다. docker-compose 사용 시에는 `/root/.ssh/id_ed25519`로 고정해서 사용합니다.
- 호스트 키 경로를 바꾸고 싶으면 `SSH_KEY_HOST_PATH=/path/to/id_ed25519`를 설정하세요.

2) 실행 (재부팅 후 자동 재시작)

```bash
docker-compose up -d --build
```

중지:

```bash
docker-compose down
```

### Build
```bash
docker build -t sbsync-client:latest .
```

### Run
```bash
docker run -d \
  --name sbsync-client \
  -v /path/to/your/vault:/vault \
  -v /path/to/ssh/keys:/root/.ssh:ro \
  --env-file .env \
  -p 8001:8001 \
  sbsync-client:latest
```
*Note: Ensure `TARGET_DIR` in `.env` matches the mount path (default `/vault`).*

## 4. Monitoring
Metrics are available at `http://localhost:8001/`.
- `sbsync_client_pulls_total`: Total number of successful pulls
- `sbsync_client_errors_total`: Total number of errors
- `sbsync_client_last_pull_timestamp`: Unix timestamp of last successful pull

## 5. Important Notes

### Read-Only Synchronization
- sbSync Client는 **로컬 변경사항을 폐기**합니다.
- Work PC에서 Vault를 수정하더라도 다음 pull 시 모든 변경사항이 사라집니다.
- Personal PC에서 sbsync로 push한 내용만 Work PC에 반영됩니다.

### Conflict Resolution
- 항상 remote의 상태를 따라가므로 conflict가 발생하지 않습니다.
- `git clean -fd && git checkout .`로 working directory를 항상 clean 상태로 유지합니다.
