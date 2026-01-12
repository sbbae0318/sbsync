# Project TODOs

## Completed

- [x] **Initial Sync Attempt on Startup**
  - Best-effort `pull --rebase` when safe (clean working tree + upstream configured).
  - Call `GitHandler.sync()` once at process start before watcher loop.
- [x] **docker-compose Orchestration**
  - Add `docker-compose.yml` with `restart: unless-stopped`.
  - Mount only the SSH private key to avoid macOS OpenSSH config incompatibilities.

## Backlog / Future Improvements

- [ ] **Bi-directional Sync**
  - Implement periodic `git pull` to fetch changes from remote (if Personal PC is not the only writer).
  - Handle merge conflicts automatically (e.g., `git merge --strategy-option theirs`).

- [ ] **Robust Error Handling**
  - [ ] Retry logic for transient network failures during Push.
  - [ ] Alerting system (Slack/Email) on persistent failures.

- [ ] **Deployment**
  - [ ] Add `healthcheck` to docker-compose.
  - [ ] Add `healthcheck` in Dockerfile.

- [ ] **Testing**
  - [ ] Add unit tests for `Debouncer`.
  - [ ] Add integration tests for Git flow using a local mock remote.

- [ ] **Optimization**
  - [ ] Support `git-lfs` for large media files in Vault.
