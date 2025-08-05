"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: permission_init.py
@DateTime: 2025/07/23
@Docs: 权限系统初始化脚本 - 智能动态权限生成系统
"""

import asyncio
import inspect
from collections.abc import Sequence
from typing import Any

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

    def _generate_permission_name(self, permission_code: str) -> str:
        """智能生成权限中文名称"""
        # 模块名称映射
        module_mapping = {
            "user": "用户",
            "role": "角色",
            "permission": "权限",
            "menu": "菜单",
            "log": "日志",
            "system": "系统",
            "admin": "后台",
            "region": "基地",
            "vendor": "厂商",
            "device": "设备",
            "query_template": "查询模板",
            "vendor_command": "厂商命令",
            "query_history": "查询历史",
            "device_config": "设备配置",
            "network_query": "网络查询",
            "import_export": "导入导出",
            "cli": "CLI",
            "statistics": "统计",
        }

        # 操作名称映射
        action_mapping = {
            "create": "创建",
            "read": "查看",
            "update": "更新",
            "delete": "删除",
            "assign_roles": "分配角色",
            "assign_permissions": "分配权限",
            "access": "模块访问",
            "view": "查看",
            "config": "配置",
            "admin": "管理",
            "write": "管理",
            "reset_password": "重置密码",
            "connection_test": "连接测试",
            "batch_operation": "批量操作",
            "activate": "激活",
            "cleanup": "清理",
            "statistics": "统计",
            "backup": "备份",
            "compare": "对比",
            "execute": "执行",
            "mac": "MAC地址查询",
            "interface": "接口状态查询",
            "custom": "自定义命令查询",
            "template_list": "查询模板列表",
            "import": "导入",
            "export": "导出",
            "device_template": "设备导入模板",
            "device_import": "设备数据导入",
            "device_export": "设备数据导出",
            "cli_access": "CLI访问",
            "cli_execute": "CLI执行",
            "cli_config": "CLI配置",
            "cli_session_manage": "CLI会话管理",
            "statistics_access": "统计模块访问",
            "statistics_read": "统计数据读取",
            "statistics_dashboard": "统计仪表板查看",
            "statistics_api_stats": "API统计查看",
            "statistics_user_stats": "用户统计查看",
            "statistics_device_stats": "设备统计查看",
            "statistics_query_stats": "查询统计查看",
            "statistics_system_stats": "系统统计查看",
        }

        # 特殊权限名称覆盖（用于处理无法通过规则生成的特殊情况）
        special_permissions = {
            "user:reset_password": "重置用户密码",
            "role:assign_permissions": "分配角色权限",
            "user:assign_permissions": "分配用户权限",
            "user:assign_roles": "分配用户角色",
        }

        # 优先检查特殊权限
        if permission_code in special_permissions:
            return special_permissions[permission_code]

        # 解析权限代码，格式通常为 "module:action" 或 "module_submodule:action"
        parts = permission_code.split(":")
        if len(parts) != 2:
            # 如果格式不符合预期，返回格式化的权限代码
            return permission_code.replace("_", " ").replace(":", " ").title()

        module_part, action_part = parts

        # 获取模块名称
        module_name = module_mapping.get(module_part, module_part.replace("_", ""))

        # 获取操作名称
        action_name = action_mapping.get(action_part, action_part.replace("_", ""))

        # 生成权限名称
        if action_part == "access":
            return f"{module_name}模块访问"
        else:
            return f"{action_name}{module_name}"

    def _get_permissions_from_class(self) -> list[dict[str, Any]]:
        """智能从Permissions类生成权限数据 - 完全动态化"""
        permissions_data = []

        # 获取Permissions类的所有权限常量
        for attr_name, attr_value in inspect.getmembers(Permissions):
            if not attr_name.startswith("_") and isinstance(attr_value, str):
                # 智能生成权限名称
                permission_name = self._generate_permission_name(attr_value)

                # 确定权限类型
                permission_type = "module" if attr_value.endswith(":access") else "api"

                permission_data = {
                    "permission_name": permission_name,
                    "permission_code": attr_value,
                    "permission_type": permission_type,
                    "description": f"{permission_name}的权限",
                }
                permissions_data.append(permission_data)

        logger.debug(f"智能生成了 {len(permissions_data)} 个权限数据")
        return permissions_data

    def _get_role_definitions(self) -> list[dict[str, Any]]:
        """定义角色配置 - 简化版本"""
        return [
            {
                "role_name": "超级管理员",
                "role_code": "super_admin",
                "description": "系统超级管理员，拥有所有权限",
                "permissions": "all",
            },
            {
                "role_name": "系统管理员",
                "role_code": "admin",
                "description": "系统管理员，拥有核心管理权限",
                "permissions": [
                    Permissions.USER_ACCESS,
                    Permissions.USER_READ,
                    Permissions.USER_CREATE,
                    Permissions.USER_UPDATE,
                    Permissions.ROLE_ACCESS,
                    Permissions.ROLE_READ,
                    Permissions.ROLE_CREATE,
                    Permissions.ROLE_UPDATE,
                    Permissions.PERMISSION_ACCESS,
                    Permissions.PERMISSION_READ,
                    Permissions.LOG_ACCESS,
                    Permissions.LOG_VIEW,
                    Permissions.ADMIN_READ,
                    Permissions.ADMIN_WRITE,
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
                    Permissions.LOG_ACCESS,
                    Permissions.LOG_VIEW,
                ],
            },
        ]

    async def initialize_permissions(self) -> None:
        """智能初始化权限数据 - 从Permissions类自动生成"""
        logger.info("开始智能初始化权限数据...")

        permissions_data = self._get_permissions_from_class()

        created_count = 0
        for perm_data in permissions_data:
            existing_permission = await self.permission_dao.get_by_permission_code(perm_data["permission_code"])
            if not existing_permission:
                await self.permission_dao.create(**perm_data)
                created_count += 1
                logger.debug(f"创建权限: {perm_data['permission_name']} ({perm_data['permission_code']})")
            else:
                logger.debug(f"权限已存在: {existing_permission.permission_name}")

        logger.info(f"智能权限初始化完成，共处理 {len(permissions_data)} 个权限，新创建 {created_count} 个。")

    async def initialize_roles(self) -> None:
        """初始化角色数据 - 简化版本"""
        logger.info("开始初始化角色数据...")

        roles_data = self._get_role_definitions()

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
                logger.debug(f"创建角色: {role.role_name} ({role.role_code})")

                # 分配权限
                await self._assign_role_permissions(role, role_data["permissions"])
            else:
                logger.debug(f"角色已存在: {existing_role.role_name}")

        logger.info(f"角色初始化完成，共处理 {len(roles_data)} 个角色，新创建 {created_count} 个。")

    async def _assign_role_permissions(self, role: Role, permissions: str | list[str]) -> None:
        """为角色分配权限"""
        if permissions == "all":
            # 分配所有权限
            all_permissions: Sequence[Permission] = await self.permission_dao.get_all()
            if all_permissions:
                await self.role_dao.set_permissions(role.id, [p.id for p in all_permissions])
                logger.info(f"为角色 '{role.role_name}' 分配了所有权限 ({len(all_permissions)} 个)。")
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
        logger.info("=== 开始智能权限系统初始化 ===")

        # 1. 智能初始化权限 - 自动从Permissions类生成
        await self.initialize_permissions()

        # 2. 初始化角色并分配权限
        await self.initialize_roles()

        logger.info("=== 智能权限系统初始化完成 ===")

    async def sync_permissions(self) -> None:
        """智能同步权限 - 检查Permissions类中新增的权限"""
        logger.info("开始智能同步权限...")

        current_permissions = self._get_permissions_from_class()
        existing_codes = {p.permission_code for p in await self.permission_dao.get_all()}

        new_permissions = [p for p in current_permissions if p["permission_code"] not in existing_codes]

        if new_permissions:
            for perm_data in new_permissions:
                await self.permission_dao.create(**perm_data)
                logger.info(f"同步新权限: {perm_data['permission_name']} ({perm_data['permission_code']})")
            logger.info(f"智能权限同步完成，新增 {len(new_permissions)} 个权限。")
        else:
            logger.info("无新权限需要同步。")


# 提供便捷的初始化函数
async def init_permission_system():
    """智能初始化权限系统的便捷函数"""
    from app.db import close_database, init_database

    try:
        # 初始化数据库连接
        await init_database()
        logger.info("数据库连接初始化成功")

        # 执行权限初始化
        initializer = PermissionInitializer()
        await initializer.initialize_all()

    except Exception as e:
        logger.error(f"权限系统初始化失败: {e}")
        raise
    finally:
        # 关闭数据库连接
        await close_database()
        logger.info("数据库连接已关闭")


async def sync_permissions_only():
    """智能同步权限的便捷函数"""
    from app.db import close_database, init_database

    try:
        # 初始化数据库连接
        await init_database()
        logger.info("数据库连接初始化成功")

        # 执行权限同步
        initializer = PermissionInitializer()
        await initializer.sync_permissions()

    except Exception as e:
        logger.error(f"权限同步失败: {e}")
        raise
    finally:
        # 关闭数据库连接
        await close_database()
        logger.info("数据库连接已关闭")


# 如果直接运行此脚本，则执行初始化
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "sync":
        asyncio.run(sync_permissions_only())
    else:
        asyncio.run(init_permission_system())
