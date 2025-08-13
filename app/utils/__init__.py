"""
-*- coding: utf-8 -*-
 @Author: li
 @Email: lijianqiao2906@live.com
 @FileName: __init__.py
 @DateTime: 2025/3/11 上午9:53
 @Docs: 实用程序模块
"""

from .logger import log_function_calls, logger

try:
    from .token_blocklist import block_jti_async, is_jti_blocked
except Exception:
    block_jti = None  # type: ignore[assignment]
    is_jti_blocked = None  # type: ignore[assignment]

__all__ = [
    "logger",
    "log_function_calls",
    "block_jti_async",
    "is_jti_blocked",
]
