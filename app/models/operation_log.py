"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: operation_log.py
@DateTime: 2025/01/01
@Docs: 操作日志模型
"""

from tortoise import fields

from app.models.base import BaseModel


class OperationLog(BaseModel):
    """
    操作日志模型 - 基础信息，用于高频查询
    """

    # 操作用户
    user = fields.ForeignKeyField(
        "models.User", related_name="operation_logs", on_delete=fields.SET_NULL, null=True, description="关联用户"
    )

    # 操作信息
    module = fields.CharField(max_length=50, description="操作模块")
    action = fields.CharField(max_length=50, description="操作类型")
    resource_id = fields.CharField(max_length=255, null=True, description="资源ID")
    resource_type = fields.CharField(max_length=50, null=True, description="资源类型")

    # 请求信息
    method = fields.CharField(max_length=10, description="请求方法")
    path = fields.CharField(max_length=500, description="请求路径")
    ip_address = fields.CharField(max_length=45, description="IP地址")

    # 响应信息
    response_code = fields.IntField(description="响应码")
    response_time = fields.IntField(description="响应时间(ms)")

    # 描述字段
    description = fields.TextField(null=True, description="描述")

    class Meta:  # type: ignore
        table = "operation_logs"
        table_description = "操作日志表"
        indexes = [
            # 基础查询索引
            ("user_id",),
            ("module",),
            ("action",),
            ("resource_type",),
            ("method",),
            ("ip_address",),
            ("response_code",),
            ("response_time",),
            # 组合索引
            ("user_id", "created_at"),
            ("module", "action"),
            ("response_code", "created_at"),
            ("response_time", "created_at"),
            ("ip_address", "created_at"),
            # 时间范围查询索引（重要）
            ("created_at",),
        ]

    def __str__(self) -> str:
        # 使用 self.user.id，因为 user 是外键对象
        user_id_str = self.user.id if self.user else "N/A"
        return f"OperationLog(user_id={user_id_str}, action={self.action})"
