"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: types.py
@DateTime: 2025/07/06
@Docs: 通用类型别名定义
"""

import uuid
from typing import Any

# 基础数据类型
type ObjectUUID = uuid.UUID
type UserID = uuid.UUID
type StrOrNone = str | None
type IntOrNone = int | None

# Pydantic模型或字典相关类型
type ModelDict = dict[str, Any]
"""表示从Pydantic模型导出的字典"""
