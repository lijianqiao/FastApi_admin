"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: batch_operations.py
@DateTime: 2025/07/08
@Docs: 批量操作工具类，提供高性能的数据库批量处理
"""

import asyncio
from collections.abc import Callable
from typing import Any
from uuid import UUID

from app.utils.logger import logger


class BatchProcessor:
    """批量处理器，用于优化大数据量的数据库操作"""

    def __init__(self, batch_size: int = 1000, max_concurrent: int = 3):
        """
        初始化批量处理器

        Args:
            batch_size: 每批次处理的记录数
            max_concurrent: 最大并发批次数
        """
        self.batch_size = batch_size
        self.max_concurrent = max_concurrent

    async def process_in_batches(
        self,
        data: list[Any],
        processor: Callable[[list[Any]], Any],
        description: str = "批量处理",
    ) -> list[Any]:
        """
        分批处理数据

        Args:
            data: 待处理的数据列表
            processor: 处理函数，接收一个批次的数据
            description: 处理描述，用于日志

        Returns:
            处理结果列表
        """
        if not data:
            return []

        total_batches = (len(data) + self.batch_size - 1) // self.batch_size
        results = []

        logger.info(f"开始{description}: 总计 {len(data)} 条记录，分 {total_batches} 批处理")

        # 使用信号量控制并发数
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def process_batch(batch_data: list[Any], batch_num: int) -> Any:
            async with semaphore:
                try:
                    logger.debug(f"{description}进度: {batch_num}/{total_batches}, 本批次: {len(batch_data)} 条")
                    return await processor(batch_data)
                except Exception as e:
                    logger.error(f"{description}批次 {batch_num} 失败: {e}")
                    return None

        # 创建批次任务
        tasks = []
        for i in range(0, len(data), self.batch_size):
            batch_data = data[i : i + self.batch_size]
            batch_num = i // self.batch_size + 1
            task = process_batch(batch_data, batch_num)
            tasks.append(task)

        # 并发执行批次
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)

        # 收集结果
        for result in batch_results:
            if result is not None and not isinstance(result, Exception):
                if isinstance(result, list):
                    results.extend(result)
                else:
                    results.append(result)

        logger.info(f"{description}完成: 成功处理 {len(results)} 条记录")
        return results

    async def bulk_create_with_retry(
        self,
        dao,
        objects_data: list[dict[str, Any]],
        max_retries: int = 3,
        ignore_conflicts: bool = False,
    ) -> list[Any]:
        """
        带重试的批量创建

        Args:
            dao: DAO对象
            objects_data: 对象数据列表
            max_retries: 最大重试次数
            ignore_conflicts: 是否忽略冲突

        Returns:
            创建的对象列表
        """
        if not objects_data:
            return []

        async def process_batch(batch_data: list[dict[str, Any]]) -> list[Any]:
            for attempt in range(max_retries):
                try:
                    if ignore_conflicts:
                        return await dao.bulk_create_ignore_conflicts(batch_data)
                    else:
                        return await dao.bulk_create(batch_data)
                except Exception as e:
                    if attempt == max_retries - 1:
                        logger.error(f"批量创建最终失败: {e}")
                        raise
                    else:
                        logger.warning(f"批量创建重试 {attempt + 1}/{max_retries}: {e}")
                        await asyncio.sleep(0.1 * (attempt + 1))  # 指数退避
            return []

        return await self.process_in_batches(objects_data, process_batch, "批量创建")

    async def bulk_update_with_retry(
        self,
        dao,
        updates: list[dict[str, Any]],
        id_field: str = "id",
        max_retries: int = 3,
    ) -> int:
        """
        带重试的批量更新

        Args:
            dao: DAO对象
            updates: 更新数据列表
            id_field: ID字段名
            max_retries: 最大重试次数

        Returns:
            更新的记录数
        """
        if not updates:
            return 0

        total_updated = 0

        async def process_batch(batch_data: list[dict[str, Any]]) -> int:
            nonlocal total_updated
            for attempt in range(max_retries):
                try:
                    count = await dao.bulk_update_optimized(batch_data, id_field, len(batch_data))
                    total_updated += count
                    return count
                except Exception as e:
                    if attempt == max_retries - 1:
                        logger.error(f"批量更新最终失败: {e}")
                        raise
                    else:
                        logger.warning(f"批量更新重试 {attempt + 1}/{max_retries}: {e}")
                        await asyncio.sleep(0.1 * (attempt + 1))
            return 0

        await self.process_in_batches(updates, process_batch, "批量更新")
        return total_updated

    async def bulk_soft_delete_with_retry(
        self,
        dao,
        ids: list[UUID],
        max_retries: int = 3,
    ) -> int:
        """
        带重试的批量软删除

        Args:
            dao: DAO对象
            ids: ID列表
            max_retries: 最大重试次数

        Returns:
            删除的记录数
        """
        if not ids:
            return 0

        total_deleted = 0

        async def process_batch(batch_ids: list[UUID]) -> int:
            nonlocal total_deleted
            for attempt in range(max_retries):
                try:
                    count = await dao.bulk_soft_delete_optimized(batch_ids, len(batch_ids))
                    total_deleted += count
                    return count
                except Exception as e:
                    if attempt == max_retries - 1:
                        logger.error(f"批量软删除最终失败: {e}")
                        raise
                    else:
                        logger.warning(f"批量软删除重试 {attempt + 1}/{max_retries}: {e}")
                        await asyncio.sleep(0.1 * (attempt + 1))
            return 0

        await self.process_in_batches(ids, process_batch, "批量软删除")
        return total_deleted

    def configure(self, batch_size: int | None = None, max_concurrent: int | None = None):
        """
        配置批量处理器参数

        Args:
            batch_size: 批次大小
            max_concurrent: 最大并发数
        """
        if batch_size is not None:
            self.batch_size = max(1, batch_size)
        if max_concurrent is not None:
            self.max_concurrent = max(1, max_concurrent)

        logger.info(f"批量处理器配置已更新: batch_size={self.batch_size}, max_concurrent={self.max_concurrent}")


# 全局批量处理器实例
_batch_processor = BatchProcessor()


def get_batch_processor() -> BatchProcessor:
    """获取全局批量处理器"""
    return _batch_processor


async def bulk_create_optimized(dao, objects_data: list[dict[str, Any]], ignore_conflicts: bool = False) -> list[Any]:
    """批量创建便捷函数"""
    return await _batch_processor.bulk_create_with_retry(dao, objects_data, ignore_conflicts=ignore_conflicts)


async def bulk_update_optimized(dao, updates: list[dict[str, Any]], id_field: str = "id") -> int:
    """批量更新便捷函数"""
    return await _batch_processor.bulk_update_with_retry(dao, updates, id_field)


async def bulk_soft_delete_optimized(dao, ids: list[UUID]) -> int:
    """批量软删除便捷函数"""
    return await _batch_processor.bulk_soft_delete_with_retry(dao, ids)


class BatchJobManager:
    """批量作业管理器，用于管理长时间运行的批量任务"""

    def __init__(self):
        self.active_jobs = {}
        self.job_counter = 0

    async def submit_batch_job(
        self,
        job_name: str,
        processor_func: Callable,
        data: list[Any],
        callback: Callable | None = None,
    ) -> str:
        """
        提交批量作业

        Args:
            job_name: 作业名称
            processor_func: 处理函数
            data: 数据
            callback: 完成回调函数

        Returns:
            作业ID
        """
        self.job_counter += 1
        job_id = f"{job_name}_{self.job_counter}"

        async def run_job():
            try:
                logger.info(f"批量作业开始: {job_id}")
                processor = get_batch_processor()
                result = await processor.process_in_batches(data, processor_func, job_name)

                if callback:
                    await callback(job_id, result, None)

                logger.info(f"批量作业完成: {job_id}")
            except Exception as e:
                logger.error(f"批量作业失败: {job_id}, 错误: {e}")
                if callback:
                    await callback(job_id, None, e)
            finally:
                self.active_jobs.pop(job_id, None)

        # 启动后台任务
        task = asyncio.create_task(run_job())
        self.active_jobs[job_id] = {
            "name": job_name,
            "task": task,
            "status": "running",
            "data_count": len(data),
        }

        return job_id

    def get_job_status(self, job_id: str) -> dict[str, Any] | None:
        """获取作业状态"""
        return self.active_jobs.get(job_id)

    def get_active_jobs(self) -> dict[str, dict[str, Any]]:
        """获取所有活跃作业"""
        return self.active_jobs.copy()


# 全局批量作业管理器
_batch_job_manager = BatchJobManager()


def get_batch_job_manager() -> BatchJobManager:
    """获取全局批量作业管理器"""
    return _batch_job_manager
