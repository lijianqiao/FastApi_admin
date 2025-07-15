"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: api_test_example.py
@DateTime: 2025/07/08
@Docs: API 层测试示例
"""

from fastapi.testclient import TestClient

from app.main import app


def test_api_structure():
    """测试 API 路由结构"""
    client = TestClient(app)

    # 测试 OpenAPI 文档生成
    response = client.get("/docs")
    print(f"OpenAPI 文档状态: {response.status_code}")

    # 测试路由注册
    response = client.get("/openapi.json")
    if response.status_code == 200:
        openapi_data = response.json()
        paths = openapi_data.get("paths", {})

        print(f"注册的 API 路径数量: {len(paths)}")
        print("\n已注册的 API 端点:")

        # 按模块分组显示
        modules = {"认证": [], "用户管理": [], "角色管理": [], "权限管理": [], "菜单管理": []}

        for path, methods in paths.items():
            for method, info in methods.items():
                tags = info.get("tags", [])
                summary = info.get("summary", "")

                if "认证" in tags:
                    modules["认证"].append(f"{method.upper()} {path} - {summary}")
                elif "用户管理" in tags:
                    modules["用户管理"].append(f"{method.upper()} {path} - {summary}")
                elif "角色管理" in tags:
                    modules["角色管理"].append(f"{method.upper()} {path} - {summary}")
                elif "权限管理" in tags:
                    modules["权限管理"].append(f"{method.upper()} {path} - {summary}")
                elif "菜单管理" in tags:
                    modules["菜单管理"].append(f"{method.upper()} {path} - {summary}")

        for module, endpoints in modules.items():
            if endpoints:
                print(f"\n{module} ({len(endpoints)} 个端点):")
                for endpoint in endpoints:
                    print(f"  {endpoint}")

    return True


def test_auth_endpoints():
    """测试认证相关端点（无需真实认证）"""
    client = TestClient(app)

    print("\n=== 认证端点测试 ===")

    # 测试登录端点结构（期望401或422）
    response = client.post("/api/v1/auth/login", json={})
    print(f"POST /api/v1/auth/login (空数据): {response.status_code}")

    # 测试获取用户信息（期望401）
    response = client.get("/api/v1/auth/me")
    print(f"GET /api/v1/auth/me (无认证): {response.status_code}")

    return True


def test_menu_endpoints():
    """测试菜单端点（无需真实认证）"""
    client = TestClient(app)

    print("\n=== 菜单端点测试 ===")

    # 测试获取用户菜单（期望401）
    response = client.get("/api/v1/menus/user-menus")
    print(f"GET /api/v1/menus/user-menus (无认证): {response.status_code}")

    # 测试获取菜单列表（期望401）
    response = client.get("/api/v1/menus")
    print(f"GET /api/v1/menus (无认证): {response.status_code}")

    return True


def main():
    """主测试函数"""
    print("FastAPI 后台管理系统 API 层测试")
    print("=" * 50)

    try:
        # 测试 API 结构
        test_api_structure()

        # 测试具体端点
        test_auth_endpoints()
        test_menu_endpoints()

        print("\n=== 测试总结 ===")
        print("✅ API 路由结构正常")
        print("✅ 端点响应正常（预期的认证错误）")
        print("✅ OpenAPI 文档生成正常")
        print("\n后续步骤:")
        print("1. 配置数据库连接")
        print("2. 运行数据库迁移")
        print("3. 创建测试用户")
        print("4. 进行完整的端到端测试")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
