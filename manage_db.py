#!/usr/bin/env python3
"""
-*- coding: utf-8 -*-
@Author: li
@Email: lijianqiao2906@live.com
@FileName: manage_db.py
@DateTime: 2025/06/16
@Docs: 数据库管理脚本
"""

import asyncio
import getpass
import sys

from tortoise import Tortoise

# # 添加项目根目录到Python路径
# sys.path.insert(0, str(Path(__file__).parent))
from app.core.config import settings
from app.core.security import SecurityManager
from app.dao.user import UserDAO
from app.db import check_database_connection, generate_schemas
from app.utils.logger import logger

# 导入权限初始化脚本
try:
    from scripts.permission_init import init_permission_system
except ImportError:
    init_permission_system = None
    logger.warning("无法导入权限初始化脚本 'scripts.permission_init'。'init' 命令将不可用。")


async def test_connection():
    """测试数据库连接"""
    logger.info("开始测试数据库连接...")
    is_connected = await check_database_connection()
    if is_connected:
        logger.info("✅ 数据库连接测试成功")
    else:
        logger.error("❌ 数据库连接测试失败")
    return is_connected


async def create_tables():
    """创建数据库表 (开发环境使用)"""
    logger.warning("警告: 此操作将生成数据库表结构")
    logger.warning("生产环境请使用: aerich upgrade")

    try:
        await generate_schemas()
        logger.info("✅ 数据库表结构生成成功")
    except Exception as e:
        logger.error(f"❌ 数据库表结构生成失败: {e}")


async def create_superuser(interactive: bool = True):
    """创建超级用户"""
    logger.info("--- 开始创建超级用户 ---")

    try:
        user_dao = UserDAO()

        # 非交互模式下使用默认配置
        if not interactive:
            username = settings.SUPERUSER_USERNAME
            phone = settings.SUPERUSER_PHONE
            password = settings.SUPERUSER_PASSWORD
            logger.info(f"非交互模式，使用默认配置创建超级用户 '{username}'。")
        else:
            # 获取用户输入或使用默认值
            print("创建超级用户 (按回车使用默认值)")
            print("-" * 40)

            # 用户名
            username_input = input(f"用户名 (默认: {settings.SUPERUSER_USERNAME}): ").strip()
            username = username_input if username_input else settings.SUPERUSER_USERNAME

            # 手机号
            phone_input = input(f"手机号 (默认: {settings.SUPERUSER_PHONE}): ").strip()
            phone = phone_input if phone_input else settings.SUPERUSER_PHONE

            # 密码
            password_input = getpass.getpass(f"密码 (默认: {settings.SUPERUSER_PASSWORD}): ")
            password = password_input if password_input else settings.SUPERUSER_PASSWORD

            # 确认密码 (如果用户输入了自定义密码)
            if password_input:
                password_confirm = getpass.getpass("确认密码: ")
                if password != password_confirm:
                    logger.error("❌ 两次输入的密码不一致")
                    return

            print("\n" + "-" * 40)
            print("即将创建的超级用户信息:")
            print(f"用户名: {username}")
            print(f"手机号: {phone}")
            print(f"昵称: {settings.SUPERUSER_NICKNAME}")
            print(f"密码: {'*' * len(password)}")
            print("-" * 40)

            confirm = input("确认创建? (y/N): ").strip().lower()
            if confirm not in ["y", "yes"]:
                logger.info("取消创建超级用户。")
                return

        # 检查用户是否已存在
        existing_user = await user_dao.get_by_username(username)
        if existing_user:
            logger.warning(f"用户 '{username}' 已存在，跳过创建。")
            return

        # 检查手机号是否已存在
        existing_phone = await user_dao.get_by_phone(phone)
        if existing_phone:
            logger.error(f"❌ 手机号 '{phone}' 已被使用")
            return

        # 创建超级用户
        security_manager = SecurityManager()
        hashed_password = security_manager.hash_password(password)

        user_data = {
            "username": username,
            "phone": phone,
            "nickname": settings.SUPERUSER_NICKNAME,
            "password_hash": hashed_password,
            "is_active": True,
            "is_superuser": True,
        }

        user = await user_dao.create(**user_data)
        if user:
            logger.info(f"✅ 超级用户 '{username}' 创建成功")
            logger.info(f"用户ID: {user.id}")
            logger.info(f"用户名: {user.username}")
            logger.info(f"手机号: {user.phone}")
            logger.info(f"昵称: {user.nickname}")
        else:
            logger.error("❌ 超级用户创建失败")

    except Exception as e:
        logger.error(f"❌ 创建超级用户失败: {e}")
    finally:
        # 关闭数据库连接
        try:
            await Tortoise.close_connections()
        except Exception:
            pass


async def init_system():
    """初始化整个系统：创建超级用户和权限数据"""
    if not init_permission_system:
        logger.error("初始化脚本 'permission_init.py' 未找到或导入失败。")
        return

    logger.info("======================================")
    logger.info("==   开始执行系统初始化流程   ==")
    logger.info("======================================")

    try:
        # 初始化数据库连接
        await Tortoise.init(config=settings.TORTOISE_ORM_CONFIG)

        # 1. 创建超级用户 (非交互模式)
        await create_superuser(interactive=False)

        # 2. 初始化权限系统
        await init_permission_system()

        logger.info("======================================")
        logger.info("==   ✅ 系统初始化成功   ==")
        logger.info("======================================")

    except Exception as e:
        logger.error(f"❌ 系统初始化过程中发生严重错误: {e}")
    finally:
        # 关闭数据库连接
        await Tortoise.close_connections()


async def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法:")
        print("  python manage_db.py test           # 测试数据库连接")
        print("  python manage_db.py create         # 创建数据库表 (开发环境)")
        print("  python manage_db.py createsuperuser # 创建超级用户")
        print("  python manage_db.py init           # 初始化系统 (创建超管和权限)")
        return

    command = sys.argv[1]

    if command == "test":
        await test_connection()
    elif command == "create":
        await create_tables()
    elif command == "createsuperuser":
        await create_superuser(interactive=True)
    elif command == "init":
        await init_system()
    else:
        logger.error(f"未知命令: {command}")


if __name__ == "__main__":
    asyncio.run(main())
