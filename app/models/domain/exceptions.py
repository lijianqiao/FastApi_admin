"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: exceptions.py
@DateTime: 2025/06/02 02:32:03
@Docs: 领域异常类定义
"""

from __future__ import annotations


class DomainException(Exception):
    """领域异常基类"""

    def __init__(self, message: str, error_code: str | None = None):
        self.message = message
        self.error_code = error_code
        super().__init__(message)


class UserInactiveError(DomainException):
    """用户未激活异常"""

    def __init__(self, user_id: str | None = None):
        message = f"用户 {user_id} 未激活" if user_id else "用户未激活"
        super().__init__(message, "USER_INACTIVE")


class PermissionDeniedError(DomainException):
    """权限拒绝异常"""

    def __init__(self, permission: str | None = None, user_id: str | None = None):
        if permission and user_id:
            message = f"用户 {user_id} 没有权限 {permission}"
        elif permission:
            message = f"没有权限 {permission}"
        else:
            message = "权限拒绝"
        super().__init__(message, "PERMISSION_DENIED")


class InvalidCredentialsError(DomainException):
    """无效凭证异常"""

    def __init__(self, credential_type: str = "用户名或密码"):
        message = f"{credential_type}错误"
        super().__init__(message, "INVALID_CREDENTIALS")


class RoleAssignmentError(DomainException):
    """角色分配异常"""

    def __init__(self, message: str):
        super().__init__(message, "ROLE_ASSIGNMENT_ERROR")


class PasswordValidationError(DomainException):
    """密码验证异常"""

    def __init__(self, message: str = "密码不符合安全要求"):
        super().__init__(message, "PASSWORD_VALIDATION_ERROR")


class EmailValidationError(DomainException):
    """邮箱验证异常"""

    def __init__(self, email: str | None = None):
        message = f"邮箱 {email} 格式不正确" if email else "邮箱格式不正确"
        super().__init__(message, "EMAIL_VALIDATION_ERROR")


class UserAlreadyExistsError(DomainException):
    """用户已存在异常"""

    def __init__(self, identifier: str, identifier_type: str = "用户名"):
        message = f"{identifier_type} {identifier} 已存在"
        super().__init__(message, "USER_ALREADY_EXISTS")


class RoleNotFoundError(DomainException):
    """角色未找到异常"""

    def __init__(self, role_id: str | None = None):
        message = f"角色 {role_id} 不存在" if role_id else "角色不存在"
        super().__init__(message, "ROLE_NOT_FOUND")


class PermissionNotFoundError(DomainException):
    """权限未找到异常"""

    def __init__(self, permission_id: str | None = None):
        message = f"权限 {permission_id} 不存在" if permission_id else "权限不存在"
        super().__init__(message, "PERMISSION_NOT_FOUND")
