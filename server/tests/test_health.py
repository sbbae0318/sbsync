import errno
import logging
import os

import pytest

from src.health import MountHealthChecker
from src.metrics import HEALTH_STATUS


class TestMountHealthChecker:
    """MountHealthChecker 클래스 테스트 — monkeypatch로 os.stat/os.listdir mock"""

    def setup_method(self):
        """각 테스트 전 HEALTH_STATUS 초기화"""
        HEALTH_STATUS.set(-1)  # sentinel value

    def test_healthy_mount(self, monkeypatch):
        """정상 디렉토리에서 check() → True"""
        monkeypatch.setattr(os, "stat", lambda path: True)
        monkeypatch.setattr(os, "listdir", lambda path: ["file1.md", "file2.md"])

        checker = MountHealthChecker("/mnt/vault")
        assert checker.check() is True

    def test_stale_mount_estale(self, monkeypatch):
        """os.stat → OSError(errno.ESTALE) 시 check() → False"""

        def stat_estale(path):
            raise OSError(errno.ESTALE, "Stale file handle")

        monkeypatch.setattr(os, "stat", stat_estale)

        checker = MountHealthChecker("/mnt/vault")
        assert checker.check() is False

    def test_stale_mount_oserror(self, monkeypatch):
        """기타 OSError 시 check() → False"""

        def stat_oserror(path):
            raise OSError(errno.EIO, "Input/output error")

        monkeypatch.setattr(os, "stat", stat_oserror)

        checker = MountHealthChecker("/mnt/vault")
        assert checker.check() is False

    def test_stale_mount_filenotfound(self, monkeypatch):
        """디렉토리 미존재 시 check() → False"""

        def stat_notfound(path):
            raise FileNotFoundError("No such file or directory")

        monkeypatch.setattr(os, "stat", stat_notfound)

        checker = MountHealthChecker("/mnt/vault")
        assert checker.check() is False

    def test_listdir_empty(self, monkeypatch):
        """os.stat 성공이지만 os.listdir 빈 결과 시 → False (부분 마운트 실패)"""
        monkeypatch.setattr(os, "stat", lambda path: True)
        monkeypatch.setattr(os, "listdir", lambda path: [])

        checker = MountHealthChecker("/mnt/vault")
        assert checker.check() is False

    def test_check_logs_critical_on_failure(self, monkeypatch, caplog):
        """실패 시 CRITICAL 레벨 로그 출력 확인"""

        def stat_estale(path):
            raise OSError(errno.ESTALE, "Stale file handle")

        monkeypatch.setattr(os, "stat", stat_estale)

        checker = MountHealthChecker("/mnt/vault")
        with caplog.at_level(logging.CRITICAL, logger="sbSync"):
            checker.check()

        critical_messages = [r for r in caplog.records if r.levelno == logging.CRITICAL]
        assert len(critical_messages) >= 1, "실패 시 CRITICAL 로그가 출력되어야 함"

    def test_check_updates_metric(self, monkeypatch):
        """실패 시 HEALTH_STATUS.set(0), 성공 시 HEALTH_STATUS.set(1)"""
        # 성공 케이스
        monkeypatch.setattr(os, "stat", lambda path: True)
        monkeypatch.setattr(os, "listdir", lambda path: ["file.md"])

        checker = MountHealthChecker("/mnt/vault")
        checker.check()
        assert HEALTH_STATUS._value.get() == 1.0

        # 실패 케이스
        def stat_fail(path):
            raise OSError(errno.ESTALE, "Stale file handle")

        monkeypatch.setattr(os, "stat", stat_fail)
        checker.check()
        assert HEALTH_STATUS._value.get() == 0.0
