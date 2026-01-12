# Project Rules

## 1. Development Environment
- **Package Manager**: MUST use `uv` for dependency management.
  - Add packages: `uv add <package>`
  - Run scripts: `uv run <script>`
  - Lock dependencies: `uv lock`

## 2. Documentation
- **Location**: All documentation MUST be stored in the `md/` directory.
- **Maintenance**: 
  - `md/architecture.md`: Update on architectural changes.
  - `md/spec.md`: Update when features are added or modified.
  - `md/status.md`: Update periodically with implementation status and health checks.
  - `md/todo.md`: Maintain backlog of tasks.
- **Rule**: Any new feature implementation MUST be accompanied by updates to the relevant `md/` files.

## 3. Implementation Principles
- **Separation of Concerns**: Vault Data and Sync Logic must remain separate.
- **Observability**: New features should expose relevant metrics (Prometheus).
- **Graceful Failure**: Network or Git errors should not crash the main process but be logged and counted.
