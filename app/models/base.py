"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: base.py
@DateTime: 2025/07/05
@Docs: 基础数据模型
"""

import uuid

from tortoise import fields
from tortoise.models import Model


class BaseModel(Model):
    """
    基础模型，所有模型的基类
    """

    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    version = fields.IntField(default=1, description="乐观锁版本号")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")
    is_deleted = fields.BooleanField(default=False, description="软删除标志")

    class Meta:  # type: ignore
        abstract = True

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id})"

    def to_dict(self, exclude_sensitive: bool = False) -> dict:
        """转换为字典，可选择排除敏感字段"""
        data = {
            "id": self.id,
            "version": self.version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

        # 在API响应中可以隐藏is_deleted字段
        if not exclude_sensitive:
            data["is_deleted"] = self.is_deleted

        return data
