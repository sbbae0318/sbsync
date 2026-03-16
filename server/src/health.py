import os

from src.metrics import HEALTH_STATUS
from src.utils import logger


class MountHealthChecker:
    """마운트 디렉토리의 건강 상태를 확인하는 클래스.

    os.stat() + os.listdir()로 마운트가 실제로 접근 가능하고
    내용물이 존재하는지 검증한다.
    """

    def __init__(self, target_dir: str):
        self.target_dir = target_dir

    def check(self) -> bool:
        """마운트 상태 확인.

        Returns:
            True: 마운트 정상 (stat 성공 + listdir 비어있지 않음)
            False: 마운트 비정상 (ESTALE, OSError, FileNotFoundError, 빈 디렉토리)

        Side effects:
            - 실패 시 CRITICAL 로그 출력
            - HEALTH_STATUS gauge 업데이트 (1=healthy, 0=unhealthy)
        """
        try:
            os.stat(self.target_dir)
        except FileNotFoundError:
            logger.critical("마운트 디렉토리 없음: %s", self.target_dir)
            HEALTH_STATUS.set(0)
            return False
        except OSError as e:
            logger.critical(
                "마운트 접근 실패: %s (errno=%s)", self.target_dir, e.errno
            )
            HEALTH_STATUS.set(0)
            return False

        entries = os.listdir(self.target_dir)
        if not entries:
            logger.critical(
                "마운트 디렉토리 비어있음 (부분 마운트 실패 의심): %s", self.target_dir
            )
            HEALTH_STATUS.set(0)
            return False

        HEALTH_STATUS.set(1)
        return True
