import os
import git
import time
from pathlib import Path
from src.config import config
from src.utils import logger
from src.metrics import PULLS_TOTAL, ERRORS_TOTAL, LAST_PULL_TIMESTAMP


class GitHandler:
    def __init__(self, repo_path=None):
        self.repo_path = repo_path or config.TARGET_DIR
        self.repo = self._init_repo()

    def _git_env(self):
        """
        Environment variables for git/ssh commands.
        NOTE: This must apply before clone/pull to avoid SSH host key prompts in containers.
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

    def _init_repo(self):
        try:
            repo_path = Path(self.repo_path)
            repo_path.mkdir(parents=True, exist_ok=True)
            git_env = self._git_env()

            if not os.path.exists(os.path.join(self.repo_path, ".git")):
                # Clone from remote if directory is empty
                is_empty_dir = not any(repo_path.iterdir())
                if config.GIT_REMOTE_URL and is_empty_dir:
                    logger.info(
                        "No git repo found. Cloning from remote into %s...", self.repo_path
                    )
                    # Apply env to the process environment for the duration of the clone
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
                repo.git.update_environment(**git_env)

            return repo
        except Exception as e:
            logger.error("Failed to initialize git repo: %s", e)
            ERRORS_TOTAL.inc()
            return None

    def clean_and_checkout(self):
        """
        Clean the working directory and checkout to discard all local changes.
        Equivalent to: git clean -fd && git checkout .
        """
        if not self.repo:
            logger.error("Repository not initialized")
            return False

        try:
            # Remove untracked files and directories
            logger.info("Running git clean -fd...")
            self.repo.git.clean("-fd")
            logger.info("Git clean completed")

            # Discard all local changes
            logger.info("Running git checkout .")
            self.repo.git.checkout(".")
            logger.info("Git checkout completed")

            return True
        except git.exc.GitCommandError as e:
            logger.error("Git clean/checkout failed: %s", e)
            ERRORS_TOTAL.inc()
            return False
        except Exception as e:
            logger.error("Unexpected error during clean/checkout: %s", e)
            ERRORS_TOTAL.inc()
            return False

    def pull(self):
        """
        Pull the latest changes from the remote repository.
        First performs clean and checkout to ensure a clean state.
        """
        if not self.repo:
            logger.error("Repository not initialized")
            return False

        try:
            # First, ensure clean working directory
            if not self.clean_and_checkout():
                logger.error("Failed to clean working directory before pull")
                return False

            # Check if we have a tracking branch
            try:
                branch = self.repo.active_branch
                tracking = branch.tracking_branch()
                if tracking is None:
                    # Try to set up tracking with origin/main or origin/master
                    logger.info("No upstream configured, attempting to set tracking branch...")
                    origin = self.repo.remote(name="origin")
                    origin.fetch()

                    # Try main first, then master
                    for branch_name in ["main", "master"]:
                        try:
                            self.repo.git.checkout(branch_name)
                            self.repo.git.branch(f"--set-upstream-to=origin/{branch_name}", branch_name)
                            logger.info("Set tracking branch to origin/%s", branch_name)
                            break
                        except git.exc.GitCommandError:
                            continue
            except Exception as e:
                logger.warning("Could not configure tracking branch: %s", e)

            # Pull from remote
            logger.info("Pulling latest changes from remote...")
            origin = self.repo.remote(name="origin")
            origin.pull()
            logger.info("Pull successful")

            PULLS_TOTAL.inc()
            LAST_PULL_TIMESTAMP.set(time.time())
            return True

        except git.exc.GitCommandError as e:
            logger.error("Git pull failed: %s", e)
            ERRORS_TOTAL.inc()
            return False
        except Exception as e:
            logger.error("Unexpected error during pull: %s", e)
            ERRORS_TOTAL.inc()
            return False

    def sync(self):
        """
        Main synchronization method: clean, checkout, and pull.
        """
        logger.info("Starting sync operation...")
        result = self.pull()
        if result:
            logger.info("Sync completed successfully")
        else:
            logger.error("Sync failed")
        return result
