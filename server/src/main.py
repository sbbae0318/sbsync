import time
import sys
import signal
from watchdog.observers import Observer as DefaultObserver
from watchdog.observers.polling import PollingObserver

from src.config import config
from src.health import MountHealthChecker
from src.metrics import start_metrics_server
from src.utils import logger, Debouncer, PeriodicTimer
from src.git_handler import GitHandler
from src.watcher import VaultEventHandler


def main():
    logger.info("Starting sbSync...")

    # 1. Validate Config
    config.validate()

    # 2. Start Metrics Server
    logger.info("Starting metrics server on port %s", config.METRICS_PORT)
    start_metrics_server(config.METRICS_PORT)

    # 3. Initialize Git Handler
    git_handler = GitHandler()
    if not git_handler.repo:
        logger.error("Could not initialize Git repository. Exiting.")
        sys.exit(1)

    # 3.1 Initial Sync Attempt (best-effort)
    # Try to update from remote first (if configured), then commit/push local changes (if any).
    # GitHandler.sync() is already resilient and should not crash the main process on Git/network errors.
    logger.info("Performing initial sync attempt...")
    git_handler.sync()

    # 4. Setup Debouncer
    # This checks for changes and commits/pushes
    debouncer = Debouncer(config.DEBOUNCE_SECONDS, git_handler.sync)

    # 4.1 Setup Periodic Sync Timer
    def _safe_sync():
        try:
            git_handler.sync()
        except Exception:
            logger.exception("Periodic sync failed, will retry next interval")

    periodic_timer = PeriodicTimer(config.PERIODIC_SYNC_SECONDS, _safe_sync)
    periodic_timer.start()
    logger.info("Periodic sync every %ss", config.PERIODIC_SYNC_SECONDS)

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
        logger.info("Monitoring directory: %s", config.TARGET_DIR)
    except FileNotFoundError:
        logger.error("Target directory %s not found.", config.TARGET_DIR)
        sys.exit(1)

    # 6. Graceful Shutdown
    def signal_handler(_sig, _frame):
        logger.info("Shutting down...")
        observer.stop()
        debouncer.cancel()
        periodic_timer.cancel()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 7. Health Check Loop (replaces idle sleep loop)
    health_checker = MountHealthChecker(config.TARGET_DIR)
    check_interval = config.HEALTH_CHECK_SECONDS
    elapsed = 0
    try:
        while True:
            time.sleep(1)
            elapsed += 1
            if elapsed >= check_interval:
                if not health_checker.check():
                    logger.critical(
                        "Mount is stale! Exiting for container recreation."
                    )
                    observer.stop()
                    debouncer.cancel()
                    periodic_timer.cancel()
                    sys.exit(1)
                elapsed = 0
    except KeyboardInterrupt:
        observer.stop()

    observer.join()


if __name__ == "__main__":
    main()
