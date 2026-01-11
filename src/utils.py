import time
import logging
from threading import Timer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger("sbSync")


class Debouncer:
    def __init__(self, interval, callback):
        self.interval = interval
        self.callback = callback
        self.timer = None

    def call(self):
        """
        Resets the timer. The callback will only be executed
        if no new calls are made within the interval.
        """
        if self.timer is not None:
            self.timer.cancel()

        self.timer = Timer(self.interval, self.callback)
        self.timer.start()
        logger.info(f"Debounce timer started. Waiting {self.interval}s...")

    def cancel(self):
        if self.timer is not None:
            self.timer.cancel()
