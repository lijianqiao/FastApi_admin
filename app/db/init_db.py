"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: init_db.py
@DateTime: 2025/06/05
@Docs: 数据库初始化 - 创建超级管理员、基本权限、角色等（修复版）
"""

import asyncio

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import get_password_hash
from app.models.models import Permission, Role, User, role_permissions, user_roles
from app.utils.logger import get_logger

logger = get_logger(__name__)


class DatabaseInitializer:
    """数据库初始化器

    提供数据库清空、权限初始化、角色初始化、超级管理员初始化等功能
    """

    def __init__(self):
        """初始化数据库初始化器"""
        self.default_permissions = [
            # 用户管理权限
            {
                "code": "user:create",
                "name": "创建用户",
                "description": "创建新用户账户",
                "resource": "user",
                "action": "create",
            },
            {
                "code": "user:read",
                "name": "查看用户",
                "description": "查看用户信息",
                "resource": "user",
                "action": "read",
            },
            {
                "code": "user:update",
                "name": "更新用户",
                "description": "更新用户信息",
                "resource": "user",
                "action": "update",
            },
            {
                "code": "user:delete",
                "name": "删除用户",
                "description": "删除用户账户",
                "resource": "user",
                "action": "delete",
            },
            {
                "code": "user:list",
                "name": "用户列表",
                "description": "查看用户列表",
                "resource": "user",
                "action": "list",
            },
            # 角色管理权限
            {
                "code": "role:create",
                "name": "创建角色",
                "description": "创建新角色",
                "resource": "role",
                "action": "create",
            },
            {
                "code": "role:read",
                "name": "查看角色",
                "description": "查看角色信息",
                "resource": "role",
                "action": "read",
            },
            {
                "code": "role:update",
                "name": "更新角色",
                "description": "更新角色信息",
                "resource": "role",
                "action": "update",
            },
            {
                "code": "role:delete",
                "name": "删除角色",
                "description": "删除角色",
                "resource": "role",
                "action": "delete",
            },
            {
                "code": "role:list",
                "name": "角色列表",
                "description": "查看角色列表",
                "resource": "role",
                "action": "list",
            },
            {
                "code": "role:assign",
                "name": "分配角色",
                "description": "为用户分配角色",
                "resource": "role",
                "action": "assign",
            },
            # 权限管理权限
            {
                "code": "permission:create",
                "name": "创建权限",
                "description": "创建新权限",
                "resource": "permission",
                "action": "create",
            },
            {
                "code": "permission:read",
                "name": "查看权限",
                "description": "查看权限信息",
                "resource": "permission",
                "action": "read",
            },
            {
                "code": "permission:update",
                "name": "更新权限",
                "description": "更新权限信息",
                "resource": "permission",
                "action": "update",
            },
            {
                "code": "permission:delete",
                "name": "删除权限",
                "description": "删除权限",
                "resource": "permission",
                "action": "delete",
            },
            {
                "code": "permission:list",
                "name": "权限列表",
                "description": "查看权限列表",
                "resource": "permission",
                "action": "list",
            },
            {
                "code": "permission:assign",
                "name": "分配权限",
                "description": "为角色分配权限",
                "resource": "permission",
                "action": "assign",
            },
            # 系统管理权限
            {
                "code": "system:config",
                "name": "系统配置",
                "description": "管理系统配置",
                "resource": "system",
                "action": "config",
            },
            {
                "code": "system:monitor",
                "name": "系统监控",
                "description": "查看系统监控信息",
                "resource": "system",
                "action": "monitor",
            },
            {
                "code": "system:audit",
                "name": "审计日志",
                "description": "查看审计日志",
                "resource": "system",
                "action": "audit",
            },
        ]

        self.default_roles = [
            {
                "name": "超级管理员",
                "description": "拥有系统所有权限的超级管理员",
                "permissions": [p["code"] for p in self.default_permissions],  # 所有权限（使用code）
            },
            {
                "name": "管理员",
                "description": "系统管理员，拥有大部分管理权限",
                "permissions": [
                    "user:create",
                    "user:read",
                    "user:update",
                    "user:list",
                    "role:read",
                    "role:list",
                    "role:assign",
                    "permission:read",
                    "permission:list",
                    "system:monitor",
                    "system:audit",
                ],
            },
            {
                "name": "普通用户",
                "description": "普通用户，只有基本权限",
                "permissions": [
                    "user:read",  # 只能查看自己的信息
                ],
            },
        ]
        self.default_admin = {
            "username": settings.admin.username,
            "email": settings.admin.email,
            "password": settings.admin.password,
            "phone": settings.admin.phone,
            "nickname": settings.admin.nickname or settings.admin.username,
            "is_superuser": True,
            "is_active": True,
        }

    async def clear_database(self, session: AsyncSession) -> None:
        """清空数据库所有数据

        Args:
            session: 异步数据库会话

        Raises:
            Exception: 清空失败时抛出
        """
        logger.info("开始清空数据库...")

        try:
            # 1. 删除关联表数据
            await session.execute(delete(user_roles))
            await session.execute(delete(role_permissions))
            logger.info("清空关联表数据")

            # 2. 删除用户数据
            await session.execute(delete(User))
            logger.info("清空用户数据")

            # 3. 删除角色数据
            await session.execute(delete(Role))
            logger.info("清空角色数据")

            # 4. 删除权限数据
            await session.execute(delete(Permission))
            logger.info("清空权限数据")

            await session.commit()
            logger.info("数据库清空完成！")

        except Exception as e:
            logger.error(f"清空数据库失败: {str(e)}")
            await session.rollback()
            raise

    async def init_permissions(self, session: AsyncSession) -> dict[str, Permission]:
        """初始化权限

        Args:
            session: 异步数据库会话

        Returns:
            权限code到Permission对象的映射
        """
        logger.info("开始初始化权限...")

        permission_map = {}
        for perm_data in self.default_permissions:
            # 检查权限是否已存在
            result = await session.execute(select(Permission).where(Permission.code == perm_data["code"]))
            permission = result.scalar_one_or_none()

            if not permission:
                permission = Permission(
                    code=perm_data["code"],
                    name=perm_data["name"],
                    description=perm_data["description"],
                    resource=perm_data["resource"],
                    action=perm_data["action"],
                )
                session.add(permission)
                logger.info(f"创建权限: {perm_data['code']} - {perm_data['name']}")
            else:
                logger.info(f"权限已存在: {perm_data['code']}")

            permission_map[perm_data["code"]] = permission

        await session.commit()
        logger.info(f"权限初始化完成，共 {len(self.default_permissions)} 个权限")
        return permission_map

    async def init_roles(self, session: AsyncSession, permission_map: dict[str, Permission]) -> dict[str, Role]:
        """初始化角色

        Args:
            session: 异步数据库会话
            permission_map: 权限映射

        Returns:
            角色名到Role对象的映射
        """
        logger.info("开始初始化角色...")

        role_map = {}
        for role_data in self.default_roles:
            # 检查角色是否已存在 (使用name字段而不是code)
            result = await session.execute(select(Role).where(Role.name == role_data["name"]))
            role = result.scalar_one_or_none()

            if not role:
                role = Role(
                    name=role_data["name"],
                    description=role_data["description"],
                )
                session.add(role)
                logger.info(f"创建角色: {role_data['name']}")
            else:
                logger.info(f"角色已存在: {role_data['name']}")

            # 分配权限给角色
            for perm_code in role_data["permissions"]:
                if perm_code in permission_map:
                    permission = permission_map[perm_code]
                    if permission not in role.permissions:
                        role.permissions.append(permission)

            role_map[role_data["name"]] = role

        await session.commit()
        logger.info(f"角色初始化完成，共 {len(self.default_roles)} 个角色")
        return role_map

    async def init_admin_user(self, session: AsyncSession, role_map: dict[str, Role]) -> User:
        """初始化超级管理员用户

        Args:
            session: 异步数据库会话
            role_map: 角色映射

        Returns:
            创建或已存在的超级管理员用户对象
        """
        logger.info("开始初始化超级管理员...")

        # 检查管理员是否已存在
        result = await session.execute(select(User).where(User.username == self.default_admin["username"]))
        admin_user = result.scalar_one_or_none()

        if not admin_user:
            # 创建超级管理员
            hashed_password = get_password_hash(self.default_admin["password"])
            admin_user = User(
                username=self.default_admin["username"],
                email=self.default_admin["email"],
                phone=self.default_admin["phone"],
                password_hash=hashed_password,  # 使用正确的字段名
                nickname=self.default_admin["nickname"],
                is_superuser=self.default_admin["is_superuser"],
                is_active=self.default_admin["is_active"],
            )
            session.add(admin_user)
            await session.flush()  # 获取用户ID            # 分配超级管理员角色 (使用name而不是code)
            super_admin_role = role_map["超级管理员"]

            # 使用insert语句而不是关系操作，避免greenlet问题
            from sqlalchemy import insert

            await session.execute(insert(user_roles).values(user_id=admin_user.id, role_id=super_admin_role.id))

            await session.commit()
            logger.info(f"超级管理员创建成功: {self.default_admin['username']}")
            logger.warning(f"默认密码: {self.default_admin['password']} - 请及时修改！")
        else:
            logger.info("超级管理员已存在")

        return admin_user

    async def initialize_database(self, clear_first: bool = False) -> None:
        """执行完整的数据库初始化

        Args:
            clear_first: 是否先清空数据库

        Raises:
            Exception: 初始化失败时抛出
        """
        logger.info("开始数据库初始化...")

        # 直接创建异步引擎和会话
        from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

        engine = create_async_engine(str(settings.database_url), echo=settings.database_echo)
        async_session = async_sessionmaker(bind=engine, expire_on_commit=False)

        async with async_session() as session:
            try:
                # 可选：先清空数据库
                if clear_first:
                    await self.clear_database(session)

                # 1. 初始化权限
                permission_map = await self.init_permissions(session)

                # 2. 初始化角色
                role_map = await self.init_roles(session, permission_map)

                # 3. 初始化超级管理员
                admin_user = await self.init_admin_user(session, role_map)

                logger.info("数据库初始化完成！")
                logger.info("=" * 50)
                logger.info("初始化摘要:")
                logger.info(f"- 权限数量: {len(permission_map)}")
                logger.info(f"- 角色数量: {len(role_map)}")
                logger.info(f"- 超级管理员: {admin_user.username}")
                logger.info("=" * 50)

            except Exception as e:
                logger.error(f"数据库初始化失败: {str(e)}")
                await session.rollback()
                raise
            finally:
                await engine.dispose()

    async def reset_database(self) -> None:
        """重置数据库（清空并重新初始化）

        Raises:
            Exception: 重置失败时抛出
        """
        logger.info("开始重置数据库...")
        await self.initialize_database(clear_first=True)
        logger.info("数据库重置完成！")


async def init_database():
    """数据库初始化入口函数

    调用 DatabaseInitializer 完成初始化
    """
    initializer = DatabaseInitializer()
    await initializer.initialize_database()


async def reset_database():
    """数据库重置入口函数

    调用 DatabaseInitializer 完成重置
    """
    initializer = DatabaseInitializer()
    await initializer.reset_database()


if __name__ == "__main__":
    # 直接运行此文件进行数据库初始化
    import asyncio

    asyncio.run(init_database())
