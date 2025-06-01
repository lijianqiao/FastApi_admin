"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: config.py
@DateTime: 2025/05/29 19:41:18
@Docs: 配置管理
"""

from functools import lru_cache
from typing import Any, ClassVar  # 导入 ClassVar

from pydantic import BaseModel, Field, PostgresDsn, RedisDsn, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# 辅助函数，如果需要的话
def alias_generator(field_name: str) -> str:
    return field_name.lower()


def parse_cors(v: Any) -> list[str] | str:
    """解析 CORS 配置"""
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)


class DatabaseSettings(BaseModel):
    """数据库配置"""

    url: PostgresDsn = Field(description="数据库连接URL")
    echo: bool = Field(default=False, description="是否输出SQL语句")
    pool_size: int = Field(default=10, description="连接池大小")
    max_overflow: int = Field(default=20, description="连接池最大溢出数量")
    pool_timeout: int = Field(default=30, description="连接池超时时间")
    pool_recycle: int = Field(default=3600, description="连接回收时间")


class JWTSettings(BaseModel):
    """JWT配置"""

    jwt_secret_key: str = Field(description="JWT密钥")
    algorithm: str = Field(default="HS256", description="JWT算法")
    access_token_expire_minutes: int = Field(default=30, description="访问令牌过期时间(分钟)")
    refresh_token_expire_days: int = Field(default=7, description="刷新令牌过期时间(天)")


class AdminSettings(BaseModel):
    """管理员初始配置"""  # 修改注释，更明确其用途

    username: str = Field(description="初始管理员用户名")
    email: str = Field(description="初始管理员邮箱")
    password: str = Field(description="初始管理员密码")


class Settings(BaseSettings):
    """
    应用配置类

    通过环境变量或 .env 文件加载配置。
    """

    # Pydantic-settings V2 配置
    # env_file: 指定 .env 文件路径
    # env_file_encoding: .env 文件编码
    # case_sensitive: 环境变量名是否区分大小写 (False 表示不区分)
    # extra: 如何处理模型中未定义的额外字段 ("ignore" 表示忽略)
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        # env_prefix="APP_", # 可选: 如果你的 .env 变量都有统一前缀，例如 APP_DEBUG
        # env_nested_delimiter="__", # 可选: 如果你想通过 APP_DATABASE__URL 这样的形式加载嵌套配置
    )

    # 应用核心配置
    app_name: str = Field(default="FastAPI后台管理系统", alias="应用名称")
    app_version: str = Field(default="1.0.0", alias="应用版本")
    app_description: str = Field(default="基于 FastAPI 构建的后台管理系统 API", alias="应用描述")
    debug: bool = Field(default=False, alias="是否启用调试模式")
    secret_key: str = Field(
        default="your_default_secret_key_please_change_me_in_production",
        alias="应用全局密钥，用于敏感操作如 session cookies 等",
    )

    # 服务器配置
    server_host: str = Field(default="0.0.0.0", alias="服务器监听主机")
    server_port: int = Field(default=8000, alias="服务器监听端口")

    # API 配置
    api_v1_prefix: str = Field(default="/api/v1", alias="API v1 版本前缀")

    # 将 PROJECT_NAME 和 API_V1_STR 移到这里，使其成为 Settings 类的直接属性
    # 使用 model_config 中的 alias_generator 或直接使用 alias
    PROJECT_NAME: str = Field(default="FastAPI Admin", alias="APP_NAME")
    API_V1_STR: str = Field(default="/api/v1", alias="API_V1_PREFIX")

    # 数据库相关配置 (扁平化定义，通过 property 组合)
    database_url: PostgresDsn = Field(
        default=PostgresDsn("postgresql+asyncpg://lijianqiao:123456@localhost:5432/fastapi_admin"),
        alias="数据库连接URL (例如 postgresql+asyncpg://<username>:<password>@localhost:5432/<database_name>)",
    )
    database_echo: bool = Field(default=False, alias="是否在日志中输出执行的SQL语句")
    database_pool_size: int = Field(default=10, alias="数据库连接池的初始大小")
    database_max_overflow: int = Field(default=20, alias="数据库连接池允许超出的最大连接数")
    database_pool_timeout: int = Field(default=30, alias="从连接池获取连接的超时时间（秒）")
    database_pool_recycle: int = Field(default=3600, alias="连接在连接池中被回收的秒数")

    # JWT 相关配置 (扁平化定义，通过 property 组合)
    jwt_secret_key: str = Field(default="your_super_secret_jwt_key_change_me", alias="用于签名和验证JWT的密钥")
    jwt_algorithm: str = Field(default="HS256", alias="JWT签名算法")
    jwt_access_token_expire_minutes: int = Field(default=30, alias="访问令牌（Access Token）的有效分钟数")
    jwt_refresh_token_expire_days: int = Field(default=7, alias="刷新令牌（Refresh Token）的有效天数")

    # Redis 配置 (可选)
    redis_url: RedisDsn | None = Field(default=None, alias="Redis 连接URL (例如 redis://localhost:6379/0)")

    # 日志配置
    log_level: str = Field(default="INFO", alias="应用日志级别 (例如 DEBUG, INFO, WARNING, ERROR)")
    log_file_path: str = Field(default="logs", alias="日志文件存储路径 (相对于项目根目录)")

    # 初始管理员账户配置 (扁平化定义，通过 property 组合)
    admin_username: str = Field(default="admin", alias="系统初始化的管理员用户名")
    admin_email: str = Field(default="admin@example.com", alias="系统初始化的管理员邮箱")
    admin_password: str = Field(default="admin@123", alias="系统初始化的管理员密码 (明文，将在首次启动时哈希处理)")

    # CORS 配置
    cors_allow_credentials: bool = Field(default=True, alias="是否允许携带凭证")
    backend_cors_origins: list[str] = Field(default=["http://localhost:8000"], alias="后端允许的 CORS 来源")
    frontend_cors_origins: list[str] = Field(default=["http://localhost:8000"], alias="前端允许的 CORS 来源")
    cors_allow_methods: list[str] = Field(default=["GET", "POST", "PUT", "DELETE", "OPTIONS"], alias="允许的 HTTP 方法")
    cors_allow_headers: list[str] = Field(default=["*"], alias="允许的 HTTP 头")

    @field_validator("backend_cors_origins", "frontend_cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str] | str:
        """验证并解析CORS配置"""
        return parse_cors(v)

    @computed_field
    @property
    def cors_origins(self) -> list[str]:
        """获取所有 CORS 配置"""
        origins = []
        if isinstance(self.backend_cors_origins, list):
            origins.extend(self.backend_cors_origins)
        if isinstance(self.frontend_cors_origins, list):
            origins.extend(self.frontend_cors_origins)
        return [str(origin).rstrip("/") for origin in origins]

    @property
    def database(self) -> DatabaseSettings:
        """获取结构化的数据库配置"""
        return DatabaseSettings(
            url=self.database_url,
            echo=self.database_echo,
            pool_size=self.database_pool_size,
            max_overflow=self.database_max_overflow,
            pool_timeout=self.database_pool_timeout,
            pool_recycle=self.database_pool_recycle,
        )

    @property
    def jwt(self) -> JWTSettings:
        """获取结构化的JWT配置"""
        return JWTSettings(
            jwt_secret_key=self.jwt_secret_key,
            algorithm=self.jwt_algorithm,
            access_token_expire_minutes=self.jwt_access_token_expire_minutes,
            refresh_token_expire_days=self.jwt_refresh_token_expire_days,
        )

    @property
    def admin(self) -> AdminSettings:
        """获取结构化的初始管理员配置"""
        return AdminSettings(
            username=self.admin_username,
            email=self.admin_email,
            password=self.admin_password,
        )


@lru_cache
def get_settings() -> Settings:
    """
    获取应用配置的单例实例.

    使用 lru_cache 确保配置只从环境变量或 .env 文件加载一次。
    """
    return Settings()


# 全局配置实例，方便在应用各处导入和使用
settings: Settings = get_settings()
