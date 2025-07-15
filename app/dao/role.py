"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: role.py
@DateTime: 2025/01/01
@Docs: 角色数据访问层
"""

from uuid import UUID

from app.dao.base import BaseDAO
from app.models.role import Role
from app.utils.logger import logger


class RoleDAO(BaseDAO[Role]):
    """角色数据访问层"""

    def __init__(self):
        super().__init__(Role)

    async def get_by_role_code(self, role_code: str) -> Role | None:
        """根据角色编码获取角色"""
        try:
            return await self.model.get_or_none(role_code=role_code, is_deleted=False)
        except Exception as e:
            logger.error(f"根据编码获取角色失败: {e}")
            return None

    async def get_by_role_codes(self, role_codes: list[str]) -> list[Role]:
        """根据角色编码列表获取角色"""
        try:
            return await self.model.filter(role_code__in=role_codes, is_deleted=False).all()
        except Exception as e:
            logger.error(f"批量获取角色失败: {e}")
            return []

    async def check_code_exists(self, code: str, exclude_id: UUID | None = None) -> bool:
        """检查角色编码是否已存在"""
        try:
            filters = {"role_code": code, "is_deleted": False}
            if exclude_id:
                filters["id__not"] = exclude_id
            return await self.model.filter(**filters).exists()
        except Exception as e:
            logger.error(f"检查角色编码是否存在失败: {e}")
            return False

    async def get_active_roles(self) -> list[Role]:
        """获取所有激活的角色"""
        try:
            return await self.model.filter(is_active=True, is_deleted=False).order_by("role_name").all()
        except Exception as e:
            logger.error(f"获取激活角色失败: {e}")
            return []

    async def search_roles(self, keyword: str | None = None, is_active: bool | None = None) -> list[Role]:
        """搜索角色"""
        try:
            filters = {"is_deleted": False}
            if is_active is not None:
                filters["is_active"] = is_active

            queryset = self.model.filter(**filters)

            if keyword:
                queryset = queryset.filter(role_name__icontains=keyword)

            return await queryset.order_by("role_name").all()
        except Exception as e:
            logger.error(f"搜索角色失败: {e}")
            return []

    async def activate_role(self, role_id: UUID) -> bool:
        """激活角色"""
        try:
            count = await self.model.filter(id=role_id, is_deleted=False).update(is_active=True)
            return count > 0
        except Exception as e:
            logger.error(f"激活角色失败: {e}")
            return False

    async def deactivate_role(self, role_id: UUID) -> bool:
        """停用角色"""
        try:
            count = await self.model.filter(id=role_id, is_deleted=False).update(is_active=False)
            return count > 0
        except Exception as e:
            logger.error(f"停用角色失败: {e}")
            return False

    async def set_permissions(self, role_id: UUID, permission_ids: list[UUID]) -> None:
        """
        【全量设置】角色的权限，先清空再添加。
        适用于UI保存操作。
        """
        try:
            role = await self.get_with_related(role_id, prefetch_related=["permissions"])
            if not role:
                logger.warning(f"设置权限时角色未找到: {role_id}")
                return

            from app.dao.permission import PermissionDAO

            permission_dao = PermissionDAO()
            permissions = await permission_dao.get_by_ids(permission_ids)
            await role.permissions.clear()
            if permissions:
                await role.permissions.add(*permissions)
            logger.info(f"成功为角色 '{role.role_name}' 设置了 {len(permissions)} 个权限。")
        except Exception as e:
            logger.error(f"为角色 {role_id} 设置权限失败: {e}")

    async def add_permissions(self, role_id: UUID, permission_ids: list[UUID]) -> None:
        """【增量添加】权限到角色。"""
        try:
            role = await self.get_by_id(role_id)
            if not role:
                logger.warning(f"添加权限时角色未找到: {role_id}")
                return

            from app.dao.permission import PermissionDAO

            permission_dao = PermissionDAO()
            permissions = await permission_dao.get_by_ids(permission_ids)
            if permissions:
                await role.permissions.add(*permissions)
            logger.info(f"成功为角色 '{role.role_name}' 添加了 {len(permissions)} 个权限。")
        except Exception as e:
            logger.error(f"为角色 {role_id} 添加权限失败: {e}")

    async def remove_permissions(self, role_id: UUID, permission_ids: list[UUID]) -> None:
        """从角色【移除】权限。"""
        try:
            role = await self.get_by_id(role_id)
            if not role:
                logger.warning(f"移除权限时角色未找到: {role_id}")
                return

            from app.dao.permission import PermissionDAO

            permission_dao = PermissionDAO()
            permissions = await permission_dao.get_by_ids(permission_ids)
            if permissions:
                await role.permissions.remove(*permissions)
            logger.info(f"成功从角色 '{role.role_name}' 移除了 {len(permissions)} 个权限。")
        except Exception as e:
            logger.error(f"从角色 {role_id} 移除权限失败: {e}")

    async def get_role_permissions(self, role_id: UUID) -> list:
        """获取角色的权限列表"""
        try:
            role = await self.get_with_related(
                id=role_id,
                prefetch_related=["permissions"],
            )
            if not role:
                logger.warning(f"获取权限时角色未找到: {role_id}")
                return []
            return list(role.permissions)
        except Exception as e:
            logger.error(f"获取角色 {role_id} 权限失败: {e}")
            return []

    # 关联查询优化方法
    async def get_roles_with_relations(self) -> list[Role]:
        """获取角色及其关联的用户和权限信息"""
        try:
            return await self.get_all_with_related(
                prefetch_related=["users", "permissions"],
            )
        except Exception as e:
            logger.error(f"获取角色及关联信息失败: {e}")
            return []

    async def get_role_with_details(self, role_id: UUID) -> Role | None:
        """获取角色详细信息"""
        try:
            return await self.get_with_related(
                id=role_id,
                prefetch_related=["users", "permissions"],
            )
        except Exception as e:
            logger.error(f"获取角色详细信息失败: {e}")
            return None

    async def get_roles_paginated_optimized(
        self, page: int = 1, page_size: int = 20, is_active: bool | None = None
    ) -> tuple[list[Role], int]:
        """分页获取角色"""
        try:
            filters = {"is_deleted": False}
            if is_active is not None:
                filters["is_active"] = is_active

            return await self.get_paginated_with_related(
                page=page,
                page_size=page_size,
                order_by=["role_name"],
                select_related=None,
                prefetch_related=["permissions"],  # 列表页通常预加载权限即可
                **filters,
            )
        except Exception as e:
            logger.error(f"分页获取角色失败: {e}")
            return [], 0
