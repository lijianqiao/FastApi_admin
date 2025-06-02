# filepath: e:\Project\fastapibase\app\models\domain\system_config.py
"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: system_config.py
@DateTime: 2025/06/02 02:32:03
@Docs: 系统配置领域模型

系统配置领域模型包含配置管理的核心业务逻辑
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from app.models.domain.exceptions import DomainException
from app.utils.enum import ConfigCategory, ConfigDataType


@dataclass
class SystemConfig:
    """系统配置领域模型

    负责管理系统配置的读写、验证、加密等核心业务逻辑
    """

    # 基本标识
    id: UUID

    # 配置信息
    key: str
    value: dict | None = None
    description: str | None = None

    # 分类管理
    category: ConfigCategory = ConfigCategory.SYSTEM
    data_type: ConfigDataType = ConfigDataType.STRING

    # 安全和权限
    is_public: bool = False
    is_encrypted: bool = False
    is_deleted: bool = False

    # 验证和默认值
    validation_rule: str | None = None
    default_value: dict | None = None

    # 版本管理
    version: int = 1  # 审计字段
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime | None = None

    def __post_init__(self):
        """初始化后的验证"""
        if isinstance(self.category, str):
            self.category = ConfigCategory(self.category)
        if isinstance(self.data_type, str):
            self.data_type = ConfigDataType(self.data_type)

        # 验证配置键格式
        self.validate_key()

        # 设置默认加密策略
        if self.data_type == ConfigDataType.PASSWORD and not self.is_encrypted:
            self.is_encrypted = True

    def validate_key(self) -> None:
        """验证配置键格式"""
        if not self.key:
            raise DomainException("配置键不能为空")

        if len(self.key) > 100:
            raise DomainException("配置键长度不能超过100个字符")

        # 配置键应该使用点分格式，如: app.database.host
        if not all(c.isalnum() or c in "._-" for c in self.key):
            raise DomainException("配置键只能包含字母、数字、点、下划线和连字符")

    def get_typed_value(self) -> Any:
        """获取类型化的配置值

        Returns:
            根据data_type转换后的值

        Raises:
            DomainException: 当值无法转换为指定类型时
        """
        if self.value is None:
            return self.get_default_value()

        try:
            raw_value = self.value.get("data") if isinstance(self.value, dict) else self.value

            match self.data_type:
                case ConfigDataType.STRING:
                    return str(raw_value) if raw_value is not None else ""
                case ConfigDataType.INTEGER:
                    return int(raw_value) if raw_value is not None else 0
                case ConfigDataType.FLOAT:
                    return float(raw_value) if raw_value is not None else 0.0
                case ConfigDataType.BOOLEAN:
                    if isinstance(raw_value, bool):
                        return raw_value
                    if isinstance(raw_value, str):
                        return raw_value.lower() in ("true", "1", "yes", "on")
                    return bool(raw_value) if raw_value is not None else False
                case ConfigDataType.JSON:
                    if isinstance(raw_value, str):
                        return json.loads(raw_value)
                    return raw_value if raw_value is not None else {}
                case ConfigDataType.LIST:
                    if isinstance(raw_value, list):
                        return raw_value
                    if isinstance(raw_value, str):
                        return json.loads(raw_value)
                    return [] if raw_value is None else [raw_value]
                case ConfigDataType.PASSWORD:
                    return str(raw_value) if raw_value is not None else ""
                case _:
                    return raw_value

        except (ValueError, TypeError, json.JSONDecodeError) as e:
            raise DomainException(f"配置值类型转换失败: {e}") from e

    def get_default_value(self) -> Any:
        """获取默认值"""
        if self.default_value is None:
            match self.data_type:
                case ConfigDataType.STRING | ConfigDataType.PASSWORD:
                    return ""
                case ConfigDataType.INTEGER:
                    return 0
                case ConfigDataType.FLOAT:
                    return 0.0
                case ConfigDataType.BOOLEAN:
                    return False
                case ConfigDataType.JSON:
                    return {}
                case ConfigDataType.LIST:
                    return []
                case _:
                    return None

        return self.default_value.get("data") if isinstance(self.default_value, dict) else self.default_value

    def set_value(self, value: Any) -> None:
        """设置配置值

        Args:
            value: 要设置的值

        Raises:
            DomainException: 当值验证失败时
        """
        # 验证值
        self.validate_value(value)  # 包装值
        self.value = {"data": value, "type": self.data_type.value}
        self.updated_at = datetime.now(UTC)
        self.version += 1

    def validate_value(self, value: Any) -> None:
        """验证配置值

        Args:
            value: 要验证的值

        Raises:
            DomainException: 当值无效时
        """
        if value is None:
            return

        # 基本类型验证
        try:
            match self.data_type:
                case ConfigDataType.STRING | ConfigDataType.PASSWORD:
                    str(value)
                case ConfigDataType.INTEGER:
                    int(value)
                case ConfigDataType.FLOAT:
                    float(value)
                case ConfigDataType.BOOLEAN:
                    if not isinstance(value, bool | str | int):
                        raise ValueError("布尔值类型无效")
                case ConfigDataType.JSON:
                    if not isinstance(value, dict | list | str):
                        raise ValueError("JSON类型无效")
                    if isinstance(value, str):
                        json.loads(value)
                case ConfigDataType.LIST:
                    if not isinstance(value, list | str):
                        raise ValueError("列表类型无效")
                    if isinstance(value, str):
                        json.loads(value)
        except (ValueError, TypeError, json.JSONDecodeError) as e:
            raise DomainException(f"配置值验证失败: {e}") from e

        # 自定义验证规则
        if self.validation_rule:
            self.validate_with_rule(value)

    def validate_with_rule(self, value: Any) -> None:
        """使用自定义规则验证值

        Args:
            value: 要验证的值

        Raises:
            DomainException: 当值不符合验证规则时
        """
        # 这里可以实现更复杂的验证逻辑
        # 例如正则表达式、范围检查等
        # 暂时保留接口，后续可扩展
        pass

    @property
    def is_sensitive(self) -> bool:
        """是否为敏感配置"""
        return (
            self.is_encrypted
            or self.data_type == ConfigDataType.PASSWORD
            or "password" in self.key.lower()
            or "secret" in self.key.lower()
            or "key" in self.key.lower()
            or "token" in self.key.lower()
        )

    @property
    def display_value(self) -> str:
        """获取用于显示的值（敏感信息会被掩码）"""
        if self.is_sensitive:
            return "***MASKED***"

        typed_value = self.get_typed_value()
        if isinstance(typed_value, dict | list):
            return json.dumps(typed_value, ensure_ascii=False)
        return str(typed_value)

    def increment_version(self) -> None:
        """增加版本号"""
        self.version += 1
        self.updated_at = datetime.now(UTC)

    def mark_deleted(self) -> None:
        """标记为已删除"""
        self.is_deleted = True
        self.updated_at = datetime.now(UTC)

    def restore(self) -> None:
        """恢复已删除的配置"""
        self.is_deleted = False
        self.updated_at = datetime.now(UTC)

    def clone(self, new_key: str) -> SystemConfig:
        """克隆配置项

        Args:
            new_key: 新的配置键

        Returns:
            新的配置项
        """
        from uuid import uuid4

        return SystemConfig(
            id=uuid4(),
            key=new_key,
            value=self.value.copy() if self.value else None,
            description=self.description,
            category=self.category,
            data_type=self.data_type,
            is_public=self.is_public,
            is_encrypted=self.is_encrypted,
            is_deleted=False,
            validation_rule=self.validation_rule,
            default_value=self.default_value.copy() if self.default_value else None,
            version=1,
        )

    def to_dict(self, include_sensitive: bool = False) -> dict:
        """转换为字典

        Args:
            include_sensitive: 是否包含敏感信息

        Returns:
            配置字典
        """
        result = {
            "id": str(self.id),
            "key": self.key,
            "description": self.description,
            "category": self.category.value,
            "data_type": self.data_type.value,
            "is_public": self.is_public,
            "is_encrypted": self.is_encrypted,
            "is_deleted": self.is_deleted,
            "version": self.version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_sensitive or not self.is_sensitive:
            result["value"] = self.get_typed_value()
        else:
            result["value"] = "***MASKED***"

        return result

    def __str__(self) -> str:
        return f"{self.key}={self.display_value}"

    def __repr__(self) -> str:
        return (
            f"SystemConfig(id={self.id}, key={self.key}, category={self.category.value}, type={self.data_type.value})"
        )
