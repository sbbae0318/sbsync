import schedule
import time
from src.utils import logger
from src.config import config


class Scheduler:
    def __init__(self, git_handler):
        self.git_handler = git_handler
        self.running = False

    def setup(self):
        """Setup the periodic pull schedule."""
        interval = config.PULL_INTERVAL_MINUTES
        schedule.every(interval).minutes.do(self._pull_job)
        logger.info("Scheduled git pull every %d minutes", interval)

    def _pull_job(self):
        """Job to be executed on schedule."""
        logger.info("Scheduled pull triggered")
        self.git_handler.sync()

    def run(self):
        """Run the scheduler loop."""
        self.running = True
        logger.info("Starting scheduler loop...")

        while self.running:
            schedule.run_pending()
            time.sleep(1)

    def stop(self):
        """Stop the scheduler."""
        self.running = False
        logger.info("Scheduler stopped")
