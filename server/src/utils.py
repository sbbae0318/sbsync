import time
import logging
from threading import Timer
from typing import Callable

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
        logger.debug("Debounce timer started. Waiting %ss...", self.interval)

    def cancel(self):
        if self.timer is not None:
            self.timer.cancel()


class PeriodicTimer:
    def __init__(self, interval: float, callback: Callable):
        self.interval = interval
        self.callback = callback
        self.timer = None
        self._cancelled = False

    def start(self):
        self._cancelled = False
        self._schedule()

    def _schedule(self):
        if self._cancelled:
            return
        self.timer = Timer(self.interval, self._run)
        self.timer.start()
        logger.debug("PeriodicTimer scheduled. Next in %ss...", self.interval)

    def _run(self):
        if self._cancelled:
            return
        self.callback()
        self._schedule()

    def cancel(self):
        self._cancelled = True
        if self.timer is not None:
            self.timer.cancel()
