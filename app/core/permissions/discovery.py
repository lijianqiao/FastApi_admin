"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: discovery.py
@DateTime: 2025/01/01
@Docs: 权限自动发现器（简化版）
"""

import importlib
import inspect
import pkgutil
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.routing import APIRoute

from app.utils.logger import logger


class PermissionDiscovery:
    """权限自动发现器"""

    def __init__(self, app: FastAPI | None = None):
        self.app = app
        self.discovered_permissions: dict[str, dict[str, Any]] = {}
        self.route_permissions: dict[str, dict[str, Any]] = {}

    def discover_from_app(self, app: FastAPI | None = None) -> dict[str, dict[str, Any]]:
        """从FastAPI应用中发现权限

        Args:
            app: FastAPI应用实例

        Returns:
            发现的权限字典
        """
        if app is None:
            app = self.app

        if app is None:
            logger.warning("未提供FastAPI应用实例")
            return {}

        logger.info("开始从FastAPI应用中发现权限...")

        # 清空之前的发现结果
        self.discovered_permissions.clear()
        self.route_permissions.clear()

        # 遍历所有路由
        for route in app.routes:
            if isinstance(route, APIRoute):
                self._discover_route_permissions(route)

        logger.info(f"发现权限总数: {len(self.discovered_permissions)}")
        logger.info(f"路由权限总数: {len(self.route_permissions)}")

        return self.discovered_permissions

    def _discover_route_permissions(self, route: APIRoute) -> None:
        """从单个路由中发现权限"""
        try:
            endpoint = route.endpoint
            if not endpoint:
                return

            route_info = {
                "path": route.path,
                "methods": list(route.methods),
                "name": route.name,
                "module": endpoint.__module__,
                "function": endpoint.__name__,
                "tags": getattr(route, "tags", []),
                "summary": getattr(route, "summary", ""),
                "description": getattr(route, "description", ""),
            }

            # 检查单一权限
            required_permission = getattr(endpoint, "_required_permission", None)
            if required_permission:
                permission_info = {
                    **route_info,
                    "permission": required_permission,
                    "permission_type": "single",
                    "description": getattr(endpoint, "_permission_description", ""),
                }
                self.route_permissions[f"{route.path}:{','.join(route.methods)}"] = permission_info

                # 添加到发现的权限中
                if required_permission not in self.discovered_permissions:
                    self._add_discovered_permission(required_permission, permission_info)

            # 检查角色要求
            required_role = getattr(endpoint, "_required_role", None)
            if required_role:
                role_info = {
                    **route_info,
                    "role": required_role,
                    "permission_type": "role",
                    "description": getattr(endpoint, "_role_description", ""),
                }
                self.route_permissions[f"{route.path}:{','.join(route.methods)}:role"] = role_info

            # 检查多权限要求
            required_permissions = getattr(endpoint, "_required_permissions", None)
            if required_permissions:
                permission_logic = getattr(endpoint, "_permission_logic", "AND")
                multi_permission_info = {
                    **route_info,
                    "permissions": required_permissions,
                    "permission_type": "multiple",
                    "logic": permission_logic,
                    "description": getattr(endpoint, "_permission_description", ""),
                }
                self.route_permissions[f"{route.path}:{','.join(route.methods)}:multi"] = multi_permission_info

                # 添加所有权限到发现的权限中
                for permission in required_permissions:
                    if permission not in self.discovered_permissions:
                        self._add_discovered_permission(permission, multi_permission_info)

        except Exception as e:
            logger.error(f"发现路由权限失败 {route.path}: {e}")

    def _add_discovered_permission(self, permission: str, route_info: dict[str, Any]) -> None:
        """添加发现的权限到集合中"""
        # 解析权限码
        resource, action = self._parse_permission_code(permission)

        permission_info = {
            "permission": permission,
            "resource": resource,
            "action": action,
            "description": route_info.get("description", f"{action} {resource}"),
            "module": route_info.get("module", ""),
            "routes": [
                {
                    "path": route_info.get("path"),
                    "methods": route_info.get("methods"),
                    "name": route_info.get("name"),
                }
            ],
            "auto_discovered": True,
        }

        # 如果权限已存在，合并路由信息
        if permission in self.discovered_permissions:
            existing = self.discovered_permissions[permission]
            existing_routes = existing.get("routes", [])
            new_route = permission_info["routes"][0]
            if new_route not in existing_routes:
                existing_routes.append(new_route)
        else:
            self.discovered_permissions[permission] = permission_info

    def _parse_permission_code(self, permission: str) -> tuple[str, str]:
        """解析权限码为资源和动作

        Args:
            permission: 权限码，格式为 "resource:action"

        Returns:
            (resource, action) 元组
        """
        if ":" in permission:
            parts = permission.split(":", 1)
            return parts[0], parts[1]
        else:
            # 如果没有冒号，将整个字符串作为资源，动作为空
            return permission, ""

    def discover_from_modules(self, package_path: str) -> dict[str, dict[str, Any]]:
        """从指定包路径中发现权限

        Args:
            package_path: 包路径，如 "app.api.v1"

        Returns:
            发现的权限字典
        """
        logger.info(f"开始从模块中发现权限: {package_path}")

        try:
            # 导入包
            package = importlib.import_module(package_path)
            if package.__file__ is None:
                logger.error(f"无法获取包文件路径: {package_path}")
                return {}

            package_dir = Path(package.__file__).parent

            # 递归扫描所有模块
            for _, module_name, _ in pkgutil.walk_packages([str(package_dir)], package_path + "."):
                try:
                    module = importlib.import_module(module_name)
                    self._scan_module_for_permissions(module)
                except Exception as e:
                    logger.warning(f"扫描模块失败 {module_name}: {e}")

            logger.info(f"从模块发现权限总数: {len(self.discovered_permissions)}")
            return self.discovered_permissions

        except Exception as e:
            logger.error(f"从模块发现权限失败: {e}")
            return {}

    def _scan_module_for_permissions(self, module) -> None:
        """扫描单个模块中的权限"""
        try:
            # 扫描模块中的所有函数
            for _, obj in inspect.getmembers(module, inspect.isfunction):
                # 检查函数是否有权限装饰器
                self._check_function_permissions(obj, module.__name__)

        except Exception as e:
            logger.error(f"扫描模块权限失败 {module.__name__}: {e}")

    def _check_function_permissions(self, func, module_name: str) -> None:
        """检查函数的权限装饰器"""
        try:
            # 检查单一权限
            required_permission = getattr(func, "_required_permission", None)
            if required_permission:
                self._add_function_permission(required_permission, func, module_name, "single")

            # 检查多权限
            required_permissions = getattr(func, "_required_permissions", None)
            if required_permissions:
                for permission in required_permissions:
                    self._add_function_permission(permission, func, module_name, "multiple")

        except Exception as e:
            logger.error(f"检查函数权限失败 {func.__name__}: {e}")

    def _add_function_permission(self, permission: str, func, module_name: str, permission_type: str) -> None:
        """添加函数权限到发现集合"""
        resource, action = self._parse_permission_code(permission)

        permission_info = {
            "permission": permission,
            "resource": resource,
            "action": action,
            "description": getattr(func, "_permission_description", f"{action} {resource}"),
            "module": module_name,
            "function": func.__name__,
            "permission_type": permission_type,
            "auto_discovered": True,
        }

        if permission not in self.discovered_permissions:
            self.discovered_permissions[permission] = permission_info

    def get_permission_tree(self) -> dict[str, dict[str, list[str]]]:
        """构建权限树结构

        Returns:
            按资源分组的权限树
        """
        tree = {}

        for permission_code, permission_info in self.discovered_permissions.items():
            resource = permission_info.get("resource", "unknown")
            action = permission_info.get("action", "unknown")

            if resource not in tree:
                tree[resource] = {}

            if action not in tree[resource]:
                tree[resource][action] = []

            tree[resource][action].append(permission_code)

        return tree

    def get_permission_summary(self) -> dict[str, Any]:
        """获取权限发现摘要"""
        tree = self.get_permission_tree()

        return {
            "total_permissions": len(self.discovered_permissions),
            "total_resources": len(tree),
            "total_routes": len(self.route_permissions),
            "resources": list(tree.keys()),
            "permission_tree": tree,
            "auto_discovered_count": len(
                [p for p in self.discovered_permissions.values() if p.get("auto_discovered", False)]
            ),
        }

    def export_permissions(self, format: str = "dict") -> Any:
        """导出发现的权限

        Args:
            format: 导出格式，支持 "dict", "json", "yaml"

        Returns:
            导出的权限数据
        """
        if format == "dict":
            return self.discovered_permissions
        elif format == "json":
            import json

            return json.dumps(self.discovered_permissions, indent=2, ensure_ascii=False)
        elif format == "yaml":
            try:
                import yaml

                return yaml.dump(self.discovered_permissions, allow_unicode=True, indent=2)
            except ImportError:
                logger.error("需要安装PyYAML才能导出YAML格式")
                return self.discovered_permissions
        else:
            raise ValueError(f"不支持的导出格式: {format}")


def create_permission_discovery(app: FastAPI | None = None) -> PermissionDiscovery:
    """创建权限发现器实例"""
    return PermissionDiscovery(app)
