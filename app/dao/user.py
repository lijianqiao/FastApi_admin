"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: user.py
@DateTime: 2025/01/01
@Docs: 用户数据访问层
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from tortoise.expressions import Q

from app.dao.base import BaseDAO
from app.models.user import User
from app.utils.logger import logger


class UserDAO(BaseDAO[User]):
    """用户数据访问层"""

    def __init__(self):
        super().__init__(User)

    async def get_by_username(self, username: str) -> User | None:
        """根据用户名获取用户"""
        try:
            return await self.model.get_or_none(username=username, is_deleted=False)
        except Exception as e:
            logger.error(f"根据用户名获取用户失败: {e}")
            return None

    async def get_by_phone(self, phone: str) -> User | None:
        """根据手机号获取用户"""
        try:
            return await self.model.get_or_none(phone=phone, is_deleted=False)
        except Exception as e:
            logger.error(f"根据手机号获取用户失败: {e}")
            return None

    async def get_by_username_or_phone(self, identifier: str) -> User | None:
        """根据用户名或手机号获取用户"""
        try:
            return await self.model.filter(Q(username=identifier) | Q(phone=identifier), is_deleted=False).first()
        except Exception as e:
            logger.error(f"根据用户名或手机号获取用户失败: {e}")
            return None

    async def check_username_exists(self, username: str, exclude_id: UUID | None = None) -> bool:
        """检查用户名是否已存在"""
        try:
            query = Q(username=username, is_deleted=False)
            if exclude_id:
                query &= ~Q(id=exclude_id)
            return await self.model.filter(query).exists()
        except Exception as e:
            logger.error(f"检查用户名是否存在失败: {e}")
            return False

    async def check_phone_exists(self, phone: str, exclude_id: UUID | None = None) -> bool:
        """检查手机号是否已存在"""
        try:
            query = Q(phone=phone, is_deleted=False)
            if exclude_id:
                query &= ~Q(id=exclude_id)
            return await self.model.filter(query).exists()
        except Exception as e:
            logger.error(f"检查手机号是否存在失败: {e}")
            return False

    async def get_active_users(self) -> list[User]:
        """获取所有激活的用户"""
        try:
            return await self.model.filter(is_active=True, is_deleted=False).all()
        except Exception as e:
            logger.error(f"获取激活用户失败: {e}")
            return []

    async def get_superusers(self) -> list[User]:
        """获取所有超级管理员"""
        try:
            return await self.model.filter(is_superuser=True, is_deleted=False).all()
        except Exception as e:
            logger.error(f"获取超级管理员失败: {e}")
            return []

    async def search_users(
        self, keyword: str | None = None, is_active: bool | None = None, role_code: str | None = None
    ) -> list[User]:
        """搜索用户"""
        try:
            query = Q(is_deleted=False)

            if is_active is not None:
                query &= Q(is_active=is_active)

            # 关键词搜索（用户名、昵称、手机号）
            if keyword:
                keyword_query = (
                    Q(username__icontains=keyword) | Q(nickname__icontains=keyword) | Q(phone__icontains=keyword)
                )
                query &= keyword_query

            # 角色筛选
            if role_code:
                query &= Q(roles__role_code=role_code)

            return await self.model.filter(query).all()
        except Exception as e:
            logger.error(f"搜索用户失败: {e}")
            return []

    async def update_last_login(self, user_id: UUID, login_time: datetime | None = None) -> bool:
        """更新用户最后登录时间"""
        try:
            if login_time is None:
                login_time = datetime.now()

            count = await self.model.filter(id=user_id).update(last_login_at=login_time)
            return count > 0
        except Exception as e:
            logger.error(f"更新用户最后登录时间失败: {e}")
            return False

    async def activate_user(self, user_id: UUID) -> bool:
        """激活用户"""
        try:
            count = await self.model.filter(id=user_id, is_deleted=False).update(is_active=True)
            return count > 0
        except Exception as e:
            logger.error(f"激活用户失败: {e}")
            return False

    async def deactivate_user(self, user_id: UUID) -> bool:
        """停用用户"""
        try:
            count = await self.model.filter(id=user_id, is_deleted=False).update(is_active=False)
            return count > 0
        except Exception as e:
            logger.error(f"停用用户失败: {e}")
            return False

    async def update_user_settings(self, user_id: UUID, settings: dict[str, Any]) -> bool:
        """更新用户配置"""
        try:
            count = await self.model.filter(id=user_id, is_deleted=False).update(user_settings=settings)
            return count > 0
        except Exception as e:
            logger.error(f"更新用户配置失败: {e}")
            return False

    async def count_by_role(self, role_code: str) -> int:
        """统计指定角色的用户数量"""
        try:
            return await self.model.filter(roles__role_code=role_code, is_deleted=False).count()
        except Exception as e:
            logger.error(f"统计角色用户数量失败: {e}")
            return 0

    async def get_recently_login_users(self, days: int = 7) -> list[User]:
        """获取最近登录的用户"""
        try:
            from datetime import timedelta

            cutoff_time = datetime.now() - timedelta(days=days)

            return (
                await self.model.filter(last_login_at__gte=cutoff_time, is_deleted=False)
                .order_by("-last_login_at")
                .all()
            )
        except Exception as e:
            logger.error(f"获取最近登录用户失败: {e}")
            return []

    # 关联查询优化示例
    async def get_users_with_logs(self, limit: int = 50) -> list[User]:
        """获取用户及其相关数据（关联查询优化）"""
        try:
            return await self.get_all_with_related(
                prefetch_related=["roles", "permissions"],  # 预加载角色和权限
                is_deleted=False,
            )
        except Exception as e:
            logger.error(f"获取用户及相关数据失败: {e}")
            return []

    async def get_user_with_details(self, user_id: UUID) -> User | None:
        """获取用户详细信息（包含关联数据）"""
        try:
            return await self.get_with_related(
                id=user_id,
                prefetch_related=["roles__permissions", "permissions", "operation_logs"],  # 预加载关联数据
            )
        except Exception as e:
            logger.error(f"获取用户详细信息失败: {e}")
            return None

    async def get_user_ids_by_role_id(self, role_id: UUID) -> list[UUID]:
        """根据角色ID获取用户ID列表"""
        try:
            # This is a more ORM-friendly way than raw SQL
            users = await self.model.filter(roles__id=role_id).values_list("id", flat=True)
            return [user_id for (user_id,) in users]
        except Exception as e:
            logger.error(f"根据角色ID获取用户ID列表失败: {e}")
            return []

    async def get_user_ids_by_role(self, role_id: UUID) -> list[UUID]:
        """根据角色ID获取用户ID列表"""
        # 这是一个用于性能的原始 SQL 查询，因为 ORM 对于多对多筛选可能很复杂。
        conn = self.model._meta.db
        query = 'SELECT user_id FROM "user_roles" WHERE role_id = $1'
        results = await conn.execute_query_dict(query, [role_id])
        return [row["user_id"] for row in results]

    # 用户-角色关系管理
    async def set_user_roles(self, user_id: UUID, role_ids: list[UUID]) -> None:
        """
        【全量设置】用户的角色，先清空再添加。
        适用于UI保存操作。
        """
        try:
            user = await self.get_by_id(user_id)
            if not user:
                logger.warning(f"设置角色时用户未找到: {user_id}")
                return

            from app.dao.role import RoleDAO

            role_dao = RoleDAO()
            roles = await role_dao.get_by_ids(role_ids)
            await user.roles.clear()
            if roles:
                await user.roles.add(*roles)
            logger.info(f"成功为用户 '{user.username}' 设置了 {len(roles)} 个角色。")
        except Exception as e:
            logger.error(f"为用户 {user_id} 设置角色失败: {e}")

    async def add_user_roles(self, user_id: UUID, role_ids: list[UUID]) -> None:
        """【增量添加】角色到用户。"""
        try:
            user = await self.get_by_id(user_id)
            if not user:
                logger.warning(f"添加角色时用户未找到: {user_id}")
                return

            from app.dao.role import RoleDAO

            role_dao = RoleDAO()
            roles = await role_dao.get_by_ids(role_ids)
            if roles:
                await user.roles.add(*roles)
            logger.info(f"成功为用户 '{user.username}' 添加了 {len(roles)} 个角色。")
        except Exception as e:
            logger.error(f"为用户 {user_id} 添加角色失败: {e}")

    async def remove_user_roles(self, user_id: UUID, role_ids: list[UUID]) -> None:
        """从用户【移除】角色。"""
        try:
            user = await self.get_by_id(user_id)
            if not user:
                logger.warning(f"移除角色时用户未找到: {user_id}")
                return

            from app.dao.role import RoleDAO

            role_dao = RoleDAO()
            roles = await role_dao.get_by_ids(role_ids)
            if roles:
                await user.roles.remove(*roles)
            logger.info(f"成功从用户 '{user.username}' 移除了 {len(roles)} 个角色。")
        except Exception as e:
            logger.error(f"从用户 {user_id} 移除角色失败: {e}")

    async def get_user_roles(self, user_id: UUID) -> list:
        """获取用户的角色列表"""
        try:
            user = await self.get_with_related(
                id=user_id,
                prefetch_related=["roles"],
            )
            if not user:
                logger.warning(f"获取角色时用户未找到: {user_id}")
                return []
            return list(user.roles)
        except Exception as e:
            logger.error(f"获取用户 {user_id} 角色失败: {e}")
            return []

    # 用户-权限关系管理
    async def set_user_permissions(self, user_id: UUID, permission_ids: list[UUID]) -> None:
        """
        【全量设置】用户的权限，先清空再添加。
        适用于UI保存操作。
        """
        try:
            user = await self.get_by_id(user_id)
            if not user:
                logger.warning(f"设置权限时用户未找到: {user_id}")
                return

            from app.dao.permission import PermissionDAO

            permission_dao = PermissionDAO()
            permissions = await permission_dao.get_by_ids(permission_ids)
            await user.permissions.clear()
            if permissions:
                await user.permissions.add(*permissions)
            logger.info(f"成功为用户 '{user.username}' 设置了 {len(permissions)} 个权限。")
        except Exception as e:
            logger.error(f"为用户 {user_id} 设置权限失败: {e}")

    async def add_user_permissions(self, user_id: UUID, permission_ids: list[UUID]) -> None:
        """【增量添加】权限到用户。"""
        try:
            user = await self.get_by_id(user_id)
            if not user:
                logger.warning(f"添加权限时用户未找到: {user_id}")
                return

            from app.dao.permission import PermissionDAO

            permission_dao = PermissionDAO()
            permissions = await permission_dao.get_by_ids(permission_ids)
            if permissions:
                await user.permissions.add(*permissions)
            logger.info(f"成功为用户 '{user.username}' 添加了 {len(permissions)} 个权限。")
        except Exception as e:
            logger.error(f"为用户 {user_id} 添加权限失败: {e}")

    async def remove_user_permissions(self, user_id: UUID, permission_ids: list[UUID]) -> None:
        """从用户【移除】权限。"""
        try:
            user = await self.get_by_id(user_id)
            if not user:
                logger.warning(f"移除权限时用户未找到: {user_id}")
                return

            from app.dao.permission import PermissionDAO

            permission_dao = PermissionDAO()
            permissions = await permission_dao.get_by_ids(permission_ids)
            if permissions:
                await user.permissions.remove(*permissions)
            logger.info(f"成功从用户 '{user.username}' 移除了 {len(permissions)} 个权限。")
        except Exception as e:
            logger.error(f"从用户 {user_id} 移除权限失败: {e}")

    async def get_user_permissions(self, user_id: UUID) -> list:
        """获取用户的权限列表"""
        try:
            user = await self.get_with_related(
                id=user_id,
                prefetch_related=["permissions"],
            )
            if not user:
                logger.warning(f"获取权限时用户未找到: {user_id}")
                return []
            return list(user.permissions)
        except Exception as e:
            logger.error(f"获取用户 {user_id} 权限失败: {e}")
            return []
