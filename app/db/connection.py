"""
-*- coding: utf-8 -*-
@Author: li
@Email: lijianqiao2906@live.com
@FileName: connection.py
@DateTime: 2025/03/12 13:47:49
@Docs: 数据库连接配置，主要供 Aerich 等迁移工具使用
"""

from tortoise import Tortoise

from app.core.config import settings
from app.utils.logger import logger

# 导出 Tortoise ORM 配置，供 Aerich 等迁移工具使用
TORTOISE_ORM = settings.TORTOISE_ORM_CONFIG


async def init_database() -> None:
    """初始化数据库连接"""
    try:
        logger.info("正在初始化数据库连接...")
        await Tortoise.init(config=dict(TORTOISE_ORM))
        logger.info("数据库连接初始化成功")
    except Exception as e:
        logger.error(f"数据库连接初始化失败: {e}")
        raise


async def close_database() -> None:
    """关闭数据库连接"""
    try:
        logger.info("正在关闭数据库连接...")
        await Tortoise.close_connections()
        logger.info("数据库连接已关闭")
    except Exception as e:
        logger.error(f"关闭数据库连接失败: {e}")


async def generate_schemas() -> None:
    """生成数据库表结构 (仅用于开发环境)

    警告: 生产环境请使用 Aerich 进行数据库迁移管理
    """
    try:
        logger.info("正在生成数据库表结构...")
        await Tortoise.generate_schemas()
        logger.info("数据库表结构生成成功")
    except Exception as e:
        logger.error(f"生成数据库表结构失败: {e}")
        raise


async def check_database_connection() -> bool:
    """检查数据库连接状态

    Returns:
        bool: 连接成功返回True，否则返回False
    """
    try:
        await init_database()
        # 执行简单查询测试连接
        from tortoise import connections

        conn = connections.get("default")
        await conn.execute_query("SELECT 1")
        await close_database()
        logger.info("数据库连接测试成功")
        return True
    except Exception as e:
        logger.error(f"数据库连接测试失败: {e}")
        return False
