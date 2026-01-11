import time
import sys
import signal
from watchdog.observers import Observer as DefaultObserver
from watchdog.observers.polling import PollingObserver

from .config import config
from .metrics import start_metrics_server
from .utils import logger, Debouncer
from .git_handler import GitHandler
from .watcher import VaultEventHandler


def main():
    logger.info("Starting sbSync...")

    # 1. Validate Config
    config.validate()

    # 2. Start Metrics Server
    logger.info(f"Starting metrics server on port {config.METRICS_PORT}")
    start_metrics_server(config.METRICS_PORT)

    # 3. Initialize Git Handler
    git_handler = GitHandler()
    if not git_handler.repo:
        logger.error("Could not initialize Git repository. Exiting.")
        sys.exit(1)

    # 4. Setup Debouncer
    # This checks for changes and commits/pushes
    debouncer = Debouncer(config.DEBOUNCE_SECONDS, git_handler.sync)

    # 5. Setup Watcher
    event_handler = VaultEventHandler(on_change_callback=debouncer.call)

    if config.USE_POLLING:
        logger.info(
            "Using PollingObserver for file monitoring (WSL/Network Drive compatibility)"
        )
        observer = PollingObserver()
    else:
        observer = DefaultObserver()

    try:
        observer.schedule(event_handler, config.TARGET_DIR, recursive=True)
        observer.start()
        logger.info(f"Monitoring directory: {config.TARGET_DIR}")
    except FileNotFoundError:
        logger.error(f"Target directory {config.TARGET_DIR} not found.")
        sys.exit(1)

    # 6. Graceful Shutdown
    def signal_handler(sig, frame):
        logger.info("Shutting down...")
        observer.stop()
        debouncer.cancel()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()


if __name__ == "__main__":
    main()
