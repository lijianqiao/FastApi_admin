"""
测试用户关系管理DAO方法
验证 UserDAO 中的用户-角色、用户-权限关系管理功能
"""

import asyncio
from uuid import uuid4

from app.dao.role import RoleDAO
from app.dao.user import UserDAO
from app.models.permission import Permission
from app.models.role import Role
from app.models.user import User


async def test_user_role_management():
    """测试用户-角色关系管理"""
    print("=== 测试用户-角色关系管理 ===")

    user_dao = UserDAO()

    # 创建测试用户
    test_user = User(
        id=uuid4(),
        username="test_user_roles",
        email="test_roles@example.com",
        phone="13800000001",
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
            role_name=f"TestRole{i}",
            role_code=f"test_role_{i}",
            role_description=f"Test Role {i}",
            is_active=True,
            is_deleted=False,
        )
        await role.save()
        test_roles.append(role)

    try:
        # 测试全量设置角色
        print("1. 测试全量设置角色...")
        await user_dao.set_user_roles(test_user.id, [role.id for role in test_roles[:2]])
        user_roles = await user_dao.get_user_roles(test_user.id)
        assert len(user_roles) == 2, f"期望2个角色，实际{len(user_roles)}个"
        print("   ✓ 全量设置角色成功")

        # 测试增量添加角色
        print("2. 测试增量添加角色...")
        await user_dao.add_user_roles(test_user.id, [test_roles[2].id])
        user_roles = await user_dao.get_user_roles(test_user.id)
        assert len(user_roles) == 3, f"期望3个角色，实际{len(user_roles)}个"
        print("   ✓ 增量添加角色成功")

        # 测试移除角色
        print("3. 测试移除角色...")
        await user_dao.remove_user_roles(test_user.id, [test_roles[0].id])
        user_roles = await user_dao.get_user_roles(test_user.id)
        assert len(user_roles) == 2, f"期望2个角色，实际{len(user_roles)}个"
        print("   ✓ 移除角色成功")

    finally:
        # 清理测试数据
        await test_user.delete()
        for role in test_roles:
            await role.delete()
        print("测试数据清理完成")


async def test_user_permission_management():
    """测试用户-权限关系管理"""
    print("\n=== 测试用户-权限关系管理 ===")

    user_dao = UserDAO()

    # 创建测试用户
    test_user = User(
        id=uuid4(),
        username="test_user_permissions",
        email="test_permissions@example.com",
        phone="13800000002",
        password_hash="hashed_password",
        is_active=True,
        is_deleted=False,
    )
    await test_user.save()

    # 创建测试权限
    test_permissions = []
    for i in range(3):
        permission = Permission(
            id=uuid4(),
            permission_name=f"TestPermission{i}",
            permission_code=f"test_perm_{i}",
            permission_type="API",
            resource_name=f"test_resource_{i}",
            is_active=True,
            is_deleted=False,
        )
        await permission.save()
        test_permissions.append(permission)

    try:
        # 测试全量设置权限
        print("1. 测试全量设置权限...")
        await user_dao.set_user_permissions(test_user.id, [perm.id for perm in test_permissions[:2]])
        user_permissions = await user_dao.get_user_permissions(test_user.id)
        assert len(user_permissions) == 2, f"期望2个权限，实际{len(user_permissions)}个"
        print("   ✓ 全量设置权限成功")

        # 测试增量添加权限
        print("2. 测试增量添加权限...")
        await user_dao.add_user_permissions(test_user.id, [test_permissions[2].id])
        user_permissions = await user_dao.get_user_permissions(test_user.id)
        assert len(user_permissions) == 3, f"期望3个权限，实际{len(user_permissions)}个"
        print("   ✓ 增量添加权限成功")

        # 测试移除权限
        print("3. 测试移除权限...")
        await user_dao.remove_user_permissions(test_user.id, [test_permissions[0].id])
        user_permissions = await user_dao.get_user_permissions(test_user.id)
        assert len(user_permissions) == 2, f"期望2个权限，实际{len(user_permissions)}个"
        print("   ✓ 移除权限成功")

    finally:
        # 清理测试数据
        await test_user.delete()
        for permission in test_permissions:
            await permission.delete()
        print("测试数据清理完成")


async def test_role_permission_management():
    """测试角色-权限关系管理"""
    print("\n=== 测试角色-权限关系管理 ===")

    role_dao = RoleDAO()

    # 创建测试角色
    test_role = Role(
        id=uuid4(),
        role_name="TestRolePermissions",
        role_code="test_role_perms",
        role_description="Test Role for Permissions",
        is_active=True,
        is_deleted=False,
    )
    await test_role.save()

    # 创建测试权限
    test_permissions = []
    for i in range(3):
        permission = Permission(
            id=uuid4(),
            permission_name=f"TestRolePermission{i}",
            permission_code=f"test_role_perm_{i}",
            permission_type="API",
            resource_name=f"test_resource_{i}",
            is_active=True,
            is_deleted=False,
        )
        await permission.save()
        test_permissions.append(permission)

    try:
        # 测试全量设置权限
        print("1. 测试全量设置权限...")
        await role_dao.set_permissions(test_role.id, [perm.id for perm in test_permissions[:2]])
        role_permissions = await role_dao.get_role_permissions(test_role.id)
        assert len(role_permissions) == 2, f"期望2个权限，实际{len(role_permissions)}个"
        print("   ✓ 全量设置权限成功")

        # 测试增量添加权限
        print("2. 测试增量添加权限...")
        await role_dao.add_permissions(test_role.id, [test_permissions[2].id])
        role_permissions = await role_dao.get_role_permissions(test_role.id)
        assert len(role_permissions) == 3, f"期望3个权限，实际{len(role_permissions)}个"
        print("   ✓ 增量添加权限成功")

        # 测试移除权限
        print("3. 测试移除权限...")
        await role_dao.remove_permissions(test_role.id, [test_permissions[0].id])
        role_permissions = await role_dao.get_role_permissions(test_role.id)
        assert len(role_permissions) == 2, f"期望2个权限，实际{len(role_permissions)}个"
        print("   ✓ 移除权限成功")

    finally:
        # 清理测试数据
        await test_role.delete()
        for permission in test_permissions:
            await permission.delete()
        print("测试数据清理完成")


async def main():
    """主测试函数"""
    print("开始测试用户关系管理DAO方法...")

    try:
        await test_user_role_management()
        await test_user_permission_management()
        await test_role_permission_management()
        print("\n🎉 所有测试通过！")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
