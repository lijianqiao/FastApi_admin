"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: user.py
@DateTime: 2025/01/01
@Docs: 用户模型
"""

from tortoise import fields

from app.models.base import BaseModel


class User(BaseModel):
    """
    用户模型
    """

    # 基础信息
    username = fields.CharField(max_length=100, unique=True, description="用户名")
    password_hash = fields.CharField(max_length=255, description="密码哈希")
    phone = fields.CharField(max_length=20, unique=True, description="手机号")
    nickname = fields.CharField(max_length=100, null=True, description="昵称")
    avatar_url = fields.CharField(max_length=500, null=True, description="头像URL")
    bio = fields.TextField(null=True, description="个人简介")

    # 状态
    is_active = fields.BooleanField(default=True, description="是否激活")
    is_superuser = fields.BooleanField(default=False, description="是否超级管理员")

    # 时间戳
    last_login_at = fields.DatetimeField(null=True, description="最后登录时间")

    # 配置
    user_settings = fields.JSONField(default=dict, description="用户个性化配置")

    # 关联关系
    roles = fields.ManyToManyField("models.Role", related_name="users", through="user_role")
    permissions = fields.ManyToManyField("models.Permission", related_name="users", through="user_permission")

    # 描述字段
    description = fields.TextField(null=True, description="描述")

    class Meta:  # type: ignore
        table = "users"
        table_description = "用户表"
        indexes = [
            ("username",),
            ("phone",),
            ("is_active",),
            ("is_superuser",),
            ("last_login_at",),
            ("created_at",),
            # 复合索引优化
            ("is_active", "is_superuser"),
            ("last_login_at", "is_active"),
        ]

    def __str__(self) -> str:
        return self.username
