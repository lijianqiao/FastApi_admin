#!/usr/bin/env python3
"""
测试 schemas 模块导入
"""

# 测试基础模型导入
try:
    from app.models.schemas import ApiResponse, BaseSchema, PageQuery, PageResponse, TimestampMixin

    print("✓ 基础模型导入成功")
except ImportError as e:
    print(f"✗ 基础模型导入失败: {e}")

# 测试用户模型导入
try:
    from app.models.schemas import UserCreate, UserListQuery, UserResponse, UserUpdate

    print("✓ 用户模型导入成功")
except ImportError as e:
    print(f"✗ 用户模型导入失败: {e}")

# 测试角色模型导入
try:
    from app.models.schemas import RoleCreate, RoleListQuery, RoleResponse, RoleUpdate

    print("✓ 角色模型导入成功")
except ImportError as e:
    print(f"✗ 角色模型导入失败: {e}")

# 测试权限模型导入
try:
    from app.models.schemas import PermissionCreate, PermissionResponse, PermissionUpdate

    print("✓ 权限模型导入成功")
except ImportError as e:
    print(f"✗ 权限模型导入失败: {e}")

# 测试认证模型导入
try:
    from app.models.schemas import LoginRequest, LoginResponse, TokenResponse

    print("✓ 认证模型导入成功")
except ImportError as e:
    print(f"✗ 认证模型导入失败: {e}")

# 测试企业级功能模型导入
try:
    from app.models.schemas import (
        BackupCreate,
        BatchOperation,
        DashboardStats,
        DictTypeCreate,
        ExportQuery,
        ImportRequest,
        NotificationCreate,
        OperationLogQuery,
        SystemHealthResponse,
        TaskStatus,
    )

    print("✓ 企业级功能模型导入成功")
except ImportError as e:
    print(f"✗ 企业级功能模型导入失败: {e}")

# 测试创建一个用户实例
try:
    user_data = UserCreate(
        username="testuser",
        email="test@example.com",
        password="Password123!",
        confirm_password="Password123!",
        full_name="Test User",
    )
    print(f"✓ 用户创建模型实例化成功: {user_data.username}")
except Exception as e:
    print(f"✗ 用户创建模型实例化失败: {e}")

# 测试创建登录请求实例
try:
    login_data = LoginRequest(username="testuser", password="Password123!", remember_me=False)
    print(f"✓ 登录请求模型实例化成功: {login_data.username}")
except Exception as e:
    print(f"✗ 登录请求模型实例化失败: {e}")

print("\n所有测试完成！")
