"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: role.py
@DateTime: 2025/06/02 02:32:03
@Docs: 角色领域模型

包含角色相关的业务逻辑和行为，不依赖于持久化技术
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from uuid import UUID

from .exceptions import DomainException, RoleAssignmentError
from .permission import Permission


class Role:
    """角色领域模型

    包含角色的业务规则和行为逻辑
    """

    def __init__(
        self,
        id: UUID,
        name: str,
        code: str,
        description: str | None = None,
        level: int = 0,
        is_active: bool = True,
        is_system: bool = False,
        is_deleted: bool = False,
        sort_order: int = 0,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        permissions: set[Permission] | None = None,
    ):
        self.id = id
        self.name = name
        self.code = code
        self.description = description
        self.level = level
        self.is_active = is_active
        self.is_system = is_system
        self.is_deleted = is_deleted
        self.sort_order = sort_order
        self.created_at = created_at
        self.updated_at = updated_at
        self.permissions = permissions or set()

    @classmethod
    def create(
        cls,
        id: UUID,
        name: str,
        code: str,
        description: str | None = None,
        level: int = 0,
        is_system: bool = False,
    ) -> Role:
        """创建新角色

        Args:
            id: 角色ID
            name: 角色名称
            code: 角色代码
            description: 角色描述
            level: 角色等级
            is_system: 是否系统角色

        Returns:
            角色实例

        Raises:
            DomainException: 当输入数据无效时
        """
        cls._validate_name(name)
        cls._validate_code(code)
        cls._validate_level(level)

        return cls(
            id=id,
            name=name,
            code=code,
            description=description,
            level=level,
            is_system=is_system,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

    def update_info(
        self,
        name: str | None = None,
        description: str | None = None,
        level: int | None = None,
        sort_order: int | None = None,
    ) -> None:
        """更新角色信息

        Args:
            name: 角色名称
            description: 角色描述
            level: 角色等级
            sort_order: 排序顺序

        Raises:
            DomainException: 当系统角色不能修改时
        """
        if self.is_system:
            raise DomainException("系统角色信息不能修改")

        if name is not None:
            self._validate_name(name)
            self.name = name

        if description is not None:
            self.description = description

        if level is not None:
            self._validate_level(level)
            self.level = level

        if sort_order is not None:
            self.sort_order = sort_order

        self.updated_at = datetime.now(UTC)

    def activate(self) -> None:
        """激活角色"""
        self.is_active = True
        self.updated_at = datetime.now(UTC)

    def deactivate(self) -> None:
        """停用角色

        Raises:
            DomainException: 当系统角色不能停用时
        """
        if self.is_system:
            raise DomainException("系统角色不能停用")

        self.is_active = False
        self.updated_at = datetime.now(UTC)

    def soft_delete(self) -> None:
        """软删除角色

        Raises:
            DomainException: 当系统角色不能删除时
        """
        if self.is_system:
            raise DomainException("系统角色不能删除")

        self.is_deleted = True
        self.is_active = False
        self.updated_at = datetime.now(UTC)

    def grant_permission(self, permission: Permission) -> None:
        """授予权限

        Args:
            permission: 权限对象

        Raises:
            RoleAssignmentError: 当角色不活跃时
        """
        if not self.is_active:
            raise RoleAssignmentError("不能给非活跃角色授予权限")

        if permission.is_deleted:
            raise RoleAssignmentError("不能授予已删除的权限")

        self.permissions.add(permission)
        self.updated_at = datetime.now(UTC)

    def revoke_permission(self, permission: Permission) -> None:
        """撤销权限

        Args:
            permission: 权限对象

        Raises:
            DomainException: 当系统角色权限不能撤销时
        """
        if self.is_system and permission.is_system:
            raise DomainException("不能撤销系统角色的系统权限")

        self.permissions.discard(permission)
        self.updated_at = datetime.now(UTC)

    def has_permission(self, permission_code: str) -> bool:
        """检查是否拥有指定权限

        Args:
            permission_code: 权限代码

        Returns:
            是否拥有权限
        """
        return any(perm.code == permission_code for perm in self.permissions)

    def can_access_resource(self, resource: str, action: str) -> bool:
        """检查是否可以访问指定资源

        Args:
            resource: 资源类型
            action: 操作类型

        Returns:
            是否可以访问
        """
        for permission in self.permissions:
            if permission.resource == resource and permission.action == action:
                return True
        return False

    def get_permissions_by_resource(self, resource: str) -> set[Permission]:
        """获取指定资源的所有权限

        Args:
            resource: 资源类型

        Returns:
            权限集合
        """
        return {perm for perm in self.permissions if perm.resource == resource}

    def get_permissions_by_category(self, category: str) -> set[Permission]:
        """获取指定分类的所有权限

        Args:
            category: 权限分类

        Returns:
            权限集合
        """
        return {perm for perm in self.permissions if perm.category == category}

    def can_assign_to_user(self, user_level: int) -> bool:
        """检查是否可以分配给指定等级的用户

        Args:
            user_level: 用户等级

        Returns:
            是否可以分配
        """
        if not self.is_active:
            return False

        # 只有更高等级的用户才能分配低等级的角色
        return user_level >= self.level

    def is_higher_level_than(self, other_role: Role) -> bool:
        """检查是否比另一个角色等级更高

        Args:
            other_role: 另一个角色

        Returns:
            是否等级更高
        """
        return self.level > other_role.level

    def merge_permissions_from(self, other_role: Role) -> None:
        """从另一个角色合并权限

        Args:
            other_role: 另一个角色

        Raises:
            DomainException: 当系统角色不能修改时
        """
        if self.is_system:
            raise DomainException("系统角色权限不能修改")

        # 只合并非系统权限
        non_system_permissions = {perm for perm in other_role.permissions if not perm.is_system}
        self.permissions.update(non_system_permissions)
        self.updated_at = datetime.now(UTC)

    def clear_permissions(self) -> None:
        """清空所有权限

        Raises:
            DomainException: 当系统角色不能修改时
        """
        if self.is_system:
            raise DomainException("系统角色权限不能清空")

        self.permissions.clear()
        self.updated_at = datetime.now(UTC)

    def get_permission_count(self) -> int:
        """获取权限数量

        Returns:
            权限数量
        """
        return len(self.permissions)

    def has_system_permissions(self) -> bool:
        """检查是否包含系统权限

        Returns:
            是否包含系统权限
        """
        return any(perm.is_system for perm in self.permissions)

    @staticmethod
    def _validate_name(name: str) -> None:
        """验证角色名称

        Args:
            name: 角色名称

        Raises:
            DomainException: 当角色名称无效时
        """
        if not name:
            raise DomainException("角色名称不能为空")

        if len(name) < 2 or len(name) > 100:
            raise DomainException("角色名称长度必须在2-100个字符之间")

    @staticmethod
    def _validate_code(code: str) -> None:
        """验证角色代码

        Args:
            code: 角色代码

        Raises:
            DomainException: 当角色代码无效时
        """
        if not code:
            raise DomainException("角色代码不能为空")

        if len(code) < 2 or len(code) > 50:
            raise DomainException("角色代码长度必须在2-50个字符之间")

        if not re.match(r"^[A-Z][A-Z0-9_]*$", code):
            raise DomainException("角色代码必须以大写字母开头，只能包含大写字母、数字和下划线")

    @staticmethod
    def _validate_level(level: int) -> None:
        """验证角色等级

        Args:
            level: 角色等级

        Raises:
            DomainException: 当角色等级无效时
        """
        if level < 0 or level > 999:
            raise DomainException("角色等级必须在0-999之间")

    def __eq__(self, other) -> bool:
        """相等性比较"""
        if not isinstance(other, Role):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """哈希值"""
        return hash(self.id)

    def __repr__(self) -> str:
        """字符串表示"""
        return f"<Role(id={self.id}, name={self.name}, code={self.code})>"
