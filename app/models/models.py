"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: models.py
@DateTime: 2025/06/02 02:32:03
@Docs: 数据模型定义
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDAuditModel


class User(UUIDAuditModel):
    """
    用户模型

    提供完整的用户信息管理，包括认证、授权、审计等功能
    """

    __tablename__ = "users"

    # 基本信息
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False, comment="用户名")
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False, comment="邮箱")
    phone: Mapped[str | None] = mapped_column(String(20), unique=True, index=True, comment="手机号")
    password: Mapped[str] = mapped_column(String(255), nullable=False, comment="密码哈希")
    full_name: Mapped[str | None] = mapped_column(String(100), comment="全名")
    avatar_url: Mapped[str | None] = mapped_column(String(500), comment="头像URL")

    # 状态字段
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True, comment="是否激活")
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, index=True, comment="是否超级用户")
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, index=True, comment="软删除标记")
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, comment="邮箱是否验证")
    phone_verified: Mapped[bool] = mapped_column(Boolean, default=False, comment="手机是否验证")

    # 安全相关字段
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), comment="最后登录时间")
    login_count: Mapped[int] = mapped_column(Integer, default=0, comment="登录次数")
    password_changed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), comment="密码修改时间"
    )  # 关联关系
    user_roles: Mapped[list[UserRole]] = relationship("UserRole", back_populates="user", cascade="all, delete-orphan")
    audit_logs: Mapped[list[AuditLog]] = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")

    # 索引优化
    __table_args__ = (
        # 复合索引 - 常用查询组合
        Index("idx_user_active_deleted", "is_active", "is_deleted"),
        Index("idx_user_email_active", "email", "is_active"),
        Index("idx_user_username_active", "username", "is_active"),
        Index("idx_user_login_time", "last_login_at"),
        Index("idx_user_created_active", "created_at", "is_active"),
        # 安全相关索引
        Index("idx_user_superuser_active", "is_superuser", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"


class Role(UUIDAuditModel):
    """
    角色模型

    基于RBAC的角色定义，支持分层权限管理
    """

    __tablename__ = "roles"

    # 基本信息
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False, comment="角色名称")
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False, comment="角色代码")
    description: Mapped[str | None] = mapped_column(Text, comment="角色描述")

    # 管理字段
    level: Mapped[int] = mapped_column(Integer, default=0, index=True, comment="角色等级")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True, comment="是否激活")
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, index=True, comment="是否系统角色")
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, index=True, comment="软删除标记")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment="排序字段")

    # 性能优化字段
    permissions_cache: Mapped[dict | None] = mapped_column(JSON, comment="权限缓存，提升查询性能")  # 关联关系
    role_permissions: Mapped[list[RolePermission]] = relationship(
        "RolePermission", back_populates="role", cascade="all, delete-orphan"
    )
    user_roles: Mapped[list[UserRole]] = relationship("UserRole", back_populates="role", cascade="all, delete-orphan")

    # 索引优化
    __table_args__ = (
        Index("idx_role_active_deleted", "is_active", "is_deleted"),
        Index("idx_role_system_active", "is_system", "is_active"),
        Index("idx_role_level_active", "level", "is_active"),
        Index("idx_role_sort_active", "sort_order", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<Role(id={self.id}, name={self.name}, code={self.code})>"


class Permission(UUIDAuditModel):
    """
    权限模型

    细粒度权限控制，支持资源级别的权限管理
    """

    __tablename__ = "permissions"

    # 基本信息
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="权限名称")
    code: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False, comment="权限代码")
    description: Mapped[str | None] = mapped_column(Text, comment="权限描述")

    # 权限定义
    resource: Mapped[str] = mapped_column(String(100), index=True, nullable=False, comment="资源类型")
    action: Mapped[str] = mapped_column(String(50), index=True, nullable=False, comment="操作类型")
    method: Mapped[str | None] = mapped_column(String(10), index=True, comment="HTTP方法")
    path: Mapped[str | None] = mapped_column(String(255), index=True, comment="API路径")
    category: Mapped[str | None] = mapped_column(String(50), index=True, comment="权限分类")

    # 管理字段
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, index=True, comment="是否系统权限")
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, index=True, comment="软删除标记")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment="排序字段")  # 关联关系
    role_permissions: Mapped[list[RolePermission]] = relationship(
        "RolePermission", back_populates="permission", cascade="all, delete-orphan"
    )

    # 索引优化
    __table_args__ = (
        Index("idx_permission_resource_action", "resource", "action"),
        Index("idx_permission_method_path", "method", "path"),
        Index("idx_permission_category_system", "category", "is_system"),
        Index("idx_permission_system_deleted", "is_system", "is_deleted"),
        UniqueConstraint("resource", "action", "method", "path", name="uq_permission_definition"),
    )

    def __repr__(self) -> str:
        return f"<Permission(id={self.id}, code={self.code}, resource={self.resource}, action={self.action})>"


class UserRole(Base):
    """
    用户角色关联模型

    支持角色的时效性管理和分配追踪
    """

    __tablename__ = "user_roles"

    # 外键关联
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, comment="用户ID"
    )
    role_id: Mapped[UUID] = mapped_column(
        ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True, comment="角色ID"
    )

    # 管理字段
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True, comment="分配时间"
    )
    assigned_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), comment="分配者")
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True, comment="过期时间")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True, comment="是否激活")

    # 关联关系
    user: Mapped[User] = relationship("User", back_populates="user_roles")
    role: Mapped[Role] = relationship("Role", back_populates="user_roles")

    # 索引优化
    __table_args__ = (
        Index("idx_user_role_active", "user_id", "is_active"),
        Index("idx_user_role_expires", "expires_at", "is_active"),
        Index("idx_user_role_assigned", "assigned_at"),
    )

    def __repr__(self) -> str:
        return f"<UserRole(user_id={self.user_id}, role_id={self.role_id})>"


class RolePermission(Base):
    """
    角色权限关联模型

    支持权限的动态分配和追踪
    """

    __tablename__ = "role_permissions"

    # 外键关联
    role_id: Mapped[UUID] = mapped_column(
        ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True, comment="角色ID"
    )
    permission_id: Mapped[UUID] = mapped_column(
        ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True, comment="权限ID"
    )

    # 管理字段
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True, comment="授权时间"
    )
    granted_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), comment="授权者")

    # 关联关系
    role: Mapped[Role] = relationship("Role", back_populates="role_permissions")
    permission: Mapped[Permission] = relationship("Permission", back_populates="role_permissions")

    # 索引优化
    __table_args__ = (Index("idx_role_permission_granted", "granted_at"),)

    def __repr__(self) -> str:
        return f"<RolePermission(role_id={self.role_id}, permission_id={self.permission_id})>"


class AuditLog(UUIDAuditModel):
    """
    审计日志模型

    提供完整的操作审计追踪，支持合规性要求
    """

    __tablename__ = "audit_logs"

    # 用户信息
    user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True, comment="用户ID"
    )
    username: Mapped[str | None] = mapped_column(String(50), index=True, comment="用户名（冗余存储）")

    # 操作信息
    action: Mapped[str] = mapped_column(String(50), index=True, nullable=False, comment="操作类型")
    resource: Mapped[str] = mapped_column(String(100), index=True, nullable=False, comment="资源类型")
    resource_id: Mapped[str | None] = mapped_column(String(100), index=True, comment="资源ID")
    resource_name: Mapped[str | None] = mapped_column(String(200), comment="资源名称")

    # HTTP信息
    method: Mapped[str | None] = mapped_column(String(10), index=True, comment="HTTP方法")
    path: Mapped[str | None] = mapped_column(String(500), index=True, comment="请求路径")

    # 数据变更
    old_values: Mapped[dict | None] = mapped_column(JSON, comment="变更前的值")
    new_values: Mapped[dict | None] = mapped_column(JSON, comment="变更后的值")

    # 请求信息
    ip_address: Mapped[str | None] = mapped_column(String(45), index=True, comment="IP地址")
    user_agent: Mapped[str | None] = mapped_column(Text, comment="用户代理")
    request_id: Mapped[str | None] = mapped_column(String(100), index=True, comment="请求ID")
    session_id: Mapped[str | None] = mapped_column(String(100), index=True, comment="会话ID")

    # 结果信息
    status: Mapped[str] = mapped_column(String(20), index=True, nullable=False, comment="操作状态")
    error_message: Mapped[str | None] = mapped_column(Text, comment="错误信息")
    duration: Mapped[int | None] = mapped_column(Integer, comment="操作耗时（毫秒）")

    # 关联关系
    user: Mapped[User | None] = relationship("User", back_populates="audit_logs")

    # 索引优化
    __table_args__ = (
        # 常用查询组合
        Index("idx_audit_user_action", "user_id", "action"),
        Index("idx_audit_resource_action", "resource", "action"),
        Index("idx_audit_created_status", "created_at", "status"),
        Index("idx_audit_ip_created", "ip_address", "created_at"),
        # 时间范围查询
        Index("idx_audit_created_desc", "created_at", postgresql_using="btree"),
        # 安全审计
        Index("idx_audit_user_time", "user_id", "created_at"),
        Index("idx_audit_resource_time", "resource", "resource_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action={self.action}, resource={self.resource})>"


class SystemConfig(UUIDAuditModel):
    """
    系统配置模型

    提供灵活的系统配置管理，支持版本控制和加密存储
    """

    __tablename__ = "system_configs"

    # 配置信息
    key: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False, comment="配置键")
    value: Mapped[dict | None] = mapped_column(JSON, comment="配置值")
    description: Mapped[str | None] = mapped_column(Text, comment="配置描述")

    # 分类管理
    category: Mapped[str] = mapped_column(String(50), index=True, nullable=False, comment="配置分类")
    data_type: Mapped[str] = mapped_column(String(20), default="string", comment="数据类型")

    # 安全和权限
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, index=True, comment="是否公开访问")
    is_encrypted: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否加密存储")
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, index=True, comment="软删除标记")

    # 验证和默认值
    validation_rule: Mapped[str | None] = mapped_column(Text, comment="验证规则")
    default_value: Mapped[dict | None] = mapped_column(JSON, comment="默认值")

    # 版本管理
    version: Mapped[int] = mapped_column(Integer, default=1, comment="版本号")

    # 索引优化
    __table_args__ = (
        Index("idx_config_category_public", "category", "is_public"),
        Index("idx_config_public_deleted", "is_public", "is_deleted"),
        Index("idx_config_key_version", "key", "version"),
    )

    def __repr__(self) -> str:
        return f"<SystemConfig(id={self.id}, key={self.key}, category={self.category})>"
