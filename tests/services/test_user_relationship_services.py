"""
用户关系管理服务层使用示例
演示如何使用 UserService 和 RoleService 中的关系管理方法
"""

import asyncio
from uuid import uuid4

from app.models.permission import Permission
from app.models.role import Role
from app.models.user import User
from app.services.role import RoleService
from app.services.user import UserService
from app.utils.deps import OperationContext


async def create_test_data():
    """创建测试数据"""
    # 创建测试用户
    test_user = User(
        id=uuid4(),
        username="test_service_user",
        email="test_service@example.com",
        phone="13800000099",
        password_hash="hashed_password",
        is_active=True,
        is_deleted=False,
    )
    await test_user.save()

    # 创建测试角色
    test_roles = []
    for i in range(3):
        role = Role(
            id=uuid4(),
            role_name=f"ServiceTestRole{i}",
            role_code=f"service_test_role_{i}",
            role_description=f"Service Test Role {i}",
            is_active=True,
            is_deleted=False,
        )
        await role.save()
        test_roles.append(role)

    # 创建测试权限
    test_permissions = []
    for i in range(5):
        permission = Permission(
            id=uuid4(),
            permission_name=f"ServiceTestPermission{i}",
            permission_code=f"service_test_perm_{i}",
            permission_type="API",
            resource_name=f"service_test_resource_{i}",
            is_active=True,
            is_deleted=False,
        )
        await permission.save()
        test_permissions.append(permission)

    return test_user, test_roles, test_permissions


async def test_user_service_role_management():
    """测试用户服务的角色管理功能"""
    print("=== 测试用户服务角色管理 ===")

    test_user, test_roles, test_permissions = await create_test_data()

    # 创建操作上下文（模拟当前登录用户）
    operation_context = OperationContext(user=test_user, request=None)

    user_service = UserService()

    try:
        # 测试全量设置角色
        print("1. 测试全量设置用户角色...")
        result = await user_service.assign_roles(test_user.id, [test_roles[0].id, test_roles[1].id], operation_context)
        print(f"   ✓ 用户 '{result.username}' 现在有 {len(result.roles)} 个角色")

        # 测试增量添加角色
        print("2. 测试增量添加用户角色...")
        result = await user_service.add_user_roles(test_user.id, [test_roles[2].id], operation_context)
        print(f"   ✓ 用户 '{result.username}' 现在有 {len(result.roles)} 个角色")

        # 测试获取用户角色
        print("3. 测试获取用户角色...")
        user_roles = await user_service.get_user_roles(test_user.id, operation_context)
        print(f"   ✓ 用户有 {len(user_roles)} 个角色: {[r['role_name'] for r in user_roles]}")

        # 测试移除角色
        print("4. 测试移除用户角色...")
        result = await user_service.remove_user_roles(test_user.id, [test_roles[0].id], operation_context)
        print(f"   ✓ 用户 '{result.username}' 现在有 {len(result.roles)} 个角色")

        # 测试用户权限管理
        print("5. 测试用户权限管理...")
        from app.schemas.user import UserAssignPermissionsRequest

        perm_request = UserAssignPermissionsRequest(permission_ids=[test_permissions[0].id, test_permissions[1].id])
        result = await user_service.assign_permissions_to_user(test_user.id, perm_request, operation_context)
        print(f"   ✓ 用户 '{result.username}' 现在有 {len(result.permissions)} 个权限")

        # 测试增量添加权限
        print("6. 测试增量添加用户权限...")
        result = await user_service.add_user_permissions(test_user.id, [test_permissions[2].id], operation_context)
        print(f"   ✓ 用户 '{result.username}' 现在有 {len(result.permissions)} 个权限")

        # 测试获取用户权限
        print("7. 测试获取用户权限...")
        user_permissions = await user_service.get_user_permissions(test_user.id, operation_context)
        print(f"   ✓ 用户有 {len(user_permissions)} 个直接权限")

    finally:
        # 清理测试数据
        await test_user.delete()
        for role in test_roles:
            await role.delete()
        for permission in test_permissions:
            await permission.delete()
        print("用户服务测试数据清理完成")


async def test_role_service_permission_management():
    """测试角色服务的权限管理功能"""
    print("\n=== 测试角色服务权限管理 ===")

    test_user, test_roles, test_permissions = await create_test_data()

    # 创建操作上下文
    operation_context = OperationContext(user=test_user, request=None)

    role_service = RoleService()

    try:
        # 测试全量设置角色权限
        print("1. 测试全量设置角色权限...")
        from app.schemas.role import RolePermissionAssignRequest

        perm_request = RolePermissionAssignRequest(
            permission_ids=[test_permissions[0].id, test_permissions[1].id, test_permissions[2].id]
        )
        result = await role_service.assign_permissions_to_role(test_roles[0].id, perm_request, operation_context)
        print(f"   ✓ 角色 '{result.role_name}' 现在有 {len(result.permissions)} 个权限")

        # 测试增量添加权限
        print("2. 测试增量添加角色权限...")
        result = await role_service.add_role_permissions(test_roles[0].id, [test_permissions[3].id], operation_context)
        print(f"   ✓ 角色 '{result.role_name}' 现在有 {len(result.permissions)} 个权限")

        # 测试获取角色权限
        print("3. 测试获取角色权限...")
        role_permissions = await role_service.get_role_permissions(test_roles[0].id, operation_context)
        print(f"   ✓ 角色有 {len(role_permissions)} 个权限: {[p['permission_name'] for p in role_permissions]}")

        # 测试移除权限
        print("4. 测试移除角色权限...")
        result = await role_service.remove_role_permissions(
            test_roles[0].id, [test_permissions[0].id], operation_context
        )
        print(f"   ✓ 角色 '{result.role_name}' 现在有 {len(result.permissions)} 个权限")

    finally:
        # 清理测试数据
        await test_user.delete()
        for role in test_roles:
            await role.delete()
        for permission in test_permissions:
            await permission.delete()
        print("角色服务测试数据清理完成")


async def main():
    """主测试函数"""
    print("开始测试用户关系管理服务层...")

    try:
        await test_user_service_role_management()
        await test_role_service_permission_management()
        print("\n🎉 所有服务层测试通过！")
    except Exception as e:
        print(f"\n❌ 服务层测试失败: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
