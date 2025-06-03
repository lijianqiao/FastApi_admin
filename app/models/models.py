"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: models.py
@DateTime: 2025/06/02 02:32:03
@Docs: 数据模型定义 - 基于 advanced_alchemy 最佳实践的简化设计
"""

from sqlalchemy import Boolean, Column, ForeignKey, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import AutoIdModel, BaseModel

# 用户角色关联表
user_roles = Table(
    "user_roles",
    BaseModel.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("role_id", ForeignKey("roles.id"), primary_key=True),
)

# 角色权限关联表
role_permissions = Table(
    "role_permissions",
    BaseModel.metadata,
    Column("role_id", ForeignKey("roles.id"), primary_key=True),
    Column("permission_id", ForeignKey("permissions.id"), primary_key=True),
)


class User(BaseModel):
    """用户模型 - 简化设计"""

    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, comment="用户名")
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, comment="邮箱")
    password: Mapped[str] = mapped_column(String(255), comment="密码哈希")
    full_name: Mapped[str | None] = mapped_column(String(100), comment="全名")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否激活")
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否超级用户")

    # 关联关系
    roles: Mapped[list["Role"]] = relationship(secondary=user_roles, back_populates="users", lazy="selectin")


class Role(BaseModel):
    """角色模型 - 简化设计"""

    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(50), unique=True, index=True, comment="角色名称")
    description: Mapped[str | None] = mapped_column(Text, comment="角色描述")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否激活")

    # 关联关系
    users: Mapped[list[User]] = relationship(secondary=user_roles, back_populates="roles", lazy="selectin")
    permissions: Mapped[list["Permission"]] = relationship(
        secondary=role_permissions, back_populates="roles", lazy="selectin"
    )


class Permission(BaseModel):
    """权限模型 - 简化设计"""

    __tablename__ = "permissions"

    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, comment="权限名称")
    code: Mapped[str] = mapped_column(String(100), unique=True, comment="权限代码")
    description: Mapped[str | None] = mapped_column(Text, comment="权限描述")

    # 关联关系
    roles: Mapped[list[Role]] = relationship(secondary=role_permissions, back_populates="permissions", lazy="selectin")


class AuditLog(AutoIdModel):
    """审计日志模型 - 简化设计"""

    __tablename__ = "audit_logs"

    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), index=True, comment="用户ID")
    action: Mapped[str] = mapped_column(String(50), index=True, comment="操作类型")
    resource: Mapped[str] = mapped_column(String(100), index=True, comment="资源类型")
    resource_id: Mapped[str | None] = mapped_column(String(100), comment="资源ID")
    ip_address: Mapped[str | None] = mapped_column(String(45), comment="IP地址")
    user_agent: Mapped[str | None] = mapped_column(Text, comment="用户代理")

    # 关联关系
    user: Mapped[User | None] = relationship("User", lazy="select")
