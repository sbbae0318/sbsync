# sbSync Server Usage Guide

> This is the **server** (push client) usage guide. For the client (pull client), see [client usage guide](../../client/md/usage.md).

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
cd sbsync/server

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
- `GIT_REMOTE_URL`: URL of the remote git repo for the vault.
- `SSH_KEY_PATH`: Path to private SSH key (if using SSH).
- `USE_POLLING`: Docker/WSL/네트워크 볼륨에서 이벤트 누락이 있으면 `true`.

### Running
```bash
uv run sbsync
```

또는 모듈로 실행:

```bash
uv run python -m src.main
```

### Startup behavior (Initial Sync Attempt)
- sbSync는 **시작 시점에 1회** `GitHandler.sync()`를 호출하여 동기화를 “먼저” 시도합니다.
- remote가 설정되어 있고 대상 디렉토리에 `.git`이 없으며 **디렉토리가 비어있으면**, 초기 실행에서 **clone으로 부트스트랩**합니다.
- remote가 설정되어 있고 working tree가 깨끗하며 upstream이 잡혀있으면, **`git pull --rebase`를 best-effort로 시도**합니다.
- 이후부터는 파일 이벤트를 디바운스하여 커밋/푸시합니다.

## 3. Docker Deployment

### Unified docker-compose (추천)

From the root directory, you can run both server and client:

```bash
cd sbsync  # root directory
cp .env.example .env
vi .env  # Edit with SERVER_* and CLIENT_* variables

# Run server only
docker-compose up -d sbsync-server

# Or run both server and client
docker-compose up -d
```

### Standalone server docker-compose

1) `.env` 설정 (git에 커밋되지 않음)
- `GIT_REMOTE_URL`, `SSH_KEY_PATH` 등 기존 설정은 그대로 사용합니다.
- docker-compose에서는 `TARGET_DIR`을 **호스트 절대 경로로 설정**하고, 해당 경로를 컨테이너에도 **동일 경로로 bind mount**합니다.
  - 예: `TARGET_DIR=/Users/sbbae/project/sbsync` 이면 컨테이너도 `/Users/sbbae/project/sbsync` 를 감시/clone/pull 합니다.
 - Docker(macOS/WSL)에서는 파일 이벤트(inotify)가 누락될 수 있어 **기본은 polling**입니다.
   - 필요 시 `.env`에 `USE_POLLING=false`로 바꾸면 inotify(기본 Observer)로 시도합니다.
 - `SSH_KEY_PATH`는 컨테이너 내부 경로(`/root/.ssh/...`)여야 합니다. docker-compose 사용 시에는 `/root/.ssh/id_ed25519`로 고정해서 사용합니다.
 - macOS의 `~/.ssh/config`에는 `UseKeychain` 같은 옵션이 들어갈 수 있는데, 리눅스 컨테이너(OpenSSH)가 이를 이해 못해 실패할 수 있습니다. 그래서 compose는 `~/.ssh` 전체가 아니라 **키 파일만 마운트**합니다.
 - 호스트 키 경로를 바꾸고 싶으면 `SSH_KEY_HOST_PATH=/path/to/id_ed25519`를 설정하세요.

2) 실행 (재부팅 후 자동 재시작)

```bash
cd sbsync/server
docker-compose up -d --build
```

중지:

```bash
docker-compose down
```

### Docker 상태 확인이 안 될 때 (Mac)
- `docker ps`에서 `Cannot connect to the Docker daemon ...`가 뜨면, 보통 **Docker Desktop(도커 데몬)** 이 꺼져있거나,
  혹은 **docker context가 다른 런타임(예: colima)** 으로 잡혀 잘못된 소켓을 보고 있는 경우가 많습니다.

확인:

```bash
docker context ls
docker context show
docker info
```

Docker Desktop을 쓴다면 컨텍스트를 `default`로:

```bash
docker context use default
docker info
```

### Docker 리소스 "전부 정리"(컨테이너/이미지/볼륨)
레포에 포함된 스크립트로 **모든 컨테이너 삭제 + 미사용 이미지/볼륨/캐시 정리**를 한 번에 할 수 있습니다.

```bash
cd sbsync  # root directory
./scripts/docker_nuke.sh --yes
```

### Build
```bash
docker build -t sbsync:latest .
```

### Run
```bash
docker run -d \
  --name sbsync \
  -v /path/to/your/vault:/vault \
  -v /path/to/ssh/keys:/root/.ssh:ro \
  --env-file .env \
  -p 8000:8000 \
  sbsync:latest
```
*Note: Ensure `TARGET_DIR` in `.env` matches the mount path (default `/vault`).*

## 4. Monitoring
Metrics are available at `http://localhost:8000/`.
- `sbsync_commits_total`
- `sbsync_last_sync_timestamp`
