"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: auth.py
@DateTime: 2025/07/08
@Docs: 认证服务层
"""

from datetime import UTC, datetime, timedelta
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
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    TokenPayload,
    TokenResponse,
    UpdateProfileRequest,
)
from app.schemas.user import UserDetailResponse, UserResponse
from app.utils.token_blocklist import block_jti_async


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
        token_payload = {"sub": str(user.id), "username": user.username, "is_superuser": user.is_superuser, "is_active": user.is_active}
        access_token = create_access_token(data=token_payload, expires_delta=expires_delta)
        refresh_token = create_refresh_token(data=token_payload)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=int(expires_delta.total_seconds()),
        )

    async def logout(self, user_id: UUID, access_token: str | None = None) -> None:
        """用户登出：将当前access token的jti拉黑，直至其过期。"""
        if not access_token:
            return
        payload = security_manager.verify_token(access_token, "access")
        if not payload:
            return
        jti = payload.get("jti")
        exp_ts = payload.get("exp")
        if not jti or not exp_ts:
            return
        # 计算剩余TTL
        now = datetime.now(UTC).timestamp()
        ttl = max(int(exp_ts - now), 0)
        if ttl > 0:
            await block_jti_async(jti, ttl)

    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        """刷新令牌轮换：校验refresh，拉黑旧refresh jti，颁发新access与新refresh。"""
        payload = security_manager.verify_token(refresh_token, "refresh")
        if not payload:
            raise UnauthorizedException("刷新令牌无效或已过期")

        token_data = TokenPayload.model_validate(payload)
        user = await self._get_user_service().get_by_id(token_data.sub)
        if not user or not user.is_active:
            raise UnauthorizedException("用户不存在或已被禁用")

        # 拉黑旧refresh jti
        old_jti = payload.get("jti")
        exp_ts = payload.get("exp")
        if old_jti and exp_ts:
            now = datetime.now(UTC).timestamp()
            ttl = max(int(exp_ts - now), 0)
            if ttl > 0:
                await block_jti_async(old_jti, ttl)

        # 颁发新access与新refresh
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        base_payload = {"sub": str(user.id), "username": user.username, "is_superuser": user.is_superuser, "is_active": user.is_active}
        new_access_token = create_access_token(data=base_payload, expires_delta=expires_delta)
        new_refresh_token = create_refresh_token(data=base_payload)

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
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

        # 密码强度校验
        self._validate_password_strength(request.new_password)

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

    # ==================== 内部工具 ====================
    @staticmethod
    def _validate_password_strength(password: str) -> None:
        """最小强度：长度>=8，包含大小写、数字、特殊字符中的三类。"""
        import re

        min_len = settings.PASSWORD_MIN_LENGTH
        min_classes = settings.PASSWORD_MIN_CLASSES
        if len(password) < min_len:
            raise BusinessException("密码至少8位")
        classes = 0
        classes += 1 if re.search(r"[a-z]", password) else 0
        classes += 1 if re.search(r"[A-Z]", password) else 0
        classes += 1 if re.search(r"\d", password) else 0
        classes += 1 if re.search(r"[^\w\s]", password) else 0
        if classes < min_classes:
            raise BusinessException("密码需包含大小写、数字、特殊字符中的至少三类")
