"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: base.py
@DateTime: 2025/06/02 02:11:38
@Docs: ORM基类 - 使用 advanced-alchemy 的基类，采用最小最优设计
"""

# 直接使用 advanced-alchemy 的基类
from advanced_alchemy.base import BigIntAuditBase, UUIDAuditBase

# 定义项目使用的基类别名
# 后台管理系统常用 UUID 作为主键，带审计字段
BaseModel = UUIDAuditBase

# 对于需要自增 ID 的场景（如日志表）
AutoIdModel = BigIntAuditBase

# 导出
__all__ = ["BaseModel", "AutoIdModel"]
