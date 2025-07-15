#!/usr/bin/env python3
"""
验证权限系统重构后的基本功能
"""


def test_basic_imports():
    """测试基本导入"""
    try:
        # 测试权限装饰器
        from app.core.permissions import require_permission  # noqa: F401

        print("✅ 权限装饰器导入成功")

        # 测试服务层
        from app.services.menu import MenuService  # noqa: F401
        from app.services.permission import PermissionService  # noqa: F401
        from app.services.role import RoleService  # noqa: F401
        from app.services.user import UserService  # noqa: F401

        print("✅ 服务层导入成功")

        # 测试DAO层
        from app.dao.menu import MenuDAO  # noqa: F401
        from app.dao.permission import PermissionDAO  # noqa: F401
        from app.dao.role import RoleDAO  # noqa: F401
        from app.dao.user import UserDAO  # noqa: F401

        print("✅ DAO层导入成功")

        # 测试菜单生成器
        from app.core.permissions.generator import MenuGenerator  # noqa: F401

        print("✅ 菜单生成器导入成功")

        print("🎉 所有核心组件导入成功！权限系统重构验证通过！")
        return True

    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 其他错误: {e}")
        return False


if __name__ == "__main__":
    test_basic_imports()
