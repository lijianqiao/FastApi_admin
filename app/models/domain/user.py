"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: user.py
@DateTime: 2025/06/02 02:32:03
@Docs: 用户领域模型

包含用户相关的业务逻辑和行为，不依赖于持久化技术
"""

from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta
from uuid import UUID

from .exceptions import (
    DomainException,
    InvalidCredentialsError,
    PermissionDeniedError,
    UserInactiveError,
)
from .permission import Permission
from .role import Role


class User:
    """用户领域模型

    包含用户的业务规则和行为逻辑
    """

    def __init__(
        self,
        id: UUID,
        username: str,
        email: str,
        password_hash: str,
        full_name: str | None = None,
        phone: str | None = None,
        avatar_url: str | None = None,
        is_active: bool = True,
        is_superuser: bool = False,
        is_deleted: bool = False,
        email_verified: bool = False,
        phone_verified: bool = False,
        last_login_at: datetime | None = None,
        login_count: int = 0,
        password_changed_at: datetime | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        roles: set[Role] | None = None,
    ):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.full_name = full_name
        self.phone = phone
        self.avatar_url = avatar_url
        self.is_active = is_active
        self.is_superuser = is_superuser
        self.is_deleted = is_deleted
        self.email_verified = email_verified
        self.phone_verified = phone_verified
        self.last_login_at = last_login_at
        self.login_count = login_count
        self.password_changed_at = password_changed_at
        self.created_at = created_at
        self.updated_at = updated_at
        self.roles = roles or set()

    @classmethod
    def create(
        cls,
        id: UUID,
        username: str,
        email: str,
        password_hash: str,
        full_name: str | None = None,
        phone: str | None = None,
    ) -> User:
        """创建新用户

        Args:
            id: 用户ID
            username: 用户名
            email: 邮箱
            password_hash: 密码哈希
            full_name: 全名
            phone: 手机号

        Returns:
            用户实例

        Raises:
            DomainException: 当输入数据无效时
        """
        cls._validate_username(username)
        cls._validate_email(email)

        if phone:
            cls._validate_phone(phone)

        return cls(
            id=id,
            username=username,
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            phone=phone,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

    def authenticate(self, password_hash: str) -> bool:
        """验证用户密码

        Args:
            password_hash: 密码哈希

        Returns:
            是否验证成功

        Raises:
            UserInactiveError: 当用户不活跃时
            InvalidCredentialsError: 当密码错误时
        """
        if not self.is_active:
            raise UserInactiveError("用户账户未激活")

        if self.is_deleted:
            raise UserInactiveError("用户账户已删除")

        if self.password_hash != password_hash:
            raise InvalidCredentialsError("密码错误")

        # 更新登录信息
        self.last_login_at = datetime.now(UTC)
        self.login_count += 1
        self.updated_at = datetime.now(UTC)

        return True

    def change_password(self, new_password_hash: str) -> None:
        """修改密码

        Args:
            new_password_hash: 新密码哈希

        Raises:
            UserInactiveError: 当用户不活跃时
        """
        if not self.is_active:
            raise UserInactiveError("用户账户未激活")

        self.password_hash = new_password_hash
        self.password_changed_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)

    def activate(self) -> None:
        """激活用户"""
        self.is_active = True
        self.updated_at = datetime.now(UTC)

    def deactivate(self) -> None:
        """停用用户"""
        self.is_active = False
        self.updated_at = datetime.now(UTC)

    def soft_delete(self) -> None:
        """软删除用户"""
        self.is_deleted = True
        self.is_active = False
        self.updated_at = datetime.now(UTC)

    def verify_email(self) -> None:
        """验证邮箱"""
        self.email_verified = True
        self.updated_at = datetime.now(UTC)

    def verify_phone(self) -> None:
        """验证手机号"""
        self.phone_verified = True
        self.updated_at = datetime.now(UTC)

    def update_profile(
        self,
        full_name: str | None = None,
        phone: str | None = None,
        avatar_url: str | None = None,
    ) -> None:
        """更新用户资料

        Args:
            full_name: 全名
            phone: 手机号
            avatar_url: 头像URL
        """
        if full_name is not None:
            self.full_name = full_name

        if phone is not None:
            self._validate_phone(phone)
            self.phone = phone
            self.phone_verified = False  # 需要重新验证

        if avatar_url is not None:
            self.avatar_url = avatar_url

        self.updated_at = datetime.now(UTC)

    def assign_role(self, role: Role) -> None:
        """分配角色

        Args:
            role: 角色对象

        Raises:
            UserInactiveError: 当用户不活跃时
        """
        if not self.is_active:
            raise UserInactiveError("不能给非活跃用户分配角色")

        if not role.is_active:
            raise DomainException("不能分配非活跃角色")

        self.roles.add(role)
        self.updated_at = datetime.now(UTC)

    def remove_role(self, role: Role) -> None:
        """移除角色

        Args:
            role: 角色对象
        """
        self.roles.discard(role)
        self.updated_at = datetime.now(UTC)

    def has_role(self, role_code: str) -> bool:
        """检查是否拥有指定角色

        Args:
            role_code: 角色代码

        Returns:
            是否拥有角色
        """
        return any(role.code == role_code for role in self.roles)

    def has_permission(self, permission_code: str) -> bool:
        """检查是否拥有指定权限

        Args:
            permission_code: 权限代码

        Returns:
            是否拥有权限
        """
        if self.is_superuser:
            return True

        for role in self.roles:
            if role.has_permission(permission_code):
                return True

        return False

    def get_all_permissions(self) -> set[Permission]:
        """获取用户所有权限

        Returns:
            权限集合
        """
        if self.is_superuser:
            # 超级用户拥有所有权限，这里返回空集合表示"所有权限"
            # 实际实现中可能需要从权限仓储获取所有权限
            return set()

        permissions = set()
        for role in self.roles:
            permissions.update(role.permissions)

        return permissions

    def check_permission(self, permission_code: str) -> None:
        """检查权限，没有权限时抛出异常

        Args:
            permission_code: 权限代码

        Raises:
            PermissionDeniedError: 当没有权限时
        """
        if not self.has_permission(permission_code):
            raise PermissionDeniedError(f"用户没有权限: {permission_code}")

    def can_access_resource(self, resource: str, action: str) -> bool:
        """检查是否可以访问指定资源

        Args:
            resource: 资源类型
            action: 操作类型

        Returns:
            是否可以访问
        """
        if self.is_superuser:
            return True

        for role in self.roles:
            if role.can_access_resource(resource, action):
                return True

        return False

    def is_password_expired(self, max_age_days: int = 90) -> bool:
        """检查密码是否过期

        Args:
            max_age_days: 密码最大有效天数

        Returns:
            密码是否过期
        """
        if not self.password_changed_at:
            return True  # 从未修改过密码，认为已过期

        expiry_date = self.password_changed_at + timedelta(days=max_age_days)
        return datetime.now(UTC) > expiry_date

    def is_login_allowed(self) -> bool:
        """检查是否允许登录

        Returns:
            是否允许登录
        """
        return self.is_active and not self.is_deleted

    @staticmethod
    def _validate_username(username: str) -> None:
        """验证用户名

        Args:
            username: 用户名

        Raises:
            DomainException: 当用户名无效时
        """
        if not username:
            raise DomainException("用户名不能为空")

        if len(username) < 3 or len(username) > 50:
            raise DomainException("用户名长度必须在3-50个字符之间")

        if not re.match(r"^[a-zA-Z0-9_-]+$", username):
            raise DomainException("用户名只能包含字母、数字、下划线和连字符")

    @staticmethod
    def _validate_email(email: str) -> None:
        """验证邮箱

        Args:
            email: 邮箱地址

        Raises:
            DomainException: 当邮箱无效时
        """
        if not email:
            raise DomainException("邮箱不能为空")

        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, email):
            raise DomainException("邮箱格式无效")

    @staticmethod
    def _validate_phone(phone: str) -> None:
        """验证手机号

        Args:
            phone: 手机号

        Raises:
            DomainException: 当手机号无效时
        """
        if not phone:
            return  # 手机号可以为空

        # 简单的手机号验证（支持中国大陆手机号）
        phone_pattern = r"^1[3-9]\d{9}$"
        if not re.match(phone_pattern, phone):
            raise DomainException("手机号格式无效")

    def __eq__(self, other) -> bool:
        """相等性比较"""
        if not isinstance(other, User):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """哈希值"""
        return hash(self.id)

    def __repr__(self) -> str:
        """字符串表示"""
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"
