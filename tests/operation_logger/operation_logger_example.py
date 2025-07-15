"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: operation_logger_example.py
@DateTime: 2025/07/08
@Docs: 操作日志系统使用示例
"""

from app.utils.operation_logger import (
    get_operation_logger,
    log_create,
    log_delete,
    log_query,
    log_update,
    setup_default_handlers,
)


async def example_usage():
    """操作日志使用示例"""

    # 1. 设置默认处理器（数据库 + 控制台）
    setup_default_handlers()

    # 2. 启动日志工作器
    operation_logger = get_operation_logger()
    await operation_logger.start_worker()

    # 示例：在服务层使用装饰器
    @log_create("user")
    async def create_user(user_data: dict, current_user: dict):
        """创建用户示例"""
        # 模拟用户创建逻辑
        new_user = {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "username": user_data.get("username"),
            "email": user_data.get("email"),
        }
        return new_user

    @log_update("user")
    async def update_user(user_id: str, user_data: dict, current_user: dict):
        """更新用户示例"""
        # 模拟用户更新逻辑
        updated_user = {
            "id": user_id,
            "username": user_data.get("username"),
            "email": user_data.get("email"),
        }
        return updated_user

    @log_delete("user")
    async def delete_user(user_id: str, current_user: dict):
        """删除用户示例"""
        # 模拟用户删除逻辑
        return {"deleted": True, "id": user_id}

    @log_query("user")
    async def get_user_list(page: int = 1, size: int = 10, current_user: dict | None = None):
        """查询用户列表示例"""
        # 模拟用户查询逻辑
        return {
            "items": [
                {"id": "123", "username": "user1"},
                {"id": "456", "username": "user2"},
            ],
            "total": 2,
            "page": page,
            "size": size,
        }

    # 模拟当前用户
    current_user = {
        "id": "admin-123",
        "username": "admin",
        "is_superuser": True,
    }

    # 执行操作（这些操作会自动记录到数据库）
    try:
        # 创建用户
        user_data = {"username": "newuser", "email": "newuser@example.com"}
        new_user = await create_user(user_data, current_user)
        print(f"创建用户: {new_user}")

        # 更新用户
        update_data = {"username": "updateduser", "email": "updated@example.com"}
        updated_user = await update_user("123", update_data, current_user)
        print(f"更新用户: {updated_user}")

        # 查询用户
        user_list = await get_user_list(page=1, size=10, current_user=current_user)
        print(f"查询用户: {user_list}")

        # 删除用户
        delete_result = await delete_user("123", current_user)
        print(f"删除用户: {delete_result}")

    except Exception as e:
        print(f"操作失败: {e}")

    finally:
        # 停止日志工作器
        await operation_logger.stop_worker()


if __name__ == "__main__":
    import asyncio

    asyncio.run(example_usage())
