import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    def __init__(self):
        self.TARGET_DIR = os.getenv("TARGET_DIR", "/vault")
        self.GIT_REMOTE_URL = os.getenv("GIT_REMOTE_URL", "")
        self.GIT_USER_NAME = os.getenv("GIT_USER_NAME", "sbSync Client")
        self.GIT_USER_EMAIL = os.getenv("GIT_USER_EMAIL", "client@sbsync.local")
        self.SSH_KEY_PATH = os.getenv("SSH_KEY_PATH", "")

        # Pull interval in minutes
        self.PULL_INTERVAL_MINUTES = int(os.getenv("PULL_INTERVAL_MINUTES", "5"))

        # Prometheus metrics port
        self.METRICS_PORT = int(os.getenv("METRICS_PORT", "8001"))

    def validate(self):
        if not self.GIT_REMOTE_URL:
            raise ValueError("GIT_REMOTE_URL is required for sbsync-client")

        if not Path(self.TARGET_DIR).exists():
            Path(self.TARGET_DIR).mkdir(parents=True, exist_ok=True)


config = Config()
