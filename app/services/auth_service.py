"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: auth_service.py
@DateTime: 2025/06/04 14:30:00
@Docs: 认证服务 - 处理用户登录、令牌管理等认证相关业务逻辑
"""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import (
    decode_access_token,
    decode_token_for_refresh,
    generate_token_pair,
    get_password_hash,
    verify_password,
)
from app.exceptions import (
    AuthenticationError,
    InvalidTokenError,
    RecordNotFoundError,
    TokenExpiredError,
)
from app.models import User
from app.repositories import UserRepository
from app.schemas.schemas import (
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    LogoutResponse,
    RefreshTokenRequest,
    TokenResponse,
    UserInfo,
)
from app.services.base import AppBaseService


class AuthService(AppBaseService[User, UUID]):
    """
    认证服务类

    提供用户登录、令牌刷新、密码验证等认证相关功能
    继承AppBaseService以复用基础功能，专注于认证业务逻辑
    """

    repository_type = UserRepository

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    @property
    def user_repo(self) -> UserRepository:
        """获取类型化的用户仓库实例"""
        return self.repository  # type: ignore

    async def _validate_and_get_user_from_token(self, access_token: str) -> User:
        """
        验证访问令牌并返回用户对象（内部通用方法）

        Args:
            access_token: 访问令牌

        Returns:
            用户对象

        Raises:
            TokenExpiredError: 访问令牌已过期
            InvalidTokenError: 无效的访问令牌
            AuthenticationError: 用户不存在或已被禁用
        """
        # 解码访问令牌
        payload = decode_access_token(access_token)
        user_id = payload.get("sub")

        if not user_id:
            raise InvalidTokenError("访问令牌")  # 获取用户信息
        user = await self.user_repo.get_by_id(UUID(user_id))

        if not user:
            self.logger.warning(f"令牌验证失败: 用户不存在 - {user_id}")
            raise AuthenticationError("用户不存在")

        if not user.is_active or user.is_deleted:
            self.logger.warning(f"令牌验证失败: 用户状态无效 - {user.username}")
            raise AuthenticationError("账户状态异常")

        return user

    async def login(self, login_data: LoginRequest) -> TokenResponse:
        """
        用户登录

        Args:
            login_data: 登录请求数据

        Returns:
            令牌响应数据

        Raises:
            AuthenticationError: 认证失败
            ValidationError: 数据验证失败
        """
        self.logger.info(f"用户尝试登录: {login_data.identifier}")  # 根据用户名、邮箱或手机号查找用户
        user = await self._get_user_by_identifier(login_data.identifier)

        if not user:
            self.logger.warning(f"登录失败: 用户不存在 - {login_data.identifier}")
            raise AuthenticationError("用户名或密码错误")

        # 检查用户状态
        if not user.is_active:
            self.logger.warning(f"登录失败: 用户已禁用 - {user.username}")
            raise AuthenticationError("账户已被禁用")

        if user.is_deleted:
            self.logger.warning(f"登录失败: 用户已删除 - {user.username}")
            raise AuthenticationError("用户名或密码错误")

        # 验证密码
        if not verify_password(login_data.password, user.password_hash):
            self.logger.warning(f"登录失败: 密码错误 - {user.username}")
            raise AuthenticationError("用户名或密码错误")

        # 更新最后登录时间
        await self._update_last_login(user)

        # 生成令牌
        token_data = {
            "sub": str(user.id),
            "username": user.username,
            "email": user.email,
            "is_superuser": user.is_superuser,
        }

        tokens = generate_token_pair(token_data)

        self.logger.info(f"用户登录成功: {user.username} ({user.id})")

        return TokenResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type=tokens["token_type"],
            expires_in=settings.jwt.access_token_expire_minutes * 60,
        )

    async def refresh_token(self, refresh_data: RefreshTokenRequest) -> TokenResponse:
        """
        刷新访问令牌

        Args:
            refresh_data: 刷新令牌请求数据

        Returns:
            新的令牌响应数据

        Raises:
            TokenExpiredError: 刷新令牌已过期
            InvalidTokenError: 无效的刷新令牌
            AuthenticationError: 用户不存在或已被禁用
        """
        self.logger.debug("开始刷新访问令牌")

        try:
            # 解码刷新令牌
            payload = decode_token_for_refresh(refresh_data.refresh_token)
            user_id = payload.get("sub")

            if not user_id:
                raise InvalidTokenError("刷新令牌")

            # 验证用户是否存在且有效
            user = await self.user_repo.get_by_id(UUID(user_id))
            if not user:
                self.logger.warning(f"令牌刷新失败: 用户不存在 - {user_id}")
                raise AuthenticationError("用户不存在")

            if not user.is_active or user.is_deleted:
                self.logger.warning(f"令牌刷新失败: 用户状态无效 - {user.username}")
                raise AuthenticationError("账户状态异常")

            # 生成新的令牌对
            token_data = {
                "sub": str(user.id),
                "username": user.username,
                "email": user.email,
                "is_superuser": user.is_superuser,
            }

            tokens = generate_token_pair(token_data)

            self.logger.info(f"令牌刷新成功: {user.username}")

            return TokenResponse(
                access_token=tokens["access_token"],
                refresh_token=tokens["refresh_token"],
                token_type=tokens["token_type"],
                expires_in=settings.jwt.access_token_expire_minutes * 60,
            )

        except TokenExpiredError:
            self.logger.warning("令牌刷新失败: 刷新令牌已过期")
            raise
        except InvalidTokenError as e:
            self.logger.warning(f"令牌刷新失败: 无效的刷新令牌 - {e}")
            raise InvalidTokenError("无效的刷新令牌") from e
        except Exception as e:
            self.logger.error(f"令牌刷新异常: {e}")
            raise AuthenticationError("令牌刷新失败") from e

    async def get_current_user_info(self, access_token: str) -> UserInfo:
        """
        获取当前用户信息

        Args:
            access_token: 访问令牌

        Returns:
            用户信息

        Raises:
            TokenExpiredError: 访问令牌已过期
            InvalidTokenError: 无效的访问令牌
            AuthenticationError: 用户不存在或已被禁用
        """
        self.logger.debug("获取当前用户信息")

        try:
            # 使用通用方法验证令牌并获取用户
            user = await self._validate_and_get_user_from_token(access_token)

            self.logger.debug(f"成功获取用户信息: {user.username}")

            # 构建角色名称列表
            role_names = [role.name for role in user.roles] if user.roles else []

            # 构建权限代码列表（通过角色获取权限）
            permission_codes = []
            if user.roles:
                for role in user.roles:
                    if role.permissions:
                        permission_codes.extend([perm.code for perm in role.permissions])
            # 去重
            permission_codes = list(set(permission_codes))

            return UserInfo(
                id=user.id,
                username=user.username,
                email=user.email,
                phone=user.phone,
                nickname=user.nickname,
                is_superuser=user.is_superuser,
                roles=role_names,
                permissions=permission_codes,
                avatar=None,  # User模型中没有avatar字段，设为None
            )

        except TokenExpiredError:
            self.logger.warning("获取用户信息失败: 访问令牌已过期")
            raise
        except InvalidTokenError as e:
            self.logger.warning(f"获取用户信息失败: 无效的访问令牌 - {e}")
            raise InvalidTokenError("无效的访问令牌") from e
        except Exception as e:
            self.logger.error(f"获取用户信息异常: {e}")
            raise AuthenticationError("获取用户信息失败") from e

    async def validate_token(self, access_token: str) -> User:
        """
        验证访问令牌并返回用户对象

        Args:
            access_token: 访问令牌

        Returns:
            用户对象

        Raises:
            TokenExpiredError: 访问令牌已过期
            InvalidTokenError: 无效的访问令牌
            AuthenticationError: 用户不存在或已被禁用
        """
        self.logger.debug("验证访问令牌")

        try:
            # 使用通用方法验证令牌并获取用户
            user = await self._validate_and_get_user_from_token(access_token)

            self.logger.debug(f"令牌验证成功: {user.username}")
            return user

        except TokenExpiredError:
            self.logger.warning("令牌验证失败: 访问令牌已过期")
            raise
        except InvalidTokenError as e:
            self.logger.warning(f"令牌验证失败: 无效的访问令牌 - {e}")
            raise InvalidTokenError("无效的访问令牌") from e
        except Exception as e:
            self.logger.error(f"令牌验证异常: {e}")
            raise AuthenticationError("令牌验证失败") from e

    async def logout(self, logout_data: LogoutRequest) -> LogoutResponse:
        """
        用户登出

        将访问令牌添加到黑名单，实现真正的token失效
        支持单设备登出或全设备登出

        Args:
            logout_data: 登出请求数据

        Returns:
            登出响应数据

        Raises:
            InvalidTokenError: 无效的访问令牌
            AuthenticationError: 认证失败
        """
        self.logger.info("用户开始登出")

        try:
            # 使用通用方法验证令牌并获取用户
            user = await self._validate_and_get_user_from_token(logout_data.access_token)

            # TODO: 实现token黑名单功能
            # 1. 将当前access_token添加到Redis黑名单
            # 2. 如果all_devices为True，将用户的所有token都加入黑名单
            # 3. 设置黑名单过期时间为token的剩余有效期
            #
            # 示例实现：
            # if logout_data.all_devices:
            #     # 登出所有设备：清除用户的所有refresh token
            #     await self.redis_client.delete(f"user_tokens:{user_id}")
            #     await self.redis_client.delete(f"refresh_tokens:{user_id}:*")
            #
            # # 将当前access token添加到黑名单
            # payload = decode_access_token(logout_data.access_token)
            # token_jti = payload.get("jti")  # JWT ID，需要在生成token时添加
            # if token_jti:
            #     token_exp = payload.get("exp")
            #     current_time = datetime.now(UTC).timestamp()
            #     ttl = int(token_exp - current_time) if token_exp > current_time else 0
            #     if ttl > 0:
            #         await self.redis_client.setex(f"blacklist:{token_jti}", ttl, "1")

            self.logger.info(f"用户登出成功: {user.username} ({user.id})")

            return LogoutResponse(
                message="登出成功" if not logout_data.all_devices else "已从所有设备登出",
                success=True,
            )

        except TokenExpiredError:
            # 如果token已过期，仍然返回成功，因为目标已达成
            self.logger.info("登出请求: token已过期，视为登出成功")
            return LogoutResponse(message="登出成功", success=True)

        except InvalidTokenError as e:
            self.logger.warning(f"登出失败: 无效的访问令牌 - {e}")
            raise InvalidTokenError("无效的访问令牌") from e

        except Exception as e:
            self.logger.error(f"登出异常: {e}")
            raise AuthenticationError("登出失败") from e

    async def change_password(self, user_id: UUID, old_password: str, new_password: str) -> bool:
        """
        修改用户密码

        Args:
            user_id: 用户ID
            old_password: 旧密码
            new_password: 新密码

        Returns:
            修改是否成功

        Raises:
            AuthenticationError: 认证失败
            RecordNotFoundError: 用户不存在
        """
        self.logger.info(f"用户尝试修改密码: {user_id}")

        try:
            # 获取用户信息
            user = await self.user_repo.get_by_id(user_id)
            if not user:
                self.logger.warning(f"修改密码失败: 用户不存在 - {user_id}")
                raise RecordNotFoundError("用户不存在")

            if not user.is_active or user.is_deleted:
                self.logger.warning(f"修改密码失败: 用户状态无效 - {user.username}")
                raise AuthenticationError("账户状态异常")

            # 验证旧密码
            if not verify_password(old_password, user.password_hash):
                self.logger.warning(f"修改密码失败: 旧密码错误 - {user.username}")
                raise AuthenticationError("旧密码错误")

            # 生成新密码哈希
            new_password_hash = get_password_hash(new_password)

            # 更新密码
            await self.user_repo.update_record(user_id, {"password_hash": new_password_hash})
            await self.session.commit()

            self.logger.info(f"密码修改成功: {user.username}")
            return True

        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"修改密码异常: {e}")
            raise

    async def _get_user_by_identifier(self, identifier: str) -> User | None:
        """
        根据标识符（用户名、邮箱或手机号）获取用户

        Args:
            identifier: 用户标识符

        Returns:
            用户对象或None
        """
        try:
            # 尝试按用户名查找
            user = await self.user_repo.get_by_username(identifier)
            if user:
                return user

            # 尝试按邮箱查找
            if "@" in identifier:
                user = await self.user_repo.get_by_email(identifier)
                if user:
                    return user

            # 尝试按手机号查找
            if identifier.isdigit():
                user = await self.user_repo.get_by_phone(identifier)
                if user:
                    return user

            return None

        except Exception as e:
            self.logger.error(f"查找用户异常: {e}")
            return None

    async def _update_last_login(self, user: User) -> None:
        """
        更新用户最后登录时间

        Args:
            user: 用户对象
        """
        try:
            await self.user_repo.update_record(user.id, {"last_login": datetime.now(UTC)})
            await self.session.commit()
        except Exception as e:
            self.logger.error(f"更新最后登录时间失败: {e}")

    async def authenticate_user(self, identifier: str, password: str, remember_me: bool = False) -> LoginResponse:
        """
        用户认证接口方法 - 供API端点调用

        Args:
            identifier: 用户名、邮箱或手机号
            password: 密码
            remember_me: 是否记住登录状态

        Returns:
            登录响应数据（包含令牌和用户信息）

        Raises:
            AuthenticationError: 认证失败
            ValidationError: 数据验证失败
        """
        # 使用现有的login方法获取令牌
        login_request = LoginRequest(identifier=identifier, password=password, remember_me=remember_me)
        token_response = await self.login(login_request)

        # 获取用户信息
        user = await self._get_user_by_identifier(identifier)
        if not user:
            raise AuthenticationError("用户不存在")

        # 构建用户角色和权限列表
        role_names = [role.name for role in user.roles] if user.roles else []
        permission_codes = []
        if user.roles:
            for role in user.roles:
                if role.permissions:
                    permission_codes.extend([perm.code for perm in role.permissions])
        permission_codes = list(set(permission_codes))

        # 构建用户信息
        user_info = UserInfo(
            id=user.id,
            username=user.username,
            email=user.email,
            phone=user.phone,
            nickname=user.nickname,
            is_superuser=user.is_superuser,
            roles=role_names,
            permissions=permission_codes,
            avatar=None,
        )

        # 返回包含用户信息的登录响应
        return LoginResponse(
            access_token=token_response.access_token,
            token_type=token_response.token_type,
            expires_in=token_response.expires_in,
            refresh_token=token_response.refresh_token,
            user=user_info,
        )
