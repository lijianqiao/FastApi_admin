#!/usr/bin/env python3
"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: init_data.py
@DateTime: 2025/06/05
@Docs: 数据库初始化脚本 - 一键初始化系统基础数据
"""

import asyncio
import sys

from app.db.init_db import init_database, reset_database
from app.utils.logger import get_logger

logger = get_logger(__name__)


def print_help():
    """打印帮助信息"""
    print("\n" + "=" * 60)
    print("📚 数据库初始化工具")
    print("=" * 60)
    print("用法:")
    print("  python init_data.py              # 初始化数据库（保留现有数据）")
    print("  python init_data.py --reset      # 重置数据库（清空并重新初始化）")
    print("  python init_data.py --help       # 显示帮助信息")
    print()
    print("说明:")
    print("  • 初始化模式：只创建不存在的数据，保留现有数据")
    print("  • 重置模式：清空所有数据后重新初始化")
    print("=" * 60)


async def init_mode():
    """初始化模式"""
    try:
        logger.info("开始执行数据库初始化...")
        await init_database()
        logger.info("数据库初始化成功完成！")

        print("\n" + "=" * 60)
        print("🎉 数据库初始化完成！")
        print("=" * 60)
        print("📋 初始化内容:")
        print("   ✅ 基础权限（用户、角色、权限、系统管理）")
        print("   ✅ 默认角色（超级管理员、管理员、普通用户）")
        print("   ✅ 超级管理员账户")
        print()
        print("🔑 默认管理员账户:")
        print("   用户名: admin")
        print("   密码: admin@123")
        print("   ⚠️  请登录后立即修改默认密码！")
        print("=" * 60)

    except Exception as e:
        logger.error(f"数据库初始化失败: {str(e)}")
        print(f"\n❌ 初始化失败: {str(e)}")
        sys.exit(1)


async def reset_mode():
    """重置模式"""
    try:
        print("\n" + "⚠️" * 20)
        print("🚨 警告：即将清空数据库所有数据！")
        print("⚠️" * 20)
        print("此操作将删除:")
        print("  • 所有用户数据")
        print("  • 所有角色数据")
        print("  • 所有权限数据")
        print("  • 所有关联关系")
        print()

        # 确认操作
        confirm = input("确认要重置数据库吗？请输入 'YES' 确认: ")
        if confirm != "YES":
            print("❌ 操作已取消")
            return

        # 二次确认
        confirm2 = input("⚠️  最后确认，数据将无法恢复！请再次输入 'RESET' 确认: ")
        if confirm2 != "RESET":
            print("❌ 操作已取消")
            return

        logger.info("开始执行数据库重置...")
        await reset_database()
        logger.info("数据库重置成功完成！")

        print("\n" + "=" * 60)
        print("🎉 数据库重置完成！")
        print("=" * 60)
        print("📋 重置内容:")
        print("   🗑️  清空所有现有数据")
        print("   ✅ 重新创建基础权限")
        print("   ✅ 重新创建默认角色")
        print("   ✅ 重新创建超级管理员账户")
        print()
        print("🔑 默认管理员账户:")
        print("   用户名: admin")
        print("   密码: admin@123")
        print("   ⚠️  请登录后立即修改默认密码！")
        print("=" * 60)

    except Exception as e:
        logger.error(f"数据库重置失败: {str(e)}")
        print(f"\n❌ 重置失败: {str(e)}")
        sys.exit(1)


async def main():
    """主函数"""
    # 解析命令行参数
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ["--help", "-h", "help"]:
            print_help()
            return
        elif arg in ["--reset", "-r", "reset"]:
            await reset_mode()
            return
        else:
            print(f"❌ 未知参数: {sys.argv[1]}")
            print_help()
            return

    # 默认初始化模式
    await init_mode()


if __name__ == "__main__":
    asyncio.run(main())
