"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: base.py
@DateTime: 2025/06/02 02:11:38
@Docs: ORM基类 - 使用 advanced-alchemy 的基类和 mixins
"""

from advanced_alchemy.base import (
    BigIntAuditBase,
    BigIntBase,
    UUIDAuditBase,
    UUIDBase,
)
from advanced_alchemy.mixins import AuditColumns, SlugKey, UniqueMixin
from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# 定义命名约定，确保生成的约束名称一致且可预测
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """
    项目基类，提供统一的命名约定
    """

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


# 直接导出 advanced-alchemy 的基类，避免重复定义
# 这些基类已经包含了所有必要的功能

# UUID 相关基类
UUIDModel = UUIDBase  # UUID 主键
UUIDAuditModel = UUIDAuditBase  # UUID 主键 + 审计字段

# BigInt 相关基类
BigIntModel = BigIntBase  # BigInt 主键
BigIntAuditModel = BigIntAuditBase  # BigInt 主键 + 审计字段

# Mixins - 用于组合功能
AuditMixin = AuditColumns  # 审计字段 mixin
SlugMixin = SlugKey  # Slug 字段 mixin
UniqueMixin = UniqueMixin  # 唯一性约束 mixin


# 导出常用的模型基类
__all__ = [
    "Base",
    # UUID 基类
    "UUIDModel",
    "UUIDAuditModel",
    # BigInt 基类
    "BigIntModel",
    "BigIntAuditModel",
    # Mixins
    "AuditMixin",
    "SlugMixin",
    "UniqueMixin",
]
