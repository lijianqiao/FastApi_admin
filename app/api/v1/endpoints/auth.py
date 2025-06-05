"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: auth.py
@DateTime: 2025/06/05
@Docs: 认证相关API端点 - 登录、登出、令牌刷新等
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.dependencies import get_current_user, get_current_user_token, get_optional_user
from app.models.models import User
from app.schemas.schemas import (
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    LogoutResponse,
    RefreshTokenRequest,
    TokenResponse,
    UserInfo,
)
from app.services.services import ServiceFactory, get_service_factory

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="用户登录",
    description="用户通过用户名/邮箱和密码进行登录，返回访问令牌和刷新令牌",
)
async def login(
    login_data: LoginRequest,
    service_factory: Annotated[ServiceFactory, Depends(get_service_factory)],
) -> LoginResponse:
    """
    用户登录

    - **identifier**: 用户名或邮箱
    - **password**: 密码
    - **remember_me**: 是否记住登录状态（影响令牌有效期）
    """
    try:
        auth_service = service_factory.get_auth_service()
        result = await auth_service.authenticate_user(
            identifier=login_data.identifier,
            password=login_data.password,
            remember_me=login_data.remember_me,
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        ) from e


@router.post(
    "/login/form",
    response_model=LoginResponse,
    summary="表单登录",
    description="兼容OAuth2标准的表单登录接口",
)
async def login_form(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    service_factory: Annotated[ServiceFactory, Depends(get_service_factory)],
) -> LoginResponse:
    """
    OAuth2兼容的表单登录

    支持标准的OAuth2密码流程，用于与第三方工具集成
    """
    try:
        auth_service = service_factory.get_auth_service()
        result = await auth_service.authenticate_user(
            identifier=form_data.username,
            password=form_data.password,
            remember_me=False,
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        ) from e


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="刷新访问令牌",
    description="使用刷新令牌获取新的访问令牌",
)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    service_factory: Annotated[ServiceFactory, Depends(get_service_factory)],
) -> TokenResponse:
    """
    刷新访问令牌

    - **refresh_token**: 有效的刷新令牌

    返回新的访问令牌和刷新令牌
    """
    try:
        auth_service = service_factory.get_auth_service()
        result = await auth_service.refresh_token(refresh_data)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        ) from e


@router.post(
    "/logout",
    response_model=LogoutResponse,
    summary="用户登出",
    description="用户登出，可选择是否登出所有设备",
)
async def logout(
    access_token: Annotated[str, Depends(get_current_user_token)],
    service_factory: Annotated[ServiceFactory, Depends(get_service_factory)],
    logout_all_devices: bool = False,
) -> LogoutResponse:
    """
    用户登出

    - **logout_all_devices**: 是否登出所有设备

    登出当前设备或所有设备的会话
    """
    try:
        auth_service = service_factory.get_auth_service()
        logout_request = LogoutRequest(
            access_token=access_token,
            all_devices=logout_all_devices,
        )
        result = await auth_service.logout(logout_request)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed",
        ) from e


@router.get(
    "/me",
    response_model=UserInfo,
    summary="获取当前用户信息",
    description="获取当前登录用户的详细信息，包括角色和权限",
)
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_user)],
    service_factory: Annotated[ServiceFactory, Depends(get_service_factory)],
) -> UserInfo:
    """
    获取当前用户信息

    返回当前登录用户的详细信息：
    - 基本信息（用户名、邮箱等）
    - 角色列表
    - 权限列表
    """
    try:
        # 简化处理：直接通过用户ID获取信息
        user_service = service_factory.get_user_service()
        user_with_roles = await user_service.get_user_with_roles(current_user.id)

        # 获取用户权限
        permission_service = service_factory.get_permission_service()
        user_permissions = await permission_service.get_user_permissions(current_user.id)

        return UserInfo(
            id=current_user.id,
            username=current_user.username,
            email=current_user.email,
            phone=current_user.phone,
            nickname=current_user.nickname,
            is_superuser=current_user.is_superuser,
            roles=[role.name for role in user_with_roles.roles],
            permissions=[perm.code for perm in user_permissions],
            avatar=None,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user info",
        ) from e


@router.get(
    "/check",
    summary="检查认证状态",
    description="检查当前用户的认证状态，支持可选认证",
)
async def check_auth_status(
    current_user: Annotated[User | None, Depends(get_optional_user)],
) -> dict[str, bool | str]:
    """
    检查认证状态

    返回当前用户的认证状态信息
    """
    if current_user:
        return {
            "authenticated": True,
            "username": current_user.username,
            "is_active": current_user.is_active,
        }
    else:
        return {
            "authenticated": False,
        }
