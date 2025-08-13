"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: security.py
@DateTime: 2025/07/08
@Docs: 安全工具类 - JWT令牌管理、密码加密等
"""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

try:
    import jwt
    from passlib.context import CryptContext
except ImportError as e:
    raise ImportError("认证依赖未安装。请运行: pip install PyJWT passlib[bcrypt]") from e

from app.core.config import settings
from app.core.exceptions import UnauthorizedException
from app.utils.logger import logger


class SecurityManager:
    """安全管理器 - 提供JWT令牌和密码加密功能"""

    def __init__(self):
        # 初始化密码加密上下文
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

        # JWT配置
        self.secret_keys = settings.ALL_SECRET_KEYS
        self.algorithm = settings.ALGORITHM
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = settings.REFRESH_TOKEN_EXPIRE_DAYS
        self.issuer = settings.JWT_ISSUER
        self.audience = settings.JWT_AUDIENCE
        self.clock_skew_seconds = settings.JWT_CLOCK_SKEW_SECONDS

    # ==================== 密码管理 ====================
    def hash_password(self, password: str) -> str:
        """密码加密

        Args:
            password: 明文密码

        Returns:
            加密后的密码哈希
        """
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码

        Args:
            plain_password: 明文密码
            hashed_password: 加密后的密码哈希

        Returns:
            密码是否匹配
        """
        return self.pwd_context.verify(plain_password, hashed_password)

    # ==================== JWT令牌管理 ====================
    def create_access_token(self, data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
        """创建访问令牌

        Args:
            data: 令牌载荷数据
            expires_delta: 过期时间增量

        Returns:
            JWT访问令牌
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(UTC) + expires_delta
        else:
            expire = datetime.now(UTC) + timedelta(minutes=self.access_token_expire_minutes)

        jti = str(uuid4())
        now = datetime.now(UTC)
        to_encode.update(
            {
                "exp": expire,
                "nbf": now,
                "iat": now,
                "iss": self.issuer,
                "aud": self.audience,
                "jti": jti,
                "type": "access",
            }
        )
        encoded_jwt = jwt.encode(to_encode, self.secret_keys[0], algorithm=self.algorithm)
        return encoded_jwt

    def create_refresh_token(self, data: dict[str, Any]) -> str:
        """创建刷新令牌

        Args:
            data: 令牌载荷数据

        Returns:
            JWT刷新令牌
        """
        to_encode = data.copy()
        expire = datetime.now(UTC) + timedelta(days=self.refresh_token_expire_days)
        jti = str(uuid4())
        now = datetime.now(UTC)
        to_encode.update(
            {
                "exp": expire,
                "nbf": now,
                "iat": now,
                "iss": self.issuer,
                "aud": self.audience,
                "jti": jti,
                "type": "refresh",
            }
        )
        encoded_jwt = jwt.encode(to_encode, self.secret_keys[0], algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str, token_type: str = "access") -> dict[str, Any] | None:
        """验证并解码JWT令牌"""
        try:
            last_error: Exception | None = None
            payload: dict[str, Any] | None = None
            # 轮询所有密钥以支持密钥轮换
            for _idx, key in enumerate(self.secret_keys):
                try:
                    payload = jwt.decode(
                        token,
                        key,
                        algorithms=[self.algorithm],
                        audience=self.audience,
                        issuer=self.issuer,
                        leeway=self.clock_skew_seconds,
                    )
                    break
                except Exception as e:  # noqa: PERF203 - 逐个尝试
                    last_error = e
                    payload = None
            if payload is None:
                raise last_error or UnauthorizedException(detail="令牌无效")

            # 检查令牌类型
            if payload.get("type") != token_type:
                raise UnauthorizedException(detail=f"令牌类型错误: 期望{token_type}类型") from None

            # 黑名单检查（需要延迟导入避免循环）
            try:
                from app.utils.token_blocklist import is_jti_blocked

                jti = payload.get("jti")
                if jti and token_type in ("access", "refresh"):
                    # 如果在黑名单，拒绝
                    if is_jti_blocked(jti):
                        raise UnauthorizedException(detail="令牌已失效")
            except Exception as _:
                # 黑名单模块不可用时忽略（仅在未配置Redis时）
                pass

            return payload
        except jwt.ExpiredSignatureError as e:
            raise UnauthorizedException(detail="令牌已过期") from e
        except jwt.InvalidTokenError as e:
            raise UnauthorizedException(detail=f"令牌无效: {str(e)}") from e
        except Exception as e:
            if not token:
                raise UnauthorizedException(detail="未提供认证令牌") from e
            else:
                raise UnauthorizedException(detail=f"令牌验证失败: {str(e)}") from e

    def extract_user_from_token(self, token: str) -> dict[str, Any] | None:
        """从令牌中提取用户信息

        Args:
            token: JWT访问令牌

        Returns:
            用户信息字典或None
        """
        logger.debug(f"开始提取用户信息，token: {token[:30]}...")

        payload = self.verify_token(token, "access")
        if not payload:
            logger.warning("Token 验证失败")
            return None

        logger.debug(f"Token 验证成功，payload: {payload}")

        return {
            "user_id": payload.get("sub"),
            "username": payload.get("username"),
            "is_superuser": payload.get("is_superuser", False),
            "is_active": payload.get("is_active", True),
            "exp": payload.get("exp"),
        }

    # ==================== 工具方法 ====================
    def generate_random_string(self, length: int = 32) -> str:
        """生成随机字符串

        Args:
            length: 字符串长度

        Returns:
            随机字符串
        """
        return secrets.token_urlsafe(length)

    def generate_api_key(self) -> str:
        """生成API密钥

        Returns:
            API密钥
        """
        return f"sk-{self.generate_random_string(32)}"

    def hash_api_key(self, api_key: str) -> str:
        """API密钥哈希

        Args:
            api_key: API密钥

        Returns:
            哈希后的API密钥
        """
        return hashlib.sha256(api_key.encode()).hexdigest()

    def create_session_id(self) -> str:
        """创建会话ID

        Returns:
            会话ID
        """
        return self.generate_random_string(16)


# 全局安全管理器实例
security_manager = SecurityManager()


# 便捷函数
def hash_password(password: str) -> str:
    """密码加密便捷函数"""
    return security_manager.hash_password(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """密码验证便捷函数"""
    return security_manager.verify_password(plain_password, hashed_password)


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """创建访问令牌便捷函数"""
    return security_manager.create_access_token(data, expires_delta)


def create_refresh_token(data: dict[str, Any]) -> str:
    """创建刷新令牌便捷函数"""
    return security_manager.create_refresh_token(data)


def verify_token(token: str, token_type: str = "access") -> dict[str, Any] | None:
    """验证令牌便捷函数"""
    return security_manager.verify_token(token, token_type)


def extract_user_from_token(token: str) -> dict[str, Any] | None:
    """从令牌提取用户信息便捷函数"""
    return security_manager.extract_user_from_token(token)
