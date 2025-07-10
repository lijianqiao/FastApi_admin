"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: auth.py
@DateTime: 2025/07/08
@Docs: 认证服务层
"""

from datetime import timedelta
from uuid import UUID

from app.core.config import settings
from app.core.exceptions import BusinessException, UnauthorizedException
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    security_manager,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import ChangePasswordRequest, LoginRequest, TokenPayload, TokenResponse, UpdateProfileRequest
from app.schemas.user import UserDetailResponse, UserResponse


class AuthService:
    """认证服务"""

    def __init__(self):
        self.user_service = None

    def _get_user_service(self):
        """延迟导入UserService以避免循环导入"""
        if self.user_service is None:
            from app.services.user import UserService

            self.user_service = UserService()
        return self.user_service

    async def login(self, request: LoginRequest, client_ip: str, user_agent: str) -> TokenResponse:
        """用户登录"""
        user = await self._get_user_service().authenticate(request.username, request.password)

        if not user:
            raise UnauthorizedException("用户名或密码错误")

        # 创建令牌
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        token_payload = {"sub": str(user.id)}
        access_token = create_access_token(data=token_payload, expires_delta=expires_delta)
        refresh_token = create_refresh_token(data=token_payload)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=int(expires_delta.total_seconds()),
        )

    async def logout(self, user_id: UUID) -> None:
        """用户登出"""
        # JWT是无状态的，服务器端登出主要是为了记录或使刷新令牌失效（如果适用）
        # 此处可以添加将token加入黑名单的逻辑
        pass

    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        """刷新访问令牌"""
        payload = security_manager.verify_token(refresh_token, "refresh")
        if not payload:
            raise UnauthorizedException("刷新令牌无效或已过期")

        token_data = TokenPayload.model_validate(payload)
        user = await self._get_user_service().get_by_id(token_data.sub)
        if not user or not user.is_active:
            raise UnauthorizedException("用户不存在或已被禁用")

        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        new_token_payload = {"sub": str(user.id)}
        new_access_token = create_access_token(data=new_token_payload, expires_delta=expires_delta)

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=refresh_token,  # 刷新令牌可以保持不变
            expires_in=int(expires_delta.total_seconds()),
        )

    async def get_current_user_profile(self, current_user: User) -> UserDetailResponse:
        """获取当前用户详情"""
        from app.dao.user import UserDAO

        dao = UserDAO()
        user = await dao.get_user_with_details(current_user.id)
        if not user:
            raise BusinessException("用户不存在")
        return UserDetailResponse.model_validate(user)

    async def update_current_user_profile(self, current_user: User, request: UpdateProfileRequest) -> UserResponse:
        """更新当前用户信息"""
        # 创建临时操作上下文（这里没有完整的请求上下文）
        from app.utils.deps import OperationContext

        operation_context = OperationContext(
            user=current_user,
            request=None,  # 没有完整的Request对象
        )

        update_data = request.model_dump(exclude_unset=True)
        # 提取version字段并传递给update方法
        version = update_data.pop("version")
        updated_user = await self._get_user_service().update(
            current_user.id, operation_context=operation_context, version=version, **update_data
        )
        if not updated_user:
            raise BusinessException("更新用户信息失败")
        return UserResponse.model_validate(updated_user)

    async def change_password(self, current_user: User, request: ChangePasswordRequest) -> None:
        """修改用户密码"""
        if not verify_password(request.old_password, current_user.password_hash):
            raise BusinessException("旧密码错误")

        # 创建临时操作上下文（这里没有完整的请求上下文）
        from app.utils.deps import OperationContext

        operation_context = OperationContext(
            user=current_user,
            request=None,  # 没有完整的Request对象
        )

        new_password_hash = hash_password(request.new_password)
        # 使用请求中的version字段进行乐观锁校验
        await self._get_user_service().update(
            current_user.id,
            operation_context=operation_context,
            version=request.version,
            password_hash=new_password_hash,
        )
