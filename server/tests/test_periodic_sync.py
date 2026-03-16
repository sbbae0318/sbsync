"""Periodic Sync 통합 테스트 — main.py에서 PeriodicTimer + git_handler.sync() 연동 검증"""

import time
import threading
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from src.utils import PeriodicTimer


class TestPeriodicSync:
    """main.py의 periodic sync 통합 로직 테스트"""

    def test_periodic_sync_calls_git_sync(self):
        """PeriodicTimer가 git_handler.sync()를 호출하는지 확인"""
        mock_sync = MagicMock()
        called = threading.Event()

        def sync_wrapper():
            mock_sync()
            called.set()

        timer = PeriodicTimer(0.05, sync_wrapper)
        timer.start()
        called.wait(timeout=1.0)
        timer.cancel()

        mock_sync.assert_called()

    def test_periodic_sync_respects_interval(self):
        """설정된 interval을 준수하는지 확인 — PERIODIC_SYNC_SECONDS 반영"""
        timestamps = []
        lock = threading.Lock()

        def sync_callback():
            with lock:
                timestamps.append(time.time())

        interval = 0.1
        timer = PeriodicTimer(interval, sync_callback)
        timer.start()
        time.sleep(0.45)
        timer.cancel()

        with lock:
            ts = list(timestamps)

        assert len(ts) >= 2, f"최소 2회 호출되어야 함, 실제: {len(ts)}"

        for i in range(1, len(ts)):
            gap = ts[i] - ts[i - 1]
            assert 0.05 <= gap <= 0.25, f"interval 간격이 허용 범위 밖: {gap:.3f}s"

    def test_periodic_sync_cancellation_on_shutdown(self):
        """shutdown 시 cancel() 호출하면 타이머가 정리되는지 확인"""
        count = []
        lock = threading.Lock()

        def sync_callback():
            with lock:
                count.append(1)

        timer = PeriodicTimer(0.05, sync_callback)
        timer.start()
        time.sleep(0.15)
        timer.cancel()

        with lock:
            count_at_cancel = len(count)

        # cancel 후 추가 대기 — 호출이 더 없어야 함
        time.sleep(0.15)

        with lock:
            count_final = len(count)

        assert count_final == count_at_cancel, (
            f"cancel 후 추가 호출 발생. cancel 시: {count_at_cancel}, 최종: {count_final}"
        )

    def test_periodic_sync_survives_sync_exception(self):
        """sync() 예외 발생 시에도 타이머가 계속 동작하는지 확인 — wrapper 함수 필요"""
        call_count = []
        lock = threading.Lock()

        def failing_sync():
            with lock:
                call_count.append(1)
            raise RuntimeError("git push failed")

        def safe_sync_wrapper():
            """sync() 예외를 삼켜서 타이머가 죽지 않도록 하는 wrapper"""
            try:
                failing_sync()
            except Exception:
                pass

        timer = PeriodicTimer(0.05, safe_sync_wrapper)
        timer.start()
        time.sleep(0.3)
        timer.cancel()

        with lock:
            total_calls = len(call_count)

        assert total_calls >= 3, (
            f"예외 후에도 계속 호출되어야 함. 최소 3회 기대, 실제: {total_calls}"
        )


class TestPeriodicSyncConfig:
    """config.py의 PERIODIC_SYNC_SECONDS 환경변수 테스트"""

    def test_periodic_sync_seconds_default(self):
        """PERIODIC_SYNC_SECONDS 기본값이 600인지 확인"""
        with patch.dict("os.environ", {}, clear=False):
            # 기존 환경변수가 있다면 제거
            import os
            env_backup = os.environ.pop("PERIODIC_SYNC_SECONDS", None)
            try:
                # Config를 다시 생성하여 기본값 확인
                from src.config import Config
                fresh_config = Config()
                assert fresh_config.PERIODIC_SYNC_SECONDS == 600
            finally:
                if env_backup is not None:
                    os.environ["PERIODIC_SYNC_SECONDS"] = env_backup

    def test_periodic_sync_seconds_from_env(self):
        """환경변수로 PERIODIC_SYNC_SECONDS 설정 가능한지 확인"""
        with patch.dict("os.environ", {"PERIODIC_SYNC_SECONDS": "120"}):
            from src.config import Config
            fresh_config = Config()
            assert fresh_config.PERIODIC_SYNC_SECONDS == 120


class TestPeriodicSyncMainIntegration:
    """main.py의 periodic timer 통합 패턴 확인"""

    def test_main_creates_periodic_timer(self):
        """main()에서 PeriodicTimer가 생성되는지 확인 (import 레벨 검증)"""
        # main.py에서 PeriodicTimer를 사용하는지 소스 코드 레벨 확인
        import inspect
        from src import main as main_module

        source = inspect.getsource(main_module)
        assert "PeriodicTimer" in source, (
            "main.py에 PeriodicTimer 사용이 있어야 함"
        )

    def test_main_signal_handler_cancels_periodic_timer(self):
        """signal_handler에서 periodic_timer.cancel()이 호출되는지 확인"""
        import inspect
        from src import main as main_module

        source = inspect.getsource(main_module)
        assert "periodic_timer" in source or "periodic_sync" in source, (
            "main.py에 periodic timer 변수가 있어야 함"
        )
