#!/usr/bin/env python3
"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: dev.py
@DateTime: 2025/07/05
@Docs: 开发工具脚本
"""

import asyncio
import subprocess
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from app.utils.logger import logger


def run_server():
    """启动开发服务器"""
    logger.info("启动开发服务器...")
    subprocess.run(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--reload",
            "--host",
            "127.0.0.1",
            "--port",
            "8000",
            "--log-level",
            "info",
        ]
    )


def run_tests():
    """运行测试"""
    logger.info("运行测试...")
    subprocess.run([sys.executable, "-m", "pytest", "-v"])


def lint_code():
    """代码检查"""
    logger.info("运行代码检查...")
    subprocess.run([sys.executable, "-m", "ruff", "check", "."])


def format_code():
    """格式化代码"""
    logger.info("格式化代码...")
    subprocess.run([sys.executable, "-m", "ruff", "format", "."])


async def init_db():
    """初始化数据库"""
    logger.info("初始化数据库...")
    subprocess.run([sys.executable, "manage_db.py", "create"])


def show_help():
    """显示帮助信息"""
    print("开发工具脚本")
    print("用法: python dev.py <command>")
    print()
    print("可用命令:")
    print("  server    启动开发服务器")
    print("  test      运行测试")
    print("  lint      代码检查")
    print("  format    格式化代码")
    print("  initdb    初始化数据库")
    print("  help      显示此帮助信息")


def main():
    """主函数"""
    if len(sys.argv) < 2:
        show_help()
        return

    command = sys.argv[1]

    if command == "server":
        run_server()
    elif command == "test":
        run_tests()
    elif command == "lint":
        lint_code()
    elif command == "format":
        format_code()
    elif command == "initdb":
        asyncio.run(init_db())
    elif command == "help":
        show_help()
    else:
        logger.error(f"未知命令: {command}")
        show_help()


if __name__ == "__main__":
    main()
