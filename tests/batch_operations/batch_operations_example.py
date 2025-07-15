"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: batch_operations_example.py
@DateTime: 2025/07/08
@Docs: 批量操作功能使用示例
"""

import asyncio
from datetime import datetime, timedelta
from uuid import uuid4

from app.dao.login_log import LoginLogDAO
from app.dao.operation_log import OperationLogDAO
from app.dao.user import UserDAO
from app.utils.batch_operations import (
    bulk_create_optimized,
    bulk_update_optimized,
    get_batch_job_manager,
    get_batch_processor,
)
from app.utils.logger import logger


async def example_bulk_create_users():
    """示例：批量创建用户"""
    user_dao = UserDAO()

    # 准备测试数据
    users_data = []
    for i in range(5000):  # 创建5000个用户
        user_data = {
            "username": f"testuser_{i}",
            "phone": f"1380000{i:04d}",
            "password_hash": "hashed_password",
            "nickname": f"用户{i}",
            "email": f"user{i}@example.com",
            "is_active": True,
        }
        users_data.append(user_data)

    logger.info("开始批量创建用户示例")
    start_time = datetime.now()

    # 使用优化的批量创建
    created_users = await bulk_create_optimized(user_dao, users_data, ignore_conflicts=True)

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    logger.info(f"批量创建用户完成: {len(created_users)} 个用户，耗时 {duration:.2f} 秒")
    return created_users


async def example_bulk_update_users():
    """示例：批量更新用户"""
    user_dao = UserDAO()

    # 获取待更新的用户
    users = await user_dao.get_all(is_active=True)
    if not users:
        logger.warning("没有找到待更新的用户")
        return

    # 准备更新数据
    updates = []
    for user in users[:1000]:  # 更新前1000个用户
        update_data = {
            "id": user.id,
            "nickname": f"更新的昵称_{datetime.now().strftime('%H%M%S')}",
            "bio": f"更新于 {datetime.now()}",
        }
        updates.append(update_data)

    logger.info("开始批量更新用户示例")
    start_time = datetime.now()

    # 使用优化的批量更新
    updated_count = await bulk_update_optimized(user_dao, updates)

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    logger.info(f"批量更新用户完成: {updated_count} 个用户，耗时 {duration:.2f} 秒")
    return updated_count


async def example_bulk_create_logs():
    """示例：批量创建日志"""
    login_log_dao = LoginLogDAO()
    operation_log_dao = OperationLogDAO()

    # 准备登录日志数据
    login_logs_data = []
    operation_logs_data = []

    base_time = datetime.now() - timedelta(days=30)
    user_id = str(uuid4())

    for i in range(10000):  # 创建10000条日志
        log_time = base_time + timedelta(minutes=i)

        # 登录日志
        login_log = {
            "user_id": user_id,
            "login_type": "password",
            "ip_address": f"192.168.1.{i % 254 + 1}",
            "location": f"城市{i % 100}",
            "device": "Chrome Browser",
            "user_agent": "Mozilla/5.0...",
            "is_success": i % 10 != 0,  # 90% 成功率
            "failure_reason": "密码错误" if i % 10 == 0 else None,
            "login_at": log_time,
            "description": f"登录记录 {i}",
        }
        login_logs_data.append(login_log)

        # 操作日志
        operation_log = {
            "user_id": user_id,
            "module": "user_management",
            "action": "view" if i % 3 == 0 else "update",
            "resource_type": "user",
            "resource_id": str(uuid4()),
            "method": "GET" if i % 3 == 0 else "POST",
            "path": f"/api/users/{i}",
            "ip_address": f"192.168.1.{i % 254 + 1}",
            "response_code": 200 if i % 20 != 0 else 404,
            "response_time": 100 + (i % 500),
            "description": f"操作记录 {i}",
        }
        operation_logs_data.append(operation_log)

    logger.info("开始批量创建日志示例")
    start_time = datetime.now()

    # 并发创建登录日志和操作日志
    login_task = bulk_create_optimized(login_log_dao, login_logs_data)
    operation_task = bulk_create_optimized(operation_log_dao, operation_logs_data)

    created_login_logs, created_operation_logs = await asyncio.gather(login_task, operation_task)

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    logger.info(
        f"批量创建日志完成: {len(created_login_logs)} 条登录日志, "
        f"{len(created_operation_logs)} 条操作日志，耗时 {duration:.2f} 秒"
    )

    return created_login_logs, created_operation_logs


async def example_batch_job_management():
    """示例：批量作业管理"""
    job_manager = get_batch_job_manager()

    # 定义一个模拟的批量处理函数
    async def simulate_data_processing(batch_data: list) -> list:
        """模拟数据处理"""
        await asyncio.sleep(0.1)  # 模拟处理时间
        return [{"processed": item, "timestamp": datetime.now()} for item in batch_data]

    # 定义作业完成回调
    async def job_completed(job_id: str, result: list | None, error: Exception | None):
        if error:
            logger.error(f"作业 {job_id} 失败: {error}")
        else:
            logger.info(f"作业 {job_id} 完成，处理了 {len(result) if result else 0} 条记录")

    # 提交批量作业
    test_data = list(range(5000))  # 5000条测试数据
    job_id = await job_manager.submit_batch_job("数据处理测试", simulate_data_processing, test_data, job_completed)

    logger.info(f"批量作业已提交: {job_id}")

    # 监控作业状态
    for _ in range(10):
        await asyncio.sleep(1)
        status = job_manager.get_job_status(job_id)
        if status:
            logger.info(f"作业 {job_id} 状态: {status['status']}")
        else:
            logger.info(f"作业 {job_id} 已完成")
            break

    return job_id


async def example_configure_batch_processor():
    """示例：配置批量处理器"""
    processor = get_batch_processor()

    logger.info("当前批量处理器配置:")
    logger.info(f"  批次大小: {processor.batch_size}")
    logger.info(f"  最大并发: {processor.max_concurrent}")

    # 调整配置以适应不同场景
    logger.info("调整批量处理器配置...")

    # 对于大数据量、内存敏感的场景
    processor.configure(batch_size=500, max_concurrent=2)

    logger.info("新的批量处理器配置:")
    logger.info(f"  批次大小: {processor.batch_size}")
    logger.info(f"  最大并发: {processor.max_concurrent}")


async def run_all_examples():
    """运行所有示例"""
    logger.info("开始批量操作功能演示")

    try:
        # 1. 配置批量处理器
        await example_configure_batch_processor()

        # 2. 批量创建用户
        await example_bulk_create_users()

        # 3. 批量更新用户
        await example_bulk_update_users()

        # 4. 批量创建日志
        await example_bulk_create_logs()

        # 5. 批量作业管理
        await example_batch_job_management()

        logger.info("所有批量操作示例完成")

    except Exception as e:
        logger.error(f"批量操作示例运行失败: {e}")


if __name__ == "__main__":
    asyncio.run(run_all_examples())
