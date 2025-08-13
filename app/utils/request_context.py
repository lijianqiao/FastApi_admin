"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: request_context.py
@DateTime: 2025/07/12
@Docs: 请求上下文（基于 contextvars），用于贯通请求ID等信息
"""

from __future__ import annotations

from contextvars import ContextVar

_request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
_client_ip_var: ContextVar[str | None] = ContextVar("client_ip", default=None)


def set_request_id(request_id: str) -> None:
    _request_id_var.set(request_id)


def get_request_id() -> str | None:
    return _request_id_var.get()


def clear_request_id() -> None:
    _request_id_var.set(None)


def set_client_ip(ip: str) -> None:
    _client_ip_var.set(ip)


def get_client_ip() -> str | None:
    return _client_ip_var.get()


def clear_client_ip() -> None:
    _client_ip_var.set(None)
