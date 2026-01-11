# Project TODOs

## Backlog / Future Improvements

- [ ] **Bi-directional Sync**
  - Implement periodic `git pull` to fetch changes from remote (if Personal PC is not the only writer).
  - Handle merge conflicts automatically (e.g., `git merge --strategy-option theirs`).

- [ ] **Robust Error Handling**
  - [ ] Retry logic for transient network failures during Push.
  - [ ] Alerting system (Slack/Email) on persistent failures.

- [ ] **Deployment**
  - [ ] Create `docker-compose.yml` for easier orchestration.
  - [ ] Add `healthcheck` in Dockerfile.

- [ ] **Testing**
  - [ ] Add unit tests for `Debouncer`.
  - [ ] Add integration tests for Git flow using a local mock remote.

- [ ] **Optimization**
  - [ ] Support `git-lfs` for large media files in Vault.
