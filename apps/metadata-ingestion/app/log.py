import logging
import sys
from pathlib import Path

from loguru import logger

from app.config import settings


class InterceptHandler(logging.Handler):
    """표준 로깅을 가로채서 loguru로 리다이렉트하는 핸들러.

    표준 라이브러리 로깅 호출을 캡처하여 정확한 호출자 정보와 함께
    loguru로 전달하여 로그 메시지에 정확한 소스 코드 위치를 추적합니다.
    """

    def emit(self, record):
        # 해당하는 Loguru 레벨이 있으면 가져오기
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # 로그 메시지가 발생한 실제 호출자 찾기
        # 일반적인 로깅 호출 스택을 건너뛰기 위해 depth 6부터 시작:
        # 0: InterceptHandler.emit() (현재)
        # 1: logging.Handler.handle()
        # 2: logging.Logger.callHandlers()
        # 3: logging.Logger.handle()
        # 4: logging.Logger._log()
        # 5: logging.Logger.info/debug/etc()
        # 6: 실제 사용자 코드 (목표)
        try:
            frame, depth = sys._getframe(6), 6
            while frame:
                if (
                    frame.f_code.co_filename != logging.__file__
                    and "logging" not in frame.f_code.co_filename
                    and frame.f_code.co_filename != __file__
                ):
                    break
                frame = frame.f_back
                depth += 1
        except ValueError:
            # 스택이 얕을 경우 대체 처리
            frame, depth = sys._getframe(1), 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def setup_logging():
    # intercept everything at the root logger
    logging.root.handlers = [InterceptHandler()]
    try:
        logging.root.setLevel(settings.log_level)
    except ValueError:
        sys.exit(f"Set appropriate 'LOG_LEVEL' environment variable. current {settings.LEVEL=}")

    # remove every other logger's handlers
    # and propagate to root logger
    for name in logging.root.manager.loggerDict.keys():
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True

    # configure loguru
    if settings.JSON_LOG:
        logger_config = dict(sink=sys.stdout, serialize=settings.JSON_LOG, format="{message}")
    else:
        # logger_config = dict(sink=sys.stdout)
        logger_config = dict(sink=sys.stdout, format=settings.LOGURU_FORMAT)
    logger.configure(handlers=[logger_config], extra={"request_id": ""})  # extra[request_id] 기본값 지정
    if settings.SAVE:
        log_save_path = Path(settings.LOG_SAVE_PATH) / "{time:YYYY}" / "{time:MM}" / "{time:YYYYMMDD}_info.log"
        logger.add(  # type: ignore
            log_save_path,
            level=settings.log_level,
            rotation=settings.ROTATION,
            retention=settings.RETENTION,
            compression=settings.COMPRESSION,
            serialize=settings.JSON_LOG,
            format=settings.LOGURU_FORMAT,
        )
    return logger.bind()


class Log:
    """todo : 펑션으로 처리"""

    TRACE: int = 10
    log_level = int(settings.log_level)

    @staticmethod
    def is_trace_enable():
        return Log.log_level <= Log.TRACE

    @staticmethod
    def is_debug_enable():
        return Log.log_level <= logging.DEBUG

    @staticmethod
    def is_info_enable():
        return Log.log_level <= logging.INFO

    @staticmethod
    def is_warn_enable():
        return Log.log_level <= logging.WARN

    @staticmethod
    def is_error_enable():
        return Log.log_level <= logging.ERROR

    @staticmethod
    def is_fatal_enable():
        return Log.log_level <= logging.FATAL
