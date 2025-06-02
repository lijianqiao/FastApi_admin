"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: __init__.py
@DateTime: 2025/06/02 02:32:03
@Docs: 仓储模块 - 数据访问层

提供统一的仓储基类和具体仓储实现
包含：
- BaseRepository: 企业级仓储基类
- 具体模型的仓储实现
"""

from app.repositories.base import BaseRepository

__all__ = [
    # 基础仓储类
    "BaseRepository",
]
