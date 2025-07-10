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
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = settings.REFRESH_TOKEN_EXPIRE_DAYS

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

        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
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
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str, token_type: str = "access") -> dict[str, Any] | None:
        """验证并解码JWT令牌"""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
            )

            # 检查令牌类型
            if payload.get("type") != token_type:
                raise UnauthorizedException(detail=f"令牌类型错误: 期望{token_type}类型") from None

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
