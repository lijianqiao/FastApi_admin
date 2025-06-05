"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: main.py
@DateTime: 2025/06/05 09:06:43
@Docs: FastAPI应用入口 - 启动和配置核心功能
"""

import asyncio
import sys

from app.config import settings


async def init_database():
    """初始化数据库"""
    from app.db.init_db import init_database

    await init_database()


def main():
    """主函数"""
    import uvicorn

    # 检查命令行参数
    if len(sys.argv) > 1 and sys.argv[1] == "init-db":
        print("🚀 开始初始化数据库...")
        asyncio.run(init_database())
        print("✅ 数据库初始化完成！")
        return

    # 启动FastAPI应用
    uvicorn.run(
        "app.main:app",  # 使用导入字符串而不是应用对象
        host=settings.server_host,
        port=settings.server_port,
        log_level=settings.log_level.value.lower(),  # 转换为小写字符串
        reload=settings.debug,  # 开发模式下启用热重载
    )


if __name__ == "__main__":
    main()
