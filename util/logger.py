import logging
import os
from collections.abc import Callable
from enum import Enum
from functools import wraps
from logging.handlers import TimedRotatingFileHandler

from base.config import config
from exc.database_exc import DatabaseErr
from exc.service_exc import ServiceErr


class ColoredFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": "\033[94m",  # 蓝色
        "INFO": "\033[92m",  # 绿色
        "WARNING": "\033[93m",  # 黄色
        "ERROR": "\033[91m",  # 红色
        "CRITICAL": "\033[91m",  # 红色
    }
    RESET = "\033[0m"

    def format(self, record):
        level_name = record.levelname
        msg = super().format(record)
        colored_level_name = self.COLORS.get(level_name, self.RESET) + level_name + self.RESET
        return f"{colored_level_name}: {msg}"


def init_logger():
    # 创建一个输出到控制台的处理器
    console_handler = logging.StreamHandler()
    console_formatter = ColoredFormatter("%(message)s")
    console_handler.setFormatter(console_formatter)

    # 创建一个按天分割输出到文件的日志处理器
    log_file = os.path.abspath(config.base.LOG_PATH)
    log_dir = os.path.dirname(log_file)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    file_handler = TimedRotatingFileHandler(log_file, when="midnight", interval=1, backupCount=7, encoding="utf-8")
    file_formatter = logging.Formatter("%(asctime)s [%(levelname)s] [%(name)s]: %(message)s")
    file_handler.setFormatter(file_formatter)

    # 使用basicConfig设置全局配置
    logging.basicConfig(level=config.base.LOG_LEVEL, handlers=[console_handler, file_handler])

    # uvicorn启动日志输出到文件
    logging.getLogger("uvicorn").addHandler(file_handler)
    # fastapi请求日志输出到文件
    logging.getLogger("uvicorn.access").addHandler(file_handler)


class LogType(Enum):
    INFO = logging.Logger.info
    ERROR = logging.Logger.error
    WARNING = logging.Logger.warning
    DEBUG = logging.Logger.debug
    CRITICAL = logging.Logger.critical


def log_and_raise(
    log_type: Callable = LogType.ERROR,
    logging_logger: logging.Logger = None,
    log_msg: str = None,
    raise_exc: Exception = None,
):
    """
    Decorator for logging and raising exceptions
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            async def log_or_raise(log: bool = True, exc: Exception = None):
                """
                Log or raise exceptions by given parameters
                """
                (await kwargs["session"].rollback()) if kwargs.get("session", None) else None
                log_type(logging_logger, f"{func.__name__} Error: {log_msg or exc}") if log else None
                if exc:
                    if raise_exc:
                        raise raise_exc from exc
                    raise exc

            try:
                return await func(*args, **kwargs)
            except (ServiceErr, DatabaseErr) as e:
                raise await log_or_raise(log=False, exc=e)
            except Exception as e:
                raise await log_or_raise(exc=e)

        return wrapper

    return decorator
