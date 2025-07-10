"""
-*- coding: utf-8 -*-
@Author: li
@Email: lijianqiao2906@live.com
@FileName: config.py
@DateTime: 2025/03/08 04:30:00
@Docs: 应用程序配置管理
"""

from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用程序配置类"""

    # 模型配置
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",  # 嵌套变量分隔符
        case_sensitive=True,  # 环境变量区分大小写
        extra="ignore",  # 忽略额外字段
    )

    # 应用配置
    APP_NAME: str = Field(default="")
    APP_VERSION: str = Field(default="0.1.0")
    APP_DESCRIPTION: str = Field(default="基于FastAPI的网络设备监控系统")
    API_PREFIX: str = Field(default="/api")
    DEBUG: bool = Field(default=False)

    # 服务器配置
    HOST: str = Field(default="127.0.0.1")
    PORT: int = Field(default=8000)

    # 运行环境
    ENVIRONMENT: str = "development"

    @property
    def IS_PRODUCTION(self) -> bool:
        """判断是否为生产环境"""
        return self.ENVIRONMENT.lower() == "production"

    @property
    def IS_DEVELOPMENT(self) -> bool:
        """判断是否为开发环境"""
        return self.ENVIRONMENT.lower() == "development"

    @property
    def IS_TESTING(self) -> bool:
        """判断是否为测试环境"""
        return self.ENVIRONMENT.lower() == "testing"

    @property
    def IS_DEBUG(self) -> bool:
        """判断是否为调试模式"""
        return self.DEBUG or self.IS_DEVELOPMENT

    @property
    def IS_LOCAL(self) -> bool:
        """判断是否为本地环境"""
        return self.ENVIRONMENT.lower() in ("development", "local")

    # 项目根目录
    BASE_DIR: Path = Path(__file__).parent.parent.parent

    # CORS配置
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str]:
        """验证CORS配置

        Args:
            v: CORS配置值

        Returns:
            处理后的CORS配置列表
        """
        if isinstance(v, str):
            if not v:
                return []
            if not v.startswith("["):
                return [i.strip() for i in v.split(",") if i.strip()]
            # 处理JSON格式的字符串
            import json

            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [v]
        elif isinstance(v, list):
            return v
        return []

    # 安全配置
    SECRET_KEY: str = "your-secret-key"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080
    ALGORITHM: str = Field(default="HS256")
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # 数据库配置
    DB_HOST: str = Field(default="localhost")
    DB_PORT: int = Field(default=5432)
    DB_USER: str = Field(default="")
    DB_PASSWORD: SecretStr = Field(default=SecretStr(""))
    DB_NAME: str = Field(default="")
    DB_POOL_MAX: int = Field(default=20)
    DB_POOL_MIN: int = Field(default=1)
    DB_POOL_CONN_LIFE: int = Field(default=500)
    DB_CONNECTION_TIMEOUT: int = Field(default=10)

    @property
    def TORTOISE_ORM_CONFIG(self) -> dict[str, Any]:
        """获取Tortoise ORM配置

        Returns:
            Dict[str, Any]: Tortoise ORM配置字典
        """
        return {
            "connections": {
                "default": {
                    "engine": "tortoise.backends.asyncpg",
                    "credentials": {
                        "host": self.DB_HOST,
                        "port": self.DB_PORT,
                        "user": self.DB_USER,
                        "password": self.DB_PASSWORD.get_secret_value(),
                        "database": self.DB_NAME,
                        "minsize": self.DB_POOL_MIN,
                        "maxsize": self.DB_POOL_MAX,
                        "max_inactive_connection_lifetime": self.DB_POOL_CONN_LIFE,
                        "timeout": self.DB_CONNECTION_TIMEOUT,
                        # 增加一些有用的连接选项
                        "server_settings": {
                            "application_name": self.APP_NAME,
                        },
                    },
                }
            },
            "apps": {
                "models": {
                    "models": ["app.models", "aerich.models"],
                    "default_connection": "default",
                }
            },
            "use_tz": False,
            "timezone": "Asia/Shanghai",
            # 生产环境建议设置
            "routers": ["app.db.router"] if not self.DEBUG else [],
        }

    # Redis配置（用于缓存）
    REDIS_HOST: str = Field(default="localhost")
    REDIS_PORT: int = Field(default=6379)
    REDIS_PASSWORD: SecretStr | None = None
    REDIS_DB: int = Field(default=0)

    @property
    def REDIS_URI(self) -> str:
        """获取Redis URI

        Returns:
            str: Redis连接URI
        """
        if self.REDIS_PASSWORD:
            return (
                f"redis://:{self.REDIS_PASSWORD.get_secret_value()}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
            )
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # 日志配置
    LOG_LEVEL: str = Field(default="INFO")

    # API文档配置
    ENABLE_DOCS: bool = Field(default=True)

    # 性能配置
    ENABLE_GZIP: bool = Field(default=True)
    GZIP_MINIMUM_SIZE: int = Field(default=1000)

    # 安全配置
    ALLOWED_HOSTS: list[str] = []
    ENABLE_HTTPS_REDIRECT: bool = Field(default=False)
    ENABLE_TRUSTED_HOST: bool = Field(default=False)
    RATE_LIMIT_PER_MINUTE: int = Field(default=60)

    # 监控配置
    ENABLE_METRICS: bool = Field(default=True)
    METRICS_PATH: str = Field(default="/metrics")
    ENABLE_REQUEST_TRACKING: bool = Field(default=True)
    ENABLE_PERFORMANCE_MONITORING: bool = Field(default=True)

    # 超级管理员配置
    SUPERUSER_USERNAME: str = Field(default="admin")
    SUPERUSER_PASSWORD: str = Field(default="Admin@123")
    SUPERUSER_PHONE: str = Field(default="13800000000")
    SUPERUSER_NICKNAME: str = Field(default="系统管理员")

    @field_validator("ALLOWED_HOSTS", mode="before")
    @classmethod
    def assemble_allowed_hosts(cls, v: str | list[str]) -> list[str]:
        """验证允许的主机配置"""
        if isinstance(v, str):
            if not v:
                return []
            if not v.startswith("["):
                return [i.strip() for i in v.split(",") if i.strip()]
            # 处理JSON格式的字符串
            import json

            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [v]
        elif isinstance(v, list):
            return v
        return []

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """验证SECRET_KEY不为空"""
        if not v:
            raise ValueError("Secret_key不能为空")
        if len(v) < 32:
            raise ValueError("Secret_key必须至少32个字符长")
        return v

    @field_validator("DB_USER", "DB_NAME")
    @classmethod
    def validate_db_required_fields(cls, v: str) -> str:
        """验证数据库必填字段"""
        if not v:
            raise ValueError("数据库配置字段一定不能为空")
        return v


@lru_cache
def get_settings() -> Settings:
    """
    获取应用配置的单例实例

    使用 lru_cache 确保配置只从环境变量或 .env 文件加载一次。
    """
    return Settings()


# 创建全局设置实例
settings = get_settings()
