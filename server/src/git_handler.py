import os
import git
import time
from pathlib import Path
from src.config import config
from src.utils import logger
from src.metrics import COMMITS_TOTAL, PUSHES_TOTAL, ERRORS_TOTAL, LAST_SYNC_TIMESTAMP


class GitHandler:
    def __init__(self, repo_path=None):
        self.repo_path = repo_path or config.TARGET_DIR
        self.repo = self._init_repo()

    def _git_env(self):
        """
        Environment variables for git/ssh commands.
        NOTE: This must apply before clone/pull/push to avoid SSH host key prompts in containers.
        """
        if not config.SSH_KEY_PATH:
            return {}

        return {
            "GIT_SSH_COMMAND": (
                f"ssh -i {config.SSH_KEY_PATH} "
                "-o IdentitiesOnly=yes "
                "-o StrictHostKeyChecking=no "
                "-o UserKnownHostsFile=/dev/null"
            )
        }

    def _try_pull_rebase(self):
        """
        Try to update the local working tree from the remote.
        - Only runs when a remote is configured.
        - Only runs when the working tree is clean (to avoid rebase/pull failures).
        - Only runs when an upstream tracking branch exists.
        """
        if not self.repo or not config.GIT_REMOTE_URL:
            return

        try:
            # Pulling with local changes often fails; skip to keep the process resilient.
            if self.repo.is_dirty(untracked_files=True):
                logger.info("Local changes detected; skipping pull --rebase.")
                return

            # active_branch can raise when HEAD is detached or the repo has no commits yet.
            branch = self.repo.active_branch
            tracking = branch.tracking_branch()
            if tracking is None:
                logger.info(
                    "No upstream configured for branch %s; skipping pull --rebase.",
                    branch.name,
                )
                return

            logger.info("Pulling latest changes (rebase) from %s...", tracking)
            self.repo.git.pull("--rebase")
            logger.info("Pull completed.")
        except git.exc.GitCommandError as e:
            logger.warning("Pull --rebase failed: %s", e)
            ERRORS_TOTAL.inc()
        except Exception as e:
            logger.warning("Pull failed: %s", e)
            ERRORS_TOTAL.inc()

    def _init_repo(self):
        try:
            repo_path = Path(self.repo_path)
            repo_path.mkdir(parents=True, exist_ok=True)
            git_env = self._git_env()

            if not os.path.exists(os.path.join(self.repo_path, ".git")):
                # If a remote is configured and the directory is empty, prefer cloning to
                # bootstrap history and tracking branches on first run.
                is_empty_dir = not any(repo_path.iterdir())
                if config.GIT_REMOTE_URL and is_empty_dir:
                    logger.info(
                        "No git repo found. Cloning from remote into %s...", self.repo_path
                    )
                    # GitPython clone happens before we can call repo.git.update_environment,
                    # so apply env to the process environment for the duration of the clone.
                    old_env = {k: os.environ.get(k) for k in git_env.keys()}
                    os.environ.update(git_env)
                    try:
                        repo = git.Repo.clone_from(config.GIT_REMOTE_URL, self.repo_path)
                    finally:
                        for k, v in old_env.items():
                            if v is None:
                                os.environ.pop(k, None)
                            else:
                                os.environ[k] = v
                else:
                    logger.info("Initializing new git repo at %s", self.repo_path)
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
                repo.git.update_environment(**git_env)

            return repo
        except Exception as e:
            logger.error("Failed to initialize git repo: %s", e)
            ERRORS_TOTAL.inc()
            return None

    def has_changes(self):
        if not self.repo:
            return False
        try:
            # Check for unstaged changes and untracked files
            return self.repo.is_dirty(untracked_files=True)
        except Exception as e:
            logger.error("Error checking changes: %s", e)
            ERRORS_TOTAL.inc()
            return False

    def sync(self):
        if not self.repo:
            return

        try:
            # Best-effort update from remote first (when safe), then commit/push local changes.
            self._try_pull_rebase()

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
            logger.info("Committed: %s", commit_message)
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
                    logger.warning("Push failed (possibly non-fast-forward): %s", e)
                    # Optional: Try pull --rebase then push?
                    # For now, just log error to avoid complex merge conflicts automatically.
                    ERRORS_TOTAL.inc()
            else:
                logger.warning("No remote URL configured, skipping push.")

            LAST_SYNC_TIMESTAMP.set(time.time())

        except Exception as e:
            logger.error("Sync failed: %s", e)
            ERRORS_TOTAL.inc()
