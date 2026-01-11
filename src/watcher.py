from watchdog.events import FileSystemEventHandler
from .utils import logger
from .metrics import FILES_CHANGED_TOTAL


class VaultEventHandler(FileSystemEventHandler):
    def __init__(self, on_change_callback):
        self.on_change_callback = on_change_callback

    def on_any_event(self, event):
        if event.is_directory:
            return

        # Ignore .git directory changes
        if ".git" in event.src_path:
            return

        # Optional: Filter for specific file types if strictly needed,
        # but Obsidian vaults can contain arbitrary attachments.
        # We rely on .gitignore in the Vault for exclusion.

        logger.info(f"✨ Detected event: {event.event_type} on {event.src_path}")
        FILES_CHANGED_TOTAL.inc()
        self.on_change_callback()
