# sbSync Usage Guide

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
cd sbsync

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

### Running
```bash
uv run src/main.py
```

## 3. Docker Deployment

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
