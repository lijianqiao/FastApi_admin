"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: permission.py
@DateTime: 2025/01/01
@Docs: 权限模型
"""

from tortoise import fields

from app.models.base import BaseModel


class Permission(BaseModel):
    """
    权限模型
    """

    # 权限信息
    permission_name = fields.CharField(max_length=100, description="权限名称")
    permission_code = fields.CharField(max_length=255, unique=True, description="权限编码")
    permission_type = fields.CharField(max_length=50, description="权限类型（如: module, button）")
    is_active = fields.BooleanField(default=True, description="是否激活")

    # 描述字段
    description = fields.TextField(null=True, description="描述")

    class Meta:  # type: ignore
        table = "permissions"
        table_description = "权限表"
        indexes = [
            ("permission_code",),
            ("permission_type",),
            ("is_active",),
            # 复合索引优化
            ("permission_type", "is_active"),
            ("is_active", "permission_type"),
        ]

    def __str__(self) -> str:
        return self.permission_name
