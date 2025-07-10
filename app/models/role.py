"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: role.py
@DateTime: 2025/01/01
@Docs: 角色模型
"""

from tortoise import fields

from app.models.base import BaseModel


class Role(BaseModel):
    """
    角色模型
    """

    # 角色信息
    role_name = fields.CharField(max_length=100, unique=True, description="角色名称")
    role_code = fields.CharField(max_length=100, unique=True, description="角色编码")
    is_active = fields.BooleanField(default=True, description="是否激活")

    # 关联关系
    permissions = fields.ManyToManyField("models.Permission", related_name="roles", through="role_permission")

    # 描述字段
    description = fields.TextField(null=True, description="描述")

    class Meta:  # type: ignore
        table = "roles"
        table_description = "角色表"
        indexes = [
            ("role_name",),
            ("role_code",),
            ("is_active",),
            # 复合索引优化
            ("is_active", "role_name"),
        ]

    def __str__(self) -> str:
        return self.role_name
