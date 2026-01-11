import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    def __init__(self):
        self.TARGET_DIR = os.getenv("TARGET_DIR", "/vault")
        self.GIT_REMOTE_URL = os.getenv("GIT_REMOTE_URL", "")
        self.GIT_USER_NAME = os.getenv("GIT_USER_NAME", "sbSync Bot")
        self.GIT_USER_EMAIL = os.getenv("GIT_USER_EMAIL", "bot@sbsync.local")
        self.SSH_KEY_PATH = os.getenv("SSH_KEY_PATH", "")

        # Debounce time in seconds
        self.DEBOUNCE_SECONDS = int(os.getenv("DEBOUNCE_SECONDS", "300"))

        # Prometheus metrics port
        self.METRICS_PORT = int(os.getenv("METRICS_PORT", "8000"))

        # Watchdog Polling Mode (useful for WSL/Docker mounted volumes)
        self.USE_POLLING = os.getenv("USE_POLLING", "false").lower() == "true"

    def validate(self):
        if not self.GIT_REMOTE_URL:
            print("WARNING: GIT_REMOTE_URL is not set. Git operations might fail.")


config = Config()
