"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: permission.py
@DateTime: 2025/01/01
@Docs: 权限数据访问层
"""

from typing import Any
from uuid import UUID

from app.dao.base import BaseDAO
from app.models.permission import Permission
from app.utils.logger import logger


class PermissionDAO(BaseDAO[Permission]):
    """权限数据访问层"""

    def __init__(self):
        super().__init__(Permission)

    async def get_by_permission_code(self, permission_code: str) -> Permission | None:
        """根据权限编码获取权限"""
        try:
            return await self.model.get_or_none(permission_code=permission_code, is_deleted=False)
        except Exception as e:
            logger.error(f"根据编码获取权限失败: {e}")
            return None

    async def get_by_permission_codes(self, permission_codes: list[str]) -> list[Permission]:
        """根据权限编码列表获取权限"""
        try:
            return await self.model.filter(permission_code__in=permission_codes, is_deleted=False).all()
        except Exception as e:
            logger.error(f"批量获取权限失败: {e}")
            return []

    async def get_by_permission_type(self, permission_type: str) -> list[Permission]:
        """根据权限类型获取权限"""
        try:
            return (
                await self.model.filter(permission_type=permission_type, is_active=True, is_deleted=False)
                .order_by("permission_name")
                .all()
            )
        except Exception as e:
            logger.error(f"根据类型获取权限失败: {e}")
            return []

    async def check_code_exists(self, code: str, exclude_id: UUID | None = None) -> bool:
        """检查权限编码是否已存在"""
        try:
            filters = {"permission_code": code, "is_deleted": False}
            if exclude_id:
                filters["id__not"] = exclude_id
            return await self.model.filter(**filters).exists()
        except Exception as e:
            logger.error(f"检查权限编码是否存在失败: {e}")
            return False

    async def search_permissions(
        self, keyword: str | None = None, permission_type: str | None = None, is_active: bool | None = None
    ) -> list[Permission]:
        """搜索权限"""
        try:
            filters: dict[str, Any] = {"is_deleted": False}

            if permission_type:
                filters["permission_type"] = permission_type
            if is_active is not None:
                filters["is_active"] = is_active

            queryset = self.model.filter(**filters)

            if keyword:
                queryset = queryset.filter(permission_name__icontains=keyword)

            return await queryset.order_by("permission_name").all()
        except Exception as e:
            logger.error(f"搜索权限失败: {e}")
            return []

    async def get_permissions_with_relations(self) -> list[Permission]:
        """获取所有权限及其关联的角色和用户"""
        try:
            permissions, _ = await self.get_paginated_with_related(
                page=1,
                page_size=10000,  # 设置足够大的页面大小获取所有记录
                prefetch_related=["roles", "users"],
                is_active=True,
                is_deleted=False,
            )
            return permissions
        except Exception as e:
            logger.error(f"获取权限及关联信息失败: {e}")
            return []
