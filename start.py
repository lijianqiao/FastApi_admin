"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: start.py
@DateTime: 2025/06/16 23:26:59
@Docs: 主程序
"""

import uvicorn

from app.core.config import settings


def main():
    """主函数"""

    # 启动FastAPI应用
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        log_level=settings.LOG_LEVEL.lower(),
        reload=settings.DEBUG,
    )


if __name__ == "__main__":
    main()
