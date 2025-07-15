"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: auth_service_example.py
@DateTime: 2025/07/08
@Docs: 认证服务使用示例和测试
"""

import asyncio
from uuid import uuid4

from app.services.auth import auth_service


async def test_auth_service():
    """测试认证服务的主要功能"""

    print("=" * 50)
    print("认证服务功能测试")
    print("=" * 50)

    # 1. 测试密码相关功能
    print("\n1. 测试密码加密和验证")
    test_password = "test123456"
    from app.core.security import hash_password, verify_password

    hashed = hash_password(test_password)
    print(f"原密码: {test_password}")
    print(f"加密后: {hashed}")
    print(f"验证结果: {verify_password(test_password, hashed)}")

    # 2. 测试令牌创建和验证
    print("\n2. 测试JWT令牌")
    from app.core.security import create_access_token, verify_token

    token_data = {"sub": str(uuid4()), "username": "test_user", "is_superuser": False, "is_active": True}

    access_token = create_access_token(token_data)
    print(f"生成的访问令牌: {access_token[:50]}...")

    # 验证令牌
    payload = verify_token(access_token, "access")
    print(f"令牌验证结果: {payload}")

    # 3. 测试用户信息提取
    print("\n3. 测试从令牌提取用户信息")
    from app.core.security import extract_user_from_token

    user_info = extract_user_from_token(access_token)
    print(f"提取的用户信息: {user_info}")

    # 4. 模拟登录流程（需要有用户数据）
    print("\n4. 认证服务结构检查")
    print(f"认证服务初始化: {auth_service is not None}")
    print(f"用户DAO: {auth_service.user_dao is not None}")
    print(f"登录日志DAO: {auth_service.login_log_dao is not None}")

    # 5. 检查方法签名
    print("\n5. 认证服务方法列表:")
    methods = [
        method for method in dir(auth_service) if not method.startswith("_") and callable(getattr(auth_service, method))
    ]
    for method in methods:
        print(f"  - {method}")

    print("\n✅ 认证服务测试完成!")


if __name__ == "__main__":
    # 运行测试
    asyncio.run(test_auth_service())
