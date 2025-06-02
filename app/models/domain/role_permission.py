# filepath: e:\Project\fastapibase\app\models\domain\role_permission.py
"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: role_permission.py
@DateTime: 2025/06/02 02:32:03
@Docs: 角色权限关联领域模型

角色权限关联领域模型管理角色和权限之间的关系
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from uuid import UUID

from app.models.domain.exceptions import DomainException


@dataclass
class RolePermission:
    """角色权限关联领域模型

    管理角色和权限之间的关联关系，支持动态权限分配和追踪
    """

    # 关联标识
    role_id: UUID
    permission_id: UUID  # 管理字段
    granted_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    granted_by: UUID | None = None

    def __post_init__(self):
        """初始化后的验证"""
        self.validate()

    def validate(self) -> None:
        """验证关联的有效性

        Raises:
            DomainException: 当关联无效时
        """
        if not self.role_id:
            raise DomainException("角色ID不能为空")

        if not self.permission_id:
            raise DomainException("权限ID不能为空")

        if self.role_id == self.permission_id:
            raise DomainException("角色ID和权限ID不能相同")

    def is_granted_by_user(self, user_id: UUID) -> bool:
        """是否由指定用户授权

        Args:
            user_id: 用户ID

        Returns:
            是否由该用户授权
        """
        return self.granted_by == user_id

    def is_recent_grant(self, hours: int = 24) -> bool:
        """是否为最近授权

        Args:
            hours: 小时数，默认24小时

        Returns:
            是否在指定时间内授权
        """
        if not self.granted_at:
            return False

        threshold = datetime.now(UTC) - timedelta(hours=hours)
        return self.granted_at > threshold

    def get_grant_age_days(self) -> int:
        """获取授权天数

        Returns:
            从授权到现在的天数
        """
        if not self.granted_at:
            return 0

        age = datetime.now(UTC) - self.granted_at
        return age.days

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "role_id": str(self.role_id),
            "permission_id": str(self.permission_id),
            "granted_at": self.granted_at.isoformat() if self.granted_at else None,
            "granted_by": str(self.granted_by) if self.granted_by else None,
            "grant_age_days": self.get_grant_age_days(),
        }

    def __str__(self) -> str:
        age_days = self.get_grant_age_days()
        return f"角色权限关联 (授权{age_days}天前)"

    def __repr__(self) -> str:
        return (
            f"RolePermission(role_id={self.role_id}, permission_id={self.permission_id}, granted_at={self.granted_at})"
        )
