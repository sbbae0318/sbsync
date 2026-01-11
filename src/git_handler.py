import os
import git
import time
from .config import config
from .utils import logger
from .metrics import COMMITS_TOTAL, PUSHES_TOTAL, ERRORS_TOTAL, LAST_SYNC_TIMESTAMP


class GitHandler:
    def __init__(self, repo_path=None):
        self.repo_path = repo_path or config.TARGET_DIR
        self.repo = self._init_repo()

    def _init_repo(self):
        try:
            if not os.path.exists(os.path.join(self.repo_path, ".git")):
                logger.info(f"Initializing new git repo at {self.repo_path}")
                repo = git.Repo.init(self.repo_path)
            else:
                repo = git.Repo(self.repo_path)

            # Configure user
            with repo.config_writer() as git_config:
                git_config.set_value("user", "name", config.GIT_USER_NAME)
                git_config.set_value("user", "email", config.GIT_USER_EMAIL)

            # Configure Remote if not exists
            if config.GIT_REMOTE_URL:
                if "origin" not in repo.remotes:
                    repo.create_remote("origin", config.GIT_REMOTE_URL)
                else:
                    repo.remotes.origin.set_url(config.GIT_REMOTE_URL)

            # Configure SSH key if provided
            if config.SSH_KEY_PATH:
                # Ensure we use the correct SSH command
                repo.git.update_environment(
                    GIT_SSH_COMMAND=f"ssh -i {config.SSH_KEY_PATH} -o IdentitiesOnly=yes -o StrictHostKeyChecking=no"
                )

            return repo
        except Exception as e:
            logger.error(f"Failed to initialize git repo: {e}")
            ERRORS_TOTAL.inc()
            return None

    def has_changes(self):
        if not self.repo:
            return False
        try:
            # Check for unstaged changes and untracked files
            return self.repo.is_dirty(untracked_files=True)
        except Exception as e:
            logger.error(f"Error checking changes: {e}")
            ERRORS_TOTAL.inc()
            return False

    def sync(self):
        if not self.repo:
            return

        try:
            if not self.has_changes():
                logger.info("No changes to sync.")
                return

            # Add all changes (Obsidian Vault assets: md, png, jpg, etc.)
            # git add . automatically respects .gitignore if present in Vault
            self.repo.git.add(A=True)
            logger.info("Added all changes.")

            # Commit
            commit_message = f"Auto-sync: {time.strftime('%Y-%m-%d %H:%M:%S')}"
            self.repo.index.commit(commit_message)
            logger.info(f"Committed: {commit_message}")
            COMMITS_TOTAL.inc()

            # Push
            if config.GIT_REMOTE_URL:
                logger.info("Pushing to remote...")
                origin = self.repo.remote(name="origin")

                # Handling push errors (e.g., non-fast-forward)
                try:
                    origin.push()
                    logger.info("Push successful.")
                    PUSHES_TOTAL.inc()
                except git.exc.GitCommandError as e:
                    logger.warning(f"Push failed (possibly non-fast-forward): {e}")
                    # Optional: Try pull --rebase then push?
                    # For now, just log error to avoid complex merge conflicts automatically.
                    ERRORS_TOTAL.inc()
            else:
                logger.warning("No remote URL configured, skipping push.")

            LAST_SYNC_TIMESTAMP.set(time.time())

        except Exception as e:
            logger.error(f"Sync failed: {e}")
            ERRORS_TOTAL.inc()
