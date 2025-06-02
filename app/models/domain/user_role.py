# filepath: e:\Project\fastapibase\app\models\domain\user_role.py
"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: user_role.py
@DateTime: 2025/06/02 02:32:03
@Docs: 用户角色关联领域模型

用户角色关联领域模型管理用户和角色之间的关系
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID

from app.models.domain.exceptions import DomainException


@dataclass
class UserRole:
    """用户角色关联领域模型

    管理用户和角色之间的关联关系，支持时效性控制和分配追踪
    """

    # 关联标识
    user_id: UUID
    role_id: UUID  # 管理字段
    assigned_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    assigned_by: UUID | None = None
    expires_at: datetime | None = None
    is_active: bool = True

    def __post_init__(self):
        """初始化后的验证"""
        self.validate()

    def validate(self) -> None:
        """验证关联的有效性

        Raises:
            DomainException: 当关联无效时
        """
        if not self.user_id:
            raise DomainException("用户ID不能为空")

        if not self.role_id:
            raise DomainException("角色ID不能为空")

        if self.user_id == self.role_id:
            raise DomainException("用户ID和角色ID不能相同")

        # 验证过期时间
        if self.expires_at and self.expires_at <= self.assigned_at:
            raise DomainException("过期时间必须晚于分配时间")

    @property
    def is_expired(self) -> bool:
        """是否已过期"""
        if self.expires_at is None:
            return False
        return datetime.now(UTC) > self.expires_at

    @property
    def is_valid(self) -> bool:
        """是否有效（活跃且未过期）"""
        return self.is_active and not self.is_expired

    def activate(self) -> None:
        """激活关联"""
        self.is_active = True

    def deactivate(self) -> None:
        """停用关联"""
        self.is_active = False

    def extend_expiry(self, new_expires_at: datetime) -> None:
        """延长过期时间

        Args:
            new_expires_at: 新的过期时间

        Raises:
            DomainException: 当新过期时间无效时
        """
        if new_expires_at <= datetime.now(UTC):
            raise DomainException("新过期时间必须晚于当前时间")

        if self.expires_at and new_expires_at <= self.expires_at:
            raise DomainException("新过期时间必须晚于当前过期时间")

        self.expires_at = new_expires_at

    def set_permanent(self) -> None:
        """设置为永久有效（移除过期时间）"""
        self.expires_at = None

    def get_remaining_days(self) -> int | None:
        """获取剩余天数

        Returns:
            剩余天数，如果无过期时间则返回None
        """
        if self.expires_at is None:
            return None

        remaining = self.expires_at - datetime.now(UTC)
        return max(0, remaining.days)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "user_id": str(self.user_id),
            "role_id": str(self.role_id),
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None,
            "assigned_by": str(self.assigned_by) if self.assigned_by else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_active": self.is_active,
            "is_expired": self.is_expired,
            "is_valid": self.is_valid,
            "remaining_days": self.get_remaining_days(),
        }

    def __str__(self) -> str:
        status = "有效" if self.is_valid else "无效"
        if self.expires_at:
            remaining = self.get_remaining_days()
            return f"用户角色关联 (剩余{remaining}天, {status})"
        return f"用户角色关联 (永久, {status})"

    def __repr__(self) -> str:
        return (
            f"UserRole(user_id={self.user_id}, role_id={self.role_id}, "
            f"is_active={self.is_active}, is_expired={self.is_expired})"
        )
