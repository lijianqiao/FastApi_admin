"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: logger.py
@DateTime: 2025/06/02 01:58:01
@Docs: 日志管理器 - 支持每日轮转和错误日志独立记录
"""

import json
import logging
import logging.handlers
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from app.config import settings


class ColoredFormatter(logging.Formatter):
    """彩色日志格式化器（仅用于控制台输出）"""

    # ANSI 颜色代码
    COLORS = {
        "DEBUG": "\033[36m",  # 青色
        "INFO": "\033[32m",  # 绿色
        "WARNING": "\033[33m",  # 黄色
        "ERROR": "\033[31m",  # 红色
        "CRITICAL": "\033[35m",  # 紫色
        "RESET": "\033[0m",  # 重置
    }

    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录"""
        # 获取颜色
        color = self.COLORS.get(record.levelname, self.COLORS["RESET"])
        reset = self.COLORS["RESET"]

        # 为级别名称添加颜色
        record.levelname = f"{color}{record.levelname}{reset}"

        return super().format(record)


class JSONFormatter(logging.Formatter):
    """JSON格式的日志格式化器（用于文件输出）"""

    def format(self, record: logging.LogRecord) -> str:
        """格式化为JSON格式"""
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
            "process_id": record.process,
            "thread_id": record.thread,
        }

        # 添加异常信息（如果存在）
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)  # 添加额外的字段
        if hasattr(record, "user_id"):
            log_entry["user_id"] = record.user_id  # type: ignore
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id  # type: ignore
        if hasattr(record, "ip_address"):
            log_entry["ip_address"] = record.ip_address  # type: ignore

        return json.dumps(log_entry, ensure_ascii=False)


class RequestFilter(logging.Filter):
    """请求相关的日志过滤器"""

    def filter(self, record: logging.LogRecord) -> bool:
        """过滤特定的日志记录"""  # 可以在这里添加特定的过滤逻辑
        # 例如：过滤掉健康检查的请求日志
        if hasattr(record, "path") and record.path in ["/health", "/metrics"]:  # type: ignore
            return False
        return True


class LoggerManager:
    """日志管理器"""

    _instance: Optional["LoggerManager"] = None
    _initialized: bool = False

    def __new__(cls) -> "LoggerManager":
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化日志管理器"""
        if self._initialized:
            return

        self.log_dir = Path(settings.log_directory)
        self.log_level = settings.log_level.value  # 使用枚举的字符串值
        self.loggers: dict[str, logging.Logger] = {}

        # 创建日志目录
        self._create_log_directories()

        # 配置根日志器
        self._configure_root_logger()

        # 标记为已初始化
        self._initialized = True

    def _create_log_directories(self) -> None:
        """创建日志目录"""
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            (self.log_dir / "errors").mkdir(exist_ok=True)
            (self.log_dir / "access").mkdir(exist_ok=True)
            (self.log_dir / "app").mkdir(exist_ok=True)
        except Exception as e:
            print(f"创建日志目录失败: {e}")
            # 如果无法创建目录，使用当前目录
            self.log_dir = Path(".")

    def _configure_root_logger(self) -> None:
        """配置根日志器"""
        root_logger = logging.getLogger()
        root_logger.setLevel(self.log_level)

        # 清除现有的处理器
        root_logger.handlers.clear()

        # 添加控制台处理器
        if settings.environment != "production":
            self._add_console_handler(root_logger)

        # 添加文件处理器
        self._add_file_handlers(root_logger)

    def _add_console_handler(self, logger: logging.Logger) -> None:
        """添加控制台处理器"""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG if settings.debug else logging.INFO)

        # 使用彩色格式化器
        formatter = ColoredFormatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        console_handler.setFormatter(formatter)

        # 添加请求过滤器
        console_handler.addFilter(RequestFilter())

        logger.addHandler(console_handler)

    def _add_file_handlers(self, logger: logging.Logger) -> None:
        """添加文件处理器"""
        # 1. 应用日志 - 每日轮转
        app_handler = logging.handlers.TimedRotatingFileHandler(
            filename=self.log_dir / "app" / "app.log",
            when="midnight",
            interval=1,
            backupCount=settings.log_backup_count,
            encoding="utf-8",
        )
        app_handler.setLevel(logging.INFO)
        app_handler.suffix = "%Y-%m-%d"

        # 使用JSON格式化器
        json_formatter = JSONFormatter()
        app_handler.setFormatter(json_formatter)

        logger.addHandler(app_handler)

        # 2. 错误日志 - 独立记录，每日轮转
        error_handler = logging.handlers.TimedRotatingFileHandler(
            filename=self.log_dir / "errors" / "error.log",
            when="midnight",
            interval=1,
            backupCount=settings.log_backup_count,
            encoding="utf-8",
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.suffix = "%Y-%m-%d"
        error_handler.setFormatter(json_formatter)

        logger.addHandler(error_handler)

        # 3. 访问日志 - 用于记录API访问
        access_handler = logging.handlers.TimedRotatingFileHandler(
            filename=self.log_dir / "access" / "access.log",
            when="midnight",
            interval=1,
            backupCount=settings.log_backup_count,
            encoding="utf-8",
        )
        access_handler.setLevel(logging.INFO)
        access_handler.suffix = "%Y-%m-%d"

        # 访问日志使用专门的格式化器
        access_formatter = logging.Formatter(
            '%(asctime)s - %(remote_addr)s - "%(method)s %(path)s %(protocol)s" '
            '%(status_code)s %(response_length)s "%(user_agent)s" %(response_time)s'
        )
        access_handler.setFormatter(access_formatter)

        # 创建专门的访问日志器
        access_logger = logging.getLogger("access")
        access_logger.addHandler(access_handler)
        access_logger.setLevel(logging.INFO)
        access_logger.propagate = False  # 不传播到根日志器

    def get_logger(self, name: str) -> logging.Logger:
        """获取指定名称的日志器"""
        if name not in self.loggers:
            logger = logging.getLogger(name)
            self.loggers[name] = logger
        return self.loggers[name]

    def log_request(
        self,
        remote_addr: str,
        method: str,
        path: str,
        protocol: str,
        status_code: int,
        response_length: int,
        user_agent: str,
        response_time: float,
        user_id: int | None = None,
        request_id: str | None = None,
    ) -> None:
        """记录API访问日志"""
        access_logger = logging.getLogger("access")

        # 创建额外的记录信息
        extra = {
            "remote_addr": remote_addr,
            "method": method,
            "path": path,
            "protocol": protocol,
            "status_code": status_code,
            "response_length": response_length,
            "user_agent": user_agent,
            "response_time": f"{response_time:.3f}s",
        }

        if user_id:
            extra["user_id"] = user_id
        if request_id:
            extra["request_id"] = request_id

        access_logger.info("API访问", extra=extra)

    def log_error_with_context(
        self, error: Exception, context: dict[str, Any], user_id: int | None = None, request_id: str | None = None
    ) -> None:
        """记录带上下文的错误日志"""
        logger = self.get_logger("error")

        extra = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context,
        }

        if user_id:
            extra["user_id"] = user_id
        if request_id:
            extra["request_id"] = request_id

        logger.error(f"应用错误: {error}", extra=extra, exc_info=True)

    def setup_uvicorn_logging(self) -> dict[str, Any]:
        """设置Uvicorn日志配置"""
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                },
                "access": {
                    "format": '%(asctime)s - %(client_addr)s - "%(request_line)s" %(status_code)s',
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                },
            },
            "handlers": {
                "default": {
                    "formatter": "default",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                },
                "access": {
                    "formatter": "access",
                    "class": "logging.handlers.TimedRotatingFileHandler",
                    "filename": str(self.log_dir / "access" / "uvicorn_access.log"),
                    "when": "midnight",
                    "interval": 1,
                    "backupCount": settings.log_backup_count,
                    "encoding": "utf-8",
                },
            },
            "loggers": {
                "uvicorn": {"handlers": ["default"], "level": "INFO", "propagate": False},
                "uvicorn.error": {"handlers": ["default"], "level": "INFO", "propagate": False},
                "uvicorn.access": {"handlers": ["access"], "level": "INFO", "propagate": False},
            },
        }


# 创建全局日志管理器实例
logger_manager = LoggerManager()


# 便捷函数
def get_logger(name: str) -> logging.Logger:
    """获取日志器的便捷函数"""
    return logger_manager.get_logger(name)


def log_request(*args, **kwargs) -> None:
    """记录请求日志的便捷函数"""
    return logger_manager.log_request(*args, **kwargs)


def log_error_with_context(*args, **kwargs) -> None:
    """记录错误日志的便捷函数"""
    return logger_manager.log_error_with_context(*args, **kwargs)


# 为常用模块创建日志器
app_logger = get_logger("app")
auth_logger = get_logger("auth")
db_logger = get_logger("database")
api_logger = get_logger("api")
