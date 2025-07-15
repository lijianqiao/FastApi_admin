"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: test_permissions.py
@DateTime: 2025/07/08
@Docs: 权限系统快速测试
"""

import asyncio

from app.core.permissions.config import get_permission_config
from app.core.permissions.decorators import get_permission_registry, register_permission
from app.utils.logger import logger


async def test_permission_config():
    """测试权限配置"""
    logger.info("测试权限配置...")

    config = get_permission_config()

    # 测试基本功能
    groups = config.get_permission_groups()
    logger.info(f"权限分组数: {len(groups)}")

    all_perms = config.get_all_permissions_from_groups()
    logger.info(f"配置权限数: {len(all_perms)}")

    default_roles = config.get_default_roles()
    logger.info(f"默认角色: {list(default_roles.keys())}")

    # 测试权限验证
    valid_perm = "user:read"
    invalid_perm = "invalid_format"

    logger.info(f"'{valid_perm}' 格式验证: {config.validate_permission_code(valid_perm)}")
    logger.info(f"'{invalid_perm}' 格式验证: {config.validate_permission_code(invalid_perm)}")


async def test_permission_registry():
    """测试权限注册"""
    logger.info("测试权限注册...")

    # 注册测试权限
    register_permission("test:read", "测试读取", "test", "read")
    register_permission("test:write", "测试写入", "test", "write")

    registry = get_permission_registry()
    logger.info(f"注册权限数: {len(registry)}")

    for code in registry.keys():
        logger.info(f"注册权限: {code}")


async def main():
    """主测试函数"""
    logger.info("开始权限系统测试...")

    await test_permission_config()
    await test_permission_registry()

    logger.info("权限系统测试完成")


if __name__ == "__main__":
    asyncio.run(main())
