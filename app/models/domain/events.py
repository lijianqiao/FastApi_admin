"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: events.py
@DateTime: 2025/06/02 02:32:03
@Docs: 领域事件定义

领域事件用于处理跨聚合的业务逻辑，实现松耦合的事件驱动架构
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID


class DomainEvent(ABC):
    """领域事件基类"""

    def __init__(self) -> None:
        self.occurred_at = datetime.now(UTC)
        self.event_id = None  # 可以添加事件ID

    @abstractmethod
    def event_name(self) -> str:
        """事件名称"""
        pass


@dataclass
class UserCreatedEvent(DomainEvent):
    """用户创建事件"""

    user_id: UUID
    username: str
    email: str
    created_by: UUID | None = None

    def event_name(self) -> str:
        return "user.created"


@dataclass
class UserLoginEvent(DomainEvent):
    """用户登录事件"""

    user_id: UUID
    username: str
    ip_address: str | None = None
    user_agent: str | None = None
    login_success: bool = True

    def event_name(self) -> str:
        return "user.login"


@dataclass
class RoleAssignedEvent(DomainEvent):
    """角色分配事件"""

    user_id: UUID
    role_id: UUID
    role_code: str
    assigned_by: UUID | None = None
    expires_at: datetime | None = None

    def event_name(self) -> str:
        return "role.assigned"


@dataclass
class PermissionGrantedEvent(DomainEvent):
    """权限授予事件"""

    role_id: UUID
    permission_id: UUID
    permission_code: str
    granted_by: UUID | None = None

    def event_name(self) -> str:
        return "permission.granted"


@dataclass
class ConfigUpdatedEvent(DomainEvent):
    """配置更新事件"""

    config_key: str
    old_value: Any | None = None
    new_value: Any | None = None
    updated_by: UUID | None = None

    def event_name(self) -> str:
        return "config.updated"


# 事件发布器接口
class EventPublisher(ABC):
    """事件发布器接口"""

    @abstractmethod
    async def publish(self, event: DomainEvent) -> None:
        """发布事件"""
        pass


# 事件处理器接口
class EventHandler(ABC):
    """事件处理器接口"""

    @abstractmethod
    async def handle(self, event: DomainEvent) -> None:
        """处理事件"""
        pass

    @abstractmethod
    def can_handle(self, event: DomainEvent) -> bool:
        """是否可以处理该事件"""
        pass

    def event_type(self) -> str:
        """事件类型"""
        return self.__class__.__name__
