"""
-*- coding: utf-8 -*-
@Author: li
@ProjectName: template
@Email: lijianqiao2906@live.com
@FileName: logger.py
@DateTime: 2025/03/08 03:51:08
@Docs: 简洁的日志管理模块
"""

import sys
from functools import wraps
from pathlib import Path

from loguru import logger

from app.core.config import settings


def setup_logger() -> None:
    """配置日志系统"""
    # 移除默认处理器
    logger.remove()

    # 创建日志目录
    log_dir = Path(settings.BASE_DIR) / "logs"
    log_dir.mkdir(exist_ok=True)

    # 日志格式
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "{extra} | <level>{message}</level>"
    )

    # 控制台输出
    logger.add(
        sys.stdout,
        format=log_format,
        level=settings.LOG_LEVEL,
        enqueue=True,
    )

    # 文件输出 - 所有日志
    logger.add(
        log_dir / "sys_{time:YYYY-MM-DD}.log",
        format=log_format,
        level="DEBUG",
        rotation="00:00",
        retention="30 days",
        compression="zip",
        encoding="utf-8",
        enqueue=True,
    )

    # 文件输出 - 错误日志
    logger.add(
        log_dir / "sys_error_{time:YYYY-MM-DD}.log",
        format=log_format,
        level="ERROR",
        rotation="00:00",
        retention="30 days",
        compression="zip",
        encoding="utf-8",
        enqueue=True,
    )


def log_function_calls(*, include_args: bool = False, include_result: bool = False):
    """简单的函数调用日志装饰器

    Args:
        include_args: 是否记录函数参数
        include_result: 是否记录返回值
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            func_name = func.__name__

            # 记录函数调用
            extra = {"function": func_name}
            if include_args:
                extra["args"] = f"args={args}, kwargs={kwargs}"

            logger.info("Function called", **extra)

            try:
                result = func(*args, **kwargs)

                if include_result:
                    logger.info("Function completed", function=func_name, result=str(result)[:200])
                else:
                    logger.info("Function completed", function=func_name)

                return result
            except Exception as e:
                logger.exception("Function failed", function=func_name, error=str(e))
                raise

        return wrapper

    return decorator


# 初始化日志系统
setup_logger()

# 导出logger实例，直接使用loguru的功能
__all__ = ["logger", "log_function_calls"]
