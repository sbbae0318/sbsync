"""Main Health Check Loop 통합 테스트 — main.py에서 MountHealthChecker + Fail-Fast 검증"""

import inspect
import os
from unittest.mock import patch

import pytest

from src.config import Config


class TestMainHealthCheck:
    """main.py의 health check loop 통합 검증"""

    def _get_main_source(self):
        from src import main as main_module

        return inspect.getsource(main_module.main)

    def test_main_exits_on_stale_mount(self):
        """health check 실패 시 sys.exit(1) 호출 패턴 확인"""
        source = self._get_main_source()
        # health_checker.check() 실패 후 sys.exit(1) 호출 패턴 확인
        assert "health_checker.check()" in source, (
            "main()에 health_checker.check() 호출이 있어야 함"
        )
        # check() 이후 exit 패턴 확인
        check_idx = source.find("health_checker.check()")
        after_check = source[check_idx:]
        assert "sys.exit(1)" in after_check, (
            "health check 실패 시 sys.exit(1)로 프로세스를 종료해야 함"
        )

    def test_health_check_runs_periodically(self):
        """health check가 주기적으로 실행되는 loop 구조 확인"""
        source = self._get_main_source()
        assert "MountHealthChecker" in source, (
            "main()에서 MountHealthChecker를 사용해야 함"
        )
        # elapsed 기반 주기적 실행 패턴 확인
        assert "elapsed" in source, "주기적 health check를 위한 elapsed 카운터가 필요함"
        assert "check_interval" in source, (
            "주기적 health check를 위한 check_interval 변수가 필요함"
        )

    def test_health_check_interval_configurable(self):
        """HEALTH_CHECK_SECONDS 환경변수로 주기 설정 가능한지 확인"""
        # 기본값 확인
        env_backup = os.environ.pop("HEALTH_CHECK_SECONDS", None)
        try:
            fresh_config = Config()
            assert fresh_config.HEALTH_CHECK_SECONDS == 60, (
                "HEALTH_CHECK_SECONDS 기본값은 60이어야 함"
            )
        finally:
            if env_backup is not None:
                os.environ["HEALTH_CHECK_SECONDS"] = env_backup

        # 환경변수로 변경 확인
        with patch.dict("os.environ", {"HEALTH_CHECK_SECONDS": "30"}):
            custom_config = Config()
            assert custom_config.HEALTH_CHECK_SECONDS == 30, (
                "환경변수로 HEALTH_CHECK_SECONDS 변경이 가능해야 함"
            )

    def test_health_check_exit_cancels_debouncer(self):
        """health check 실패 → exit 경로에서 debouncer.cancel() 호출 확인"""
        source = self._get_main_source()
        check_idx = source.find("health_checker.check()")
        assert check_idx != -1, "health_checker.check() 호출이 있어야 함"

        # check() 이후 코드에서 debouncer.cancel() 확인
        after_check = source[check_idx:]
        assert "debouncer.cancel()" in after_check, (
            "health check 실패 시 debouncer.cancel()이 호출되어야 함"
        )

    def test_health_check_exit_cancels_periodic_sync(self):
        """health check 실패 → exit 경로에서 periodic_timer.cancel() 호출 확인"""
        source = self._get_main_source()
        check_idx = source.find("health_checker.check()")
        assert check_idx != -1, "health_checker.check() 호출이 있어야 함"

        # check() 이후 코드에서 periodic_timer.cancel() 확인
        after_check = source[check_idx:]
        assert "periodic_timer.cancel()" in after_check, (
            "health check 실패 시 periodic_timer.cancel()이 호출되어야 함"
        )
