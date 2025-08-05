"""批量操作服务层 - 提供事务安全的批量操作.

@Author: li
@Email: lijianqiao2906@live.com
@FileName: batch_service.py
@DateTime: 2025/07/08
@Docs: 批量操作服务层，提供事务安全的批量处理功能
"""

import asyncio
from typing import Any
from uuid import UUID

from tortoise.transactions import in_transaction

from app.core.exceptions import DatabaseTransactionException
from app.dao.user import UserDAO
from app.schemas.user import UserUpdateRequest
from app.services.user import UserService
from app.utils.deps import OperationContext
from app.utils.logger import logger


class BatchService:
    """批量操作服务，提供事务安全的批量处理功能."""

    def __init__(self):
        self.user_dao = UserDAO()
        self.user_service = UserService()

    async def batch_update_user_status(
        self, user_ids: list[UUID], is_active: bool, operation_context: OperationContext
    ) -> dict[str, Any]:
        """批量更新用户状态（事务安全）.

        Args:
            user_ids: 用户ID列表
            is_active: 激活状态
            operation_context: 操作上下文

        Returns:
            dict[str, Any]: 操作结果统计

        Raises:
            DatabaseTransactionException: 当事务失败时
        """
        if not user_ids:
            return {"success_count": 0, "failed_count": 0, "total_count": 0}

        success_count = 0
        failed_count = 0
        failed_users = []

        try:
            async with in_transaction():
                for user_id in user_ids:
                    try:
                        user = await self.user_dao.get_by_id(user_id)
                        if not user:
                            failed_count += 1
                            failed_users.append({"user_id": str(user_id), "reason": "用户不存在"})
                            continue

                        update_request = UserUpdateRequest(is_active=is_active, version=user.version)
                        await self.user_service.update_user(user_id, update_request, operation_context)
                        success_count += 1
                    except Exception as e:
                        failed_count += 1
                        failed_users.append({"user_id": str(user_id), "reason": str(e)})
                        logger.error(f"更新用户 {user_id} 状态失败: {e}")

            logger.info(f"批量更新用户状态完成: 成功 {success_count}, 失败 {failed_count}")
            return {
                "success_count": success_count,
                "failed_count": failed_count,
                "total_count": len(user_ids),
                "failed_users": failed_users,
            }

        except Exception as e:
            logger.error(f"批量更新用户状态事务失败: {e}")
            raise DatabaseTransactionException(f"批量更新用户状态失败: {str(e)}") from e

    async def batch_assign_user_roles(
        self, user_ids: list[UUID], role_ids: list[UUID], operation_context: OperationContext
    ) -> dict[str, Any]:
        """批量分配用户角色（事务安全）.

        Args:
            user_ids: 用户ID列表
            role_ids: 角色ID列表
            operation_context: 操作上下文

        Returns:
            dict[str, Any]: 操作结果统计

        Raises:
            DatabaseTransactionException: 当事务失败时
        """
        if not user_ids or not role_ids:
            return {"success_count": 0, "failed_count": 0, "total_count": 0}

        success_count = 0
        failed_count = 0
        failed_users = []

        try:
            async with in_transaction():
                for user_id in user_ids:
                    try:
                        await self.user_service.assign_roles(user_id, role_ids, operation_context)
                        success_count += 1
                    except Exception as e:
                        failed_count += 1
                        failed_users.append({"user_id": str(user_id), "reason": str(e)})
                        logger.error(f"为用户 {user_id} 分配角色失败: {e}")

            logger.info(f"批量分配用户角色完成: 成功 {success_count}, 失败 {failed_count}")
            return {
                "success_count": success_count,
                "failed_count": failed_count,
                "total_count": len(user_ids),
                "failed_users": failed_users,
            }

        except Exception as e:
            logger.error(f"批量分配用户角色事务失败: {e}")
            raise DatabaseTransactionException(f"批量分配用户角色失败: {str(e)}") from e

    async def batch_add_user_roles(
        self, user_ids: list[UUID], role_ids: list[UUID], operation_context: OperationContext
    ) -> dict[str, Any]:
        """批量添加用户角色（事务安全）.

        Args:
            user_ids: 用户ID列表
            role_ids: 角色ID列表
            operation_context: 操作上下文

        Returns:
            dict[str, Any]: 操作结果统计

        Raises:
            DatabaseTransactionException: 当事务失败时
        """
        if not user_ids or not role_ids:
            return {"success_count": 0, "failed_count": 0, "total_count": 0}

        success_count = 0
        failed_count = 0
        failed_users = []

        try:
            async with in_transaction():
                for user_id in user_ids:
                    try:
                        await self.user_service.add_user_roles(user_id, role_ids, operation_context)
                        success_count += 1
                    except Exception as e:
                        failed_count += 1
                        failed_users.append({"user_id": str(user_id), "reason": str(e)})
                        logger.error(f"为用户 {user_id} 添加角色失败: {e}")

            logger.info(f"批量添加用户角色完成: 成功 {success_count}, 失败 {failed_count}")
            return {
                "success_count": success_count,
                "failed_count": failed_count,
                "total_count": len(user_ids),
                "failed_users": failed_users,
            }

        except Exception as e:
            logger.error(f"批量添加用户角色事务失败: {e}")
            raise DatabaseTransactionException(f"批量添加用户角色失败: {str(e)}") from e

    async def batch_remove_user_roles(
        self, user_ids: list[UUID], role_ids: list[UUID], operation_context: OperationContext
    ) -> dict[str, Any]:
        """批量移除用户角色（事务安全）.

        Args:
            user_ids: 用户ID列表
            role_ids: 角色ID列表
            operation_context: 操作上下文

        Returns:
            dict[str, Any]: 操作结果统计

        Raises:
            DatabaseTransactionException: 当事务失败时
        """
        if not user_ids or not role_ids:
            return {"success_count": 0, "failed_count": 0, "total_count": 0}

        success_count = 0
        failed_count = 0
        failed_users = []

        try:
            async with in_transaction():
                for user_id in user_ids:
                    try:
                        await self.user_service.remove_user_roles(user_id, role_ids, operation_context)
                        success_count += 1
                    except Exception as e:
                        failed_count += 1
                        failed_users.append({"user_id": str(user_id), "reason": str(e)})
                        logger.error(f"从用户 {user_id} 移除角色失败: {e}")

            logger.info(f"批量移除用户角色完成: 成功 {success_count}, 失败 {failed_count}")
            return {
                "success_count": success_count,
                "failed_count": failed_count,
                "total_count": len(user_ids),
                "failed_users": failed_users,
            }

        except Exception as e:
            logger.error(f"批量移除用户角色事务失败: {e}")
            raise DatabaseTransactionException(f"批量移除用户角色失败: {str(e)}") from e

    async def batch_assign_user_permissions(
        self, user_ids: list[UUID], permission_ids: list[UUID], operation_context: OperationContext
    ) -> dict[str, Any]:
        """批量分配用户权限（事务安全）.

        Args:
            user_ids: 用户ID列表
            permission_ids: 权限ID列表
            operation_context: 操作上下文

        Returns:
            dict[str, Any]: 操作结果统计

        Raises:
            DatabaseTransactionException: 当事务失败时
        """
        if not user_ids or not permission_ids:
            return {"success_count": 0, "failed_count": 0, "total_count": 0}

        success_count = 0
        failed_count = 0
        failed_users = []

        try:
            async with in_transaction():
                for user_id in user_ids:
                    try:
                        await self.user_service.add_user_permissions(user_id, permission_ids, operation_context)
                        success_count += 1
                    except Exception as e:
                        failed_count += 1
                        failed_users.append({"user_id": str(user_id), "reason": str(e)})
                        logger.error(f"为用户 {user_id} 分配权限失败: {e}")

            logger.info(f"批量分配用户权限完成: 成功 {success_count}, 失败 {failed_count}")
            return {
                "success_count": success_count,
                "failed_count": failed_count,
                "total_count": len(user_ids),
                "failed_users": failed_users,
            }

        except Exception as e:
            logger.error(f"批量分配用户权限事务失败: {e}")
            raise DatabaseTransactionException(f"批量分配用户权限失败: {str(e)}") from e

    async def batch_process_with_concurrency(
        self, items: list[Any], processor_func, max_concurrent: int = 5, batch_size: int = 100
    ) -> dict[str, Any]:
        """并发批量处理（带并发控制）.

        Args:
            items: 待处理的项目列表
            processor_func: 处理函数
            max_concurrent: 最大并发数
            batch_size: 批次大小

        Returns:
            dict[str, Any]: 处理结果统计
        """
        if not items:
            return {"success_count": 0, "failed_count": 0, "total_count": 0}

        success_count = 0
        failed_count = 0
        failed_items = []

        # 创建信号量控制并发数
        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_item(item):
            nonlocal success_count, failed_count
            async with semaphore:
                try:
                    await processor_func(item)
                    success_count += 1
                except Exception as e:
                    failed_count += 1
                    failed_items.append({"item": str(item), "reason": str(e)})
                    logger.error(f"处理项目 {item} 失败: {e}")

        # 分批处理以避免内存问题
        for i in range(0, len(items), batch_size):
            batch_items = items[i : i + batch_size]
            tasks = [process_item(item) for item in batch_items]
            await asyncio.gather(*tasks, return_exceptions=True)

        logger.info(f"并发批量处理完成: 成功 {success_count}, 失败 {failed_count}")
        return {
            "success_count": success_count,
            "failed_count": failed_count,
            "total_count": len(items),
            "failed_items": failed_items,
        }
