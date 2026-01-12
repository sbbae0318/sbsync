import sys
import signal
from src.config import config
from src.metrics import start_metrics_server
from src.utils import logger
from src.git_handler import GitHandler
from src.scheduler import Scheduler


def main():
    logger.info("Starting sbSync Client...")

    # 1. Validate Config
    try:
        config.validate()
    except ValueError as e:
        logger.error("Configuration error: %s", e)
        sys.exit(1)

    # 2. Start Metrics Server
    logger.info("Starting metrics server on port %s", config.METRICS_PORT)
    start_metrics_server(config.METRICS_PORT)

    # 3. Initialize Git Handler
    git_handler = GitHandler()
    if not git_handler.repo:
        logger.error("Could not initialize Git repository. Exiting.")
        sys.exit(1)

    # 4. Perform Initial Sync
    logger.info("Performing initial sync...")
    git_handler.sync()

    # 5. Setup Scheduler
    scheduler = Scheduler(git_handler)
    scheduler.setup()

    # 6. Graceful Shutdown
    def signal_handler(_sig, _frame):
        logger.info("Shutting down...")
        scheduler.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 7. Run Scheduler
    try:
        scheduler.run()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
        scheduler.stop()


if __name__ == "__main__":
    main()
