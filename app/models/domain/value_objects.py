"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: value_objects.py
@DateTime: 2025/06/02 02:32:03
@Docs: 值对象定义

值对象是不可变的、只包含数据的对象，用于表示领域中的概念
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .exceptions import DomainException


@dataclass(frozen=True)
class Email:
    """邮箱值对象"""

    value: str

    def __post_init__(self) -> None:
        """验证邮箱格式"""
        if not self.value:
            raise DomainException("邮箱不能为空")

        # 简单的邮箱格式验证
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, self.value):
            raise DomainException("邮箱格式无效")

        if len(self.value) > 255:
            raise DomainException("邮箱长度不能超过255个字符")

    @property
    def domain(self) -> str:
        """获取邮箱域名"""
        return self.value.split("@")[1]

    @property
    def local_part(self) -> str:
        """获取邮箱本地部分"""
        return self.value.split("@")[0]

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class Phone:
    """手机号值对象"""

    value: str

    def __post_init__(self) -> None:
        """验证手机号格式"""
        if not self.value:
            raise DomainException("手机号不能为空")

        # 移除所有非数字字符
        cleaned = re.sub(r"[^\d]", "", self.value)

        # 检查长度（支持11位中国手机号）
        if len(cleaned) != 11:
            raise DomainException("手机号格式无效，必须是11位数字")

        # 检查是否以1开头
        if not cleaned.startswith("1"):
            raise DomainException("手机号必须以1开头")

        # 更新值为清理后的格式
        object.__setattr__(self, "value", cleaned)

    @property
    def formatted(self) -> str:
        """格式化显示：138-8888-8888"""
        return f"{self.value[:3]}-{self.value[3:7]}-{self.value[7:]}"

    @property
    def masked(self) -> str:
        """掩码显示：138****8888"""
        return f"{self.value[:3]}****{self.value[7:]}"

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class Username:
    """用户名值对象"""

    value: str

    def __post_init__(self) -> None:
        """验证用户名格式"""
        if not self.value:
            raise DomainException("用户名不能为空")

        if len(self.value) < 3 or len(self.value) > 50:
            raise DomainException("用户名长度必须在3-50个字符之间")

        # 用户名只能包含字母、数字、下划线和连字符
        if not re.match(r"^[a-zA-Z0-9_-]+$", self.value):
            raise DomainException("用户名只能包含字母、数字、下划线和连字符")

        # 不能以数字开头
        if self.value[0].isdigit():
            raise DomainException("用户名不能以数字开头")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class RoleCode:
    """角色代码值对象"""

    value: str

    def __post_init__(self) -> None:
        """验证角色代码格式"""
        if not self.value:
            raise DomainException("角色代码不能为空")

        if len(self.value) < 2 or len(self.value) > 50:
            raise DomainException("角色代码长度必须在2-50个字符之间")

        # 角色代码必须以大写字母开头，只能包含大写字母、数字和下划线
        if not re.match(r"^[A-Z][A-Z0-9_]*$", self.value):
            raise DomainException("角色代码必须以大写字母开头，只能包含大写字母、数字和下划线")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class PermissionCode:
    """权限代码值对象"""

    value: str

    def __post_init__(self) -> None:
        """验证权限代码格式"""
        if not self.value:
            raise DomainException("权限代码不能为空")

        if len(self.value) < 2 or len(self.value) > 100:
            raise DomainException("权限代码长度必须在2-100个字符之间")

        # 权限代码建议使用点分格式：module.resource.action
        if not re.match(r"^[a-zA-Z][a-zA-Z0-9._-]*$", self.value):
            raise DomainException("权限代码必须以字母开头，只能包含字母、数字、点、下划线和连字符")

    @property
    def parts(self) -> list[str]:
        """获取权限代码的各个部分"""
        return self.value.split(".")

    @property
    def module(self) -> str | None:
        """获取模块名"""
        parts = self.parts
        return parts[0] if len(parts) >= 1 else None

    @property
    def resource(self) -> str | None:
        """获取资源名"""
        parts = self.parts
        return parts[1] if len(parts) >= 2 else None

    @property
    def action(self) -> str | None:
        """获取操作名"""
        parts = self.parts
        return parts[2] if len(parts) >= 3 else None

    def __str__(self) -> str:
        return self.value
