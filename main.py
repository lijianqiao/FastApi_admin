"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: main.py
@DateTime: 2025/06/05 09:06:43
@Docs: FastAPI应用入口 - 启动和配置核心功能
"""

if __name__ == "__main__":
    import uvicorn

    from app.config import settings
    from app.main import app

    # 启动FastAPI应用
    uvicorn.run(
        app,
        host=settings.server_host,
        port=settings.server_port,
        log_level=settings.log_level,
        reload=settings.debug,  # 开发模式下启用热重载
    )
