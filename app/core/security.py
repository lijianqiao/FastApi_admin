"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: security.py
@DateTime: 2025/06/04 10:07:04
@Docs: 安全相关工具函数

提供密码哈希、JWT令牌生成和验证等安全功能。
"""

from datetime import datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError
from passlib.context import CryptContext

from app.config import settings
from app.exceptions import (
    InvalidTokenError,
    TokenExpiredError,
)

# 密码哈希上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """
    生成密码哈希值

    Args:
        password: 明文密码

    Returns:
        哈希后的密码
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码

    Args:
        plain_password: 明文密码
        hashed_password: 哈希密码

    Returns:
        验证结果
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """
    创建访问令牌

    Args:
        data: 要编码的数据
        expires_delta: 过期时间增量

    Returns:
        JWT访问令牌
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt.access_token_expire_minutes)

    to_encode.update({"exp": expire, "type": "access"})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt.secret_key,
        algorithm=settings.jwt.algorithm,
    )

    return encoded_jwt


def create_refresh_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """
    创建刷新令牌

    Args:
        data: 要编码的数据
        expires_delta: 过期时间增量

    Returns:
        JWT刷新令牌
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.jwt.refresh_token_expire_days)

    to_encode.update({"exp": expire, "type": "refresh"})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt.refresh_secret_key,
        algorithm=settings.jwt.algorithm,
    )

    return encoded_jwt


def decode_token_for_refresh(token: str) -> dict[str, Any]:
    """
    解码刷新令牌

    Args:
        token: JWT刷新令牌

    Returns:
        解码后的数据

    Raises:
        TokenExpiredError: 令牌已过期
        InvalidTokenError: 无效令牌
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt.refresh_secret_key,
            algorithms=[settings.jwt.algorithm],
        )

        # 检查令牌类型
        token_type = payload.get("type")
        if token_type != "refresh":
            raise InvalidTokenError("刷新令牌")

        return payload

    except ExpiredSignatureError as e:
        raise TokenExpiredError("刷新令牌") from e
    except JWTError as e:
        raise InvalidTokenError("刷新令牌") from e


def decode_access_token(token: str) -> dict[str, Any]:
    """
    解码访问令牌

    Args:
        token: JWT访问令牌

    Returns:
        解码后的数据

    Raises:
        TokenExpiredError: 令牌已过期
        InvalidTokenError: 无效令牌
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt.secret_key,
            algorithms=[settings.jwt.algorithm],
        )

        # 检查令牌类型
        token_type = payload.get("type")
        if token_type != "access":
            raise InvalidTokenError("访问令牌")

        return payload
    except ExpiredSignatureError as e:
        raise TokenExpiredError("访问令牌") from e
    except JWTError as e:
        raise InvalidTokenError("访问令牌") from e
        raise InvalidTokenError("访问令牌") from e


def generate_token_pair(user_data: dict[str, Any]) -> dict[str, str]:
    """
    生成令牌对（访问令牌 + 刷新令牌）

    Args:
        user_data: 用户数据

    Returns:
        包含access_token和refresh_token的字典
    """
    access_token = create_access_token(data=user_data)
    refresh_token = create_refresh_token(data=user_data)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }
