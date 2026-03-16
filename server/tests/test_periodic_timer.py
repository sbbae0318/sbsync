import time
import threading
import pytest
from src.utils import PeriodicTimer


class TestPeriodicTimer:
    """PeriodicTimer 클래스 테스트"""

    def test_timer_fires_callback(self):
        """interval 후 callback이 호출되는지 확인"""
        fired = threading.Event()

        def callback():
            fired.set()

        timer = PeriodicTimer(0.05, callback)
        timer.start()
        result = fired.wait(timeout=0.5)
        timer.cancel()
        assert result, "callback이 interval 내에 호출되어야 함"

    def test_timer_fires_multiple_times(self):
        """callback이 여러 번 반복 호출되는지 확인"""
        count = []
        lock = threading.Lock()

        def callback():
            with lock:
                count.append(1)

        timer = PeriodicTimer(0.05, callback)
        timer.start()
        time.sleep(0.3)
        timer.cancel()

        with lock:
            call_count = len(count)

        assert call_count >= 3, f"최소 3번 호출되어야 함, 실제: {call_count}"

    def test_cancel_stops_timer(self):
        """cancel() 후 callback이 더 이상 호출되지 않는지 확인"""
        count = []
        lock = threading.Lock()

        def callback():
            with lock:
                count.append(1)

        timer = PeriodicTimer(0.05, callback)
        timer.start()
        time.sleep(0.15)
        timer.cancel()

        with lock:
            count_after_cancel = len(count)

        # cancel 후 추가 대기
        time.sleep(0.15)

        with lock:
            count_final = len(count)

        assert count_final == count_after_cancel, (
            f"cancel 후 callback이 호출되면 안 됨. "
            f"cancel 전: {count_after_cancel}, 최종: {count_final}"
        )

    def test_cancel_before_start_is_safe(self):
        """start 전에 cancel() 호출해도 에러 없어야 함"""
        def callback():
            pass

        timer = PeriodicTimer(0.1, callback)
        # start 없이 cancel 호출 - 에러 없어야 함
        timer.cancel()

    def test_cancel_twice_is_safe(self):
        """cancel()을 두 번 호출해도 에러 없어야 함"""
        fired = threading.Event()

        def callback():
            fired.set()

        timer = PeriodicTimer(0.05, callback)
        timer.start()
        fired.wait(timeout=0.5)
        timer.cancel()
        timer.cancel()  # 두 번째 cancel - 에러 없어야 함

    def test_timer_interval_is_respected(self):
        """interval이 대략적으로 지켜지는지 확인"""
        timestamps = []
        lock = threading.Lock()

        def callback():
            with lock:
                timestamps.append(time.time())

        interval = 0.1
        timer = PeriodicTimer(interval, callback)
        timer.start()
        time.sleep(0.45)
        timer.cancel()

        with lock:
            ts = list(timestamps)

        assert len(ts) >= 2, "최소 2번 이상 호출되어야 함"

        # 연속 호출 간격 확인 (±50ms 허용)
        for i in range(1, len(ts)):
            gap = ts[i] - ts[i - 1]
            assert 0.05 <= gap <= 0.2, f"interval 간격이 예상 범위 밖: {gap:.3f}s"
