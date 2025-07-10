"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: permission_init.py
@DateTime: 2025/07/10
@Docs: 权限系统初始化脚本 - 自动创建权限和角色数据
"""

import asyncio
from collections.abc import Sequence

from app.core.permissions.simple_decorators import Permissions
from app.dao.permission import PermissionDAO
from app.dao.role import RoleDAO
from app.models.permission import Permission
from app.models.role import Role
from app.utils.logger import logger


class PermissionInitializer:
    """权限系统初始化器"""

    def __init__(self):
        self.permission_dao = PermissionDAO()
        self.role_dao = RoleDAO()

    async def initialize_permissions(self) -> None:
        """初始化权限数据"""
        # 定义权限数据 - 基于 Permissions 类的常量
        permissions_data = [
            # 用户管理权限
            {
                "permission_name": "创建用户",
                "permission_code": Permissions.USER_CREATE,
                "permission_type": "api",
                "description": "创建新用户的权限",
            },
            {
                "permission_name": "查看用户",
                "permission_code": Permissions.USER_READ,
                "permission_type": "api",
                "description": "查看用户信息的权限",
            },
            {
                "permission_name": "更新用户",
                "permission_code": Permissions.USER_UPDATE,
                "permission_type": "api",
                "description": "更新用户信息的权限",
            },
            {
                "permission_name": "删除用户",
                "permission_code": Permissions.USER_DELETE,
                "permission_type": "api",
                "description": "删除用户的权限",
            },
            {
                "permission_name": "分配用户角色",
                "permission_code": Permissions.USER_ASSIGN_ROLES,
                "permission_type": "api",
                "description": "给用户分配角色的权限",
            },
            {
                "permission_name": "分配用户权限",
                "permission_code": Permissions.USER_ASSIGN_PERMISSIONS,
                "permission_type": "api",
                "description": "给用户分配权限的权限",
            },
            {
                "permission_name": "用户模块访问",
                "permission_code": Permissions.USER_ACCESS,
                "permission_type": "module",
                "description": "访问用户管理模块的权限",
            },
            # 角色管理权限
            {
                "permission_name": "创建角色",
                "permission_code": Permissions.ROLE_CREATE,
                "permission_type": "api",
                "description": "创建新角色的权限",
            },
            {
                "permission_name": "查看角色",
                "permission_code": Permissions.ROLE_READ,
                "permission_type": "api",
                "description": "查看角色信息的权限",
            },
            {
                "permission_name": "更新角色",
                "permission_code": Permissions.ROLE_UPDATE,
                "permission_type": "api",
                "description": "更新角色信息的权限",
            },
            {
                "permission_name": "删除角色",
                "permission_code": Permissions.ROLE_DELETE,
                "permission_type": "api",
                "description": "删除角色的权限",
            },
            {
                "permission_name": "分配角色权限",
                "permission_code": Permissions.ROLE_ASSIGN_PERMISSIONS,
                "permission_type": "api",
                "description": "给角色分配权限的权限",
            },
            {
                "permission_name": "角色模块访问",
                "permission_code": Permissions.ROLE_ACCESS,
                "permission_type": "module",
                "description": "访问角色管理模块的权限",
            },
            # 权限管理权限
            {
                "permission_name": "创建权限",
                "permission_code": Permissions.PERMISSION_CREATE,
                "permission_type": "api",
                "description": "创建新权限的权限",
            },
            {
                "permission_name": "查看权限",
                "permission_code": Permissions.PERMISSION_READ,
                "permission_type": "api",
                "description": "查看权限信息的权限",
            },
            {
                "permission_name": "更新权限",
                "permission_code": Permissions.PERMISSION_UPDATE,
                "permission_type": "api",
                "description": "更新权限信息的权限",
            },
            {
                "permission_name": "删除权限",
                "permission_code": Permissions.PERMISSION_DELETE,
                "permission_type": "api",
                "description": "删除权限的权限",
            },
            {
                "permission_name": "权限模块访问",
                "permission_code": Permissions.PERMISSION_ACCESS,
                "permission_type": "module",
                "description": "访问权限管理模块的权限",
            },
            # 日志管理权限
            {
                "permission_name": "查看日志",
                "permission_code": Permissions.LOG_VIEW,
                "permission_type": "api",
                "description": "查看操作日志的权限",
            },
            {
                "permission_name": "删除日志",
                "permission_code": Permissions.LOG_DELETE,
                "permission_type": "api",
                "description": "删除操作日志的权限",
            },
            {
                "permission_name": "日志模块访问",
                "permission_code": Permissions.LOG_ACCESS,
                "permission_type": "module",
                "description": "访问日志管理模块的权限",
            },
            # 系统管理权限
            {
                "permission_name": "系统配置",
                "permission_code": Permissions.SYSTEM_CONFIG,
                "permission_type": "api",
                "description": "修改系统配置的权限",
            },
            {
                "permission_name": "系统管理",
                "permission_code": Permissions.SYSTEM_ADMIN,
                "permission_type": "api",
                "description": "系统管理员权限",
            },
        ]

        # 批量创建权限
        created_count = 0
        for perm_data in permissions_data:
            existing_permission = await self.permission_dao.get_by_permission_code(perm_data["permission_code"])
            if not existing_permission:
                await self.permission_dao.create(**perm_data)
                created_count += 1
                logger.info(f"创建权限: {perm_data['permission_name']} ({perm_data['permission_code']})")
            else:
                logger.debug(f"权限已存在: {existing_permission.permission_name}")

        logger.info(f"权限初始化完成，共创建 {created_count} 个新权限。")

    async def initialize_roles(self):
        """初始化角色数据"""
        # 定义角色数据
        roles_data = [
            {
                "role_name": "超级管理员",
                "role_code": "super_admin",
                "description": "系统超级管理员，拥有所有权限",
                "permissions": "all",  # 特殊标记，表示拥有所有权限
            },
            {
                "role_name": "管理员",
                "role_code": "admin",
                "description": "系统管理员，拥有大部分权限",
                "permissions": [
                    Permissions.USER_ACCESS,
                    Permissions.USER_READ,
                    Permissions.USER_CREATE,
                    Permissions.USER_UPDATE,
                    Permissions.USER_ASSIGN_ROLES,
                    Permissions.ROLE_ACCESS,
                    Permissions.ROLE_READ,
                    Permissions.ROLE_CREATE,
                    Permissions.ROLE_UPDATE,
                    Permissions.ROLE_ASSIGN_PERMISSIONS,
                    Permissions.PERMISSION_ACCESS,
                    Permissions.PERMISSION_READ,
                    Permissions.LOG_ACCESS,
                    Permissions.LOG_VIEW,
                ],
            },
            {
                "role_name": "用户管理员",
                "role_code": "user_admin",
                "description": "用户管理员，负责用户管理",
                "permissions": [
                    Permissions.USER_ACCESS,
                    Permissions.USER_READ,
                    Permissions.USER_CREATE,
                    Permissions.USER_UPDATE,
                    Permissions.USER_ASSIGN_ROLES,
                ],
            },
            {
                "role_name": "只读用户",
                "role_code": "readonly",
                "description": "只读用户，只能查看数据",
                "permissions": [
                    Permissions.USER_ACCESS,
                    Permissions.USER_READ,
                    Permissions.ROLE_ACCESS,
                    Permissions.ROLE_READ,
                    Permissions.PERMISSION_ACCESS,
                    Permissions.PERMISSION_READ,
                    Permissions.LOG_ACCESS,
                    Permissions.LOG_VIEW,
                ],
            },
        ]

        # 批量创建角色
        created_count = 0
        for role_data in roles_data:
            existing_role = await self.role_dao.get_by_role_code(role_data["role_code"])
            if not existing_role:
                # 创建角色
                role_create_data = {
                    "role_name": role_data["role_name"],
                    "role_code": role_data["role_code"],
                    "description": role_data["description"],
                }
                role = await self.role_dao.create(**role_create_data)

                # 检查角色是否成功创建
                if not role:
                    logger.warning(f"创建角色失败，跳过权限分配: {role_data['role_name']}")
                    continue

                created_count += 1
                logger.info(f"创建角色: {role.role_name} ({role.role_code})")

                # 分配权限
                await self._assign_role_permissions(role, role_data["permissions"])
            else:
                logger.debug(f"角色已存在: {existing_role.role_name}")

        logger.info(f"角色初始化完成，共创建 {created_count} 个新角色。")

    async def _assign_role_permissions(self, role: Role, permissions: str | list[str]) -> None:
        """为角色分配权限"""
        if permissions == "all":
            # 分配所有权限
            all_permissions: Sequence[Permission] = await self.permission_dao.get_all()
            if all_permissions:
                await self.role_dao.set_permissions(role.id, [p.id for p in all_permissions])
                logger.info(f"为角色 '{role.role_name}' 分配了所有权限。")
        elif isinstance(permissions, list) and permissions:
            # 优化：一次性获取所有需要的权限
            perms_to_assign: Sequence[Permission] = await self.permission_dao.model.filter(
                permission_code__in=permissions
            ).all()
            missing_perms = set(permissions) - {p.permission_code for p in perms_to_assign}
            if missing_perms:
                logger.warning(f"以下权限未找到，无法分配给角色 '{role.role_name}': {', '.join(missing_perms)}")

            if perms_to_assign:
                permission_ids = [p.id for p in perms_to_assign]
                await self.role_dao.set_permissions(role.id, permission_ids)
                logger.info(f"为角色 '{role.role_name}' 分配了 {len(permission_ids)} 个权限。")

    async def initialize_all(self) -> None:
        """初始化所有权限系统数据"""
        logger.info("--- 开始初始化权限系统 ---")

        # 1. 初始化权限
        await self.initialize_permissions()

        # 2. 初始化角色并分配权限
        await self.initialize_roles()

        logger.info("--- 权限系统初始化完成 ---")


# 提供便捷的初始化函数
async def init_permission_system():
    """初始化权限系统的便捷函数"""
    initializer = PermissionInitializer()
    await initializer.initialize_all()


# 如果直接运行此脚本，则执行初始化
if __name__ == "__main__":
    asyncio.run(init_permission_system())
