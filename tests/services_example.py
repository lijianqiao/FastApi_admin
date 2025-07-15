"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: services_example.py
@DateTime: 2025/07/08
@Docs: 服务层使用示例
"""

import asyncio
from datetime import datetime
from uuid import uuid4

from app.schemas.login_log import LoginLogCreateRequest, LoginLogListRequest
from app.schemas.menu import MenuCreateRequest
from app.schemas.operation_log import OperationLogCreateRequest, OperationLogListRequest
from app.schemas.permission import PermissionCreateRequest
from app.schemas.role import RoleCreateRequest, RoleListRequest
from app.schemas.system_config import SystemConfigCreateRequest
from app.services import (
    LoginLogService,
    MenuService,
    OperationLogService,
    PermissionService,
    RoleService,
    SystemConfigService,
)


async def demo_role_service():
    """演示角色服务的使用"""
    print("=== 角色服务示例 ===")

    role_service = RoleService()

    # 创建角色
    role_data = RoleCreateRequest(name="测试角色", code="test_role", description="这是一个测试角色", sort_order=1)

    try:
        # 这里需要数据库连接，实际使用时需要先初始化数据库
        # role = await role_service.create_role(role_data)
        # print(f"创建角色成功: {role.name}")

        # 查询角色列表
        query = RoleListRequest(page=1, page_size=10)
        # roles = await role_service.list_roles(query)
        # print(f"查询到 {roles.total} 个角色")

        print("角色服务示例完成")
    except Exception as e:
        print(f"角色服务示例失败: {e}")


async def demo_permission_service():
    """演示权限服务的使用"""
    print("=== 权限服务示例 ===")

    permission_service = PermissionService()

    # 创建权限
    permission_data = PermissionCreateRequest(
        name="用户管理", code="user:manage", resource_type="user", action="manage", description="用户管理权限"
    )

    try:
        # permission = await permission_service.create_permission(permission_data)
        # print(f"创建权限成功: {permission.name}")

        # 查询权限树
        # tree = await permission_service.get_permission_tree()
        # print(f"权限树包含 {len(tree.data)} 个顶级权限")

        print("权限服务示例完成")
    except Exception as e:
        print(f"权限服务示例失败: {e}")


async def demo_menu_service():
    """演示菜单服务的使用"""
    print("=== 菜单服务示例 ===")

    menu_service = MenuService()

    # 创建菜单
    menu_data = MenuCreateRequest(
        name="用户管理", path="/user", component="UserManagement", icon="user", sort_order=1, menu_type="menu"
    )

    try:
        # menu = await menu_service.create_menu(menu_data)
        # print(f"创建菜单成功: {menu.name}")

        # 查询菜单树
        # tree = await menu_service.get_menu_tree()
        # print(f"菜单树包含 {len(tree.data)} 个顶级菜单")

        print("菜单服务示例完成")
    except Exception as e:
        print(f"菜单服务示例失败: {e}")


async def demo_system_config_service():
    """演示系统配置服务的使用"""
    print("=== 系统配置服务示例 ===")

    config_service = SystemConfigService()

    # 创建配置
    config_data = SystemConfigCreateRequest(
        config_key="site_name",
        config_value="FastAPI Admin",
        config_type="string",
        group_name="基础配置",
        description="网站名称",
    )

    try:
        # config = await config_service.create_config(config_data)
        # print(f"创建配置成功: {config.config_key}")

        # 获取配置值
        # value = await config_service.get_config_value("site_name")
        # print(f"配置值: {value}")

        print("系统配置服务示例完成")
    except Exception as e:
        print(f"系统配置服务示例失败: {e}")


async def demo_operation_log_service():
    """演示操作日志服务的使用"""
    print("=== 操作日志服务示例 ===")

    log_service = OperationLogService()

    # 创建操作日志
    log_data = OperationLogCreateRequest(
        user_id=uuid4(),
        module="用户管理",
        action="创建用户",
        method="POST",
        path="/api/users",
        ip_address="127.0.0.1",
        response_code=200,
        response_time=150,
    )

    try:
        # log = await log_service.create_log(log_data)
        # print(f"创建操作日志成功: {log.action}")

        # 查询操作日志
        query = OperationLogListRequest(page=1, page_size=10)
        # logs = await log_service.list_logs(query)
        # print(f"查询到 {logs.total} 条操作日志")

        print("操作日志服务示例完成")
    except Exception as e:
        print(f"操作日志服务示例失败: {e}")


async def demo_login_log_service():
    """演示登录日志服务的使用"""
    print("=== 登录日志服务示例 ===")

    login_service = LoginLogService()

    # 创建登录日志
    login_data = LoginLogCreateRequest(
        user_id=uuid4(),
        login_type="password",
        ip_address="127.0.0.1",
        location="北京",
        device="Chrome Browser",
        is_success=True,
        login_at=datetime.now(),
    )

    try:
        # log = await login_service.create_login_log(login_data)
        # print(f"创建登录日志成功: {log.login_type}")

        # 查询登录日志
        query = LoginLogListRequest(page=1, page_size=10)
        # logs = await login_service.list_logs(query)
        # print(f"查询到 {logs.total} 条登录日志")

        print("登录日志服务示例完成")
    except Exception as e:
        print(f"登录日志服务示例失败: {e}")


async def main():
    """主函数"""
    print("FastAPI Admin 服务层使用示例")
    print("=" * 50)

    # 注意：以下示例需要先初始化数据库连接才能实际运行
    # 这里只是演示服务的使用方式

    await demo_role_service()
    print()

    await demo_permission_service()
    print()

    await demo_menu_service()
    print()

    await demo_system_config_service()
    print()

    await demo_operation_log_service()
    print()

    await demo_login_log_service()
    print()

    print("所有服务示例完成")


if __name__ == "__main__":
    # 运行示例
    asyncio.run(main())
