"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: examples_standalone.py
@DateTime: 2025/07/08
@Docs: 权限系统独立使用示例（无需数据库连接）
"""

import asyncio
from uuid import UUID, uuid4

from app.core.permissions import (
    cache_with_ttl,
    clear_all_permission_cache,
    get_cache_stats,
    permission_required,
    require_all_permissions,
    require_any_permission,
    require_role,
)
from app.core.permissions.config import get_permission_config
from app.core.permissions.decorators import get_permission_registry, register_permission
from app.utils.logger import logger


class StandalonePermissionExamples:
    """权限系统独立使用示例（无需数据库）"""

    def __init__(self):
        pass

    # 装饰器使用示例
    @permission_required("user:create", "创建用户权限")
    async def create_user_endpoint(self, user_data: dict, current_user: dict):
        """创建用户接口 - 需要单一权限"""
        logger.info(f"用户 {current_user['username']} 创建新用户")
        return {"message": "用户创建成功"}

    @require_role("admin", "管理员角色")
    async def admin_only_endpoint(self, current_user: dict):
        """管理员专用接口"""
        logger.info(f"管理员 {current_user['username']} 访问管理功能")
        return {"message": "管理员功能访问成功"}

    @require_any_permission(["user:read", "user:admin"], "查看用户权限或用户管理权限")
    async def view_users_endpoint(self, current_user: dict):
        """查看用户列表 - 需要任一权限"""
        logger.info(f"用户 {current_user['username']} 查看用户列表")
        return {"message": "用户列表获取成功"}

    @require_all_permissions(["user:update", "role:assign"], "更新用户和分配角色权限")
    async def update_user_role_endpoint(self, user_id: str, role_data: dict, current_user: dict):
        """更新用户角色 - 需要所有权限"""
        logger.info(f"用户 {current_user['username']} 更新用户角色")
        return {"message": "用户角色更新成功"}

    # 缓存装饰器使用示例
    @cache_with_ttl(ttl=1800, key_prefix="user_profile:")
    async def get_user_profile(self, user_id: UUID) -> dict:
        """获取用户资料 - 30分钟缓存"""
        logger.info(f"从数据库加载用户资料: {user_id}")
        # 模拟数据库查询
        await asyncio.sleep(0.1)  # 模拟查询时间
        return {
            "id": str(user_id),
            "username": "example_user",
            "email": "user@example.com",
            "roles": ["user"],
            "permissions": ["user:read", "menu:read"],
        }

    @cache_with_ttl(ttl=3600, key_prefix="role_info:", include_args=True)
    async def get_role_info(self, role_code: str) -> dict:
        """获取角色信息 - 1小时缓存"""
        logger.info(f"从数据库加载角色信息: {role_code}")
        await asyncio.sleep(0.1)  # 模拟查询时间
        return {
            "code": role_code,
            "name": "示例角色",
            "permissions": ["user:read", "menu:read"],
        }

    # 权限配置示例
    async def permission_config_example(self):
        """权限配置示例"""
        logger.info("权限配置示例...")

        config = get_permission_config()

        # 获取权限分组
        groups = config.get_permission_groups()
        logger.info(f"权限分组数量: {len(groups)}")

        # 获取所有权限
        all_permissions = config.get_all_permissions_from_groups()
        logger.info(f"配置文件中的权限总数: {len(all_permissions)}")

        # 获取默认角色
        default_roles = config.get_default_roles()
        logger.info(f"默认角色: {list(default_roles.keys())}")

        # 获取角色权限
        admin_permissions = config.get_role_permissions("admin")
        logger.info(f"管理员权限数量: {len(admin_permissions)}")

        return {
            "groups_count": len(groups),
            "permissions_count": len(all_permissions),
            "default_roles": list(default_roles.keys()),
            "admin_permissions_count": len(admin_permissions),
        }

    # 权限注册示例
    async def permission_registry_example(self):
        """权限注册示例"""
        logger.info("权限注册示例...")

        # 手动注册一些权限
        register_permission("test:read", "测试读取权限", "test", "read", "测试模块")
        register_permission("test:write", "测试写入权限", "test", "write", "测试模块")

        # 获取注册的权限
        registry = get_permission_registry()
        logger.info(f"当前注册的权限数量: {len(registry)}")

        for code, info in registry.items():
            logger.info(f"权限: {code} - {info.get('description', 'N/A')}")

        return {
            "registered_permissions": len(registry),
            "permissions": list(registry.keys()),
        }

    # 缓存管理示例
    async def cache_management_example(self):
        """缓存管理示例"""
        logger.info("缓存管理示例...")

        # 先调用一些缓存方法来产生缓存数据
        user_id = uuid4()
        await self.get_user_profile(user_id)
        await self.get_role_info("admin")

        # 获取缓存统计
        stats = await get_cache_stats()
        logger.info(f"缓存统计: {stats}")

        # 再次调用相同方法，应该从缓存获取
        logger.info("第二次调用（应该从缓存获取）...")
        await self.get_user_profile(user_id)
        await self.get_role_info("admin")

        # 清除所有权限缓存
        clear_result = await clear_all_permission_cache()
        logger.info(f"缓存清理结果: {clear_result}")

        # 再次获取统计
        stats_after = await get_cache_stats()
        logger.info(f"清理后缓存统计: {stats_after}")

        return {
            "stats_before": stats,
            "clear_result": clear_result,
            "stats_after": stats_after,
        }

    # 权限验证示例
    async def permission_validation_example(self):
        """权限验证示例"""
        logger.info("权限验证示例...")

        config = get_permission_config()

        # 测试权限格式验证
        valid_permissions = ["user:read", "role:create", "menu:update"]
        invalid_permissions = ["invalid_format", "user", "role:"]

        validation_results = {}

        for perm in valid_permissions:
            is_valid = config.validate_permission_code(perm)
            validation_results[perm] = is_valid
            logger.info(f"权限 '{perm}' 格式检查: {'有效' if is_valid else '无效'}")

        for perm in invalid_permissions:
            is_valid = config.validate_permission_code(perm)
            validation_results[perm] = is_valid
            logger.info(f"权限 '{perm}' 格式检查: {'有效' if is_valid else '无效'}")

        return validation_results


# 使用示例函数
async def run_standalone_examples():
    """运行所有独立示例"""
    examples = StandalonePermissionExamples()

    logger.info("=" * 50)
    logger.info("开始权限系统独立示例演示")
    logger.info("=" * 50)

    # 权限配置示例
    config_result = await examples.permission_config_example()
    logger.info(f"配置示例结果: {config_result}")

    logger.info("-" * 30)

    # 权限注册示例
    registry_result = await examples.permission_registry_example()
    logger.info(f"注册示例结果: {registry_result}")

    logger.info("-" * 30)

    # 缓存管理示例
    cache_result = await examples.cache_management_example()
    logger.info(f"缓存示例结果: {cache_result}")

    logger.info("-" * 30)

    # 权限验证示例
    validation_result = await examples.permission_validation_example()
    logger.info(f"验证示例结果: {validation_result}")

    logger.info("=" * 50)
    logger.info("权限系统独立示例演示完成")
    logger.info("=" * 50)


if __name__ == "__main__":
    asyncio.run(run_standalone_examples())
