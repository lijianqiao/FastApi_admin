"""
-*- coding: utf-8 -*-
@Author: li
@Email: lijianqiao2906@live.com
@FileName: router.py
@DateTime: 2025/06/16
@Docs: 数据库路由器 (用于读写分离等高级功能)
"""

from tortoise import Model


class DatabaseRouter:
    """
    数据库路由器，用于实现读写分离等功能

    注意：这是一个示例实现，实际使用时需要根据业务需求调整
    """

    def db_for_read(self, model: type[Model]) -> str | None:
        """
        确定读操作使用的数据库

        Args:
            model: Tortoise模型类

        Returns:
            数据库连接名称，None表示使用默认连接
        """
        # 示例：可以根据模型类型或其他条件选择不同的数据库
        # if model._meta.app == "user_models":
        #     return "user_db_read"
        return None

    def db_for_write(self, model: type[Model]) -> str | None:
        """
        确定写操作使用的数据库

        Args:
            model: Tortoise模型类

        Returns:
            数据库连接名称，None表示使用默认连接
        """
        # 示例：写操作通常使用主数据库
        return None
