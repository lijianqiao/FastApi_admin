"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: user_service_examples.py
@DateTime: 2025/07/08
@Docs: 用户服务层使用示例 - 展示如何使用 Pydantic schemas 进行数据校验和序列化
"""

from uuid import UUID, uuid4

from app.schemas.user import (
    UserBatchStatusRequest,
    UserCreateRequest,
    UserListRequest,
    UserPasswordResetRequest,
    UserPermissionAssignRequest,
    UserRoleAssignRequest,
    UserUpdateRequest,
)
from app.services.user import UserService


class UserServiceExamples:
    """用户服务使用示例"""

    def __init__(self):
        self.user_service = UserService()

    async def example_create_user(self):
        """示例：创建用户"""
        # 使用 Pydantic 模型进行数据校验
        user_data = UserCreateRequest(
            username="testuser",
            phone="13800138000",
            password="123456",
            nickname="测试用户",
            role_codes=["user"],
            is_active=True,
        )

        # 调用服务层方法，自动进行数据校验
        try:
            user_response = await self.user_service.create_user(
                user_data=user_data, current_user={"id": uuid4(), "username": "admin"}
            )
            print(f"创建用户成功: {user_response.username}")
            return user_response
        except Exception as e:
            print(f"创建用户失败: {e}")
            return None

    async def example_update_user(self, user_id: UUID):
        """示例：更新用户"""
        # 只更新部分字段，其他字段保持不变
        update_data = UserUpdateRequest(
            nickname="新昵称",
            version=1,  # 乐观锁版本号
        )

        try:
            user_response = await self.user_service.update_user(
                user_id=user_id, user_data=update_data, current_user={"id": uuid4(), "username": "admin"}
            )
            print(f"更新用户成功: {user_response.username}")
            return user_response
        except Exception as e:
            print(f"更新用户失败: {e}")
            return None

    async def example_get_user_list(self):
        """示例：获取用户列表"""
        # 使用 Pydantic 模型构建查询参数
        query = UserListRequest(
            page=1, page_size=10, keyword="test", is_active=True, sort_by="created_at", sort_order="desc"
        )

        try:
            list_response = await self.user_service.list_users(
                query=query, current_user={"id": uuid4(), "username": "admin"}
            )
            print(f"获取用户列表成功，共 {list_response.total} 条记录")
            return list_response
        except Exception as e:
            print(f"获取用户列表失败: {e}")
            return None

    async def example_get_user_detail(self, user_id: UUID):
        """示例：获取用户详情"""
        try:
            user_detail = await self.user_service.get_user_detail(
                user_id=user_id, current_user={"id": uuid4(), "username": "admin"}
            )
            if user_detail:
                print(f"获取用户详情成功: {user_detail.username}")
                return user_detail
            else:
                print("用户不存在")
                return None
        except Exception as e:
            print(f"获取用户详情失败: {e}")
            return None

    async def example_reset_password(self, user_id: UUID):
        """示例：重置密码"""
        # 使用 Pydantic 模型进行密码重置
        reset_data = UserPasswordResetRequest(new_password="newpassword123", force_change=True, version=1)

        try:
            success = await self.user_service.reset_password(
                user_id=user_id, reset_data=reset_data, current_user={"id": uuid4(), "username": "admin"}
            )
            if success:
                print("密码重置成功")
            else:
                print("密码重置失败")
            return success
        except Exception as e:
            print(f"密码重置异常: {e}")
            return False

    async def example_bulk_assign_roles(self, user_ids: list[UUID], role_ids: list[UUID]):
        """示例：批量分配角色"""
        # 使用 Pydantic 模型进行批量角色分配
        assign_data = UserRoleAssignRequest(
            target_ids=user_ids,
            assign_ids=role_ids,
            replace_all=False,  # 添加角色而不是替换所有角色
        )

        try:
            results = await self.user_service.assign_roles_bulk(
                assign_data=assign_data, current_user={"id": uuid4(), "username": "admin"}
            )
            success_count = sum(1 for success in results.values() if success)
            print(f"角色分配完成，成功: {success_count}，失败: {len(results) - success_count}")
            return results
        except Exception as e:
            print(f"批量分配角色失败: {e}")
            return {}

    async def example_bulk_assign_permissions(self, user_ids: list[UUID], permission_ids: list[UUID]):
        """示例：批量分配权限"""
        # 使用 Pydantic 模型进行批量权限分配
        assign_data = UserPermissionAssignRequest(
            target_ids=user_ids,
            assign_ids=permission_ids,
            replace_all=True,  # 替换所有权限
        )

        try:
            results = await self.user_service.assign_permissions_bulk(
                assign_data=assign_data, current_user={"id": uuid4(), "username": "admin"}
            )
            success_count = sum(1 for success in results.values() if success)
            print(f"权限分配完成，成功: {success_count}，失败: {len(results) - success_count}")
            return results
        except Exception as e:
            print(f"批量分配权限失败: {e}")
            return {}

    async def example_bulk_update_status(self, user_ids: list[UUID], is_active: bool):
        """示例：批量更新用户状态"""
        # 使用 Pydantic 模型进行批量状态更新
        status_data = UserBatchStatusRequest(user_ids=user_ids, is_active=is_active)

        try:
            result = await self.user_service.bulk_update_status(
                status_data=status_data, current_user={"id": uuid4(), "username": "admin"}
            )
            print(f"批量状态更新完成，成功: {result['success_count']}，失败: {result['failed_count']}")
            return result
        except Exception as e:
            print(f"批量更新状态失败: {e}")
            return None

    async def example_get_statistics(self):
        """示例：获取用户统计"""
        try:
            stats = await self.user_service.get_user_statistics()
            print(f"用户统计 - 总数: {stats.total_users}, 激活: {stats.active_users}, 未激活: {stats.inactive_users}")
            return stats
        except Exception as e:
            print(f"获取统计失败: {e}")
            return None

    async def example_search_users(self, keyword: str):
        """示例：搜索用户"""
        try:
            users = await self.user_service.search_users(keyword=keyword, is_active=True)
            print(f"搜索到 {len(users)} 个用户")
            return users
        except Exception as e:
            print(f"搜索用户失败: {e}")
            return []


# 使用示例
async def main():
    """主函数示例"""
    examples = UserServiceExamples()

    # 创建用户示例
    user_response = await examples.example_create_user()
    if user_response:
        user_id = user_response.id

        # 更新用户示例
        await examples.example_update_user(user_id)

        # 获取用户详情示例
        await examples.example_get_user_detail(user_id)

        # 重置密码示例
        await examples.example_reset_password(user_id)

    # 获取用户列表示例
    await examples.example_get_user_list()

    # 获取统计信息示例
    await examples.example_get_statistics()

    # 搜索用户示例
    await examples.example_search_users("test")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
