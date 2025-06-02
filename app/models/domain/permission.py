"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: permission.py
@DateTime: 2025/06/02 02:32:03
@Docs: 权限领域模型

包含权限相关的业务逻辑和行为，不依赖于持久化技术
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from uuid import UUID

from .exceptions import DomainException


class Permission:
    """权限领域模型

    包含权限的业务规则和行为逻辑
    """

    def __init__(
        self,
        id: UUID,
        name: str,
        code: str,
        resource: str,
        action: str,
        description: str | None = None,
        method: str | None = None,
        path: str | None = None,
        category: str | None = None,
        is_system: bool = False,
        is_deleted: bool = False,
        sort_order: int = 0,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        self.id = id
        self.name = name
        self.code = code
        self.resource = resource
        self.action = action
        self.description = description
        self.method = method
        self.path = path
        self.category = category
        self.is_system = is_system
        self.is_deleted = is_deleted
        self.sort_order = sort_order
        self.created_at = created_at
        self.updated_at = updated_at

    @classmethod
    def create(
        cls,
        id: UUID,
        name: str,
        code: str,
        resource: str,
        action: str,
        description: str | None = None,
        method: str | None = None,
        path: str | None = None,
        category: str | None = None,
        is_system: bool = False,
    ) -> Permission:
        """创建新权限

        Args:
            id: 权限ID
            name: 权限名称
            code: 权限代码
            resource: 资源类型
            action: 操作类型
            description: 权限描述
            method: HTTP方法
            path: API路径
            category: 权限分类
            is_system: 是否系统权限

        Returns:
            权限实例

        Raises:
            DomainException: 当输入数据无效时
        """
        cls._validate_name(name)
        cls._validate_code(code)
        cls._validate_resource(resource)
        cls._validate_action(action)

        if method:
            cls._validate_method(method)

        if path:
            cls._validate_path(path)

        return cls(
            id=id,
            name=name,
            code=code,
            resource=resource,
            action=action,
            description=description,
            method=method,
            path=path,
            category=category,
            is_system=is_system,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

    def update_info(
        self,
        name: str | None = None,
        description: str | None = None,
        method: str | None = None,
        path: str | None = None,
        category: str | None = None,
        sort_order: int | None = None,
    ) -> None:
        """更新权限信息

        Args:
            name: 权限名称
            description: 权限描述
            method: HTTP方法
            path: API路径
            category: 权限分类
            sort_order: 排序顺序

        Raises:
            DomainException: 当系统权限不能修改时
        """
        if self.is_system:
            raise DomainException("系统权限信息不能修改")

        if name is not None:
            self._validate_name(name)
            self.name = name

        if description is not None:
            self.description = description

        if method is not None:
            self._validate_method(method)
            self.method = method

        if path is not None:
            self._validate_path(path)
            self.path = path

        if category is not None:
            self.category = category

        if sort_order is not None:
            self.sort_order = sort_order

        self.updated_at = datetime.now(UTC)

    def soft_delete(self) -> None:
        """软删除权限

        Raises:
            DomainException: 当系统权限不能删除时
        """
        if self.is_system:
            raise DomainException("系统权限不能删除")

        self.is_deleted = True
        self.updated_at = datetime.now(UTC)

    def restore(self) -> None:
        """恢复已删除的权限"""
        self.is_deleted = False
        self.updated_at = datetime.now(UTC)

    def matches_request(self, method: str, path: str) -> bool:
        """检查是否匹配请求

        Args:
            method: HTTP方法
            path: 请求路径

        Returns:
            是否匹配
        """
        # 如果权限没有指定方法和路径，则只匹配资源和操作
        if not self.method and not self.path:
            return True

        # 检查方法匹配
        if self.method and self.method.upper() != method.upper():
            return False

        # 检查路径匹配
        if self.path and not self._path_matches(self.path, path):
            return False

        return True

    def is_resource_permission(self, resource: str) -> bool:
        """检查是否是指定资源的权限

        Args:
            resource: 资源类型

        Returns:
            是否匹配资源
        """
        return self.resource == resource

    def is_action_permission(self, action: str) -> bool:
        """检查是否是指定操作的权限

        Args:
            action: 操作类型

        Returns:
            是否匹配操作
        """
        return self.action == action

    def is_category_permission(self, category: str) -> bool:
        """检查是否是指定分类的权限

        Args:
            category: 权限分类

        Returns:
            是否匹配分类
        """
        return self.category == category

    def get_permission_key(self) -> str:
        """获取权限唯一键

        Returns:
            权限唯一键
        """
        parts = [self.resource, self.action]
        if self.method:
            parts.append(self.method)
        if self.path:
            parts.append(self.path)
        return ":".join(parts)

    def is_api_permission(self) -> bool:
        """检查是否是API权限

        Returns:
            是否是API权限
        """
        return bool(self.method and self.path)

    def is_general_permission(self) -> bool:
        """检查是否是通用权限

        Returns:
            是否是通用权限
        """
        return not self.is_api_permission()

    def can_be_inherited(self) -> bool:
        """检查是否可以被继承

        Returns:
            是否可以被继承
        """
        return not self.is_system or self.is_general_permission()

    @staticmethod
    def _path_matches(pattern: str, path: str) -> bool:
        """检查路径是否匹配模式

        Args:
            pattern: 路径模式
            path: 实际路径

        Returns:
            是否匹配
        """
        # 简单的路径匹配，支持通配符 *
        if pattern == path:
            return True

        # 支持通配符匹配
        if "*" in pattern:
            import fnmatch

            return fnmatch.fnmatch(path, pattern)

        # 支持路径参数匹配，如 /users/{id}
        if "{" in pattern and "}" in pattern:
            pattern_parts = pattern.split("/")
            path_parts = path.split("/")

            if len(pattern_parts) != len(path_parts):
                return False

            for pattern_part, path_part in zip(pattern_parts, path_parts, strict=False):
                if pattern_part.startswith("{") and pattern_part.endswith("}"):
                    # 路径参数，跳过
                    continue
                if pattern_part != path_part:
                    return False

            return True

        return False

    @staticmethod
    def _validate_name(name: str) -> None:
        """验证权限名称

        Args:
            name: 权限名称

        Raises:
            DomainException: 当权限名称无效时
        """
        if not name:
            raise DomainException("权限名称不能为空")

        if len(name) < 2 or len(name) > 100:
            raise DomainException("权限名称长度必须在2-100个字符之间")

    @staticmethod
    def _validate_code(code: str) -> None:
        """验证权限代码

        Args:
            code: 权限代码

        Raises:
            DomainException: 当权限代码无效时
        """
        if not code:
            raise DomainException("权限代码不能为空")

        if len(code) < 2 or len(code) > 100:
            raise DomainException("权限代码长度必须在2-100个字符之间")

        if not re.match(r"^[a-zA-Z][a-zA-Z0-9_:.-]*$", code):
            raise DomainException("权限代码必须以字母开头，只能包含字母、数字、下划线、冒号、点和连字符")

    @staticmethod
    def _validate_resource(resource: str) -> None:
        """验证资源类型

        Args:
            resource: 资源类型

        Raises:
            DomainException: 当资源类型无效时
        """
        if not resource:
            raise DomainException("资源类型不能为空")

        if len(resource) < 2 or len(resource) > 100:
            raise DomainException("资源类型长度必须在2-100个字符之间")

        if not re.match(r"^[a-zA-Z][a-zA-Z0-9_-]*$", resource):
            raise DomainException("资源类型必须以字母开头，只能包含字母、数字、下划线和连字符")

    @staticmethod
    def _validate_action(action: str) -> None:
        """验证操作类型

        Args:
            action: 操作类型

        Raises:
            DomainException: 当操作类型无效时
        """
        if not action:
            raise DomainException("操作类型不能为空")

        if len(action) < 2 or len(action) > 50:
            raise DomainException("操作类型长度必须在2-50个字符之间")

        if not re.match(r"^[a-zA-Z][a-zA-Z0-9_-]*$", action):
            raise DomainException("操作类型必须以字母开头，只能包含字母、数字、下划线和连字符")

    @staticmethod
    def _validate_method(method: str) -> None:
        """验证HTTP方法

        Args:
            method: HTTP方法

        Raises:
            DomainException: 当HTTP方法无效时
        """
        valid_methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]
        if method.upper() not in valid_methods:
            raise DomainException(f"无效的HTTP方法: {method}")

    @staticmethod
    def _validate_path(path: str) -> None:
        """验证API路径

        Args:
            path: API路径

        Raises:
            DomainException: 当API路径无效时
        """
        if not path.startswith("/"):
            raise DomainException("API路径必须以 / 开头")

        if len(path) > 255:
            raise DomainException("API路径长度不能超过255个字符")

    def __eq__(self, other) -> bool:
        """相等性比较"""
        if not isinstance(other, Permission):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """哈希值"""
        return hash(self.id)

    def __repr__(self) -> str:
        """字符串表示"""
        return f"<Permission(id={self.id}, code={self.code}, resource={self.resource}, action={self.action})>"
