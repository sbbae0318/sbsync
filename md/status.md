# sbSync Implementation Status

## 1. 구현 현황 (Implementation Status)

### 1.1 Core Features
- **File Monitoring**: `watchdog` 라이브러리를 사용하여 지정된 디렉토리(`TARGET_DIR`)의 파일 변경을 실시간 감지.
- **Debounced Sync**: 변경 감지 후 즉시 동작하지 않고, 설정된 `DEBOUNCE_SECONDS` (기본 300초) 동안 추가 변경이 없을 때 Git Sync 수행.
- **Git Integration**: `GitPython`을 사용하여 `git add`, `git commit`, `git push` 자동화. `.gitignore`에 정의된 파일은 자동으로 제외됨 (Vault 설정 준수).
- **Initial Sync Attempt on Startup**: 프로세스 시작 시 1회, best-effort로 원격 반영을 시도한 뒤(woking tree가 깨끗하고 upstream이 있을 때 `pull --rebase`), 로컬 변경이 있으면 커밋/푸시 수행.
- **Environment Management**: `uv` 패키지 매니저 사용. Docker 배포 시에도 `uv`를 활용하여 빠른 빌드 지원.

### 1.4 Recent Changes (2026-01)
- **docker-compose 지원**: `restart: unless-stopped`로 재부팅/재시작 시 자동 복구.
- **Docker build 안정화(맥)**: Keychain 비대화형 이슈로 레지스트리 pull이 막힐 수 있어, 필요 시 `DOCKER_CONFIG` 분리로 우회 가능.
- **SSH 안정화**:
  - macOS `~/.ssh/config`의 `UseKeychain` 옵션이 컨테이너(OpenSSH)에서 실패할 수 있어 키 파일만 마운트.
  - clone 시점부터 `GIT_SSH_COMMAND` 적용(Host key verification/프롬프트 회피).

### 1.2 Security
- **Sensitive Data**: `.env` 파일을 통해 중요 정보(Git URL, User Info 등) 관리.
- **SSH Key**: SSH Key 경로를 환경변수로 받아 Git 연동 시 활용 (Docker 볼륨 마운트 필요).

### 1.3 Observability
- **Prometheus Metrics**: `8000` 포트(설정 가능)로 메트릭 노출.
    - `sbsync_commits_total`
    - `sbsync_pushes_total`
    - `sbsync_errors_total`
    - `sbsync_last_sync_timestamp`
    - `sbsync_files_changed_total`

## 2. 잠재적 취약점 (Potential Vulnerabilities)

1. **Git Conflict Resolution**:
    - 현재 로직은 `check changes -> add -> commit -> push`의 단순한 단방향 흐름입니다.
    - Remote에 다른 변경사항이 있어 Push가 거부될 경우(Rejection), 현재 로직은 실패 로그를 남기고 `errors_total`을 증가시킵니다.
    - 시작 시점에 working tree가 깨끗하고 upstream이 있을 때는 `pull --rebase`를 best-effort로 시도하지만, 자동 머지/충돌 해결은 하지 않습니다.
    - **Mitigation**: 업무용 PC는 Read-only라서 충돌 가능성이 낮으나, Personal PC에서 다른 작업이 병행되면 충돌 가능.

2. **Race Conditions**:
    - 매우 빈번한 파일 변경 시 Debounce가 계속 밀려 Sync가 늦어질 수 있습니다.

3. **SSH Host Verification**:
    - 편의를 위해 `StrictHostKeyChecking=no` 옵션을 사용했습니다. 중간자 공격(MITM) 가능성이 이론상 존재합니다.

## 3. 개선 포인트 (Future Improvements)

1. **Robust Git Flow**:
    - Push 실패 시 `git pull --rebase` 시도 로직 추가.
2. **Health Check**:
    - 컨테이너 오케스트레이션(Kubernetes 등)을 위한 `/healthz` 엔드포인트 추가.
3. **Notification**:
    - Sync 실패 시 Slack/Discord 알림 연동.
4. **Binary Large Objects**:
    - 대용량 파일이 많을 경우 `git-lfs` 지원 고려 필요.
