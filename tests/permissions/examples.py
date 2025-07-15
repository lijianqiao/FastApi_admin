"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: examples.py
@DateTime: 2025/07/08
@Docs: 权限系统使用示例
"""

from uuid import UUID

from app.core.permissions import (
    cache_with_ttl,
    clear_all_permission_cache,
    get_cache_stats,
    invalidate_role_cache,
    invalidate_user_cache,
    permission_required,
    require_all_permissions,
    require_any_permission,
    require_role,
)
from app.core.permissions.initializer import create_permission_initializer
from app.utils.logger import logger


class PermissionExamples:
    """权限系统使用示例"""

    def __init__(self):
        self.initializer = create_permission_initializer()

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
        return {
            "code": role_code,
            "name": "示例角色",
            "permissions": ["user:read", "menu:read"],
        }

    # 缓存失效示例
    @invalidate_user_cache("user_123")
    async def update_user_permissions(self, user_id: str, permissions: list[str]):
        """更新用户权限 - 自动清除相关缓存"""
        logger.info(f"更新用户 {user_id} 权限: {permissions}")
        # 模拟权限更新
        return {"message": "权限更新成功"}

    @invalidate_role_cache("admin")
    async def update_role_permissions(self, role_code: str, permissions: list[str]):
        """更新角色权限 - 自动清除相关缓存"""
        logger.info(f"更新角色 {role_code} 权限: {permissions}")
        # 模拟权限更新
        return {"message": "角色权限更新成功"}

    # 权限清理示例
    async def cleanup_permissions_example(self):
        """权限清理示例"""
        logger.info("开始权限清理检查...")

        # 试运行模式，不实际删除
        result = await self.initializer.cleanup_permissions(dry_run=True)

        logger.info("权限清理检查结果:")
        logger.info(f"  总权限数: {result['total_permissions']}")
        logger.info(f"  未使用权限: {len(result['unused_permissions'])}")
        logger.info(f"  无效权限: {len(result['invalid_permissions'])}")
        logger.info(f"  孤立权限: {len(result['orphaned_permissions'])}")

        # 如果需要实际清理，设置 dry_run=False
        # cleanup_result = await self.initializer.cleanup_permissions(dry_run=False)

        return result

    # 缓存管理示例
    async def cache_management_example(self):
        """缓存管理示例"""
        logger.info("缓存管理示例...")

        # 获取缓存统计
        stats = await get_cache_stats()
        logger.info(f"缓存统计: {stats}")

        # 清除特定用户的缓存
        # await invalidate_user_cache("user_123")

        # 清除特定角色的缓存
        # await invalidate_role_cache("admin")

        # 清除所有权限缓存
        clear_result = await clear_all_permission_cache()
        logger.info(f"缓存清理结果: {clear_result}")

        return {
            "stats_before": stats,
            "clear_result": clear_result,
        }

    # 权限初始化示例
    async def permission_initialization_example(self, app=None):
        """权限初始化示例"""
        logger.info("权限系统初始化示例...")

        # 检查初始化状态
        status = await self.initializer.get_initialization_status()
        logger.info(f"当前初始化状态: {status}")

        # 如果未完全初始化，执行初始化
        if not status.get("is_fully_initialized", False):
            logger.info("执行权限系统初始化...")

            init_result = await self.initializer.initialize_permissions(
                app=app,
                sync_from_app=True,
                sync_from_modules=True,
                module_paths=["app.api.v1"],
                create_default_roles=True,
                create_superuser=True,
            )

            logger.info(f"初始化结果: {init_result}")
            return init_result
        else:
            logger.info("权限系统已完全初始化")
            return status


# 使用示例函数
async def run_examples():
    """运行所有示例（需要数据库连接）"""
    try:
        # 初始化数据库连接
        from app.db.connection import init_database

        await init_database()
        logger.info("数据库连接初始化成功")

        examples = PermissionExamples()

        # 权限清理示例
        await examples.cleanup_permissions_example()

        # 缓存管理示例
        await examples.cache_management_example()

        # 权限初始化示例
        await examples.permission_initialization_example()

    except ImportError as e:
        logger.error(f"导入数据库模块失败: {e}")
        logger.info("请使用 examples_standalone.py 进行无数据库的示例演示")
    except Exception as e:
        logger.error(f"运行示例失败: {e}")
        logger.info("请确保数据库配置正确，或使用 examples_standalone.py")


async def run_examples_without_db():
    """运行无需数据库的示例"""
    from .examples_standalone import run_standalone_examples

    await run_standalone_examples()


if __name__ == "__main__":
    import asyncio

    # 首先尝试运行无数据库版本
    print("运行权限系统独立示例（无需数据库）...")
    asyncio.run(run_examples_without_db())
